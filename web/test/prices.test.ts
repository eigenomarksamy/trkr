import { afterEach, describe, expect, it, vi } from 'vitest';
import { priceMarket } from '../src/market';
import { fetchQuote, parseQuote, PriceError } from '../src/prices';
import worker, { type Env } from '../src/worker';
import { MAX_YEARS, pricesRoute, quoteFromChart, TICKER } from '../src/yahoo';

// The Worker's clock in these tests: 2025-01-29, a Wednesday.
const NOW = new Date(Date.UTC(2025, 0, 29, 15, 30));
const TODAY_S = Date.UTC(2025, 0, 29) / 1000;
const H = 3600;

// A made-up answer from Yahoo's chart API, in its shape: weekly bars stamped at midnight in
// Berlin, which is 23:00 UTC the day before.
function chart(meta: Record<string, unknown> = {}, adjclose: (number | null)[] | null = [10, null, 12.5, 13]) {
  const timestamp = [Date.UTC(2025, 0, 5, 23) / 1000, Date.UTC(2025, 0, 12, 23) / 1000, Date.UTC(2025, 0, 19, 23) / 1000, Date.UTC(2025, 0, 26, 23) / 1000];
  return {
    chart: {
      result: [
        {
          meta: { currency: 'EUR', symbol: 'AAA.DE', exchangeTimezoneName: 'Europe/Berlin', gmtoffset: H, regularMarketPrice: 13.2, ...meta },
          timestamp,
          indicators: {
            quote: [{ close: [11, 11.5, 12.9, 13.4] }],
            ...(adjclose ? { adjclose: [{ adjclose }] } : {}),
          },
        },
      ],
      error: null,
    },
  };
}

const request = (query: string, headers: Record<string, string> = { 'Sec-Fetch-Site': 'same-origin' }, method = 'GET') =>
  new Request(`https://trkr.example/api/prices?${query}`, { headers, method });

function stubYahoo(response: Response | (() => Promise<Response>)) {
  const calls: { url: string; init: RequestInit & { cf?: unknown } }[] = [];
  vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return typeof response === 'function' ? response() : response.clone();
  });
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('price route', () => {
  it('answers a quote with adjusted weekly closes dated where the exchange is', async () => {
    const calls = stubYahoo(Response.json(chart()));
    const response = await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      currency: 'EUR',
      price: 13.2,
      closes: [
        { date: '2025-01-06', close: 10 },
        { date: '2025-01-13', close: null },
        { date: '2025-01-20', close: 12.5 },
        { date: '2025-01-27', close: 13 },
      ],
    });
    expect(calls).toHaveLength(1);
    const url = new URL(calls[0]!.url);
    expect(url.origin + url.pathname).toBe('https://query1.finance.yahoo.com/v8/finance/chart/AAA.DE');
    expect(Object.fromEntries(url.searchParams)).toEqual({
      period1: String(Date.UTC(2025, 0, 6) / 1000),
      period2: String(TODAY_S),
      interval: '1wk',
      events: 'div,splits',
      includeAdjustedClose: 'true',
    });
    expect(calls[0]!.init.cf).toMatchObject({ cacheEverything: true, cacheTtlByStatus: { '200-299': 3600, '429': 0 } });
  });

  it('sends nothing but the ticker and the dates', async () => {
    const calls = stubYahoo(Response.json(chart()));
    await pricesRoute(request('ticker=AAA.DE&from=2025-01-06&quantity=10&price=99'), NOW);
    expect(calls[0]!.url).not.toMatch(/quantity|price|99/);
  });

  it('encodes a currency pair in the path', async () => {
    const calls = stubYahoo(Response.json(chart({ currency: 'EUR', exchangeTimezoneName: 'Europe/London', gmtoffset: 0 })));
    await pricesRoute(request('ticker=USDEUR%3DX&from=2025-01-06'), NOW);
    expect(calls[0]!.url).toContain('/chart/USDEUR%3DX?');
  });

  it('falls back to the unadjusted close, the last close and the offset', async () => {
    stubYahoo(Response.json(chart({ regularMarketPrice: undefined, exchangeTimezoneName: 'Not/AZone' }, null)));
    const quote = await (await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW)).json();
    expect(quote.price).toBe(13.4);
    expect(quote.closes.map((bar: { date: string }) => bar.date)).toEqual(['2025-01-06', '2025-01-13', '2025-01-20', '2025-01-27']);
    expect(quote.closes[0].close).toBe(11);
  });

  it('gives no closes for a history that starts today, as the CLI does', async () => {
    const calls = stubYahoo(Response.json(chart()));
    const quote = await (await pricesRoute(request('ticker=AAA.DE&from=2025-01-29'), NOW)).json();
    expect(quote).toEqual({ currency: 'EUR', price: 13.2, closes: [] });
    expect(new URL(calls[0]!.url).searchParams.get('period1')).toBe(String(TODAY_S - 7 * 86_400));
  });

  it('refuses requests not from its own pages, and other methods', async () => {
    const calls = stubYahoo(Response.json(chart()));
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06', {}), NOW)).status).toBe(403);
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06', { 'Sec-Fetch-Site': 'cross-site' }), NOW)).status).toBe(403);
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06', { 'Sec-Fetch-Site': 'same-site' }), NOW)).status).toBe(403);
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06', undefined, 'POST'), NOW)).status).toBe(405);
    expect(calls).toHaveLength(0);
  });

  it('takes only ticker-shaped input and days in range', async () => {
    const calls = stubYahoo(Response.json(chart()));
    for (const query of [
      'from=2025-01-06',
      'ticker=&from=2025-01-06',
      'ticker=..%2Fquote&from=2025-01-06',
      'ticker=https%3A%2F%2Fevil.example&from=2025-01-06',
      'ticker=AAA%20B&from=2025-01-06',
      `ticker=${'A'.repeat(25)}&from=2025-01-06`,
      'ticker=AAA.DE',
      'ticker=AAA.DE&from=2025-1-6',
      'ticker=AAA.DE&from=2025-02-30',
      'ticker=AAA.DE&from=2025-01-30',
      `ticker=AAA.DE&from=${2025 - MAX_YEARS - 1}-01-01`,
    ]) {
      const response = await pricesRoute(request(query), NOW);
      expect(response.status, query).toBe(400);
      expect((await response.json()).error).toMatch(/^[a-z]/);
    }
    expect(calls).toHaveLength(0);
    for (const ticker of ['VWCE.DE', 'BRK-B', 'USDEUR=X', '^GSPC', 'M&M.NS', 'BTC-USD', 'IWDA.L']) expect(TICKER.test(ticker)).toBe(true);
  });

  it('says when yahoo has no such ticker or refuses', async () => {
    stubYahoo(Response.json({ chart: { result: null, error: { code: 'Not Found' } } }, { status: 404 }));
    const missing = await pricesRoute(request('ticker=NOPE&from=2025-01-06'), NOW);
    expect(missing.status).toBe(404);
    expect((await missing.json()).error).toBe('yahoo finance has no prices for NOPE.');

    stubYahoo(new Response('Too Many Requests', { status: 429 }));
    const refused = await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW);
    expect(refused.status).toBe(502);
    expect((await refused.json()).error).toContain('(429)');

    stubYahoo(() => Promise.reject(new TypeError('network down')));
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW)).status).toBe(502);

    stubYahoo(new Response('<html>', { status: 200 }));
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW)).status).toBe(502);

    stubYahoo(Response.json({ chart: { result: [], error: null } }));
    expect((await pricesRoute(request('ticker=AAA.DE&from=2025-01-06'), NOW)).status).toBe(404);
  });

  it('is served by the worker with its headers, never cached by the browser', async () => {
    stubYahoo(Response.json(chart()));
    const env: Env = { ASSETS: { fetch: async () => new Response('asset') } };
    const response = await worker.fetch(request('ticker=AAA.DE&from=2025-01-06'), env);
    expect(response.status).toBe(200);
    expect(response.headers.get('Cache-Control')).toBe('no-store');
    expect(response.headers.get('X-Frame-Options')).toBe('DENY');
  });

  it("gives market.ts what it prices with", () => {
    const quote = quoteFromChart(chart(), true)!;
    const market = priceMarket(['AAA.DE'], new Map([['AAA.DE', quote]]), 'EUR', '2025-01-29');
    expect(market.price.get('AAA.DE')).toBe(13.2);
    expect([...market.history.get('AAA.DE')!]).toEqual([['2025-01', 13]]);
  });
});

describe('the page asking for prices', () => {
  it('asks its own origin with the ticker and day only, and checks the answer', async () => {
    const urls: string[] = [];
    vi.stubGlobal('fetch', async (url: string) => {
      urls.push(url);
      return Response.json({ currency: 'GBp', price: 101, closes: [{ date: '2025-01-06', close: 99 }] });
    });
    expect(await fetchQuote('IWDA.L', '2025-01-06')).toEqual({ currency: 'GBp', price: 101, closes: [{ date: '2025-01-06', close: 99 }] });
    expect(urls).toEqual(['/api/prices?ticker=IWDA.L&from=2025-01-06']);
  });

  it("passes on the route's message", async () => {
    vi.stubGlobal('fetch', async () => Response.json({ error: 'yahoo finance has no prices for NOPE.' }, { status: 404 }));
    await expect(fetchQuote('NOPE', '2025-01-06')).rejects.toThrow(new PriceError('yahoo finance has no prices for NOPE.'));
    vi.stubGlobal('fetch', async () => new Response('bad gateway', { status: 502 }));
    await expect(fetchQuote('AAA', '2025-01-06')).rejects.toThrow('could not be read (502)');
    vi.stubGlobal('fetch', () => Promise.reject(new TypeError('offline')));
    await expect(fetchQuote('AAA', '2025-01-06')).rejects.toThrow('check the connection');
  });

  it('refuses an answer of the wrong shape', () => {
    for (const bad of [null, {}, { currency: 'EUR', price: '1', closes: [] }, { currency: 'EUR', price: 1 }, { currency: 'EUR', price: 1, closes: [{ date: 1, close: 1 }] }, { currency: 'EUR', price: 1, closes: [{ date: '2025-01-06', close: '1' }] }]) {
      expect(() => parseQuote(bad, 'AAA')).toThrow(PriceError);
    }
  });
});
