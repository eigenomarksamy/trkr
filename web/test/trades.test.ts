import { describe, expect, it } from 'vitest';
import exampleTransactions from '../../examples/transactions.csv?raw';
import golden from '../../tests/golden/exec/snapshot.json?raw';
import { isGuide, isTrades } from '../src/app';
import { MarketError, type Quote } from '../src/market';
import { buildPortfolio, TradeError } from '../src/portfolio';
import { PriceError } from '../src/prices';
import { parseSnapshot, type Transaction } from '../src/snapshot';
import { byDate, checkTrade, COLUMNS, loadKept, makeSnapshot, readTrades, saveKept, snapshotFile, tradeFields, tradesCsv, type TradeFields } from '../src/trades';
import { TRADES_HREF } from '../src/views/trades';

const TODAY = '2024-06-30';

function fields(extra: Partial<TradeFields> = {}): TradeFields {
  return {
    type: 'buy',
    date: '2024-01-08',
    quantity: '10',
    fees: '1',
    price: '105.20',
    currency: 'EUR',
    symbol: 'VWCE.DE',
    exchange: 'XETRA',
    platform: 'broker-a',
    ex_rate: '1',
    ex_fees: '0',
    ...extra,
  };
}

const problemsOf = (extra: Partial<TradeFields>) => {
  const result = checkTrade(fields(extra), TODAY);
  return Array.isArray(result) ? result.map((p) => p.column) : [];
};

describe('a trade from the form', () => {
  it('reads the eleven columns as the CLI does', () => {
    expect(checkTrade(fields({ type: ' Buy ', symbol: 'vwce.de', currency: 'usd', fees: '', ex_rate: '', ex_fees: '', quantity: '1e1' }), TODAY)).toEqual({
      type: 'buy',
      date: '2024-01-08',
      quantity: 10,
      fees: 0,
      price: 105.2,
      currency: 'USD',
      symbol: 'VWCE.DE',
      exchange: 'XETRA',
      platform: 'broker-a',
      ex_rate: 1,
      ex_fees: 0,
    });
    expect(checkTrade(fields({ type: 'sell', exchange: '', platform: '', price: '0' }), TODAY)).toMatchObject({ type: 'sell', price: 0, exchange: '' });
  });

  it('says what is wrong with each column', () => {
    expect(problemsOf({ type: 'dividend' })).toEqual(['type']);
    expect(problemsOf({ date: '2024-1-8' })).toEqual(['date']);
    expect(problemsOf({ date: '2024-02-30' })).toEqual(['date']);
    expect(problemsOf({ date: '2024-07-01' })).toEqual(['date']);
    expect(problemsOf({ quantity: '' })).toEqual(['quantity']);
    expect(problemsOf({ quantity: '0' })).toEqual(['quantity']);
    expect(problemsOf({ quantity: '1,5' })).toEqual(['quantity']);
    expect(problemsOf({ quantity: 'inf' })).toEqual(['quantity']);
    expect(problemsOf({ price: '-1' })).toEqual(['price']);
    expect(problemsOf({ fees: 'nan' })).toEqual(['fees']);
    expect(problemsOf({ ex_rate: '0' })).toEqual(['ex_rate']);
    expect(problemsOf({ ex_fees: '-0.5' })).toEqual(['ex_fees']);
    expect(problemsOf({ currency: 'EURO' })).toEqual(['currency']);
    expect(problemsOf({ symbol: '' })).toEqual(['symbol']);
    expect(problemsOf({ symbol: 'A B' })).toEqual(['symbol']);
    expect(problemsOf({ exchange: '=HYPERLINK("x")' })).toEqual(['exchange']);
    expect(problemsOf({ platform: '-1' })).toEqual(['platform']);
    expect(problemsOf({ platform: 'a\nb' })).toEqual(['platform']);
    expect(problemsOf({ platform: 'x'.repeat(41) })).toEqual(['platform']);
    expect(problemsOf({ type: '', date: '', quantity: '', price: '', currency: '', symbol: '' })).toEqual(['type', 'date', 'quantity', 'price', 'currency', 'symbol']);
    const result = checkTrade(fields({ ex_rate: '0' }), TODAY);
    expect(Array.isArray(result) && result[0]?.message).toBe('ex_rate should be more than 0.');
  });

  it('goes back into the form as it was', () => {
    const trade = checkTrade(fields({ quantity: '0.1', price: '1e-7' }), TODAY) as Transaction;
    expect(checkTrade(tradeFields(trade), TODAY)).toEqual(trade);
  });
});

describe('the trades as files', () => {
  const trades = [
    checkTrade(fields({ date: '2024-03-04', symbol: 'AAPL', currency: 'USD', price: '175.10', quantity: '2', ex_rate: '1.08', ex_fees: '2', platform: 'broker, b' }), TODAY) as Transaction,
    checkTrade(fields(), TODAY) as Transaction,
  ];

  it("writes trkr's columns in order, oldest first, for the CLI to read", () => {
    const csv = tradesCsv(trades, TODAY);
    expect(csv.name).toBe('trkr-transactions-2024-06-30.csv');
    expect(csv.data).toBe(
      'type,date,quantity,fees,price,currency,symbol,exchange,platform,ex_rate,ex_fees\r\n' +
        'buy,2024-01-08,10,1,105.2,EUR,VWCE.DE,XETRA,broker-a,1,0\r\n' +
        'buy,2024-03-04,2,1,175.1,USD,AAPL,XETRA,"broker, b",1.08,2\r\n',
    );
    expect(COLUMNS).toHaveLength(11);
  });

  it('keeps them on this device, and drops any that no longer read', () => {
    const store = new Map<string, string>();
    const storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
      removeItem: (key: string) => void store.delete(key),
    };
    expect(loadKept(storage, TODAY)).toEqual({ currency: 'EUR', trades: [] });
    expect(saveKept(storage, { currency: 'USD', trades })).toBe(true);
    expect(loadKept(storage, TODAY)).toEqual({ currency: 'USD', trades });

    const stored = JSON.parse(store.get('trkr.trades')!);
    stored.trades.push({ ...trades[0], quantity: -1 }, { nonsense: true }, null);
    stored.currency = 'dollars';
    store.set('trkr.trades', JSON.stringify(stored));
    expect(loadKept(storage, TODAY)).toEqual({ currency: 'EUR', trades });

    store.set('trkr.trades', '{not json');
    expect(loadKept(storage, TODAY)).toEqual({ currency: 'EUR', trades: [] });
    expect(loadKept(undefined, TODAY).trades).toEqual([]);

    expect(saveKept(storage, { currency: 'EUR', trades: [] })).toBe(true);
    expect(store.has('trkr.trades')).toBe(false);
    expect(saveKept({ setItem: () => { throw new Error('full'); }, removeItem: () => undefined }, { currency: 'USD', trades })).toBe(false);
  });
});

describe('trades in bulk', () => {
  const HEADER = COLUMNS.join(',');
  const ROWS = ['buy,2024-01-08,10,1,105.20,EUR,VWCE.DE,XETRA,broker-a,1,0', 'sell,2024-03-04,2,1,175.10,usd,aapl,NASDAQ,"broker, b",1.08,2'];
  const trades = [
    fields(),
    fields({ type: 'sell', date: '2024-03-04', quantity: '2', price: '175.10', currency: 'usd', symbol: 'aapl', exchange: 'NASDAQ', platform: 'broker, b', ex_rate: '1.08', ex_fees: '2' }),
  ].map((typed) => checkTrade(typed, TODAY) as Transaction);

  it('adds pasted or opened rows, with a header or without', () => {
    for (const text of [ROWS.join('\n'), [HEADER, ...ROWS].join('\r\n') + '\r\n', `﻿${HEADER.toUpperCase()}\n${ROWS.join('\n')}`]) {
      const bulk = readTrades(text, TODAY);
      expect(bulk.bad).toEqual([]);
      expect(bulk.good.map((row) => row.trade)).toEqual(trades);
      expect(bulk.header).toBe(text.toLowerCase().includes('type,date'));
    }
    expect(readTrades([HEADER, ...ROWS].join('\n'), TODAY).good.map((row) => row.line)).toEqual([2, 3]);
  });

  it('reads rows copied from a spreadsheet, with its empty cells after the last column', () => {
    const tabs = ['Type\tDate\tQty\tFees\tPrice\tCcy\tTicker\tExchange\tWallet\tFX\tFX fees\t\t', 'buy\t2024-01-08\t10\t1\t105.20\tEUR\tVWCE.DE\tXETRA\tbroker-a\t1\t0\t\t'].join('\n');
    const bulk = readTrades(tabs, TODAY);
    expect(bulk).toMatchObject({ header: true, bad: [] });
    expect(bulk.good.map((row) => row.trade)).toEqual([trades[0]]);
  });

  it("reads back the trades page's own transactions.csv as the same trades", () => {
    const tricky = checkTrade(fields({ quantity: '0.1', price: '1e-7', fees: '', exchange: 'say "x"', platform: 'a, b' }), TODAY) as Transaction;
    const all = [...trades, tricky];
    const bulk = readTrades(tradesCsv(all, TODAY).data as string, TODAY);
    expect(bulk).toMatchObject({ header: true, bad: [] });
    expect(bulk.good.map((row) => row.trade)).toEqual(byDate(all));
  });

  it("reads the CLI's example transactions, whose symbols the browser takes as tickers", () => {
    const bulk = readTrades(exampleTransactions, '2026-11-25');
    expect(bulk).toMatchObject({ header: true, bad: [] });
    expect(bulk.good.map((row) => row.trade.symbol)).toEqual(['VWCE', 'AAPL', 'VWCE', 'AAPL', 'VWCE']);
  });

  it("lists each bad row with its line and reasons, and doesn't add it", () => {
    const text = [
      HEADER,
      ROWS[0],
      'dividend,2024-02-01,1,0,3,EUR,VWCE.DE,XETRA,broker-a,1,0',
      '',
      'buy,2024-07-01,0,1,10,EURO,VWCE.DE,,,1,0',
      'buy,2024-01-08,10,1,105.20,EUR,VWCE.DE',
      `${ROWS[0]},extra`,
      `${ROWS[0]},,`,
      'buy,"2024-01-08,10',
    ].join('\n');
    const bulk = readTrades(text, TODAY);
    expect(bulk.good.map((row) => row.line)).toEqual([2, 8]);
    expect(bulk.bad.map((row) => [row.line, row.problems])).toEqual([
      [3, ['type should be buy or sell.']],
      [5, ['date is after today, and a trade needs prices from its day on.', 'quantity should be more than 0.', 'currency should be a three-letter code, such as EUR or USD.']],
      [6, [`it has 7 columns, and a trade has 11, in this order: ${COLUMNS.join(', ')}.`]],
      [7, [`it has 12 columns, and a trade has 11, in this order: ${COLUMNS.join(', ')}.`]],
      [9, ['a quote opens and never closes, so the rest of the text was read as one cell.']],
    ]);
    expect(bulk.bad[0]?.source).toBe('dividend,2024-02-01,1,0,3,EUR,VWCE.DE,XETRA,broker-a,1,0');
  });

  it('takes a first row as a header only when it reads as no trade', () => {
    // A bad trade on a day is a row, not a header.
    const first = readTrades('dividend,2024-02-01,1,0,3,EUR,VWCE.DE,XETRA,broker-a,1,0', TODAY);
    expect(first).toMatchObject({ header: false, good: [] });
    expect(first.bad).toHaveLength(1);
    expect(readTrades(HEADER, TODAY)).toEqual({ header: true, good: [], bad: [] });
    expect(readTrades(' \n', TODAY)).toEqual({ header: false, good: [], bad: [] });
  });
});

// tests/conftest.py's made-up market, as test/portfolio.test.ts builds it.
const MONDAYS = Array.from({ length: 26 }, (_, week) => new Date(Date.UTC(2024, 0, 1 + 7 * week)).toISOString().slice(0, 10));
const quote = (currency: string, base: number, current: number): Quote => ({
  currency,
  price: current,
  closes: MONDAYS.map((date, bar) => ({ date, close: base * (1 + 0.01 * bar) })),
});
const MARKET = new Map<string, Quote>([
  ['AAA.AS', quote('EUR', 50, 62)],
  ['BBB', quote('USD', 100, 130)],
  ['USDEUR=X', quote('EUR', 0.9, 0.92)],
]);
// Noon on the golden run's day, in this machine's zone.
const NOW = new Date(2024, 5, 30, 12, 0, 5);

function stubMarket(market: Map<string, Quote>) {
  const asked: [string, string][] = [];
  const fetchQuote = async (ticker: string, from: string) => {
    asked.push([ticker, from]);
    const found = market.get(ticker);
    if (!found) throw new PriceError(`yahoo finance has no prices for ${ticker}.`);
    return found;
  };
  return { asked, fetchQuote };
}

describe('making a snapshot', () => {
  it("gives the CLI's golden portfolio from the same trades and market", async () => {
    const expected = parseSnapshot(golden);
    // The CLI also charts USDEUR=X, because the fixture's symbol map lists the default
    // currency. The browser has no symbol map (test/portfolio.test.ts).
    delete expected.portfolio.prices['USDEUR=X'];
    const { asked, fetchQuote } = stubMarket(MARKET);
    const progress: string[] = [];
    const snapshot = await makeSnapshot(expected.portfolio.transactions, 'eur', fetchQuote, NOW, (ticker) => progress.push(ticker));
    expect(snapshot.portfolio).toEqual(expected.portfolio);
    // Each ticker from the first trade's day, then the pair its currency needs.
    expect(asked).toEqual([
      ['AAA.AS', '2024-01-15'],
      ['BBB', '2024-01-15'],
      ['USDEUR=X', '2024-01-15'],
    ]);
    expect(progress).toEqual(['AAA.AS', 'BBB', 'USDEUR=X']);
    expect(snapshot.config).toEqual({
      default_currency: 'EUR',
      history_variant: 'lite',
      sources: { transactions: 'browser', symbols_map: null, positions: null },
    });
    expect(snapshot.generated_at).toBe('2024-06-30T12:00:05');
    expect(snapshot.symbol_map).toEqual({});
    expect(snapshot.imaginary).toEqual([]);
    expect(snapshot.projection).toBeNull();
  });

  it('downloads a file that opens again', async () => {
    const { fetchQuote } = stubMarket(MARKET);
    const trades = parseSnapshot(golden).portfolio.transactions;
    const snapshot = await makeSnapshot(trades, 'EUR', fetchQuote, NOW);
    const file = snapshotFile(snapshot);
    expect(file.name).toBe('trkr-snapshot-2024-06-30.json');
    expect(parseSnapshot(file.data as string)).toEqual(snapshot);
    expect(buildPortfolio(trades, MARKET, 'EUR', TODAY)).toEqual(snapshot.portfolio);
  });

  it('fetches a pair once, and none for the default currency', async () => {
    const usdOnly = new Map([...MARKET].filter(([ticker]) => ticker === 'BBB'));
    const { asked, fetchQuote } = stubMarket(usdOnly);
    const trade = checkTrade(fields({ symbol: 'BBB', currency: 'USD', date: '2024-02-05' }), TODAY) as Transaction;
    const snapshot = await makeSnapshot([trade, { ...trade, date: '2024-03-04' }], 'USD', fetchQuote, NOW);
    expect(asked).toEqual([['BBB', '2024-02-05']]);
    expect(snapshot.portfolio.holdings[0]?.amount).toBe(20);
  });

  it("passes on the price route's and the money math's messages", async () => {
    const trade = checkTrade(fields({ symbol: 'NOPE' }), TODAY) as Transaction;
    await expect(makeSnapshot([trade], 'EUR', stubMarket(MARKET).fetchQuote, NOW)).rejects.toThrow(PriceError);

    const noPair = new Map([...MARKET].filter(([ticker]) => ticker !== 'USDEUR=X'));
    const bbb = checkTrade(fields({ symbol: 'BBB' }), TODAY) as Transaction;
    await expect(makeSnapshot([bbb], 'EUR', stubMarket(noPair).fetchQuote, NOW)).rejects.toThrow('yahoo finance has no prices for USDEUR=X.');

    const noCurrency = new Map([['AAA.AS', { ...quote('', 50, 62) }]]);
    const aaa = checkTrade(fields({ symbol: 'AAA.AS' }), TODAY) as Transaction;
    await expect(makeSnapshot([aaa], 'EUR', stubMarket(noCurrency).fetchQuote, NOW)).rejects.toThrow(MarketError);

    const oversell = checkTrade(fields({ symbol: 'AAA.AS', type: 'sell', quantity: '11', date: '2024-02-05' }), TODAY) as Transaction;
    await expect(makeSnapshot([aaa, oversell], 'EUR', stubMarket(MARKET).fetchQuote, NOW)).rejects.toThrow(TradeError);
    await expect(makeSnapshot([], 'EUR', stubMarket(MARKET).fetchQuote, NOW)).rejects.toThrow('add at least one trade.');
  });
});

describe('routes', () => {
  it('knows the trades page, which needs no snapshot', () => {
    expect(isTrades(TRADES_HREF)).toBe(true);
    expect(isTrades('#trades/')).toBe(true);
    expect(isTrades('#/transactions')).toBe(false);
    expect(isGuide(TRADES_HREF)).toBe(false);
  });
});
