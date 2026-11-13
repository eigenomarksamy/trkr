// Prices for a snapshot made in the browser: a port of MarketDataYahoo's lite (weekly) history
// and of convert_currencies (src/market_mngr.py). A change to either needs the same change here.
// test/portfolio.test.ts checks the port against the CLI's golden snapshot.

/** One ticker's prices from Yahoo, in its own currency. The Worker's price route answers these. */
export interface Quote {
  // Yahoo's code, which can be a minor unit such as GBp.
  currency: string;
  // The latest price.
  price: number;
  // Weekly bars, oldest first, each dated with its Monday (YYYY-MM-DD).
  closes: { date: string; close: number | null }[];
}

/** Current prices and month-end closes, all in the default currency. */
export interface Market {
  price: Map<string, number>;
  // Ticker -> YYYY-MM -> the month's last close.
  history: Map<string, Map<string, number>>;
}

export class MarketError extends Error {}

// Yahoo quotes some listings in a minor unit, such as most London listings in pence.
const MINOR_UNITS: Record<string, [string, number]> = {
  GBp: ['GBP', 100],
  GBX: ['GBP', 100],
  ZAc: ['ZAR', 100],
  ILA: ['ILS', 100],
};

export const monthOf = (day: string): string => day.slice(0, 7);

/** The Yahoo ticker whose price is one unit of currency in target. */
export function rateTicker(currency: string, target: string): string {
  return `${currency}${target}=X`;
}

function unitOf(currency: string): [string, number] {
  return MINOR_UNITS[currency] ?? [currency.toUpperCase(), 1];
}

/**
 * Month -> the last close in it. The month of today gets today's price when it has no bar yet:
 * weekly bars carry their Monday, so a month has none before its first Monday (bug 13).
 */
function liteHistory(quote: Quote, today: string): Map<string, number> {
  const history = new Map<string, number>();
  for (const bar of quote.closes) {
    // The CLI would carry a missing close into its sums; here the bar is skipped instead.
    if (bar.close !== null && Number.isFinite(bar.close)) history.set(monthOf(bar.date), bar.close);
  }
  const month = monthOf(today);
  if (!history.has(month)) history.set(month, quote.price);
  return history;
}

/**
 * Prices tickers in target. Each currency is converted with its own pair, such as USDEUR=X for
 * USD into EUR, which quotes must hold too. A month uses the pair's close for that month, or
 * the current rate when the pair has none.
 */
export function priceMarket(tickers: string[], quotes: Map<string, Quote>, target: string, today: string): Market {
  const want = target.toUpperCase();
  const loaded = new Map<string, { quote: Quote; history: Map<string, number> }>();
  const load = (ticker: string) => {
    let entry = loaded.get(ticker);
    if (!entry) {
      const quote = quotes.get(ticker);
      if (!quote) throw new MarketError(`there are no prices for ${ticker}.`);
      entry = { quote, history: liteHistory(quote, today) };
      loaded.set(ticker, entry);
    }
    return entry;
  };

  const market: Market = { price: new Map(), history: new Map() };
  for (const ticker of tickers) {
    const { quote, history } = load(ticker);
    if (!quote.currency) throw new MarketError(`yahoo gave no currency for ${ticker}, so it can't be converted.`);
    const [currency, units] = unitOf(quote.currency);
    let rateNow = 1;
    let rates = new Map<string, number>();
    if (currency !== want) {
      const pair = load(rateTicker(currency, want));
      rateNow = pair.quote.price;
      rates = pair.history;
    }
    const factor = (month: string) => (rates.get(month) ?? rateNow) / units;
    market.price.set(ticker, quote.price * (rateNow / units));
    market.history.set(ticker, new Map([...history].map(([month, close]) => [month, close * factor(month)])));
  }
  return market;
}
