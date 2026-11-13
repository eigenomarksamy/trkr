import { describe, expect, it } from 'vitest';
import golden from '../../tests/golden/exec/snapshot.json?raw';
import symbolsCsv from '../../tests/fixtures/symbols.csv?raw';
import transactionsCsv from '../../tests/fixtures/transactions.csv?raw';
import { MarketError, priceMarket, type Quote } from '../src/market';
import { buildPortfolio, TradeError } from '../src/portfolio';
import { parseSnapshot, type Transaction } from '../src/snapshot';

// tests/conftest.py's made-up market: weekly closes on the Mondays from 2024-01-01 to
// 2024-06-24, rising 1% of 'base' a week, and 'current' as today's price. Today is 2024-06-30.
const TODAY = '2024-06-30';
const MONDAYS = Array.from({ length: 26 }, (_, week) => new Date(Date.UTC(2024, 0, 1 + 7 * week)).toISOString().slice(0, 10));

function quote(currency: string, base: number, current: number, mondays = MONDAYS): Quote {
  return { currency, price: current, closes: mondays.map((date, bar) => ({ date, close: base * (1 + 0.01 * bar) })) };
}

const FIXTURE_MARKET = new Map<string, Quote>([
  ['AAA.AS', quote('EUR', 50, 62)],
  ['BBB', quote('USD', 100, 130)],
  ['USDEUR=X', quote('EUR', 0.9, 0.92)],
]);

// A fixture CSV's rows as column -> cell. The fixtures have no quoted cells.
function records(csv: string): ((column: string) => string)[] {
  const [header = '', ...lines] = csv.trim().split(/\r?\n/);
  const columns = header.split(',');
  return lines.map((line) => {
    const cells = line.split(',');
    return (column: string) => cells[columns.indexOf(column)] ?? '';
  });
}

// The fixture's trades as the CLI reads them, symbols mapped to Yahoo tickers.
function fixtureTrades(): Transaction[] {
  const map = new Map(records(symbolsCsv).map((row) => [row('symbol').toLowerCase(), row('ticker')]));
  return records(transactionsCsv).map((row) => ({
    type: row('type'),
    date: row('date'),
    quantity: Number(row('quantity')),
    fees: Number(row('fees')),
    price: Number(row('price')),
    currency: row('currency'),
    symbol: map.get(row('symbol').toLowerCase()) ?? row('symbol').toLowerCase(),
    exchange: row('exchange'),
    platform: row('platform'),
    ex_rate: Number(row('ex_rate')),
    ex_fees: Number(row('ex_fees')),
  }));
}

function trade(type: string, date: string, symbol: string, quantity: number, price: number, extra: Partial<Transaction> = {}): Transaction {
  return { type, date, quantity, fees: 0, price, currency: 'EUR', symbol, exchange: 'XAMS', platform: 'broker-x', ex_rate: 1, ex_fees: 0, ...extra };
}

// A flat market for the portfolio tests: each ticker has no bars yet and is worth its price today.
function flat(prices: Record<string, number>): Map<string, Quote> {
  return new Map(Object.entries(prices).map(([ticker, price]) => [ticker, { currency: 'EUR', price, closes: [] }]));
}

describe('buildPortfolio, against the CLI', () => {
  it("matches the golden snapshot's portfolio to the last digit", () => {
    const expected = parseSnapshot(golden).portfolio;
    // The CLI also charts USDEUR=X, because the fixture's symbol map has an entry for the
    // default currency. The browser has no symbol map.
    delete expected.prices['USDEUR=X'];
    expect(buildPortfolio(fixtureTrades(), FIXTURE_MARKET, 'EUR', TODAY)).toEqual(expected);
  });

  it('keeps the trades in date order, in the shape the viewer reads', () => {
    const shuffled = fixtureTrades().reverse();
    const portfolio = buildPortfolio(shuffled, FIXTURE_MARKET, 'EUR', TODAY);
    expect(portfolio.transactions.map((t) => t.date)).toEqual(['2024-01-15', '2024-02-12', '2024-04-08']);
    expect(portfolio.holdings.map((h) => h.symbol)).toEqual(['AAA.AS', 'BBB']);
  });
});

describe('buildPortfolio, against the CLI with sells', () => {
  // Awkward made-up trades: partial sells, fees, exchange rates, a crypto-sized quantity, and a
  // last sell that closes A only through the isclose rule. The expected figures are what the
  // CLI's Portfolio printed for the same trades and prices, with today frozen at 2024-06-30.
  const trades = [
    trade('buy', '2024-01-15', 'A', 3.7, 101.13, { fees: 1.25, ex_rate: 1.0837, ex_fees: 0.4 }),
    trade('buy', '2024-02-20', 'A', 1.9, 97.41, { fees: 0.99, ex_rate: 1.0791, ex_fees: 0.3 }),
    trade('sell', '2024-03-05', 'A', 2.3, 105.77, { fees: 1.1, ex_rate: 1.0864, ex_fees: 0.35 }),
    trade('buy', '2024-03-18', 'B', 0.137, 61234.5, { fees: 3.2 }),
    trade('sell', '2024-05-02', 'B', 0.051, 64120.75, { fees: 2.1 }),
    trade('sell', '2024-06-10', 'A', 3.3, 110.02, { fees: 1, ex_rate: 1.0712 }),
  ];
  const bars = (closes: Record<string, number>) => Object.entries(closes).map(([date, close]) => ({ date, close }));
  const quotes = new Map<string, Quote>([
    ['A', { currency: 'EUR', price: 112.4, closes: bars({ '2024-01-29': 99.8, '2024-02-26': 100.6, '2024-04-29': 107.3, '2024-06-24': 112.4 }) }],
    ['B', { currency: 'EUR', price: 66001.3, closes: bars({ '2024-03-25': 62000.1, '2024-05-27': 64999.9, '2024-06-24': 66001.3 }) }],
  ]);

  it('matches the CLI to the last digit', () => {
    const portfolio = buildPortfolio(trades, quotes, 'EUR', TODAY);
    expect(portfolio.holdings).toEqual([
      {
        symbol: 'B',
        exchange: 'XAMS',
        amount: 0.08600000000000002,
        value: 5676.1118000000015,
        spending: 5268.1757591240885,
        spending_percent: 100.0,
        profit_net: 407.936040875913,
        profit_percent: 7.743402261577893,
        current_price: 66001.3,
        break_even_price: 61257.857664233576,
        price25: 76572.32208029197,
        price50: 91886.78649635037,
        price75: 107201.25091240875,
        price100: 122515.71532846715,
        price150: 153144.64416058394,
        realized_profit: 143.90750912408748,
      },
    ]);
    expect(portfolio.total).toEqual({
      value: 5676.1118000000015,
      spending: 5268.1757591240885,
      profit_net: 407.936040875913,
      profit_percent: 7.743402261577893,
      realized_profit: 184.98581276968312,
      cash_out: 5392.306210000002,
      time_interval_days: 167,
      time_interval_months: 5.566666666666666,
      time_interval_years: 0.4575342465753425,
      avg_day_roi: 0.046367678213041275,
      avg_month_roi: 1.3910303463912381,
      avg_year_roi: 16.924202547760064,
    });
    expect(portfolio.monthly_spending.map((m) => m.amount)).toEqual([346.8035434160745, 172.70781206561023, 8392.326500000001, 0, 0, 0]);
    expect(portfolio.valuation.map((m) => m.value)).toEqual([369.26, 563.3599999999999, 8825.9937, 8848.103700000001, 5944.081400000002, 5676.1118000000015]);
  });
});

// The same cases as tests/test_portfolio.py.
describe('buildPortfolio, average cost', () => {
  it('keeps the rest of the cost basis after a partial sell', () => {
    const { holdings, total } = buildPortfolio(
      [trade('buy', '2024-01-10', 'A', 10, 10), trade('buy', '2024-01-10', 'B', 10, 10), trade('sell', '2024-02-10', 'A', 5, 12)],
      flat({ A: 12, B: 10 }),
      'EUR',
      TODAY,
    );
    const a = holdings.find((h) => h.symbol === 'A');
    expect(a).toMatchObject({ amount: 5, spending: 50, break_even_price: 10, profit_net: 10, realized_profit: 10 });
    expect(a?.spending_percent).toBeCloseTo(100 / 3);
    expect(total).toMatchObject({ spending: 150, value: 160, profit_net: 10, realized_profit: 10 });
    expect(total.profit_percent).toBeCloseTo((10 / 150) * 100);
  });

  it('uses the average cost, with fees and the exchange rate in the proceeds', () => {
    const { holdings, total } = buildPortfolio(
      [
        trade('buy', '2024-01-10', 'A', 10, 10),
        trade('buy', '2024-02-10', 'A', 10, 20),
        trade('sell', '2024-03-10', 'A', 10, 15, { fees: 1, ex_rate: 0.5, ex_fees: 1 }),
      ],
      flat({ A: 15 }),
      'EUR',
      TODAY,
    );
    expect(holdings[0]).toMatchObject({ spending: 150, break_even_price: 15 });
    expect(total.realized_profit).toBeCloseTo(296 - 150);
  });

  it('drops a closed position but keeps its realized profit', () => {
    const { holdings, total } = buildPortfolio(
      [trade('buy', '2024-01-10', 'A', 10, 10), trade('buy', '2024-01-10', 'B', 1, 50), trade('sell', '2024-02-10', 'A', 10, 13)],
      flat({ A: 99, B: 50 }),
      'EUR',
      TODAY,
    );
    expect(holdings.map((h) => h.symbol)).toEqual(['B']);
    expect(total.spending).toBe(50);
    expect(total.realized_profit).toBeCloseTo(30);
  });

  it('leaves no dust after selling everything', () => {
    const { holdings, total } = buildPortfolio(
      [trade('buy', '2024-01-10', 'BTC', 0.1, 100), trade('buy', '2024-01-11', 'BTC', 0.2, 100), trade('sell', '2024-02-10', 'BTC', 0.3, 200)],
      flat({ BTC: 300 }),
      'EUR',
      TODAY,
    );
    expect(holdings).toEqual([]);
    expect(total.spending).toBe(0);
    expect(total.realized_profit).toBeCloseTo(30);
  });

  it('walks the trades by date, not in the order they were entered', () => {
    const { holdings, total } = buildPortfolio(
      [trade('sell', '2024-02-10', 'A', 4, 15), trade('buy', '2024-01-10', 'A', 10, 10)],
      flat({ A: 15 }),
      'EUR',
      TODAY,
    );
    expect(holdings[0]).toMatchObject({ amount: 6, current_price: 15 });
    expect(total.realized_profit).toBeCloseTo(20);
  });

  it('refuses a sell of more than is held, naming the trade', () => {
    const trades = [trade('buy', '2024-01-10', 'A', 10, 10), trade('sell', '2024-02-10', 'A', 11, 10)];
    expect(() => buildPortfolio(trades, flat({ A: 10 }), 'EUR', TODAY)).toThrow(TradeError);
    expect(() => buildPortfolio(trades, flat({ A: 10 }), 'EUR', TODAY)).toThrow('the sell of 11 A on 2024-02-10 is more than the 10 held.');
  });

  it('needs at least one trade', () => {
    expect(() => buildPortfolio([], flat({}), 'EUR', TODAY)).toThrow(TradeError);
  });

  it('values a trade made today at the current price, with no bars yet (bug 13)', () => {
    const { valuation, prices, total } = buildPortfolio([trade('buy', TODAY, 'A', 2, 10)], flat({ A: 11 }), 'EUR', TODAY);
    expect(valuation).toEqual([{ month: '2024-06', value: 22 }]);
    expect(prices).toEqual({ A: [{ date: '2024-06-01', close: 11 }] });
    expect(total.time_interval_days).toBe(0);
    expect(total.avg_day_roi).toBe(0);
  });
});

// The same cases as tests/test_market.py.
describe('priceMarket', () => {
  const quotes = new Map<string, Quote>([
    ...FIXTURE_MARKET,
    ['LLL.L', quote('GBp', 2000, 2500)],
    ['SSS.SW', quote('CHF', 80, 90)],
    ['GBPEUR=X', quote('EUR', 1.1, 1.15)],
    ['CHFEUR=X', quote('EUR', 1, 1.05)],
    ['EURUSD=X', quote('USD', 1.1, 1.08)],
  ]);

  it('converts each currency with its own pair, and pence to pounds', () => {
    const market = priceMarket(['AAA.AS', 'BBB', 'LLL.L', 'SSS.SW'], quotes, 'EUR', TODAY);
    expect(market.price.get('AAA.AS')).toBe(62);
    expect(market.price.get('BBB')).toBeCloseTo(130 * 0.92);
    expect(market.price.get('LLL.L')).toBeCloseTo(25 * 1.15);
    expect(market.price.get('SSS.SW')).toBeCloseTo(90 * 1.05);
    expect(market.history.get('LLL.L')?.get('2024-06')).toBeCloseTo(((2000 * 1.25) / 100) * 1.1 * 1.25);
    expect(market.history.get('SSS.SW')?.get('2024-06')).toBeCloseTo(80 * 1.25 * 1.0 * 1.25);
  });

  it('can price in USD', () => {
    const market = priceMarket(['AAA.AS', 'BBB'], quotes, 'usd', TODAY);
    expect(market.price.get('BBB')).toBe(130);
    expect(market.price.get('AAA.AS')).toBeCloseTo(62 * 1.08);
  });

  it('keeps the last close of each month, and gives the current month today’s price', () => {
    const market = priceMarket(['AAA.AS', 'BBB'], quotes, 'EUR', '2024-07-03');
    const history = market.history.get('AAA.AS');
    expect([...(history?.keys() ?? [])].slice(-2)).toEqual(['2024-06', '2024-07']);
    expect(history?.get('2024-06')).toBe(62.5);
    expect(history?.get('2024-07')).toBe(62);
    expect(market.history.get('BBB')?.get('2024-07')).toBe(130 * 0.92);
  });

  it('skips a bar without a close', () => {
    const gappy: Quote = { currency: 'EUR', price: 9, closes: [{ date: '2024-06-03', close: 8 }, { date: '2024-06-10', close: null }] };
    expect(priceMarket(['G'], new Map([['G', gappy]]), 'EUR', TODAY).history.get('G')?.get('2024-06')).toBe(8);
  });

  it('names a missing currency pair, and a ticker without a currency', () => {
    expect(() => priceMarket(['SSS.SW'], new Map([['SSS.SW', quote('CHF', 80, 90)]]), 'EUR', TODAY)).toThrow(
      new MarketError('there are no prices for CHFEUR=X.'),
    );
    expect(() => priceMarket(['X'], new Map([['X', quote('', 1, 1)]]), 'EUR', TODAY)).toThrow(MarketError);
  });
});
