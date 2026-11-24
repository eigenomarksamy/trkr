import type { Context } from '../app';
import { h, type Child } from '../dom';
import { runTime } from '../format';
import { reportFiles } from '../report-files';
import { dataReport, SOURCE_NAMES } from '../reports';
import { filesMenu, save } from '../save';
import { forget } from '../store';
import { snapshotFile, tradesCsv } from '../trades';
import { TRADES_HREF } from './trades';


export function dataPage(context: Context): Child[] {
  const { snapshot, loaded } = context;
  const { sources } = snapshot.config;
  const source = (value: keyof typeof SOURCE_NAMES | null) => (value ? SOURCE_NAMES[value] : 'not used');
  const map = Object.entries(snapshot.symbol_map).sort(([a], [b]) => a.localeCompare(b));
  return [
    h(
      'div',
      { class: 'page-head' },
      h('h1', null, 'data'),
      filesMenu(() => reportFiles(dataReport(snapshot, fileLabel(context)), snapshot)),
    ),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'this snapshot'),
      h(
        'dl',
        { class: 'facts' },
        h('dt', null, 'file'),
        h('dd', null, fileLabel(context)),
        h('dt', null, 'run'),
        h('dd', null, runTime(snapshot.generated_at)),
        h('dt', null, 'default currency'),
        h('dd', null, snapshot.config.default_currency),
        h('dt', null, 'price history'),
        h('dd', null, snapshot.config.history_variant === 'lite' ? 'lite (weekly closes)' : 'full (daily closes)'),
        h('dt', null, 'transactions from'),
        h('dd', null, source(sources.transactions)),
        h('dt', null, 'symbol map from'),
        h('dd', null, source(sources.symbols_map)),
        h('dt', null, 'positions from'),
        h('dd', null, source(sources.positions)),
        h('dt', null, 'imaginary portfolios'),
        h('dd', null, snapshot.imaginary.map((p) => p.name).join(', ') || 'none'),
        h('dt', null, 'format version'),
        h('dd', null, String(snapshot.schema_version)),
      ),
    ),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'on this device'),
      loaded.origin === 'made'
        ? madeHere(context)
        : h(
            'p',
            null,
            loaded.remembered
              ? 'this browser keeps a copy of the snapshot, so the page opens on it next time. nothing was uploaded.'
              : 'the snapshot is open in this tab only. nothing was uploaded, and closing the tab forgets it.',
          ),
      loaded.remembered
        ? h(
            'button',
            {
              type: 'button',
              class: 'button quiet',
              onclick: () => {
                forget();
                context.reload({ ...loaded, remembered: false });
              },
            },
            'forget the copy on this device',
          )
        : null,
    ),
    map.length > 0
      ? h(
          'section',
          { class: 'card' },
          h('h2', null, 'symbol map'),
          h(
            'div',
            { class: 'scroll' },
            h(
              'table',
              null,
              h('thead', null, h('tr', null, h('th', null, 'symbol'), h('th', null, 'yahoo ticker'))),
              h('tbody', null, map.map(([symbol, ticker]) => h('tr', null, h('td', null, symbol), h('td', null, ticker)))),
            ),
          ),
        )
      : null,
  ];
}

/** A snapshot made here: its trades stay on this device, and it downloads to open again later. */
function madeHere(context: Context): Child[] {
  const { snapshot } = context;
  const button = (label: string, onclick: () => void) => h('button', { type: 'button', class: 'button quiet', onclick }, label);
  return [
    h(
      'p',
      null,
      'this snapshot was made in this browser from the trades kept on this device. its prices are from when it was made. ',
      h('a', { href: TRADES_HREF }, 'edit the trades'),
      ' to make it again, or download it to open it later, here or on another device.',
    ),
    h(
      'p',
      { class: 'buttons' },
      button('download snapshot.json', () => save(snapshotFile(snapshot))),
      button('download transactions.csv', () => save(tradesCsv(snapshot.portfolio.transactions, snapshot.generated_at.slice(0, 10)))),
    ),
  ];
}

/** How the page names the open file. */
export function fileLabel(context: Pick<Context, 'loaded'>): string {
  return context.loaded.origin === 'demo' ? 'the made-up demo' : context.loaded.name;
}
