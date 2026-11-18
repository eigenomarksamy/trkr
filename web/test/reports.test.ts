import { describe, expect, it } from 'vitest';
import golden from '../../tests/golden/exec/snapshot.json?raw';
import demo from '../public/demo-snapshot.json?raw';
import { dayLabel, money, monthLabel, percent, quantity } from '../src/format';
import { combinedHtml, combinedZip, reportFiles, runDate } from '../src/report-files';
import {
  allReports,
  dataReport,
  display,
  holdingsReport,
  overviewReport,
  projectionReport,
  symbolsOf,
  transactionsReport,
  type Part,
  type Report,
  type Table,
} from '../src/reports';
import { parseSnapshot, type Snapshot } from '../src/snapshot';
import { unzip } from './unzip';

const session = (snapshot: Snapshot) => ({ fileLabel: 'snapshot.json', projectionInputs: snapshot.projection?.inputs ?? null });

function tables(report: Report): Table[] {
  return report.parts.flatMap((part: Part) => (part.kind === 'table' || part.kind === 'facts' ? [part.table] : []));
}

function table(report: Report, title: string): Table {
  const found = tables(report).find((t) => t.title === title);
  if (!found) throw new Error(`no table ${title}`);
  return found;
}

function csvLines(text: string | Uint8Array): string[] {
  return String(text).trimEnd().split('\r\n');
}

describe('the reports', () => {
  const snapshot = parseSnapshot(golden);

  it('lists the holdings by value, largest first, with the snapshot’s figures', () => {
    const holdings = table(holdingsReport('', snapshot.portfolio), 'holdings');
    const byValue = [...snapshot.portfolio.holdings].sort((a, b) => b.value - a.value);
    expect(holdings.rows.map((row) => row[0])).toEqual(byValue.map((x) => x.symbol));
    expect(holdings.rows[0]).toEqual([
      byValue[0]?.symbol,
      byValue[0]?.amount,
      byValue[0]?.current_price,
      byValue[0]?.value,
      byValue[0]?.spending,
      byValue[0]?.profit_net,
      byValue[0]?.profit_percent,
      byValue[0]?.spending_percent,
      byValue[0]?.break_even_price,
    ]);
    expect(holdings.footer?.[3]).toBe(snapshot.portfolio.total.value);
  });

  it('keeps the order the page gives, such as its current sort', () => {
    const order = [...snapshot.portfolio.holdings].sort((a, b) => a.symbol.localeCompare(b.symbol)).reverse();
    expect(table(holdingsReport('', snapshot.portfolio, order), 'holdings').rows.map((row) => row[0])).toEqual(order.map((x) => x.symbol));
  });

  it('lists trades newest first, and only the ones given', () => {
    const trades = snapshot.portfolio.transactions;
    const all = table(transactionsReport('', snapshot.portfolio), 'transactions');
    expect(all.rows.length).toBe(trades.length);
    expect(all.rows[0]?.[0]).toBe(trades[trades.length - 1]?.date);
    expect(all.columns.map((c) => c.label)).toEqual(['date', 'type', 'symbol', 'quantity', 'price', 'fees', 'ex. rate', 'ex. fees', 'currency', 'platform']);
    const one = trades.slice(0, 1);
    expect(table(transactionsReport('', snapshot.portfolio, one), 'transactions').rows.length).toBe(1);
    expect(transactionsReport('', snapshot.portfolio, []).parts).toEqual([{ kind: 'note', text: 'no trades match.' }]);
  });

  it('puts the overview’s totals and monthly figures in its tables', () => {
    const overview = overviewReport(snapshot, '', snapshot.portfolio);
    expect(table(overview, 'totals').rows[0]?.[0]).toBe(snapshot.portfolio.total.value);
    expect(table(overview, 'value at each month end').rows).toEqual(snapshot.portfolio.valuation.map((m) => [m.month, m.value]));
    expect(table(overview, 'invested each month').rows).toEqual(snapshot.portfolio.monthly_spending.map((m) => [m.month, m.amount]));
    expect(overview.parts.filter((p) => p.kind === 'chart').map((p) => (p.kind === 'chart' ? p.chart.kind : ''))).toEqual(['line', 'column']);
  });

  it('shows raw values the way the page does', () => {
    // In the viewer's locale, through the page's own formatting.
    expect(display(1234.5, 'money', 'EUR')).toBe(money(1234.5, 'EUR'));
    expect(display(-50, 'signed-money', 'EUR')).toBe(money(-50, 'EUR', { signed: true }));
    expect(display(12.345, 'signed-percent', 'EUR')).toBe(percent(12.345, { signed: true }));
    expect(display(0.00012345, 'quantity', 'EUR')).toBe(quantity(0.00012345));
    expect(display(null, 'money', 'EUR')).toBe('–');
    expect(display(null, 'text', 'EUR')).toBe('');
    expect(display('2024-03-01', 'month-day', 'EUR')).toBe(monthLabel('2024-03', 'long'));
    expect(display('2024-03-15', 'day', 'EUR')).toBe(dayLabel('2024-03-15'));
    expect(display(2055, 'text', 'EUR')).toBe('2055');
  });
});

describe('the projection report', () => {
  const snapshot = parseSnapshot(demo);
  const projection = snapshot.projection;
  if (!projection) throw new Error('The demo has no projection.');

  it('gives the rows the CLI computed, for the config’s inputs', () => {
    const rows = table(projectionReport(snapshot, projection.inputs), 'net worth by year').rows;
    expect(rows.length).toBe(projection.rows.length);
    rows.forEach((row, i) => {
      const expected = projection.rows[i];
      expect(row[0]).toBe(expected?.year);
      expect(row[8]).toBeCloseTo(expected?.net_worth_after_fees ?? Number.NaN, 6);
      // The demo has inflation, so today's money is the last column.
      expect(row[9]).toBeCloseTo(expected?.net_worth_real ?? Number.NaN, 6);
    });
  });

  it('follows inputs changed on the page', () => {
    const rows = table(projectionReport(snapshot, { ...projection.inputs, retirement_age: projection.inputs.retirement_age - 1 }), 'net worth by year').rows;
    expect(rows.length).toBe(projection.rows.length - 1);
  });

  it('says why there is no projection', () => {
    expect(projectionReport(snapshot, null).parts[0]).toMatchObject({ kind: 'note' });
    const invalid = projectionReport(snapshot, { ...projection.inputs, birth_year: Number.NaN });
    expect(invalid.parts).toHaveLength(1);
    expect(invalid.parts[0]).toMatchObject({ kind: 'note', text: expect.stringMatching(/birth-year/) });
  });
});

describe('the files of a report', () => {
  const snapshot = parseSnapshot(demo);
  const date = runDate(snapshot);

  it('names each file after the page, the part and the run date', () => {
    const files = reportFiles(holdingsReport('', snapshot.portfolio), snapshot);
    expect(files.map((f) => [f.name, f.path, f.label])).toEqual([[`trkr-holdings-${date}.csv`, 'portfolio/holdings.csv', 'holdings (csv)']]);
    const imaginary = snapshot.imaginary[0];
    if (!imaginary) throw new Error('The demo has no imaginary portfolio.');
    const names = reportFiles(overviewReport(snapshot, imaginary.name, imaginary), snapshot).map((f) => f.name);
    expect(names).toContain(`trkr-imaginary-${imaginary.name}-overview-totals-${date}.csv`);
    expect(names).toContain(`trkr-imaginary-${imaginary.name}-overview-value-at-each-month-end-${date}.svg`);
  });

  it('writes each table as CSV with the page’s columns', () => {
    const [file] = reportFiles(holdingsReport('', snapshot.portfolio), snapshot);
    const lines = csvLines(file?.data ?? '');
    expect(lines[0]).toBe('symbol,quantity,price,value,cost,profit,profit %,weight,break-even');
    // One line per holding, and no totals row.
    expect(lines.length).toBe(snapshot.portfolio.holdings.length + 1);
    const top = [...snapshot.portfolio.holdings].sort((a, b) => b.value - a.value)[0];
    expect(lines[1]?.split(',')[3]).toBe(String(top?.value));
  });

  it('writes each chart as an SVG that stands on its own', () => {
    const svgs = reportFiles(overviewReport(snapshot, '', snapshot.portfolio), snapshot).filter((f) => f.mime === 'image/svg+xml');
    expect(svgs.map((f) => f.label)).toEqual(['value at each month end (svg)', 'invested each month (svg)']);
    for (const svg of svgs) {
      const text = String(svg.data);
      expect(text.startsWith('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg"')).toBe(true);
      expect(text).toContain('<title>');
      expect(text).toContain('<style>');
      expect(text).toContain('class="bg"');
      expect(text).not.toMatch(/NaN|undefined|Infinity/);
    }
    const projection = reportFiles(projectionReport(snapshot, snapshot.projection?.inputs ?? null), snapshot).find((f) => f.mime === 'image/svg+xml');
    // Three series, so the legend is in the file.
    expect(String(projection?.data).match(/class="key-line s\d"/g)).toHaveLength(3);
  });

  it('makes no file for a note', () => {
    expect(reportFiles(projectionReport(snapshot, null), snapshot)).toEqual([]);
  });
});

describe('the combined report', () => {
  const snapshot = parseSnapshot(demo);
  const reports = allReports(snapshot, session(snapshot));

  it('covers every page of every portfolio, then the whole snapshot', () => {
    const expected = [snapshot.portfolio, ...snapshot.imaginary].reduce((sum, p) => sum + 3 + symbolsOf(p).length, 0) + 2;
    expect(reports.length).toBe(expected);
    expect(reports.filter((r) => r.page === 'overview').map((r) => r.portfolio)).toEqual(['', ...snapshot.imaginary.map((p) => p.name)]);
    expect(reports.slice(-2).map((r) => r.page)).toEqual(['projection', 'data']);
  });

  it('is one HTML file with every report, that loads and runs nothing', () => {
    const file = combinedHtml(snapshot, reports, { demo: true });
    const html = String(file.data);
    expect(file.name).toBe(`trkr-report-${runDate(snapshot)}.html`);
    expect(html.startsWith('<!doctype html>\n<html lang="en">')).toBe(true);
    expect(html).toContain('made-up demo data');
    expect(html).toContain('<section class="group" id="portfolio">');
    for (const p of snapshot.imaginary) expect(html).toContain(`id="imaginary-${p.name}"`);
    expect(html.match(/<h3>/g)).toHaveLength(reports.length);
    expect(html.match(/<svg /g)?.length).toBeGreaterThan(reports.length);
    expect(html).toContain("http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'");
    expect(html).not.toMatch(/<script|<link|<img|<iframe|\ssrc=|url\(|https?:\/\//i);
    expect(html).not.toMatch(/NaN|undefined/);
  });

  it('escapes what the snapshot holds', () => {
    const tricky = parseSnapshot(demo);
    const trade = tricky.portfolio.transactions[0];
    if (!trade) throw new Error('The demo has no trades.');
    trade.platform = '<script>alert(1)</script>';
    const html = String(combinedHtml(tricky, allReports(tricky, session(tricky)), { demo: false }).data);
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(html).not.toContain('made-up demo data');
  });

  it('is a zip of the separate files, in a folder of its own', () => {
    const file = combinedZip(snapshot, reports);
    const root = `trkr-report-${runDate(snapshot)}`;
    expect(file.name).toBe(`${root}.zip`);
    const entries = unzip(file.data as Uint8Array);
    const paths = entries.map((e) => e.path);
    expect(new Set(paths).size).toBe(paths.length);
    expect(paths.every((p) => p.startsWith(`${root}/`))).toBe(true);
    const imaginary = snapshot.imaginary[0]?.name;
    expect(paths).toEqual(
      expect.arrayContaining([
        `${root}/portfolio/overview-totals.csv`,
        `${root}/portfolio/holdings.csv`,
        `${root}/portfolio/transactions.csv`,
        `${root}/portfolio/symbol-${snapshot.portfolio.holdings[0]?.symbol.toLowerCase()}-price.svg`,
        `${root}/imaginary-${imaginary}/holdings.csv`,
        `${root}/projection-net-worth-by-year.svg`,
        `${root}/data-symbol-map.csv`,
      ]),
    );
    const holdings = reportFiles(holdingsReport('', snapshot.portfolio), snapshot)[0];
    expect(entries.find((e) => e.path === `${root}/portfolio/holdings.csv`)?.text).toBe(holdings?.data);
  });

  it('names the open file on the data page', () => {
    expect(table(dataReport(snapshot, 'my-snapshot.json'), 'this snapshot').rows[0]?.[0]).toBe('my-snapshot.json');
  });
});
