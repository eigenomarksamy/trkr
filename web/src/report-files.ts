// The report downloads (W12): each page's tables as CSV and charts as SVG, and the combined
// report as one offline HTML file or as a zip of the separate files. Built from the open
// snapshot only: no DOM, no network, and the HTML file loads nothing and runs nothing.

import { CHART_CSS, chartMarkup } from './chart';
import { slug, toCsv, zip, type Download } from './download';
import { runTime } from './format';
import { m, toMarkup, type MNode } from './markup';
import { display, numeric, signed, type Part, type Report, type Table } from './reports';
import type { Snapshot } from './snapshot';

// A downloaded chart's width: about the page's content width on a laptop.
export const CHART_WIDTH = 960;

/** The snapshot's run date, YYYY-MM-DD, which every file name carries. */
export function runDate(snapshot: Snapshot): string {
  return snapshot.generated_at.slice(0, 10);
}

/** The folder of a report's files in the zip: its portfolio, or none for the whole snapshot. */
function folderOf(report: Report): string {
  if (report.page === 'projection' || report.page === 'data') return '';
  return report.portfolio ? `imaginary-${slug(report.portfolio)}` : 'portfolio';
}

function pageSlug(report: Report): string {
  return report.page === 'symbol' ? `symbol-${slug(report.symbol ?? '')}` : report.page;
}

/** A report's anchor in the combined HTML file. */
function anchorOf(report: Report): string {
  return [folderOf(report), pageSlug(report)].filter(Boolean).join('-');
}

function partTitle(part: Part): string | null {
  if (part.kind === 'chart') return part.title;
  if (part.kind === 'table' || part.kind === 'facts') return part.table.title;
  return null;
}

/** Each table of a report as CSV, and each chart as SVG. Notes make no file. */
export function reportFiles(report: Report, snapshot: Snapshot): Download[] {
  const files: Download[] = [];
  const page = pageSlug(report);
  const imaginary = report.portfolio && folderOf(report) ? `imaginary-${slug(report.portfolio)}` : null;
  for (const part of report.parts) {
    const title = partTitle(part);
    if (title === null) continue;
    const stem = slug(title) === page ? page : `${page}-${slug(title)}`;
    let ext: string;
    let mime: string;
    let data: string;
    if (part.kind === 'chart') {
      const svg = chartMarkup(part.chart, CHART_WIDTH, true);
      if (!svg) continue;
      ext = 'svg';
      mime = 'image/svg+xml';
      data = `<?xml version="1.0" encoding="UTF-8"?>\n${toMarkup(svg)}\n`;
    } else if (part.kind === 'table' || part.kind === 'facts') {
      ext = 'csv';
      mime = 'text/csv;charset=utf-8';
      data = toCsv(
        part.table.columns.map((c) => c.label),
        part.table.rows,
      );
    } else {
      continue;
    }
    files.push({
      name: `${['trkr', imaginary, stem, runDate(snapshot)].filter(Boolean).join('-')}.${ext}`,
      path: [folderOf(report), `${stem}.${ext}`].filter(Boolean).join('/'),
      label: `${title} (${ext})`,
      mime,
      data,
    });
  }
  return files;
}

/** The combined report as a zip of every report's separate files, in a folder of its own. */
export function combinedZip(snapshot: Snapshot, reports: Report[]): Download {
  const root = `trkr-report-${runDate(snapshot)}`;
  const seen = new Set<string>();
  const files = reports.flatMap((report) => reportFiles(report, snapshot)).map((file) => {
    // Two symbols can make the same file name, such as BTC-EUR and BTC=EUR.
    let path = `${root}/${file.path}`;
    for (let n = 2; seen.has(path); n++) path = `${root}/${file.path.replace(/(\.[a-z]+)$/, `-${n}$1`)}`;
    seen.add(path);
    return { path, data: file.data };
  });
  return {
    name: `${root}.zip`,
    path: `${root}.zip`,
    label: 'a zip of the separate files',
    mime: 'application/zip',
    data: zip(files, snapshot.generated_at),
  };
}

// The combined HTML file.

function tableMarkup(table: Table, currency: string): MNode {
  const cellClass = (i: number, cell: unknown): string | null => {
    const column = table.columns[i];
    if (!column || !numeric(column.kind)) return null;
    const tone = signed(column.kind) && typeof cell === 'number' && Math.abs(cell) >= 0.005 ? (cell > 0 ? ' up' : ' down') : '';
    return `num${tone}`;
  };
  return m(
    'div',
    { class: 'scroll' },
    m(
      'table',
      null,
      m('thead', null, m('tr', null, table.columns.map((c, i) => m('th', { class: cellClass(i, null), scope: 'col' }, c.label)))),
      m(
        'tbody',
        null,
        table.rows.map((row) =>
          m('tr', null, row.map((cell, i) => m('td', { class: cellClass(i, cell) }, display(cell, table.columns[i]?.kind ?? 'text', currency)))),
        ),
      ),
      table.footer
        ? m(
            'tfoot',
            null,
            m(
              'tr',
              null,
              table.footer.map((cell, i) =>
                i === 0
                  ? m('th', { scope: 'row' }, display(cell, 'text', currency))
                  : m('td', { class: cellClass(i, cell) }, display(cell, table.columns[i]?.kind ?? 'text', currency)),
              ),
            ),
          )
        : null,
    ),
  );
}

function partMarkup(part: Part, currency: string): MNode | null {
  switch (part.kind) {
    case 'facts': {
      const row = part.table.rows[0] ?? [];
      return m(
        'dl',
        { class: 'facts' },
        part.table.columns.map((column, i) => [m('dt', null, column.label), m('dd', null, display(row[i] ?? null, column.kind, currency))]),
      );
    }
    case 'table':
      return m('div', { class: 'card' }, m('h4', null, part.table.title), tableMarkup(part.table, currency));
    case 'chart': {
      const svg = chartMarkup(part.chart, CHART_WIDTH, false);
      return m('div', { class: 'card' }, m('h4', null, part.title), svg ? m('div', { class: 'chart' }, svg) : m('p', { class: 'muted' }, 'no data to chart.'));
    }
    case 'note':
      return m('p', { class: 'notice' }, part.text);
  }
}

function reportMarkup(report: Report, currency: string): MNode {
  return m('section', { class: 'report', id: anchorOf(report) }, m('h3', null, report.title), report.parts.map((part) => partMarkup(part, currency)));
}

interface Group {
  id: string;
  title: string;
  reports: Report[];
}

function groupsOf(snapshot: Snapshot, reports: Report[]): Group[] {
  const groups: Group[] = [
    { id: 'portfolio', title: 'real portfolio', reports: [] },
    ...snapshot.imaginary.map((p) => ({ id: `imaginary-${slug(p.name)}`, title: `${p.name} (imaginary)`, reports: [] as Report[] })),
    { id: 'snapshot', title: 'the whole snapshot', reports: [] },
  ];
  for (const report of reports) {
    const folder = folderOf(report) || 'snapshot';
    (groups.find((g) => g.id === folder) ?? groups[groups.length - 1])?.reports.push(report);
  }
  return groups.filter((g) => g.reports.length > 0);
}

// The report's own look: the app's tokens, light and dark, and the chart styles.
const REPORT_CSS = `
:root {
  color-scheme: light dark;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --grid: #e1e0d9; --axis: #c3c2b7;
  --border: rgba(11, 11, 11, 0.1); --accent: #1c5cab; --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --up: #006300; --down: #c03030;
}
@media (prefers-color-scheme: dark) {
  :root {
    --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --grid: #2c2c2a; --axis: #383835;
    --border: rgba(255, 255, 255, 0.1); --accent: #6da7ec; --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --up: #0ca30c; --down: #e66767;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink); font: 15px/1.5 system-ui, -apple-system, 'Segoe UI', sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 16px 48px; }
a { color: var(--accent); }
h1 { font-size: 1.6rem; line-height: 1.2; margin: 0 0 0.5rem; }
h2 { font-size: 1.35rem; margin: 2.5rem 0 0.5rem; padding-bottom: 4px; border-bottom: 2px solid var(--grid); }
h3 { font-size: 1.15rem; margin: 1.5rem 0 0.75rem; }
h4 { font-size: 1rem; margin: 0 0 0.5rem; }
p { margin: 0 0 0.75rem; }
.muted { color: var(--ink-2); }
.badge { display: inline-block; padding: 0 8px; margin-right: 8px; border-radius: 999px; border: 1px solid var(--border); color: var(--ink-2); font-size: 0.8rem; }
.notice { padding: 8px 12px; border-radius: 8px; background: var(--surface); border: 1px solid var(--border); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin: 0 0 16px; }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; margin: 0 0 16px; }
.facts dt { color: var(--ink-2); }
.facts dd { margin: 0; }
.toc ol { margin: 0.25rem 0 0.5rem; padding-left: 1.25rem; }
.toc .pages { display: flex; flex-wrap: wrap; gap: 2px 16px; padding: 0; list-style: none; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--grid); }
th { font-weight: 600; color: var(--ink-2); white-space: nowrap; }
tfoot th, tfoot td { border-bottom: none; border-top: 2px solid var(--grid); font-weight: 600; color: var(--ink); }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.up { color: var(--up); }
.down { color: var(--down); }
.chart svg { display: block; max-width: 100%; height: auto; }
@media (max-width: 560px) {
  .facts { grid-template-columns: 1fr; }
  .facts dd { margin-bottom: 6px; }
}
@media print {
  :root {
    color-scheme: light;
    --page: #ffffff; --surface: #ffffff; --ink: #0b0b0b; --ink-2: #52514e; --grid: #e1e0d9; --axis: #c3c2b7;
    --border: rgba(11, 11, 11, 0.1); --accent: #1c5cab; --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
    --up: #006300; --down: #c03030;
  }
  main { max-width: none; padding: 0; }
  .card { break-inside: avoid; }
  h2, h3, h4 { break-after: avoid; }
  .toc { display: none; }
}
`;

// The file may show its own markup and nothing else: no scripts, no requests, no forms.
const REPORT_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'";

/** The combined report as one HTML file that opens offline in any browser. */
export function combinedHtml(snapshot: Snapshot, reports: Report[], options: { demo: boolean }): Download {
  const currency = snapshot.config.default_currency;
  const groups = groupsOf(snapshot, reports);
  const title = `trkr report, snapshot of ${runDate(snapshot)}`;
  const page = m(
    'html',
    { lang: 'en' },
    m(
      'head',
      null,
      m('meta', { charset: 'utf-8' }),
      m('meta', { name: 'viewport', content: 'width=device-width, initial-scale=1' }),
      m('meta', { 'http-equiv': 'Content-Security-Policy', content: REPORT_CSP }),
      m('meta', { name: 'referrer', content: 'no-referrer' }),
      m('meta', { name: 'robots', content: 'noindex, nofollow' }),
      m('title', null, title),
      m('style', null, REPORT_CSS, CHART_CSS),
    ),
    m(
      'body',
      null,
      m(
        'main',
        null,
        m('h1', null, 'trkr report'),
        m(
          'p',
          { class: 'muted' },
          options.demo ? m('span', { class: 'badge' }, 'made-up demo data') : null,
          `snapshot of ${runTime(snapshot.generated_at)}, figures in ${currency}. it holds the snapshot's holdings and transactions, so keep it as private as the snapshot.`,
        ),
        m(
          'nav',
          { class: 'toc', 'aria-label': 'contents' },
          m(
            'ol',
            null,
            groups.map((group) =>
              m(
                'li',
                null,
                m('a', { href: `#${group.id}` }, group.title),
                m('ol', { class: 'pages' }, group.reports.map((report) => m('li', null, m('a', { href: `#${anchorOf(report)}` }, report.title)))),
              ),
            ),
          ),
        ),
        groups.map((group) =>
          m('section', { class: 'group', id: group.id }, m('h2', null, group.title), group.reports.map((report) => reportMarkup(report, currency))),
        ),
      ),
    ),
  );
  const root = `trkr-report-${runDate(snapshot)}`;
  return {
    name: `${root}.html`,
    path: `${root}.html`,
    label: 'one html file',
    mime: 'text/html;charset=utf-8',
    data: `<!doctype html>\n${toMarkup(page)}\n`,
  };
}
