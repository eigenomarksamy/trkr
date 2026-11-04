// The snapshot.json each trkr run writes to its generation directory (src/snapshot.py).
// Numbers can be null where Yahoo gave no price.

export const SCHEMA = 'trkr-snapshot';
export const SCHEMA_VERSION = 1;

export type Source = 'local' | 'cloud' | null;

export interface Holding {
  symbol: string;
  exchange: string;
  amount: number;
  value: number;
  spending: number;
  spending_percent: number;
  profit_net: number;
  profit_percent: number;
  current_price: number;
  break_even_price: number;
  price25: number;
  price50: number;
  price75: number;
  price100: number;
  price150: number;
  realized_profit: number;
}

export interface Total {
  value: number;
  spending: number;
  profit_net: number;
  profit_percent: number;
  realized_profit: number;
  cash_out: number;
  time_interval_days: number;
  time_interval_months: number;
  time_interval_years: number;
  avg_day_roi: number;
  avg_month_roi: number;
  avg_year_roi: number;
}

export interface Transaction {
  type: string;
  date: string;
  quantity: number;
  fees: number;
  price: number;
  currency: string;
  symbol: string;
  exchange: string;
  platform: string;
  ex_rate: number;
  ex_fees: number;
}

export interface PricePoint {
  // YYYY-MM-DD. With lite history, a month's 1st stands for the month's last close.
  date: string;
  close: number | null;
}

export interface Portfolio {
  holdings: Holding[];
  total: Total;
  monthly_spending: { month: string; amount: number }[];
  // Market value of the holdings at each month end, through the run's month.
  valuation: { month: string; value: number | null }[];
  // Symbol -> YYYY-MM of its first buy.
  entry_points: Record<string, string>;
  transactions: Transaction[];
  // Ticker -> closes in the default currency, oldest first.
  prices: Record<string, PricePoint[]>;
}

export interface ImaginaryPortfolio extends Portfolio {
  name: string;
}

export interface ProjectionInputs {
  birth_year: number;
  retirement_age: number;
  // Percentages are whole numbers: 7 means 7%.
  yearly_return: number;
  // A fixed amount, 'portfolio' or an imaginary portfolio's name.
  start_net_worth: number | string;
  cash: number;
  income: number;
  income_growth: number;
  invest_percent: number;
  fees: number;
  inflation: number | null;
  // Calendar year -> amount; negative amounts are withdrawals.
  deposits_withdrawals: Record<string, number>;
}

export interface ProjectionRow {
  year: number;
  age: number;
  income: number;
  contribution: number;
  deposit_withdrawal: number;
  return_before_fees: number;
  net_worth_before_fees: number;
  return_after_fees: number;
  net_worth_after_fees: number;
  net_worth_real: number | null;
}

export interface ProjectionSnapshot {
  inputs: ProjectionInputs;
  start_year: number;
  start_value: number;
  start_label: string;
  invested_last_12_months: number;
  rows: ProjectionRow[];
}

export interface Snapshot {
  schema: typeof SCHEMA;
  schema_version: typeof SCHEMA_VERSION;
  // Local time of the run, without a zone: YYYY-MM-DDTHH:MM:SS.
  generated_at: string;
  config: {
    default_currency: string;
    history_variant: 'lite' | 'full';
    sources: { transactions: Source; symbols_map: Source; positions: Source };
  };
  // Symbol in the sheet -> Yahoo ticker. Empty with symbols-standard: yahoo.
  symbol_map: Record<string, string>;
  portfolio: Portfolio;
  imaginary: ImaginaryPortfolio[];
  projection: ProjectionSnapshot | null;
}

export class SnapshotError extends Error {}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function checkPortfolio(value: unknown, where: string): void {
  if (!isRecord(value)) throw broken(where);
  for (const key of ['holdings', 'monthly_spending', 'valuation', 'transactions']) {
    if (!Array.isArray(value[key])) throw broken(`${where}.${key}`);
  }
  for (const key of ['total', 'entry_points', 'prices']) {
    if (!isRecord(value[key])) throw broken(`${where}.${key}`);
  }
}

function broken(where: string): SnapshotError {
  return new SnapshotError(`this snapshot is incomplete: ${where} is missing or has the wrong type.`);
}

/** Parses a snapshot.json's text, or throws a SnapshotError that says what to do instead. */
export function parseSnapshot(text: string): Snapshot {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new SnapshotError(
      'this file is not JSON. open the snapshot.json that a trkr run writes to its generation directory.',
    );
  }
  if (!isRecord(data) || data.schema !== SCHEMA) {
    throw new SnapshotError(
      'this JSON file is not a trkr snapshot. open the snapshot.json that a trkr run writes to its generation directory.',
    );
  }
  const version = data.schema_version;
  if (version !== SCHEMA_VERSION) {
    const newer = typeof version === 'number' && version > SCHEMA_VERSION;
    throw new SnapshotError(
      `this snapshot has format version ${String(version)}, and this app reads version ${SCHEMA_VERSION}. ` +
        (newer ? 'update and redeploy the web app.' : 'run trkr again to write a new snapshot.'),
    );
  }
  if (typeof data.generated_at !== 'string' || Number.isNaN(Date.parse(data.generated_at))) {
    throw broken('generated_at');
  }
  if (!isRecord(data.config) || typeof data.config.default_currency !== 'string') {
    throw broken('config');
  }
  if (!isRecord(data.symbol_map)) throw broken('symbol_map');
  checkPortfolio(data.portfolio, 'portfolio');
  if (!Array.isArray(data.imaginary)) throw broken('imaginary');
  data.imaginary.forEach((portfolio, i) => checkPortfolio(portfolio, `imaginary[${i}]`));
  if (data.projection !== null) {
    if (!isRecord(data.projection) || !isRecord(data.projection.inputs) || !Array.isArray(data.projection.rows)) {
      throw broken('projection');
    }
  }
  return data as unknown as Snapshot;
}

/** The real portfolio for name '', else the imaginary portfolio of that name. */
export function portfolioNamed(snapshot: Snapshot, name: string): Portfolio | undefined {
  return name === '' ? snapshot.portfolio : snapshot.imaginary.find((p) => p.name === name);
}
