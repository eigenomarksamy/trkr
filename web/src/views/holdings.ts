import { href, type Context } from '../app';
import { h, mount, type Child } from '../dom';
import { direction, money, percent, quantity } from '../format';
import type { Holding } from '../snapshot';

interface Column {
  label: string;
  value: (holding: Holding) => number | string;
  cell: (holding: Holding, currency: string) => Child;
  tone?: (holding: Holding) => string;
}

const COLUMNS: Column[] = [
  { label: 'symbol', value: (x) => x.symbol, cell: () => null },
  { label: 'quantity', value: (x) => x.amount, cell: (x) => quantity(x.amount) },
  { label: 'price', value: (x) => x.current_price, cell: (x, c) => money(x.current_price, c) },
  { label: 'value', value: (x) => x.value, cell: (x, c) => money(x.value, c) },
  { label: 'cost', value: (x) => x.spending, cell: (x, c) => money(x.spending, c) },
  {
    label: 'profit',
    value: (x) => x.profit_net,
    cell: (x, c) => money(x.profit_net, c, { signed: true }),
    tone: (x) => direction(x.profit_net),
  },
  {
    label: 'profit %',
    value: (x) => x.profit_percent,
    cell: (x) => percent(x.profit_percent, { signed: true }),
    tone: (x) => direction(x.profit_net),
  },
  { label: 'weight', value: (x) => x.spending_percent, cell: (x) => percent(x.spending_percent) },
  { label: 'break-even', value: (x) => x.break_even_price, cell: (x, c) => money(x.break_even_price, c) },
];

// Kept across visits, like a remembered filter.
let sortBy = 3;
let descending = true;

export function holdingsPage(context: Context): Child[] {
  const { portfolio, currency } = context;
  if (portfolio.holdings.length === 0) {
    return [
      h('h1', null, 'holdings'),
      h('p', null, `nothing is held. sells made ${money(portfolio.total.realized_profit, currency, { signed: true })}.`),
    ];
  }
  const table = h('div', { class: 'scroll' });
  const render = () => mount(table, holdingsTable(context));
  const holdingsTable = (ctx: Context): HTMLElement => {
    const column = COLUMNS[sortBy] ?? COLUMNS[0]!;
    const rows = [...ctx.portfolio.holdings].sort((a, b) => {
      const x = column.value(a);
      const y = column.value(b);
      const order = typeof x === 'string' || typeof y === 'string' ? String(x).localeCompare(String(y)) : (x ?? 0) - (y ?? 0);
      return descending ? -order : order;
    });
    const total = ctx.portfolio.total;
    return h(
      'table',
      { class: 'holdings' },
      h(
        'thead',
        null,
        h(
          'tr',
          null,
          COLUMNS.map((col, i) =>
            h(
              'th',
              { class: i === 0 ? 'sticky' : 'num', 'aria-sort': i === sortBy ? (descending ? 'descending' : 'ascending') : null },
              h(
                'button',
                {
                  type: 'button',
                  class: 'sort',
                  onclick: () => {
                    descending = i === sortBy ? !descending : i !== 0;
                    sortBy = i;
                    render();
                  },
                },
                col.label,
                i === sortBy ? (descending ? ' ↓' : ' ↑') : '',
              ),
            ),
          ),
        ),
      ),
      h(
        'tbody',
        null,
        rows.map((holding) =>
          h(
            'tr',
            null,
            h('td', { class: 'sticky' }, h('a', { href: href(ctx.portfolioName, 'symbol', holding.symbol) }, holding.symbol)),
            COLUMNS.slice(1).map((col) => h('td', { class: `num ${col.tone?.(holding) ?? ''}` }, col.cell(holding, ctx.currency))),
          ),
        ),
      ),
      h(
        'tfoot',
        null,
        h(
          'tr',
          null,
          h('th', { class: 'sticky', scope: 'row' }, 'total'),
          h('td', null),
          h('td', null),
          h('td', { class: 'num' }, money(total.value, ctx.currency)),
          h('td', { class: 'num' }, money(total.spending, ctx.currency)),
          h('td', { class: `num ${direction(total.profit_net)}` }, money(total.profit_net, ctx.currency, { signed: true })),
          h('td', { class: `num ${direction(total.profit_net)}` }, percent(total.profit_percent, { signed: true })),
          h('td', { class: 'num' }, percent(100)),
          h('td', null),
        ),
      ),
    );
  };
  render();
  return [
    h('h1', null, 'holdings'),
    h('p', { class: 'muted' }, `prices and values in ${currency}. cost is what the units still held cost, fees included.`),
    table,
  ];
}
