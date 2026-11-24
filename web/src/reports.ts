// What each page reports, as data (W12): tables of raw values, the charts' options, notes.
// The downloads are made from it (report-files.ts), and the pages take their charts from
// it, so a downloaded chart is the one on screen. No DOM here.

import type { ChartSpec, ColumnChartOptions, LineChartOptions } from './chart';
import type { Cell } from './download';
import { dayDate, dayLabel, money, monthDate, monthLabel, number, percent, quantity, runTime } from './format';
import { projectionProblem, projectNetWorth, resolveStartValue } from './projection';
import type { Holding, Portfolio, ProjectionInputs, ProjectionRow, Snapshot, Transaction } from './snapshot';

// How a column's raw value is shown. The CSV keeps the raw value.
export type Kind =
  | 'text'
  | 'money'
  | 'signed-money'
  | 'percent'
  | 'signed-percent'
  | 'quantity'
  | 'number'
  | 'price'
  | 'rate'
  | 'day'
  | 'month'
  // A YYYY-MM-DD that stands for its month: lite history's month-end closes.
  | 'month-day'
  | 'run';

export interface Column {
  label: string;
  kind: Kind;
}

export interface Table {
  title: string;
  columns: Column[];
  rows: Cell[][];
  // A totals row: shown under the table, left out of the CSV.
  footer?: Cell[];
}

export type Part =
  | { kind: 'table'; table: Table }
  // A one-row table, shown as a list of figures.
  | { kind: 'facts'; table: Table }
  | { kind: 'chart'; title: string; chart: ChartSpec }
  | { kind: 'note'; text: string };

export type ReportPage = 'overview' | 'holdings' | 'symbol' | 'transactions' | 'projection' | 'data';

export interface Report {
  page: ReportPage;
  // '' for the real portfolio, and for the projection and the data page, which cover the
  // whole snapshot.
  portfolio: string;
  symbol?: string;
  title: string;
  parts: Part[];
}

const DASH = '–';

/** A raw value as the page shows it. */
export function display(cell: Cell, kind: Kind, currency: string): string {
  if (cell === null) return kind === 'text' ? '' : DASH;
  const value = typeof cell === 'number' ? cell : Number.NaN;
  switch (kind) {
    case 'money':
      return money(value, currency);
    case 'signed-money':
      return money(value, currency, { signed: true });
    case 'percent':
      return percent(value);
    case 'signed-percent':
      return percent(value, { signed: true });
    case 'quantity':
      return quantity(value);
    case 'number':
      return number(value);
    case 'price':
      return number(value, 4);
    case 'rate':
      return number(value, 6);
    case 'day':
      return dayLabel(String(cell));
    case 'month':
      return monthLabel(String(cell), 'long');
    case 'month-day':
      return monthLabel(String(cell).slice(0, 7), 'long');
    case 'run':
      return runTime(String(cell));
    default:
      return String(cell);
  }
}

/** Whether a column's figures are coloured by their sign. */
export function signed(kind: Kind): boolean {
  return kind === 'signed-money' || kind === 'signed-percent';
}

export function numeric(kind: Kind): boolean {
  return !['text', 'day', 'month', 'month-day', 'run'].includes(kind);
}

// Charts: the pages draw these, and the downloads draw the same.

export function valuationChart(portfolio: Portfolio, currency: string): LineChartOptions {
  const months = portfolio.valuation;
  return {
    label: 'value at each month end',
    x: months.map((m) => monthDate(m.month).getTime()),
    xTick: (x) => monthLabel(new Date(x)),
    xReadout: (x) => monthLabel(new Date(x), 'long'),
    yTick: (y) => money(y, currency, { compact: true }),
    yReadout: (y) => money(y, currency),
    series: [{ name: 'value', values: months.map((m) => m.value) }],
    area: true,
    zero: true,
  };
}

export function spendingChart(portfolio: Portfolio, currency: string): ColumnChartOptions {
  const months = portfolio.monthly_spending;
  return {
    label: 'invested each month',
    values: months.map((m) => m.amount),
    tick: (i) => monthLabel(months[i]?.month ?? ''),
    readout: (i) => monthLabel(months[i]?.month ?? '', 'long'),
    yTick: (y) => money(y, currency, { compact: true }),
    yReadout: (y) => money(y, currency),
  };
}

export function priceChart(portfolio: Portfolio, ticker: string, currency: string, lite: boolean): LineChartOptions {
  const holding = portfolio.holdings.find((x) => x.symbol === ticker);
  const prices = portfolio.prices[ticker] ?? [];
  const entry = portfolio.entry_points[ticker];
  return {
    label: `${ticker} price`,
    x: prices.map((p) => dayDate(p.date).getTime()),
    xTick: (x) => monthLabel(new Date(x)),
    xReadout: (x) => (lite ? monthLabel(new Date(x), 'long') : dayLabel(new Date(x))),
    yTick: (y) => money(y, currency, { compact: Math.abs(y) >= 10_000 }),
    yReadout: (y) => money(y, currency),
    series: [{ name: 'close', values: prices.map((p) => p.close) }],
    references: holding ? [{ y: holding.break_even_price, label: `break-even ${money(holding.break_even_price, currency)}` }] : [],
    markers: entry ? [{ x: monthDate(entry).getTime(), label: 'first buy' }] : [],
  };
}

export function projectionChart(inputs: ProjectionInputs, rows: ProjectionRow[], currency: string): LineChartOptions {
  const series = [
    { name: 'net worth', values: rows.map((r) => r.net_worth_before_fees) },
    { name: 'after fees', values: rows.map((r) => r.net_worth_after_fees) },
  ];
  if (inputs.inflation !== null) series.push({ name: 'after fees, today’s money', values: rows.map((r) => r.net_worth_real ?? 0) });
  return {
    label: 'projected net worth by year',
    x: rows.map((r) => r.year),
    xTick: (year) => String(year),
    xReadout: (year) => `${year}, age ${year - inputs.birth_year}`,
    yTick: (y) => money(y, currency, { compact: true }),
    yReadout: (y) => money(y, currency),
    series,
    zero: true,
  };
}

// The projection's start: the CLI starts it the year after the run.

export function projectionStartYear(snapshot: Snapshot): number {
  return snapshot.projection?.start_year ?? new Date(snapshot.generated_at).getFullYear() + 1;
}

/** 'portfolio' and each imaginary portfolio's name -> its value. */
export function portfolioValues(snapshot: Snapshot): Record<string, number> {
  const values: Record<string, number> = { portfolio: snapshot.portfolio.total.value };
  for (const p of snapshot.imaginary) values[p.name] = p.total.value;
  return values;
}

// The reports, page by page.

export function overviewReport(snapshot: Snapshot, name: string, portfolio: Portfolio): Report {
  const total = portfolio.total;
  const parts: Part[] = [
    {
      kind: 'facts',
      table: {
        title: 'totals',
        columns: [
          { label: 'value', kind: 'money' },
          { label: 'invested', kind: 'money' },
          { label: 'profit', kind: 'signed-money' },
          { label: 'profit %', kind: 'signed-percent' },
          { label: 'realized profit', kind: 'signed-money' },
          { label: 'years since the first trade', kind: 'number' },
          { label: 'average yearly profit %', kind: 'signed-percent' },
          { label: 'value less 5%', kind: 'money' },
        ],
        rows: [
          [
            total.value,
            total.spending,
            total.profit_net,
            total.profit_percent,
            total.realized_profit,
            total.time_interval_years,
            total.avg_year_roi,
            total.cash_out,
          ],
        ],
      },
    },
    { kind: 'chart', title: 'value at each month end', chart: { kind: 'line', options: valuationChart(portfolio, currencyOf(snapshot)) } },
    {
      kind: 'table',
      table: {
        title: 'value at each month end',
        columns: [
          { label: 'month', kind: 'month' },
          { label: 'value', kind: 'money' },
        ],
        rows: portfolio.valuation.map((m) => [m.month, m.value]),
      },
    },
    { kind: 'chart', title: 'invested each month', chart: { kind: 'column', options: spendingChart(portfolio, currencyOf(snapshot)) } },
    {
      kind: 'table',
      table: {
        title: 'invested each month',
        columns: [
          { label: 'month', kind: 'month' },
          { label: 'invested', kind: 'money' },
        ],
        rows: portfolio.monthly_spending.map((m) => [m.month, m.amount]),
      },
    },
  ];
  if (name === '' && snapshot.imaginary.length > 0) {
    parts.push({
      kind: 'table',
      table: {
        title: 'imaginary portfolios',
        columns: [
          { label: 'portfolio', kind: 'text' },
          { label: 'invested', kind: 'money' },
          { label: 'value', kind: 'money' },
          { label: 'profit', kind: 'signed-money' },
          { label: 'profit %', kind: 'signed-percent' },
        ],
        rows: [
          { name: 'real portfolio', total: snapshot.portfolio.total },
          ...snapshot.imaginary.map((p) => ({ name: p.name, total: p.total })),
        ].map((row) => [row.name, row.total.spending, row.total.value, row.total.profit_net, row.total.profit_percent]),
      },
    });
  }
  return { page: 'overview', portfolio: name, title: 'overview', parts };
}

export const HOLDING_COLUMNS: Column[] = [
  { label: 'symbol', kind: 'text' },
  { label: 'quantity', kind: 'quantity' },
  { label: 'price', kind: 'money' },
  { label: 'value', kind: 'money' },
  { label: 'cost', kind: 'money' },
  { label: 'profit', kind: 'signed-money' },
  { label: 'profit %', kind: 'signed-percent' },
  { label: 'weight', kind: 'percent' },
  { label: 'break-even', kind: 'money' },
];

/** Holdings in the order given, by default the page's: by value, largest first. */
export function holdingsReport(name: string, portfolio: Portfolio, order?: Holding[]): Report {
  const holdings = order ?? [...portfolio.holdings].sort((a, b) => b.value - a.value);
  const total = portfolio.total;
  const parts: Part[] =
    holdings.length === 0
      ? [{ kind: 'note', text: 'nothing is held.' }]
      : [
          {
            kind: 'table',
            table: {
              title: 'holdings',
              columns: HOLDING_COLUMNS,
              rows: holdings.map((x) => [
                x.symbol,
                x.amount,
                x.current_price,
                x.value,
                x.spending,
                x.profit_net,
                x.profit_percent,
                x.spending_percent,
                x.break_even_price,
              ]),
              footer: ['total', null, null, total.value, total.spending, total.profit_net, total.profit_percent, 100, null],
            },
          },
        ];
  return { page: 'holdings', portfolio: name, title: 'holdings', parts };
}

/** Each symbol with a page: those held or traded, in alphabetical order. */
export function symbolsOf(portfolio: Portfolio): string[] {
  const symbols = new Set([...portfolio.holdings.map((x) => x.symbol), ...portfolio.transactions.map((t) => t.symbol)]);
  return [...symbols].sort((a, b) => a.localeCompare(b));
}

export const TARGETS = [
  ['price25', '+25%'],
  ['price50', '+50%'],
  ['price75', '+75%'],
  ['price100', '+100%'],
  ['price150', '+150%'],
] as const;

export function symbolReport(snapshot: Snapshot, name: string, portfolio: Portfolio, ticker: string): Report {
  const holding = portfolio.holdings.find((x) => x.symbol === ticker);
  const prices = portfolio.prices[ticker] ?? [];
  const trades = portfolio.transactions.filter((t) => t.symbol === ticker);
  const lite = snapshot.config.history_variant === 'lite';
  const parts: Part[] = [];
  if (holding) {
    parts.push({
      kind: 'facts',
      table: {
        title: 'holding',
        columns: [
          { label: 'value', kind: 'money' },
          { label: 'quantity', kind: 'quantity' },
          { label: 'price', kind: 'money' },
          { label: 'cost', kind: 'money' },
          { label: 'profit', kind: 'signed-money' },
          { label: 'profit %', kind: 'signed-percent' },
          { label: 'break-even price', kind: 'money' },
        ],
        rows: [[holding.value, holding.amount, holding.current_price, holding.spending, holding.profit_net, holding.profit_percent, holding.break_even_price]],
      },
    });
  } else {
    parts.push({ kind: 'note', text: 'not held any more.' });
  }
  if (prices.length > 0) {
    parts.push(
      { kind: 'chart', title: 'price', chart: { kind: 'line', options: priceChart(portfolio, ticker, currencyOf(snapshot), lite) } },
      {
        kind: 'table',
        table: {
          title: 'price',
          columns: [
            { label: 'date', kind: lite ? 'month-day' : 'day' },
            { label: 'close', kind: 'money' },
          ],
          rows: prices.map((p) => [p.date, p.close]),
        },
      },
    );
  }
  if (holding) {
    parts.push({
      kind: 'table',
      table: {
        title: 'price targets',
        columns: [
          { label: 'target', kind: 'text' },
          { label: 'price', kind: 'money' },
          { label: 'from today', kind: 'signed-percent' },
        ],
        rows: TARGETS.map(([key, label]) => [label, holding[key], (holding[key] / holding.current_price - 1) * 100]),
      },
    });
  }
  parts.push({ kind: 'table', table: tradesTable('trades', trades, false) });
  return { page: 'symbol', portfolio: name, symbol: ticker, title: holding?.exchange ? `${ticker} (${holding.exchange})` : ticker, parts };
}

/** Trades, newest first, with the columns the page shows. */
export function tradesTable(title: string, trades: Transaction[], withSymbol: boolean): Table {
  return {
    title,
    columns: [
      { label: 'date', kind: 'day' },
      { label: 'type', kind: 'text' },
      ...(withSymbol ? [{ label: 'symbol', kind: 'text' } as Column] : []),
      { label: 'quantity', kind: 'quantity' },
      { label: 'price', kind: 'price' },
      { label: 'fees', kind: 'number' },
      { label: 'ex. rate', kind: 'rate' },
      { label: 'ex. fees', kind: 'number' },
      { label: 'currency', kind: 'text' },
      { label: 'platform', kind: 'text' },
    ],
    rows: [...trades]
      .reverse()
      .map((t) => [t.date, t.type, ...(withSymbol ? [t.symbol] : []), t.quantity, t.price, t.fees, t.ex_rate, t.ex_fees, t.currency, t.platform]),
  };
}

/** The trades given, by default every one; the page passes the ones its filters show. */
export function transactionsReport(name: string, portfolio: Portfolio, shown?: Transaction[]): Report {
  const trades = shown ?? portfolio.transactions;
  const parts: Part[] =
    trades.length === 0 ? [{ kind: 'note', text: 'no trades match.' }] : [{ kind: 'table', table: tradesTable('transactions', trades, true) }];
  return { page: 'transactions', portfolio: name, title: 'transactions', parts };
}

/** The projection for the inputs given: the page's current ones, or the config's. */
export function projectionReport(snapshot: Snapshot, inputs: ProjectionInputs | null): Report {
  const report: Report = { page: 'projection', portfolio: '', title: 'projection', parts: [] };
  if (!inputs) {
    report.parts.push({ kind: 'note', text: 'the config has no projection block, and none was filled in on the projection page.' });
    return report;
  }
  const startYear = projectionStartYear(snapshot);
  const values = portfolioValues(snapshot);
  const problem = projectionProblem(inputs, Object.keys(values), startYear - 1);
  if (problem) {
    report.parts.push({ kind: 'note', text: `the projection's inputs don't check out: ${problem}` });
    return report;
  }
  const startValue = resolveStartValue(inputs, values);
  const rows = projectNetWorth(inputs, startValue, startYear);
  const real = inputs.inflation !== null;
  const last = rows[rows.length - 1];
  const currency = currencyOf(snapshot);
  if (last) {
    report.parts.push({
      kind: 'facts',
      table: {
        title: 'outcome',
        columns: [
          { label: 'start value', kind: 'money' },
          { label: 'retirement year', kind: 'text' },
          { label: 'age', kind: 'text' },
          { label: 'net worth after fees', kind: 'money' },
          ...(real ? [{ label: 'in today’s money', kind: 'money' } as Column] : []),
          { label: 'net worth before fees', kind: 'money' },
        ],
        rows: [[startValue, last.year, last.age, last.net_worth_after_fees, ...(real ? [last.net_worth_real] : []), last.net_worth_before_fees]],
      },
    });
  }
  report.parts.push(
    { kind: 'chart', title: 'net worth by year', chart: { kind: 'line', options: projectionChart(inputs, rows, currency) } },
    {
      kind: 'table',
      table: {
        title: 'net worth by year',
        columns: [
          { label: 'year', kind: 'text' },
          { label: 'age', kind: 'text' },
          { label: 'income', kind: 'money' },
          { label: 'invested', kind: 'money' },
          { label: 'deposit/withdrawal', kind: 'signed-money' },
          { label: 'return', kind: 'money' },
          { label: 'net worth', kind: 'money' },
          { label: 'return after fees', kind: 'money' },
          { label: 'after fees', kind: 'money' },
          ...(real ? [{ label: 'today’s money', kind: 'money' } as Column] : []),
        ],
        rows: rows.map((r) => [
          r.year,
          r.age,
          r.income,
          r.contribution,
          r.deposit_withdrawal,
          r.return_before_fees,
          r.net_worth_before_fees,
          r.return_after_fees,
          r.net_worth_after_fees,
          ...(real ? [r.net_worth_real] : []),
        ]),
      },
    },
  );
  return report;
}

export const SOURCE_NAMES = { local: 'a local file', cloud: 'a google sheet', browser: 'trades typed into this app' } as const;

/** The data page: facts about the snapshot and its symbol map. fileLabel names the open file. */
export function dataReport(snapshot: Snapshot, fileLabel: string): Report {
  const { sources } = snapshot.config;
  const source = (value: keyof typeof SOURCE_NAMES | null) => (value ? SOURCE_NAMES[value] : 'not used');
  const map = Object.entries(snapshot.symbol_map).sort(([a], [b]) => a.localeCompare(b));
  const parts: Part[] = [
    {
      kind: 'facts',
      table: {
        title: 'this snapshot',
        columns: [
          { label: 'file', kind: 'text' },
          { label: 'run', kind: 'run' },
          { label: 'default currency', kind: 'text' },
          { label: 'price history', kind: 'text' },
          { label: 'transactions from', kind: 'text' },
          { label: 'symbol map from', kind: 'text' },
          { label: 'positions from', kind: 'text' },
          { label: 'imaginary portfolios', kind: 'text' },
          { label: 'format version', kind: 'text' },
        ],
        rows: [
          [
            fileLabel,
            snapshot.generated_at,
            snapshot.config.default_currency,
            snapshot.config.history_variant === 'lite' ? 'lite (weekly closes)' : 'full (daily closes)',
            source(sources.transactions),
            source(sources.symbols_map),
            source(sources.positions),
            snapshot.imaginary.map((p) => p.name).join(', ') || 'none',
            snapshot.schema_version,
          ],
        ],
      },
    },
  ];
  if (map.length > 0) {
    parts.push({
      kind: 'table',
      table: {
        title: 'symbol map',
        columns: [
          { label: 'symbol', kind: 'text' },
          { label: 'yahoo ticker', kind: 'text' },
        ],
        rows: map,
      },
    });
  }
  return { page: 'data', portfolio: '', title: 'data', parts };
}

export interface Session {
  // How the data page names the open file.
  fileLabel: string;
  // The projection page's current inputs, or null for none.
  projectionInputs: ProjectionInputs | null;
}

/**
 * Every report of the open snapshot, for the combined download: each page of the real
 * portfolio and of each imaginary one, then the projection and the data page.
 */
export function allReports(snapshot: Snapshot, session: Session): Report[] {
  const portfolios: [string, Portfolio][] = [['', snapshot.portfolio], ...snapshot.imaginary.map((p): [string, Portfolio] => [p.name, p])];
  const reports: Report[] = [];
  for (const [name, portfolio] of portfolios) {
    reports.push(overviewReport(snapshot, name, portfolio), holdingsReport(name, portfolio));
    for (const ticker of symbolsOf(portfolio)) reports.push(symbolReport(snapshot, name, portfolio, ticker));
    reports.push(transactionsReport(name, portfolio));
  }
  reports.push(projectionReport(snapshot, session.projectionInputs), dataReport(snapshot, session.fileLabel));
  return reports;
}

function currencyOf(snapshot: Snapshot): string {
  return snapshot.config.default_currency;
}
