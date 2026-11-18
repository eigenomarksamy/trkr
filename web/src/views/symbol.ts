import { href, type Context } from '../app';
import { lineChart, tableView } from '../chart';
import { h, type Child } from '../dom';
import { dayLabel, direction, money, monthLabel, percent, quantity } from '../format';
import { reportFiles } from '../report-files';
import { priceChart, symbolReport, TARGETS } from '../reports';
import { filesMenu } from '../save';
import { tile } from './overview';
import { tradesTable } from './transactions';

export function symbolPage(context: Context, ticker: string): Child[] {
  const { portfolio, currency, snapshot } = context;
  const holding = portfolio.holdings.find((x) => x.symbol === ticker);
  const prices = portfolio.prices[ticker] ?? [];
  const trades = portfolio.transactions.filter((t) => t.symbol === ticker);
  const back = h('p', null, h('a', { href: href(context.portfolioName, 'holdings') }, '← holdings'));
  if (!holding && prices.length === 0 && trades.length === 0) {
    return [back, h('h1', null, ticker), h('p', null, 'this snapshot has nothing on this symbol.')];
  }
  const lite = snapshot.config.history_variant === 'lite';
  return [
    back,
    h(
      'div',
      { class: 'page-head' },
      h('h1', null, ticker, holding?.exchange ? h('span', { class: 'subtitle' }, holding.exchange) : null),
      filesMenu(() => reportFiles(symbolReport(snapshot, context.portfolioName, portfolio, ticker), snapshot)),
    ),
    holding
      ? h(
          'div',
          { class: 'tiles' },
          tile('value', money(holding.value, currency), { hero: true, note: `${quantity(holding.amount)} at ${money(holding.current_price, currency)}` }),
          tile('cost', money(holding.spending, currency)),
          tile('profit', money(holding.profit_net, currency, { signed: true }), {
            note: percent(holding.profit_percent, { signed: true }),
            tone: direction(holding.profit_net),
          }),
          tile('break-even price', money(holding.break_even_price, currency)),
        )
      : h('p', { class: 'notice' }, 'not held any more.'),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'price'),
      h('p', { class: 'muted' }, lite ? `month-end closes in ${currency}.` : `daily closes in ${currency}.`),
      lineChart(priceChart(portfolio, ticker, currency, lite)),
      tableView(
        ['date', 'close'],
        prices.map((p) => [lite ? monthLabel(p.date.slice(0, 7), 'long') : dayLabel(p.date), money(p.close, currency)]),
      ),
    ),
    holding
      ? h(
          'section',
          { class: 'card' },
          h('h2', null, 'price targets'),
          h('p', { class: 'muted' }, 'the price at which the holding is up by each step on its break-even price.'),
          h(
            'div',
            { class: 'scroll' },
            h(
              'table',
              null,
              h('thead', null, h('tr', null, h('th', null, 'target'), h('th', { class: 'num' }, 'price'), h('th', { class: 'num' }, 'from today'))),
              h(
                'tbody',
                null,
                TARGETS.map(([key, label]) =>
                  h(
                    'tr',
                    null,
                    h('td', null, label),
                    h('td', { class: 'num' }, money(holding[key], currency)),
                    h('td', { class: 'num' }, percent((holding[key] / holding.current_price - 1) * 100, { signed: true })),
                  ),
                ),
              ),
            ),
          ),
        )
      : null,
    h('section', { class: 'card' }, h('h2', null, 'trades'), tradesTable(trades, false)),
  ];
}
