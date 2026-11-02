import type { Context } from '../app';
import { h, type Child } from '../dom';
import { runTime } from '../format';
import { forget } from '../store';

const SOURCE_NAMES = { local: 'a local file', cloud: 'a Google Sheet' } as const;

export function dataPage(context: Context): Child[] {
  const { snapshot, loaded } = context;
  const { sources } = snapshot.config;
  const source = (value: 'local' | 'cloud' | null) => (value ? SOURCE_NAMES[value] : 'not used');
  const map = Object.entries(snapshot.symbol_map).sort(([a], [b]) => a.localeCompare(b));
  return [
    h('h1', null, 'Data'),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'This snapshot'),
      h(
        'dl',
        { class: 'facts' },
        h('dt', null, 'File'),
        h('dd', null, loaded.origin === 'demo' ? 'The made-up demo' : loaded.name),
        h('dt', null, 'Run'),
        h('dd', null, runTime(snapshot.generated_at)),
        h('dt', null, 'Default currency'),
        h('dd', null, snapshot.config.default_currency),
        h('dt', null, 'Price history'),
        h('dd', null, snapshot.config.history_variant === 'lite' ? 'lite (weekly closes)' : 'full (daily closes)'),
        h('dt', null, 'Transactions from'),
        h('dd', null, source(sources.transactions)),
        h('dt', null, 'Symbol map from'),
        h('dd', null, source(sources.symbols_map)),
        h('dt', null, 'Positions from'),
        h('dd', null, source(sources.positions)),
        h('dt', null, 'Imaginary portfolios'),
        h('dd', null, snapshot.imaginary.map((p) => p.name).join(', ') || 'none'),
        h('dt', null, 'Format version'),
        h('dd', null, String(snapshot.schema_version)),
      ),
    ),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'On this device'),
      h(
        'p',
        null,
        loaded.remembered
          ? 'This browser keeps a copy of the snapshot, so the page opens on it next time. Nothing was uploaded.'
          : 'The snapshot is open in this tab only. Nothing was uploaded, and closing the tab forgets it.',
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
            'Forget the copy on this device',
          )
        : null,
    ),
    map.length > 0
      ? h(
          'section',
          { class: 'card' },
          h('h2', null, 'Symbol map'),
          h(
            'div',
            { class: 'scroll' },
            h(
              'table',
              null,
              h('thead', null, h('tr', null, h('th', null, 'Symbol'), h('th', null, 'Yahoo ticker'))),
              h('tbody', null, map.map(([symbol, ticker]) => h('tr', null, h('td', null, symbol), h('td', null, ticker)))),
            ),
          ),
        )
      : null,
  ];
}
