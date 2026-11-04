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
    h('h1', null, 'overview'),
    h(
      'div',
      { class: 'tiles' },
      tile('value', money(total.value, currency), { hero: true, note: nothingHeld ? 'nothing is held.' : undefined }),
      tile('invested', money(total.spending, currency), { note: 'what the holdings cost' }),
      tile('profit', money(total.profit_net, currency, { signed: true }), {
        note: percent(total.profit_percent, { signed: true }),
        tone: direction(total.profit_net),
      }),
      tile('realized profit', money(total.realized_profit, currency, { signed: true }), {
        note: 'from sells',
        tone: direction(total.realized_profit),
      }),
    ),
    h(
      'dl',
      { class: 'facts' },
      h('dt', null, 'first trade'),
      h('dd', null, `${number(total.time_interval_years, 1)} years ago`),
      h('dt', null, 'average yearly profit'),
      h('dd', null, `${percent(total.avg_year_roi, { signed: true })} (profit % spread evenly over the years)`),
      h('dt', null, 'value less 5%'),
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
    h('h2', null, 'value at each month end'),
    h('p', { class: 'muted' }, 'what the holdings of the time were worth at the month’s last close.'),
    lineChart({
      label: 'value at each month end',
      x: months.map((m) => monthDate(m.month).getTime()),
      xTick: (x) => monthLabel(new Date(x)),
      xReadout: (x) => monthLabel(new Date(x), 'long'),
      yTick: (y) => money(y, currency, { compact: true }),
      yReadout: (y) => money(y, currency),
      series: [{ name: 'value', values: months.map((m) => m.value) }],
      area: true,
      zero: true,
    }),
    tableView(
      ['month', 'value'],
      months.map((m) => [monthLabel(m.month, 'long'), money(m.value, currency)]),
    ),
  );
}

function spendingSection(portfolio: Portfolio, currency: string): HTMLElement {
  const months = portfolio.monthly_spending;
  return h(
    'section',
    { class: 'card' },
    h('h2', null, 'invested each month'),
    h('p', { class: 'muted' }, 'buys with their fees, in the default currency.'),
    columnChart({
      label: 'invested each month',
      values: months.map((m) => m.amount),
      tick: (i) => monthLabel(months[i]?.month ?? ''),
      readout: (i) => monthLabel(months[i]?.month ?? '', 'long'),
      yTick: (y) => money(y, currency, { compact: true }),
      yReadout: (y) => money(y, currency),
    }),
    tableView(
      ['month', 'invested'],
      months.map((m) => [monthLabel(m.month, 'long'), money(m.amount, currency)]),
    ),
  );
}

function comparison(context: Context): HTMLElement {
  const { snapshot, currency } = context;
  const rows = [
    { name: 'real portfolio', link: href('', 'overview'), total: snapshot.portfolio.total },
    ...snapshot.imaginary.map((p) => ({ name: p.name, link: href(p.name, 'overview'), total: p.total })),
  ];
  return h(
    'section',
    { class: 'card' },
    h('h2', null, 'imaginary portfolios'),
    h(
      'div',
      { class: 'scroll' },
      h(
        'table',
        null,
        h(
          'thead',
          null,
          h('tr', null, h('th', null, 'portfolio'), ['invested', 'value', 'profit', 'profit %'].map((name) => h('th', { class: 'num' }, name))),
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
