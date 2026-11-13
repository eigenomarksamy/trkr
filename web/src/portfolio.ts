// The money math for a snapshot made in the browser: a port of Portfolio (src/portfolio_mngr.py)
// and portfolio_snapshot (src/snapshot.py), lite history only. A change to either needs the same
// change here. It walks the trades and adds up in the CLI's order, so the figures match to the
// last digit; test/portfolio.test.ts checks them against the CLI's golden snapshot.

import { monthOf, priceMarket, type Market, type Quote } from './market';
import type { Holding, Portfolio, Total, Transaction } from './snapshot';

export class TradeError extends Error {}

const DAY_MS = 86_400_000;

// The first and last trade dates, YYYY-MM-DD.
interface Span {
  first: string;
  last: string;
}

const paid = (t: Transaction) => (t.price * t.quantity + t.fees + t.ex_fees) / t.ex_rate;
const received = (t: Transaction) => (t.price * t.quantity - t.fees - t.ex_fees) / t.ex_rate;

// math.isclose with its default rel_tol: selling all of 0.1 + 0.2 bought sells 0.3.
const isClose = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(Math.abs(a), Math.abs(b));

// Months are YYYY-MM, days YYYY-MM-DD.
const yearOf = (month: string) => Number(month.slice(0, 4));
const monthNumber = (month: string) => Number(month.slice(5, 7));

function nextMonth(month: string): string {
  const [year, m] = [yearOf(month), monthNumber(month)];
  return m === 12 ? `${year + 1}-01` : `${year}-${String(m + 1).padStart(2, '0')}`;
}

function lastDay(month: string): string {
  const days = new Date(Date.UTC(yearOf(month), monthNumber(month), 0)).getUTCDate();
  return `${month}-${String(days).padStart(2, '0')}`;
}

function daysBetween(from: string, to: string): number {
  const utc = (day: string) => Date.UTC(Number(day.slice(0, 4)), Number(day.slice(5, 7)) - 1, Number(day.slice(8, 10)));
  return Math.round((utc(to) - utc(from)) / DAY_MS);
}

function emptyHolding(symbol: string, exchange: string): Holding {
  return {
    symbol,
    exchange,
    amount: 0,
    value: 0,
    spending: 0,
    spending_percent: 0,
    profit_net: 0,
    profit_percent: 0,
    current_price: 0,
    break_even_price: 0,
    price25: 0,
    price50: 0,
    price75: 0,
    price100: 0,
    price150: 0,
    realized_profit: 0,
  };
}

/** Portfolio.calculate: average cost, walked by date. Only what is still held is listed. */
function holdingsAndTotal(trades: Transaction[], span: Span, market: Market, today: string): { holdings: Holding[]; total: Total } {
  const walked = new Map<string, Holding>();
  for (const t of trades) {
    let holding = walked.get(t.symbol);
    if (!holding) {
      holding = emptyHolding(t.symbol, t.exchange);
      walked.set(t.symbol, holding);
    }
    if (t.type === 'buy') {
      holding.amount += t.quantity;
      holding.spending += paid(t);
    } else if (t.type === 'sell') {
      const held = holding.amount;
      let cost: number;
      if (isClose(t.quantity, held)) {
        cost = holding.spending;
        holding.amount = 0;
      } else if (t.quantity < held) {
        cost = (holding.spending * t.quantity) / held;
        holding.amount -= t.quantity;
      } else {
        throw new TradeError(`the sell of ${t.quantity} ${t.symbol} on ${t.date} is more than the ${held} held.`);
      }
      holding.spending -= cost;
      holding.realized_profit += received(t) - cost;
    }
  }

  const total: Total = {
    value: 0,
    spending: 0,
    profit_net: 0,
    profit_percent: 0,
    realized_profit: 0,
    cash_out: 0,
    time_interval_days: 0,
    time_interval_months: 0,
    time_interval_years: 0,
    avg_day_roi: 0,
    avg_month_roi: 0,
    avg_year_roi: 0,
  };
  const holdings: Holding[] = [];
  for (const holding of walked.values()) {
    total.realized_profit += holding.realized_profit;
    if (holding.amount === 0) continue;
    const price = market.price.get(holding.symbol) ?? NaN;
    holding.current_price = price;
    holding.value = holding.amount * price;
    holding.break_even_price = holding.spending / holding.amount;
    holding.profit_net = holding.value - holding.spending;
    holding.profit_percent = holding.spending !== 0 ? (holding.profit_net / holding.spending) * 100 : 0;
    holding.price25 = holding.break_even_price * 1.25;
    holding.price50 = holding.break_even_price * 1.5;
    holding.price75 = holding.break_even_price * 1.75;
    holding.price100 = holding.break_even_price * 2;
    holding.price150 = holding.break_even_price * 2.5;
    holdings.push(holding);
    total.value += holding.value;
    total.spending += holding.spending;
  }
  for (const holding of holdings) {
    holding.spending_percent = total.spending !== 0 ? (holding.spending / total.spending) * 100 : 0;
  }

  total.profit_net = total.value - total.spending;
  total.profit_percent = total.spending !== 0 ? (total.profit_net / total.spending) * 100 : 0;
  total.cash_out = total.value * 0.95;
  total.time_interval_days = daysBetween(span.first, today);
  total.time_interval_months = total.time_interval_days / 30;
  total.time_interval_years = total.time_interval_days / 365;
  if (total.time_interval_days > 0) {
    total.avg_day_roi = total.profit_percent / total.time_interval_days;
    total.avg_month_roi = total.avg_day_roi * 30;
    total.avg_year_roi = total.avg_day_roi * 365;
  }
  return { holdings, total };
}

/** compute_spending_history: what buys cost in each month, from the first trade's to the last's. */
function monthlySpending(trades: Transaction[], span: Span): Portfolio['monthly_spending'] {
  const rows: Portfolio['monthly_spending'] = [];
  const last = monthOf(span.last);
  for (let month = monthOf(span.first); month <= last; month = nextMonth(month)) {
    let amount = 0;
    for (const t of trades) if (t.type === 'buy' && monthOf(t.date) === month) amount += paid(t);
    rows.push({ month, amount });
  }
  return rows;
}

/** get_entry_points_months: the month of each symbol's first buy. */
function entryPoints(trades: Transaction[]): Record<string, string> {
  const entries: Record<string, string> = {};
  for (const t of trades) if (t.type === 'buy' && !(t.symbol in entries)) entries[t.symbol] = monthOf(t.date);
  return entries;
}

/**
 * compute_historical_valuation: the market value of the holdings at each month end, through
 * this month. A month without a close takes the one before it, or else today's price.
 */
function valuation(trades: Transaction[], span: Span, market: Market, today: string): Portfolio['valuation'] {
  const rows: Portfolio['valuation'] = [];
  const held = new Map<string, number>();
  const lastClose = new Map<string, number>();
  let next = 0;
  for (let month = monthOf(span.first); month <= monthOf(today); month = nextMonth(month)) {
    const end = lastDay(month);
    for (; next < trades.length; next++) {
      const t = trades[next];
      if (t === undefined || t.date > end) break;
      if (t.type === 'buy') held.set(t.symbol, (held.get(t.symbol) ?? 0) + t.quantity);
      else if (t.type === 'sell') held.set(t.symbol, (held.get(t.symbol) ?? 0) - t.quantity);
    }
    for (const [ticker, closes] of market.history) {
      const close = closes.get(month);
      if (close !== undefined) lastClose.set(ticker, close);
    }
    let value = 0;
    for (const [symbol, quantity] of held) value += quantity * (lastClose.get(symbol) ?? market.price.get(symbol) ?? NaN);
    rows.push({ month, value });
  }
  return rows;
}

/**
 * A snapshot's portfolio from trades and Yahoo quotes. Symbols are Yahoo tickers; quotes must
 * also hold the currency pair of each currency that isn't target. today is YYYY-MM-DD, local.
 */
export function buildPortfolio(trades: Transaction[], quotes: Map<string, Quote>, target: string, today: string): Portfolio {
  // Average cost depends on the order of the trades. The sort is stable, so trades on the same
  // day keep the order they were entered in.
  const sorted = [...trades].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const first = sorted[0]?.date;
  const last = sorted[sorted.length - 1]?.date;
  if (first === undefined || last === undefined) throw new TradeError('add at least one trade.');
  const span = { first, last };
  // In the order they first appear, like get_symbols_of_interest.
  const tickers = [...new Set(trades.map((t) => t.symbol))];
  const market = priceMarket(tickers, quotes, target, today);
  return {
    ...holdingsAndTotal(sorted, span, market, today),
    monthly_spending: monthlySpending(sorted, span),
    valuation: valuation(sorted, span, market, today),
    entry_points: entryPoints(sorted),
    transactions: sorted.map((t) => ({ ...t })),
    prices: Object.fromEntries(
      tickers.map((ticker) => [
        ticker,
        [...(market.history.get(ticker) ?? [])]
          .sort(([a], [b]) => (a < b ? -1 : 1))
          .map(([month, close]) => ({ date: `${month}-01`, close })),
      ]),
    ),
  };
}
