import { href, type Context } from '../app';
import { columnChart, lineChart, tableView } from '../chart';
import { h, type Child } from '../dom';
import { direction, money, monthDate, monthLabel, number, percent } from '../format';
import type { Portfolio } from '../snapshot';

export function tile(label: string, value: string, options: { note?: string; tone?: string; hero?: boolean } = {}): HTMLElement {
  return h(
    'div',
    { class: `tile${options.hero ? ' hero' : ''}` },
    h('p', { class: 'tile-label' }, label),
    h('p', { class: `tile-value ${options.tone ?? ''}` }, value),
    options.note ? h('p', { class: `tile-note ${options.tone ?? ''}` }, options.note) : null,
  );
}

export function overviewPage(context: Context): Child[] {
  const { portfolio, currency } = context;
  const total = portfolio.total;
  const nothingHeld = portfolio.holdings.length === 0;
  return [
    h('h1', null, 'Overview'),
    h(
      'div',
      { class: 'tiles' },
      tile('Value', money(total.value, currency), { hero: true, note: nothingHeld ? 'Nothing is held.' : undefined }),
      tile('Invested', money(total.spending, currency), { note: 'What the holdings cost' }),
      tile('Profit', money(total.profit_net, currency, { signed: true }), {
        note: percent(total.profit_percent, { signed: true }),
        tone: direction(total.profit_net),
      }),
      tile('Realized profit', money(total.realized_profit, currency, { signed: true }), {
        note: 'From sells',
        tone: direction(total.realized_profit),
      }),
    ),
    h(
      'dl',
      { class: 'facts' },
      h('dt', null, 'First trade'),
      h('dd', null, `${number(total.time_interval_years, 1)} years ago`),
      h('dt', null, 'Average yearly profit'),
      h('dd', null, `${percent(total.avg_year_roi, { signed: true })} (profit % spread evenly over the years)`),
      h('dt', null, 'Value less 5%'),
      h('dd', null, money(total.cash_out, currency)),
    ),
    valuationSection(portfolio, currency),
    spendingSection(portfolio, currency),
    context.portfolioName === '' && context.snapshot.imaginary.length > 0 ? comparison(context) : null,
  ];
}

function valuationSection(portfolio: Portfolio, currency: string): HTMLElement {
  const months = portfolio.valuation;
  return h(
    'section',
    { class: 'card' },
    h('h2', null, 'Value at each month end'),
    h('p', { class: 'muted' }, 'What the holdings of the time were worth at the month’s last close.'),
    lineChart({
      label: 'Value at each month end',
      x: months.map((m) => monthDate(m.month).getTime()),
      xTick: (x) => monthLabel(new Date(x)),
      xReadout: (x) => monthLabel(new Date(x), 'long'),
      yTick: (y) => money(y, currency, { compact: true }),
      yReadout: (y) => money(y, currency),
      series: [{ name: 'Value', values: months.map((m) => m.value) }],
      area: true,
      zero: true,
    }),
    tableView(
      ['Month', 'Value'],
      months.map((m) => [monthLabel(m.month, 'long'), money(m.value, currency)]),
    ),
  );
}

function spendingSection(portfolio: Portfolio, currency: string): HTMLElement {
  const months = portfolio.monthly_spending;
  return h(
    'section',
    { class: 'card' },
    h('h2', null, 'Invested each month'),
    h('p', { class: 'muted' }, 'Buys with their fees, in the default currency.'),
    columnChart({
      label: 'Invested each month',
      values: months.map((m) => m.amount),
      tick: (i) => monthLabel(months[i]?.month ?? ''),
      readout: (i) => monthLabel(months[i]?.month ?? '', 'long'),
      yTick: (y) => money(y, currency, { compact: true }),
      yReadout: (y) => money(y, currency),
    }),
    tableView(
      ['Month', 'Invested'],
      months.map((m) => [monthLabel(m.month, 'long'), money(m.amount, currency)]),
    ),
  );
}

function comparison(context: Context): HTMLElement {
  const { snapshot, currency } = context;
  const rows = [
    { name: 'Real portfolio', link: href('', 'overview'), total: snapshot.portfolio.total },
    ...snapshot.imaginary.map((p) => ({ name: p.name, link: href(p.name, 'overview'), total: p.total })),
  ];
  return h(
    'section',
    { class: 'card' },
    h('h2', null, 'Imaginary portfolios'),
    h(
      'div',
      { class: 'scroll' },
      h(
        'table',
        null,
        h(
          'thead',
          null,
          h('tr', null, h('th', null, 'Portfolio'), ['Invested', 'Value', 'Profit', 'Profit %'].map((name) => h('th', { class: 'num' }, name))),
        ),
        h(
          'tbody',
          null,
          rows.map((row) =>
            h(
              'tr',
              null,
              h('td', null, h('a', { href: row.link }, row.name)),
              h('td', { class: 'num' }, money(row.total.spending, currency)),
              h('td', { class: 'num' }, money(row.total.value, currency)),
              h('td', { class: `num ${direction(row.total.profit_net)}` }, money(row.total.profit_net, currency, { signed: true })),
              h('td', { class: `num ${direction(row.total.profit_net)}` }, percent(row.total.profit_percent, { signed: true })),
            ),
          ),
        ),
      ),
    ),
  );
}
