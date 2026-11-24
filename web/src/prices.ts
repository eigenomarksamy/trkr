// The page's side of the Worker's price route (src/yahoo.ts): a ticker's quote for market.ts.
// Only the ticker and a day are sent, to this site's own origin.

import type { Quote } from './market';

export class PriceError extends Error {}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Checks the route's answer, so market.ts gets the shape it expects. */
export function parseQuote(value: unknown, ticker: string): Quote {
  const broken = () => new PriceError(`the prices for ${ticker} came back incomplete.`);
  if (!isRecord(value) || typeof value.currency !== 'string' || typeof value.price !== 'number') throw broken();
  if (!Array.isArray(value.closes)) throw broken();
  const closes = value.closes.map((bar: unknown) => {
    if (!isRecord(bar) || typeof bar.date !== 'string' || (bar.close !== null && typeof bar.close !== 'number')) {
      throw broken();
    }
    return { date: bar.date, close: bar.close };
  });
  return { currency: value.currency, price: value.price, closes };
}

/** One ticker's weekly closes from from (YYYY-MM-DD) to today, and its price now. */
export async function fetchQuote(ticker: string, from: string): Promise<Quote> {
  const query = new URLSearchParams({ ticker, from });
  let response: Response;
  try {
    response = await fetch(`/api/prices?${query}`, { headers: { Accept: 'application/json' } });
  } catch {
    throw new PriceError(`the prices for ${ticker} could not be fetched. check the connection and try again.`);
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new PriceError(`the prices for ${ticker} could not be read (${response.status}).`);
  }
  if (!response.ok) {
    throw new PriceError(isRecord(body) && typeof body.error === 'string' ? body.error : `no prices for ${ticker} (${response.status}).`);
  }
  return parseQuote(body, ticker);
}
