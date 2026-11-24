// The Worker's price route, GET /api/prices?ticker=<t>&from=<YYYY-MM-DD>: one ticker's weekly
// closes from Yahoo's chart API, for a snapshot made in the browser (W11). It answers a Quote,
// the input market.ts takes. It sees a ticker and a date, never quantities, prices paid or fees,
// and it keeps nothing: Cloudflare's cache holds Yahoo's public answer for an hour.

import { TICKER, type Quote } from './market';

export { TICKER };
const DAY = /^\d{4}-\d{2}-\d{2}$/;
// The longest history asked for in one request.
export const MAX_YEARS = 50;
export const CACHE_SECONDS = 3600;
const DAY_SECONDS = 86_400;

const CHART = 'https://query1.finance.yahoo.com/v8/finance/chart/';
// Yahoo refuses requests without a browser-like user agent.
const USER_AGENT = 'Mozilla/5.0 (compatible; trkr)';

// Cloudflare's cache options on a Worker's fetch. Without a zone, as on workers.dev, they do nothing.
type CachedInit = RequestInit & { cf?: { cacheEverything: boolean; cacheTtlByStatus: Record<string, number> } };

const answer = (status: number, error: string) => Response.json({ error }, { status });

/** Seconds since the epoch of a YYYY-MM-DD day's start in UTC, or NaN when it is no day. */
function dayStart(day: string): number {
  if (!DAY.test(day)) return NaN;
  const [year, month, date] = [Number(day.slice(0, 4)), Number(day.slice(5, 7)), Number(day.slice(8, 10))];
  const ms = Date.UTC(year, month - 1, date);
  // Date.UTC rolls 2024-02-30 over into March, so a day that changed wasn't one.
  return new Date(ms).toISOString().slice(0, 10) === day ? ms / 1000 : NaN;
}

/** A bar's day where its exchange is, as yfinance dates it. */
function dayFormatter(timeZone: unknown, gmtoffset: unknown): (seconds: number) => string {
  if (typeof timeZone === 'string') {
    try {
      const format = new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' });
      return (seconds) => {
        const parts = Object.fromEntries(format.formatToParts(new Date(seconds * 1000)).map((p) => [p.type, p.value]));
        return `${parts.year}-${parts.month}-${parts.day}`;
      };
    } catch {
      // An unknown zone: fall back to the offset.
    }
  }
  const offset = typeof gmtoffset === 'number' && Number.isFinite(gmtoffset) ? gmtoffset : 0;
  return (seconds) => new Date((seconds + offset) * 1000).toISOString().slice(0, 10);
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
const finite = (value: unknown): number | null => (typeof value === 'number' && Number.isFinite(value) ? value : null);

/**
 * A Quote from Yahoo's chart answer, or null when it holds no ticker. Closes are adjusted for
 * splits and dividends, as yfinance's history is by default (auto_adjust).
 */
export function quoteFromChart(data: unknown, withCloses: boolean): Quote | null {
  if (!isRecord(data) || !isRecord(data.chart) || !Array.isArray(data.chart.result)) return null;
  const result: unknown = data.chart.result[0];
  if (!isRecord(result) || !isRecord(result.meta)) return null;
  const { meta } = result;
  const timestamps = Array.isArray(result.timestamp) ? result.timestamp : [];
  const indicators = isRecord(result.indicators) ? result.indicators : {};
  const series = (key: string, field: string): unknown[] | null => {
    const list = indicators[key];
    const first: unknown = Array.isArray(list) ? list[0] : undefined;
    return isRecord(first) && Array.isArray(first[field]) ? first[field] : null;
  };
  const values = series('adjclose', 'adjclose') ?? series('quote', 'close') ?? [];
  const day = dayFormatter(meta.exchangeTimezoneName, meta.gmtoffset);
  const closes = withCloses
    ? timestamps.flatMap((t: unknown, i) => (typeof t === 'number' ? [{ date: day(t), close: finite(values[i]) }] : []))
    : [];
  // yfinance takes today's price from the last daily close; the chart's meta carries it.
  const last = [...closes].reverse().find((bar) => bar.close !== null)?.close ?? null;
  const price = finite(meta.regularMarketPrice) ?? last;
  if (price === null) return null;
  return { currency: typeof meta.currency === 'string' ? meta.currency : '', price, closes };
}

/** GET /api/prices. now is the request's time, for the tests. */
export async function pricesRoute(request: Request, now: Date = new Date()): Promise<Response> {
  if (request.method !== 'GET') return answer(405, 'prices are only read, with GET.');
  // Browsers mark a request from the app's own page as same-origin. Anything else is refused,
  // so the route is no general proxy to Yahoo for other sites.
  if (request.headers.get('Sec-Fetch-Site') !== 'same-origin') {
    return answer(403, "prices are only for this site's own pages.");
  }
  const params = new URL(request.url).searchParams;
  const ticker = params.get('ticker') ?? '';
  const from = params.get('from') ?? '';
  if (!TICKER.test(ticker)) return answer(400, 'ticker should be a yahoo finance ticker, such as VWCE.DE or AAPL.');
  const start = dayStart(from);
  if (Number.isNaN(start)) return answer(400, 'from should be a day as YYYY-MM-DD.');

  // Like yfinance, history runs from the first day to today, today not included.
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) / 1000;
  if (start > today) return answer(400, 'from is after today.');
  if (start < today - MAX_YEARS * 365.25 * DAY_SECONDS) {
    return answer(400, `from is more than ${MAX_YEARS} years ago.`);
  }
  // A history that starts today is empty, as in the CLI, but Yahoo still needs a range.
  const withCloses = start < today;
  const period1 = withCloses ? start : today - 7 * DAY_SECONDS;
  const query = new URLSearchParams({
    period1: String(period1),
    period2: String(today),
    interval: '1wk',
    events: 'div,splits',
    includeAdjustedClose: 'true',
  });
  const init: CachedInit = {
    headers: { 'User-Agent': USER_AGENT, Accept: 'application/json' },
    // The URL changes once a day, so a cached answer is at most an hour old. Refusals aren't kept.
    cf: { cacheEverything: true, cacheTtlByStatus: { '200-299': CACHE_SECONDS, '404': CACHE_SECONDS, '429': 0, '500-599': 0 } },
  };

  let upstream: Response;
  try {
    upstream = await fetch(`${CHART}${encodeURIComponent(ticker)}?${query}`, init);
  } catch {
    return answer(502, `yahoo finance could not be reached for ${ticker}. try again later.`);
  }
  if (upstream.status === 404) return answer(404, `yahoo finance has no prices for ${ticker}.`);
  if (!upstream.ok) {
    return answer(502, `yahoo finance didn't answer for ${ticker} (${upstream.status}). try again later.`);
  }
  let data: unknown;
  try {
    data = await upstream.json();
  } catch {
    return answer(502, `yahoo finance gave an answer for ${ticker} that isn't JSON.`);
  }
  const quote = quoteFromChart(data, withCloses);
  if (!quote) return answer(404, `yahoo finance has no prices for ${ticker}.`);
  return Response.json(quote);
}
