import type { Context } from '../app';
import { h, mount, type Child } from '../dom';
import { dayLabel, number, quantity } from '../format';
import type { Transaction } from '../snapshot';

// The platform build_positions gives the rows of a positions file.
const POSITION = 'positions file';

// Kept across visits, like a remembered filter.
const filters = { symbol: '', type: '', platform: '' };

/** Trades, newest first. */
export function tradesTable(trades: Transaction[], withSymbol: boolean): HTMLElement {
  if (trades.length === 0) return h('p', { class: 'muted' }, 'No trades match.');
  const newestFirst = [...trades].reverse();
  return h(
    'div',
    { class: 'scroll' },
    h(
      'table',
      null,
      h(
        'thead',
        null,
        h(
          'tr',
          null,
          h('th', null, 'Date'),
          h('th', null, 'Type'),
          withSymbol ? h('th', null, 'Symbol') : null,
          ['Quantity', 'Price', 'Fees', 'Ex. rate', 'Ex. fees'].map((name) => h('th', { class: 'num' }, name)),
          h('th', null, 'Currency'),
          h('th', null, 'Platform'),
        ),
      ),
      h(
        'tbody',
        null,
        newestFirst.map((t) =>
          h(
            'tr',
            null,
            h('td', { class: 'nowrap' }, dayLabel(t.date)),
            h('td', null, t.platform === POSITION ? h('span', { class: 'badge' }, 'position') : t.type),
            withSymbol ? h('td', null, t.symbol) : null,
            h('td', { class: 'num' }, quantity(t.quantity)),
            h('td', { class: 'num' }, number(t.price, 4)),
            h('td', { class: 'num' }, number(t.fees)),
            h('td', { class: 'num' }, number(t.ex_rate, 6)),
            h('td', { class: 'num' }, number(t.ex_fees)),
            h('td', null, t.currency),
            h('td', null, t.platform),
          ),
        ),
      ),
    ),
  );
}

function select(label: string, key: keyof typeof filters, options: string[], onChange: () => void): HTMLElement {
  const element = h(
    'select',
    {
      onchange: (event: Event) => {
        filters[key] = (event.target as HTMLSelectElement).value;
        onChange();
      },
    },
    h('option', { value: '' }, 'All'),
    options.map((option) => h('option', { value: option }, option)),
  );
  // A remembered value the portfolio doesn't have falls back to All.
  if (!options.includes(filters[key])) filters[key] = '';
  element.value = filters[key];
  return h('label', { class: 'field inline' }, h('span', null, label), element);
}

export function transactionsPage(context: Context): Child[] {
  const trades = context.portfolio.transactions;
  const distinct = (pick: (t: Transaction) => string) => [...new Set(trades.map(pick))].sort();
  const results = h('div');
  const render = () => {
    const shown = trades.filter(
      (t) =>
        (!filters.symbol || t.symbol === filters.symbol) &&
        (!filters.type || t.type === filters.type) &&
        (!filters.platform || t.platform === filters.platform),
    );
    mount(results, h('p', { class: 'muted' }, `${shown.length} of ${trades.length} trades`), tradesTable(shown, true));
  };
  const controls = h(
    'div',
    { class: 'filters' },
    select('Symbol', 'symbol', distinct((t) => t.symbol), render),
    select('Type', 'type', distinct((t) => t.type), render),
    select('Platform', 'platform', distinct((t) => t.platform), render),
  );
  render();
  return [
    h('h1', null, 'Transactions'),
    h(
      'p',
      { class: 'muted' },
      'As the run read them, with symbols mapped to Yahoo tickers. Rows marked position come from the positions file; the trades they already include are left out.',
    ),
    controls,
    results,
  ];
}
