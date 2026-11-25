// Make a snapshot here (W11): trades typed in one at a time or pasted in bulk, kept on this
// device, priced through the Worker and opened in the viewer. It needs no snapshot, so the
// router shows it before anything is open.

import { h, mount } from '../dom';
import { dayLabel, number, quantity } from '../format';
import { fetchQuote } from '../prices';
import { save } from '../save';
import type { Transaction } from '../snapshot';
import type { Loaded } from '../store';
import {
  byDate,
  checkCurrency,
  checkTrade,
  COLUMNS,
  loadKept,
  localDay,
  makeSnapshot,
  readTrades,
  saveKept,
  tradeFields,
  tradesCsv,
  type Bulk,
  type Column,
  type TradeFields,
} from '../trades';

export const TRADES_PAGE = 'trades';
export const TRADES_HREF = `#/${TRADES_PAGE}`;

type Reload = (loaded: Loaded | null) => void;

interface FieldSpec {
  label: string;
  hint?: string;
  // Typed, rather than chosen from a list.
  kind: 'text' | 'number' | 'date' | 'type';
  // Kept after a trade is added, for the next one.
  keep?: boolean;
  empty: string;
}

const FIELDS: Record<Column, FieldSpec> = {
  type: { label: 'type', kind: 'type', keep: true, empty: 'buy' },
  date: { label: 'date', kind: 'date', keep: true, empty: '' },
  symbol: { label: 'symbol', kind: 'text', hint: 'the ticker as yahoo finance writes it, such as VWCE.DE or AAPL.', empty: '' },
  quantity: { label: 'quantity', kind: 'number', empty: '' },
  price: { label: 'price', kind: 'number', hint: "per unit, in the trade's currency.", empty: '' },
  currency: { label: 'currency', kind: 'text', keep: true, hint: "the trade's currency.", empty: '' },
  fees: { label: 'fees', kind: 'number', hint: "in the trade's currency.", empty: '0' },
  ex_rate: {
    label: 'ex. rate',
    kind: 'number',
    keep: true,
    hint: "units of the trade's currency that one unit of the default currency buys: 1 when they are the same.",
    empty: '1',
  },
  ex_fees: { label: 'ex. fees', kind: 'number', hint: "currency exchange fees, in the trade's currency.", empty: '0' },
  exchange: { label: 'exchange', kind: 'text', keep: true, hint: 'only shown.', empty: '' },
  platform: { label: 'platform', kind: 'text', keep: true, hint: 'only shown.', empty: '' },
};
// The form's order: what a trade is first, then what it cost.
const FORM_ORDER: Column[] = ['type', 'date', 'symbol', 'quantity', 'price', 'currency', 'fees', 'ex_rate', 'ex_fees', 'exchange', 'platform'];

function browserStorage(): Storage | undefined {
  try {
    return localStorage;
  } catch {
    return undefined;
  }
}

const message = (problem: unknown) => (problem instanceof Error ? problem.message : String(problem));

// A trade's columns in the tables, the trades so far and the rows to add.
const tradeHeads = () => [
  h('th', null, 'date'),
  h('th', null, 'type'),
  h('th', null, 'symbol'),
  h('th', { class: 'num' }, 'quantity'),
  h('th', { class: 'num' }, 'price'),
  h('th', null, 'currency'),
  ['fees', 'ex. rate', 'ex. fees'].map((name) => h('th', { class: 'num' }, name)),
  h('th', null, 'exchange'),
  h('th', null, 'platform'),
];

const tradeCells = (t: Transaction) => [
  h('td', { class: 'nowrap' }, dayLabel(t.date)),
  h('td', null, t.type),
  h('td', null, t.symbol),
  h('td', { class: 'num' }, quantity(t.quantity)),
  h('td', { class: 'num' }, number(t.price, 4)),
  h('td', null, t.currency),
  h('td', { class: 'num' }, number(t.fees)),
  h('td', { class: 'num' }, number(t.ex_rate, 6)),
  h('td', { class: 'num' }, number(t.ex_fees)),
  h('td', null, t.exchange),
  h('td', null, t.platform),
];

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/**
 * Trades in bulk (W11b): rows pasted into the box or a CSV file opened into it, checked, and
 * previewed with each bad row and its reasons. add gets the good rows' trades. The bad rows
 * stay in the box, to fix and check again.
 */
function bulkForm(today: string, add: (trades: Transaction[]) => void): HTMLElement {
  const box = h('textarea', {
    id: 'bulk-text',
    rows: 6,
    wrap: 'off',
    spellcheck: 'false',
    autocomplete: 'off',
    'aria-describedby': 'bulk-hint',
    placeholder: 'buy,2024-01-08,10,1,105.20,EUR,VWCE.DE,XETRA,broker-a,1,0',
  });
  const file = h('input', { type: 'file', accept: '.csv,.tsv,.txt,text/csv,text/tab-separated-values,text/plain', class: 'visually-hidden' });
  const preview = h('div', { class: 'bulk-preview', hidden: true });
  const status = h('p', { class: 'notice', role: 'status', hidden: true });
  let read: Bulk | null = null;

  const close = () => {
    read = null;
    preview.hidden = true;
    preview.replaceChildren();
  };
  const say = (text: string | null) => {
    status.textContent = text ?? '';
    status.hidden = text === null;
  };

  const check = () => {
    say(null);
    read = readTrades(box.value, today);
    const { header, good, bad } = read;
    const rows = good.length + bad.length;
    const summary =
      rows === 0
        ? 'there are no rows to add in the text.'
        : `${plural(rows, 'row', 'rows')}: ${good.length} to add, ${bad.length} with problems.`;
    const addButton = h('button', { type: 'button', class: 'button primary', onclick: () => commit() }, `add ${plural(good.length, 'trade', 'trades')}`);
    mount(
      preview,
      h('p', null, summary, header ? ' the first row was read as a header, and left out.' : null),
      bad.length > 0
        ? h(
            'div',
            { class: 'notice error' },
            h('p', null, bad.length === 1 ? "this row isn't added:" : "these rows aren't added:"),
            h(
              'ul',
              null,
              bad.map((row) =>
                h('li', null, h('strong', null, `line ${row.line}`), ' ', h('code', null, row.source), h('ul', null, row.problems.map((problem) => h('li', null, problem)))),
              ),
            ),
          )
        : null,
      good.length > 0
        ? h(
            'div',
            { class: 'scroll' },
            h('table', null, h('thead', null, h('tr', null, h('th', { class: 'num' }, 'line'), tradeHeads())), h('tbody', null, good.map((row) => h('tr', null, h('td', { class: 'num' }, row.line), tradeCells(row.trade))))),
          )
        : null,
      h('p', { class: 'buttons' }, good.length > 0 ? addButton : null, h('button', { type: 'button', class: 'button quiet', onclick: close }, 'cancel')),
    );
    preview.hidden = false;
    (good.length > 0 ? addButton : box).focus();
  };

  const commit = () => {
    if (!read) return;
    const { good, bad } = read;
    add(good.map((row) => row.trade));
    box.value = bad.map((row) => row.source).join('\n');
    close();
    say(
      `added ${plural(good.length, 'trade', 'trades')}.` +
        (bad.length > 0 ? ` the ${plural(bad.length, 'row', 'rows')} with problems ${bad.length === 1 ? 'is' : 'are'} left in the box, to fix and check again.` : ''),
    );
    box.focus();
  };

  // A preview is of the text it was made from, so a change in the box closes it.
  box.addEventListener('input', () => {
    close();
    say(null);
  });
  file.addEventListener('change', async () => {
    const chosen = file.files?.[0];
    file.value = '';
    if (!chosen) return;
    try {
      box.value = await chosen.text();
      check();
    } catch {
      close();
      say(`${chosen.name} couldn't be read.`);
    }
  });

  return h(
    'section',
    { class: 'bulk', 'aria-labelledby': 'bulk-heading' },
    h('h2', { id: 'bulk-heading' }, 'add trades in bulk'),
    h(
      'div',
      { class: 'field' },
      h('label', { for: 'bulk-text' }, 'rows of trades'),
      box,
      h(
        'span',
        { class: 'hint', id: 'bulk-hint' },
        `paste rows from a spreadsheet or a CSV file, or open the file. the columns go in trkr's order: ${COLUMNS.join(', ')}, as transactions.csv below has them. a header row is optional.`,
      ),
    ),
    h(
      'p',
      { class: 'buttons' },
      h('button', { type: 'button', class: 'button quiet', onclick: check }, 'check the rows'),
      h('label', { class: 'button quiet' }, file, 'open a CSV file'),
    ),
    preview,
    status,
  );
}

export function tradesPage(reload: Reload): HTMLElement {
  const today = localDay(new Date());
  const kept = loadKept(browserStorage(), today);
  let editing: Transaction | null = null;

  const status = h('p', { class: 'notice', role: 'status', hidden: true });
  const formError = h('div', { class: 'notice error', role: 'alert', hidden: true });
  const makeError = h('p', { class: 'notice error', role: 'alert', hidden: true });
  const storageWarning = h(
    'p',
    { class: 'notice warn', role: 'status', hidden: true },
    "this browser won't keep the trades, so they are lost when the tab closes. download transactions.csv to keep them.",
  );
  const say = (element: HTMLElement, text: string | null) => {
    element.textContent = text ?? '';
    element.hidden = text === null;
  };
  const persist = () => {
    storageWarning.hidden = saveKept(browserStorage(), kept);
  };

  // The default currency.
  const currency = h('input', { id: 'default-currency', type: 'text', maxlength: 3, autocomplete: 'off', spellcheck: 'false', autocapitalize: 'characters', value: kept.currency });
  const currencyError = h('span', { class: 'hint error-text', hidden: true });
  currency.addEventListener('change', () => {
    const problem = checkCurrency(currency.value);
    say(currencyError, problem);
    currency.setAttribute('aria-invalid', problem ? 'true' : 'false');
    if (problem) return;
    kept.currency = currency.value.trim().toUpperCase();
    currency.value = kept.currency;
    persist();
  });

  // The form for one trade.
  const inputs = new Map<Column, HTMLInputElement | HTMLSelectElement>();
  for (const column of COLUMNS) {
    const spec = FIELDS[column];
    const id = `trade-${column}`;
    const describedBy = spec.hint ? `${id}-hint` : null;
    const input =
      spec.kind === 'type'
        ? h('select', { id, name: column }, h('option', { value: 'buy' }, 'buy'), h('option', { value: 'sell' }, 'sell'))
        : h('input', {
            id,
            name: column,
            type: spec.kind === 'date' ? 'date' : 'text',
            max: spec.kind === 'date' ? today : null,
            inputmode: spec.kind === 'number' ? 'decimal' : null,
            autocomplete: 'off',
            spellcheck: 'false',
            autocapitalize: column === 'symbol' || column === 'currency' ? 'characters' : null,
            maxlength: column === 'currency' ? 3 : null,
            'aria-describedby': describedBy,
          });
    inputs.set(column, input);
  }
  const fieldOf = (column: Column) => inputs.get(column) as HTMLInputElement | HTMLSelectElement;
  const fill = (fields: Partial<TradeFields>) => {
    for (const column of COLUMNS) {
      const value = fields[column];
      if (value !== undefined) fieldOf(column).value = value;
      fieldOf(column).removeAttribute('aria-invalid');
    }
  };
  const blank = (keepSome: boolean) => {
    const fields: Partial<TradeFields> = {};
    for (const column of COLUMNS) {
      if (!keepSome || !FIELDS[column].keep) fields[column] = FIELDS[column].empty;
    }
    if (!keepSome) fields.currency = kept.currency;
    fill(fields);
  };

  const submit = h('button', { type: 'submit', class: 'button primary' }, 'add trade');
  const cancel = h('button', { type: 'button', class: 'button quiet', hidden: true }, 'cancel the edit');
  const stopEditing = () => {
    editing = null;
    submit.textContent = 'add trade';
    cancel.hidden = true;
  };
  cancel.addEventListener('click', () => {
    stopEditing();
    blank(false);
    say(formError, null);
  });

  const form = h(
    'form',
    { class: 'trade-form', novalidate: true, 'aria-label': 'a trade' },
    FORM_ORDER.map((column) => {
      const spec = FIELDS[column];
      return h(
        'div',
        { class: 'field' },
        h('label', { for: `trade-${column}` }, spec.label),
        fieldOf(column),
        spec.hint ? h('span', { class: 'hint', id: `trade-${column}-hint` }, spec.hint) : null,
      );
    }),
    h('div', { class: 'field wide buttons' }, submit, cancel),
    h('div', { class: 'wide' }, formError),
  );
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const fields = Object.fromEntries(COLUMNS.map((column) => [column, fieldOf(column).value])) as TradeFields;
    const result = checkTrade(fields, today);
    for (const column of COLUMNS) fieldOf(column).removeAttribute('aria-invalid');
    if (Array.isArray(result)) {
      for (const problem of result) fieldOf(problem.column).setAttribute('aria-invalid', 'true');
      mount(formError, h('ul', null, result.map((problem) => h('li', null, problem.message))));
      formError.hidden = false;
      fieldOf(result[0]!.column).focus();
      return;
    }
    say(formError, null);
    const index = editing ? kept.trades.indexOf(editing) : -1;
    if (index >= 0) kept.trades[index] = result;
    else kept.trades.push(result);
    persist();
    say(status, `${index >= 0 ? 'saved' : 'added'}: ${result.type} ${quantity(result.quantity)} ${result.symbol} on ${dayLabel(result.date)}.`);
    stopEditing();
    blank(true);
    refresh();
    fieldOf('symbol').focus();
  });

  // The trades so far.
  const table = h('div');
  const count = h('span', { class: 'subtitle' });
  const tradeActions = h('p', { class: 'buttons' });
  const refresh = () => {
    count.textContent = kept.trades.length === 1 ? '1 trade' : `${kept.trades.length} trades`;
    tradeActions.hidden = kept.trades.length === 0;
    makeButton.disabled = kept.trades.length === 0;
    if (kept.trades.length === 0) {
      mount(table, h('p', { class: 'muted' }, 'no trades yet. add the first one above.'));
      return;
    }
    const row = (t: Transaction) =>
      h(
        'tr',
        { class: t === editing ? 'editing' : null },
        tradeCells(t),
        h(
          'td',
          { class: 'nowrap' },
          h(
            'button',
            {
              type: 'button',
              class: 'button link',
              'aria-label': `edit the ${t.type} of ${t.symbol} on ${t.date}`,
              onclick: () => {
                editing = t;
                fill(tradeFields(t));
                submit.textContent = 'save the trade';
                cancel.hidden = false;
                say(formError, null);
                refresh();
                form.scrollIntoView({ block: 'start' });
                fieldOf('type').focus();
              },
            },
            'edit',
          ),
          ' ',
          h(
            'button',
            {
              type: 'button',
              class: 'button link',
              'aria-label': `delete the ${t.type} of ${t.symbol} on ${t.date}`,
              onclick: () => {
                kept.trades.splice(kept.trades.indexOf(t), 1);
                if (editing === t) {
                  stopEditing();
                  blank(false);
                }
                persist();
                say(status, `deleted: ${t.type} ${quantity(t.quantity)} ${t.symbol} on ${dayLabel(t.date)}.`);
                refresh();
              },
            },
            'delete',
          ),
        ),
      );
    mount(
      table,
      h(
        'div',
        { class: 'scroll' },
        h(
          'table',
          null,
          h(
            'thead',
            null,
            h('tr', null, tradeHeads(), h('th', null, h('span', { class: 'visually-hidden' }, 'actions'))),
          ),
          h('tbody', null, byDate(kept.trades).map(row)),
        ),
      ),
    );
  };

  mount(
    tradeActions,
    h('button', { type: 'button', class: 'button quiet', onclick: () => save(tradesCsv(kept.trades, today)) }, 'download transactions.csv'),
    ' ',
    h(
      'button',
      {
        type: 'button',
        class: 'button quiet',
        onclick: () => {
          if (!confirm(`delete all ${kept.trades.length} trades from this device?`)) return;
          kept.trades.splice(0);
          stopEditing();
          blank(false);
          persist();
          say(status, 'deleted every trade.');
          refresh();
        },
      },
      'delete all trades',
    ),
  );

  // Make the snapshot.
  const makeButton = h('button', { type: 'button', class: 'button primary' }, 'make snapshot');
  const progress = h('p', { class: 'muted', role: 'status' });
  makeButton.addEventListener('click', async () => {
    const problem = checkCurrency(currency.value);
    if (problem) {
      say(makeError, problem);
      currency.focus();
      return;
    }
    say(makeError, null);
    makeButton.disabled = true;
    progress.textContent = 'fetching prices…';
    try {
      const snapshot = await makeSnapshot(kept.trades, currency.value, fetchQuote, new Date(), (ticker) => {
        progress.textContent = `fetching prices: ${ticker}…`;
      });
      // The viewer opens on the new snapshot, and the back button returns here.
      history.pushState(null, '', '#/');
      reload({ snapshot, origin: 'made', name: 'made in this browser', remembered: false });
    } catch (error) {
      progress.textContent = '';
      say(makeError, message(error));
      makeButton.disabled = false;
    }
  });

  blank(false);
  refresh();

  return h(
    'main',
    { class: 'guide trades' },
    h('a', { class: 'back', href: '#/' }, '← back'),
    h('h1', null, 'make a snapshot here'),
    h(
      'p',
      { class: 'lede' },
      'type or paste your trades, and this page prices them with yahoo finance and makes a snapshot you can open, download and come back to. there is nothing to install.',
    ),
    h(
      'p',
      { class: 'privacy' },
      "the trades stay in this browser, on this device. to price them, the page asks this site for each ticker's prices, and sends nothing else: no quantities, prices or fees.",
    ),
    storageWarning,
    h(
      'section',
      { class: 'card' },
      h(
        'div',
        { class: 'field inline' },
        h('label', { for: 'default-currency' }, 'default currency'),
        currency,
        h('span', { class: 'hint' }, 'every value in the snapshot is shown in it.'),
      ),
      currencyError,
    ),
    h('h2', null, 'add a trade'),
    form,
    status,
    bulkForm(today, (trades) => {
      kept.trades.push(...trades);
      persist();
      say(status, null);
      refresh();
    }),
    h('h2', null, 'trades ', count),
    table,
    tradeActions,
    h(
      'section',
      { class: 'card make' },
      h('h2', null, 'make the snapshot'),
      h(
        'p',
        null,
        'fetches weekly prices for each ticker from the first trade on, and the exchange rates into the default currency, then opens the snapshot. it takes a few seconds.',
      ),
      makeButton,
      progress,
      makeError,
    ),
  );
}
