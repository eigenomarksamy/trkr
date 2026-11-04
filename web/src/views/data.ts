import type { Context } from '../app';
import { h, type Child } from '../dom';
import { runTime } from '../format';
import { forget } from '../store';

const SOURCE_NAMES = { local: 'a local file', cloud: 'a google sheet' } as const;

export function dataPage(context: Context): Child[] {
  const { snapshot, loaded } = context;
  const { sources } = snapshot.config;
  const source = (value: 'local' | 'cloud' | null) => (value ? SOURCE_NAMES[value] : 'not used');
  const map = Object.entries(snapshot.symbol_map).sort(([a], [b]) => a.localeCompare(b));
  return [
    h('h1', null, 'data'),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'this snapshot'),
      h(
        'dl',
        { class: 'facts' },
        h('dt', null, 'file'),
        h('dd', null, loaded.origin === 'demo' ? 'the made-up demo' : loaded.name),
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
      h(
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
