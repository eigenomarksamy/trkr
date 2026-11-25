// Trades typed or pasted into the app, and the snapshot made from them (W11). Trades are checked as the
// CLI reads a transactions CSV (Transaction in src/transactions.py), kept in this browser's
// storage, and download as a transactions CSV the CLI reads too. Pricing them sends only each
// ticker and the first trade's day to the Worker's price route. No DOM here.

import { readRows } from './csv';
import { toCsv, type Download } from './download';
import { pairsFor, TICKER, type Quote } from './market';
import { buildPortfolio } from './portfolio';
import { SCHEMA, SCHEMA_VERSION, type Snapshot, type Transaction } from './snapshot';

/** trkr's column order for a transactions CSV: the CLI reads the columns by position. */
export const COLUMNS = ['type', 'date', 'quantity', 'fees', 'price', 'currency', 'symbol', 'exchange', 'platform', 'ex_rate', 'ex_fees'] as const;
export type Column = (typeof COLUMNS)[number];
export type TradeFields = Record<Column, string>;

export interface TradeProblem {
  column: Column;
  message: string;
}

const DAY = /^\d{4}-\d{2}-\d{2}$/;
const CURRENCY = /^[A-Za-z]{3}$/;
// What Python's float() reads, less inf and nan: digits with an optional dot and exponent.
const NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/;
// A spreadsheet reads a cell that starts like this as a formula.
const FORMULA_START = /^[=+\-@]/;
const MAX_TEXT = 40;

/** Today in this browser, YYYY-MM-DD. */
export function localDay(now: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** The time of a run as snapshot.py writes it: local, YYYY-MM-DDTHH:MM:SS, no zone. */
function localTime(now: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${localDay(now)}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function isDay(text: string): boolean {
  if (!DAY.test(text)) return false;
  const ms = Date.UTC(Number(text.slice(0, 4)), Number(text.slice(5, 7)) - 1, Number(text.slice(8, 10)));
  return new Date(ms).toISOString().slice(0, 10) === text;
}

export function checkCurrency(text: string): string | null {
  return CURRENCY.test(text.trim()) ? null : 'the default currency should be a three-letter code, such as EUR or USD.';
}

/**
 * A trade from the form's text, or what is wrong with it. Empty fees and ex_fees are 0 and an
 * empty ex_rate is 1, as in the guide's example. today is YYYY-MM-DD.
 */
export function checkTrade(fields: TradeFields, today: string): Transaction | TradeProblem[] {
  const problems: TradeProblem[] = [];
  const text = (column: Column) => fields[column].trim();
  const problem = (column: Column, message: string) => problems.push({ column, message });

  const type = text('type').toLowerCase();
  if (type !== 'buy' && type !== 'sell') problem('type', 'type should be buy or sell.');

  const date = text('date');
  if (!isDay(date)) problem('date', 'date should be a day, as YYYY-MM-DD.');
  else if (date > today) problem('date', 'date is after today, and a trade needs prices from its day on.');

  const number = (column: Column, empty: number | null, ok: (n: number) => boolean, rule: string): number => {
    const value = text(column);
    if (value === '' && empty !== null) return empty;
    const parsed = NUMBER.test(value) ? Number(value) : NaN;
    if (!Number.isFinite(parsed)) {
      problem(column, `${column} should be a number, written with a dot for decimals.`);
    } else if (!ok(parsed)) {
      problem(column, `${column} ${rule}.`);
    }
    return parsed;
  };
  const quantity = number('quantity', null, (n) => n > 0, 'should be more than 0');
  const price = number('price', null, (n) => n >= 0, "can't be negative");
  const fees = number('fees', 0, (n) => n >= 0, "can't be negative");
  const exRate = number('ex_rate', 1, (n) => n > 0, 'should be more than 0');
  const exFees = number('ex_fees', 0, (n) => n >= 0, "can't be negative");

  const currency = text('currency').toUpperCase();
  if (!CURRENCY.test(currency)) problem('currency', 'currency should be a three-letter code, such as EUR or USD.');

  const symbol = text('symbol').toUpperCase();
  if (!TICKER.test(symbol)) problem('symbol', 'symbol should be a yahoo finance ticker, such as VWCE.DE or AAPL.');

  const label = (column: Column): string => {
    const value = text(column);
    if (value.length > MAX_TEXT) problem(column, `${column} should be at most ${MAX_TEXT} characters.`);
    else if (FORMULA_START.test(value)) problem(column, `${column} can't start with =, +, - or @, which spreadsheets read as a formula.`);
    else if (/[\r\n\t]/.test(value)) problem(column, `${column} should be one line.`);
    return value;
  };
  const exchange = label('exchange');
  const platform = label('platform');

  if (problems.length > 0) return problems;
  return { type, date, quantity, fees, price, currency, symbol, exchange, platform, ex_rate: exRate, ex_fees: exFees };
}

/** The form's text for a trade, to edit it. */
export function tradeFields(trade: Transaction): TradeFields {
  return Object.fromEntries(COLUMNS.map((column) => [column, String(trade[column])])) as TradeFields;
}

/** A row of trades in bulk that reads as a trade, with the line it starts on. */
export interface BulkTrade {
  line: number;
  trade: Transaction;
}

/** A row of trades in bulk that doesn't, and why. */
export interface BulkProblem {
  line: number;
  source: string;
  problems: string[];
}

export interface Bulk {
  /** Whether the first row was a header, and so left out. */
  header: boolean;
  good: BulkTrade[];
  bad: BulkProblem[];
}

// A header names its columns, so none of these three cells reads as a trade's. A first row
// that is a bad trade, such as a dividend on a day, still reads as a row and is flagged.
function isHeader(cells: string[]): boolean {
  const cell = (column: Column) => (cells[COLUMNS.indexOf(column)] ?? '').trim();
  return !/^(buy|sell)$/i.test(cell('type')) && !DAY.test(cell('date')) && !NUMBER.test(cell('quantity'));
}

/**
 * Trades pasted or opened as a file (W11b): rows in trkr's column order, comma- or
 * tab-separated, with a header or without. Each row is checked as the form checks a trade.
 * Empty cells after the eleventh are allowed, as a spreadsheet adds them. The CLI ignores
 * extra cells, but one with a value usually means the columns are in another order, so it's flagged.
 */
export function readTrades(text: string, today: string): Bulk {
  const rows = readRows(text);
  const header = rows[0] !== undefined && isHeader(rows[0].cells);
  const bulk: Bulk = { header, good: [], bad: [] };
  for (const row of header ? rows.slice(1) : rows) {
    const flag = (problems: string[]) => bulk.bad.push({ line: row.line, source: row.source, problems });
    if (!row.closed) {
      flag(['a quote opens and never closes, so the rest of the text was read as one cell.']);
      continue;
    }
    let width = row.cells.length;
    while (width > COLUMNS.length && row.cells[width - 1]!.trim() === '') width -= 1;
    if (width !== COLUMNS.length) {
      flag([`it has ${width} ${width === 1 ? 'column' : 'columns'}, and a trade has ${COLUMNS.length}, in this order: ${COLUMNS.join(', ')}.`]);
      continue;
    }
    const fields = Object.fromEntries(COLUMNS.map((column, index) => [column, row.cells[index]!])) as TradeFields;
    const result = checkTrade(fields, today);
    if (Array.isArray(result)) flag(result.map((problem) => problem.message));
    else bulk.good.push({ line: row.line, trade: result });
  }
  return bulk;
}

/** Trades in date order. The sort is stable, so a day's trades keep the order they were added in. */
export function byDate(trades: Transaction[]): Transaction[] {
  return [...trades].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
}

/** The trades as a transactions CSV, in trkr's column order, for the CLI or for later. */
export function tradesCsv(trades: Transaction[], today: string): Download {
  const name = `trkr-transactions-${today}.csv`;
  return {
    name,
    path: name,
    label: 'transactions.csv',
    mime: 'text/csv',
    data: toCsv([...COLUMNS], byDate(trades).map((t) => COLUMNS.map((column) => t[column]))),
  };
}

/** A snapshot as a file to open again later, here or anywhere the app runs. */
export function snapshotFile(snapshot: Snapshot): Download {
  const name = `trkr-snapshot-${snapshot.generated_at.slice(0, 10)}.json`;
  return { name, path: name, label: 'snapshot.json', mime: 'application/json', data: JSON.stringify(snapshot, null, 1) + '\n' };
}

// Storage: the trades and the default currency, on this device only.
const KEPT = 'trkr.trades';

export interface Kept {
  currency: string;
  trades: Transaction[];
}

function isTrade(value: unknown, today: string): value is Transaction {
  if (typeof value !== 'object' || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!COLUMNS.every((column) => typeof record[column] === 'string' || typeof record[column] === 'number')) return false;
  return !Array.isArray(checkTrade(tradeFields(record as unknown as Transaction), today));
}

/** The trades kept on this device, without any that no longer read. */
export function loadKept(storage: Pick<Storage, 'getItem'> | undefined, today: string): Kept {
  const empty = { currency: 'EUR', trades: [] };
  try {
    const stored = storage?.getItem(KEPT);
    if (!stored) return empty;
    const data = JSON.parse(stored) as { currency?: unknown; trades?: unknown };
    const currency = typeof data.currency === 'string' && !checkCurrency(data.currency) ? data.currency : 'EUR';
    const trades = Array.isArray(data.trades) ? data.trades.filter((t): t is Transaction => isTrade(t, today)) : [];
    return { currency, trades };
  } catch {
    return empty;
  }
}

/** Keeps the trades on this device. False when the browser refuses, as when storage is full. */
export function saveKept(storage: Pick<Storage, 'setItem' | 'removeItem'> | undefined, kept: Kept): boolean {
  try {
    if (!storage) return false;
    if (kept.trades.length === 0 && kept.currency === 'EUR') storage.removeItem(KEPT);
    else storage.setItem(KEPT, JSON.stringify(kept));
    return true;
  } catch {
    return false;
  }
}

export type FetchQuote = (ticker: string, from: string) => Promise<Quote>;

/** Runs fetches a few at a time, in the order given. */
async function fetchAll(tickers: string[], from: string, fetchQuote: FetchQuote, quotes: Map<string, Quote>, progress: (ticker: string) => void): Promise<void> {
  const queue = [...tickers];
  const worker = async () => {
    for (let ticker = queue.shift(); ticker !== undefined; ticker = queue.shift()) {
      progress(ticker);
      quotes.set(ticker, await fetchQuote(ticker, from));
    }
  };
  await Promise.all(Array.from({ length: Math.min(4, queue.length) }, worker));
}

/**
 * A snapshot of the trades, as a CLI run with these settings would write it: lite history,
 * Yahoo tickers as symbols, no symbol map, no positions, imaginary portfolios or projection.
 * Each ticker, then each currency pair, is priced from the first trade's day. Throws
 * PriceError, MarketError or TradeError with a message for the page.
 */
export async function makeSnapshot(
  trades: Transaction[],
  currency: string,
  fetchQuote: FetchQuote,
  now: Date,
  progress: (ticker: string) => void = () => undefined,
): Promise<Snapshot> {
  const target = currency.trim().toUpperCase();
  const sorted = byDate(trades);
  const from = sorted[0]?.date;
  const quotes = new Map<string, Quote>();
  if (from !== undefined) {
    const tickers = [...new Set(sorted.map((t) => t.symbol))];
    await fetchAll(tickers, from, fetchQuote, quotes, progress);
    const pairs = pairsFor(quotes.values(), target).filter((pair) => !quotes.has(pair));
    await fetchAll(pairs, from, fetchQuote, quotes, progress);
  }
  return {
    schema: SCHEMA,
    schema_version: SCHEMA_VERSION,
    generated_at: localTime(now),
    config: {
      default_currency: target,
      history_variant: 'lite',
      sources: { transactions: 'browser', symbols_map: null, positions: null },
    },
    symbol_map: {},
    portfolio: buildPortfolio(trades, quotes, target, localDay(now)),
    imaginary: [],
    projection: null,
  };
}
