import pytest

from conftest import FrozenDatetime
from src import portfolio_mngr
from src.portfolio_mngr import Portfolio
from src.transactions import Transaction, Transactions

# These pin the current behaviour, so later refactors can't change it unnoticed. Sells use
# average cost: a sell removes its share of the cost basis and books the rest as realized.


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(portfolio_mngr, 'datetime', FrozenDatetime)


def trade(kind, date, symbol, quantity, price, fees=0, ex_rate=1, ex_fees=0):
    return Transaction(
        {
            'type': kind,
            'date': date,
            'quantity': quantity,
            'fees': fees,
            'price': price,
            'currency': 'EUR',
            'symbol': symbol,
            'exchange': 'XAMS',
            'platform': 'broker-x',
            'ex_rate': ex_rate,
            'ex_fees': ex_fees,
        }
    )


def make_portfolio(trades, prices=None):
    transactions = Transactions()
    for t in trades:
        transactions.add(t)
    market_data = {symbol: {'price': price} for symbol, price in (prices or {}).items()}
    return Portfolio(transactions, market_data, is_quiet=True)


def test_calculate_buys_of_several_symbols():
    portfolio, total = make_portfolio(
        [
            trade('buy', '2024-01-10', 'AAA', 10, 20, fees=2),
            trade('buy', '2024-02-20', 'BBB', 4, 50, fees=1, ex_rate=1.25, ex_fees=1),
            trade('buy', '2024-03-05', 'AAA', 5, 30, fees=2),
        ],
        prices={'AAA': 26, 'BBB': 45},
    ).calculate()

    # AAA: (10*20 + 2) + (5*30 + 2) = 354 for 15 shares. BBB: (4*50 + 1 + 1) / 1.25 = 161.6.
    assert list(portfolio) == ['AAA', 'BBB']
    assert portfolio['AAA'].pop('exchange') == 'XAMS'
    assert portfolio['AAA'] == pytest.approx(
        {
            'amount': 15,
            'value': 390,
            'spending': 354,
            'spending_percent': 354 / 515.6 * 100,
            'profit_net': 36,
            'profit_percent': 36 / 354 * 100,
            'current_price': 26,
            'break_even_price': 23.6,
            'price25': 29.5,
            'price50': 35.4,
            'price75': 41.3,
            'price100': 47.2,
            'price150': 59,
            'realized_profit': 0,
        }
    )
    assert portfolio['BBB'].pop('exchange') == 'XAMS'
    assert portfolio['BBB'] == pytest.approx(
        {
            'amount': 4,
            'value': 180,
            'spending': 161.6,
            'spending_percent': 161.6 / 515.6 * 100,
            'profit_net': 18.4,
            'profit_percent': 18.4 / 161.6 * 100,
            'current_price': 45,
            'break_even_price': 40.4,
            'price25': 50.5,
            'price50': 60.6,
            'price75': 70.7,
            'price100': 80.8,
            'price150': 101,
            'realized_profit': 0,
        }
    )

    # 172 days from the first buy to the frozen today, 2024-06-30.
    profit_percent = 54.4 / 515.6 * 100
    assert total == pytest.approx(
        {
            'value': 570,
            'spending': 515.6,
            'profit_net': 54.4,
            'profit_percent': profit_percent,
            'realized_profit': 0,
            'cash_out': 541.5,
            'time_interval_days': 172,
            'time_interval_months': 172 / 30,
            'time_interval_years': 172 / 365,
            'avg_day_roi': profit_percent / 172,
            'avg_month_roi': profit_percent / 172 * 30,
            'avg_year_roi': profit_percent / 172 * 365,
        }
    )


def test_a_partial_sell_keeps_the_rest_of_the_cost_basis():
    # Reported before the fix: total spending 100 (all of A's cost gone) and profit +60%.
    portfolio, total = make_portfolio(
        [
            trade('buy', '2024-01-10', 'A', 10, 10),
            trade('buy', '2024-01-10', 'B', 10, 10),
            trade('sell', '2024-02-10', 'A', 5, 12),
        ],
        prices={'A': 12, 'B': 10},
    ).calculate()
    assert portfolio['A']['amount'] == 5
    assert portfolio['A']['spending'] == pytest.approx(50)
    assert portfolio['A']['break_even_price'] == pytest.approx(10)
    assert portfolio['A']['profit_net'] == pytest.approx(10)
    assert portfolio['A']['realized_profit'] == pytest.approx(10)
    assert portfolio['A']['spending_percent'] == pytest.approx(100 / 3)
    assert total['spending'] == pytest.approx(150)
    assert total['value'] == pytest.approx(160)
    assert total['profit_net'] == pytest.approx(10)
    assert total['profit_percent'] == pytest.approx(10 / 150 * 100)
    assert total['realized_profit'] == pytest.approx(10)


def test_a_partial_sell_of_the_only_symbol():
    # Used to raise ZeroDivisionError: the sell took the total spending to 0.
    portfolio, total = make_portfolio(
        [trade('buy', '2024-01-10', 'A', 10, 10), trade('sell', '2024-02-10', 'A', 4, 8)],
        prices={'A': 9},
    ).calculate()
    assert portfolio['A']['amount'] == 6
    assert portfolio['A']['spending_percent'] == pytest.approx(100)
    assert total['spending'] == pytest.approx(60)
    assert total['profit_net'] == pytest.approx(-6)
    assert total['realized_profit'] == pytest.approx(-8)


def test_sells_use_the_average_cost():
    portfolio, total = make_portfolio(
        [
            trade('buy', '2024-01-10', 'A', 10, 10),
            trade('buy', '2024-02-10', 'A', 10, 20),
            trade('sell', '2024-03-10', 'A', 10, 15, fees=1, ex_rate=0.5, ex_fees=1),
        ],
        prices={'A': 15},
    ).calculate()
    # 10 of 20 shares carry half of the 300 cost; the proceeds are (150 - 2) / 0.5.
    assert portfolio['A']['spending'] == pytest.approx(150)
    assert portfolio['A']['break_even_price'] == pytest.approx(15)
    assert total['realized_profit'] == pytest.approx(296 - 150)


def test_a_closed_position_leaves_the_portfolio_but_keeps_its_realized_profit():
    portfolio, total = make_portfolio(
        [
            trade('buy', '2024-01-10', 'A', 10, 10),
            trade('buy', '2024-01-10', 'B', 1, 50),
            trade('sell', '2024-02-10', 'A', 10, 13),
        ],
        prices={'A': 99, 'B': 50},
    ).calculate()
    assert list(portfolio) == ['B']
    assert total['spending'] == pytest.approx(50)
    assert total['realized_profit'] == pytest.approx(30)


def test_selling_everything_leaves_no_dust():
    # 0.1 + 0.2 is 0.30000000000000004, so an exact comparison kept a crypto position open.
    portfolio, total = make_portfolio(
        [
            trade('buy', '2024-01-10', 'BTC', 0.1, 100),
            trade('buy', '2024-01-11', 'BTC', 0.2, 100),
            trade('sell', '2024-02-10', 'BTC', 0.3, 200),
        ],
        prices={'BTC': 300},
    ).calculate()
    assert portfolio == {}
    assert total['spending'] == 0
    assert total['realized_profit'] == pytest.approx(30)


def test_trades_are_walked_by_date_not_by_row():
    # The sheet lists the sell first, but it happened after the buy.
    portfolio, total = make_portfolio(
        [trade('sell', '2024-02-10', 'A', 4, 15), trade('buy', '2024-01-10', 'A', 10, 10)],
        prices={'A': 15},
    ).calculate()
    assert portfolio['A']['amount'] == 6
    assert portfolio['A']['current_price'] == 15
    assert total['realized_profit'] == pytest.approx(20)


def test_selling_more_than_is_held_is_an_input_error(capsys):
    portfolio = make_portfolio(
        [trade('buy', '2024-01-10', 'A', 10, 10), trade('sell', '2024-02-10', 'A', 11, 10)],
        prices={'A': 10},
    )
    with pytest.raises(Exception, match='^400$'):
        portfolio.calculate()
    assert 'A' in capsys.readouterr().out


def test_spending_history_sums_buys_per_month_and_ignores_sells():
    portfolio = make_portfolio(
        [
            trade('buy', '2024-03-20', 'BBB', 4, 50, fees=1, ex_rate=1.25, ex_fees=1),
            trade('buy', '2024-01-10', 'AAA', 10, 20, fees=2),
            trade('sell', '2024-03-25', 'AAA', 5, 30),
        ]
    )
    assert portfolio.compute_spending_history() == pytest.approx(
        {'jan24': 202, 'feb24': 0, 'mar24': 161.6}
    )
    # It sorts the shared transactions list in place.
    assert [t.date for t in portfolio.transactions.get()] == [
        '2024-01-10',
        '2024-03-20',
        '2024-03-25',
    ]


def test_spending_history_keeps_the_last_month_when_its_day_is_earlier():
    # Stepping a month at a time from 2024-01-20 would go past 2024-03-05 and skip March.
    portfolio = make_portfolio(
        [
            trade('buy', '2024-01-20', 'AAA', 1, 10),
            trade('buy', '2024-03-05', 'AAA', 1, 10),
        ]
    )
    assert portfolio.compute_spending_history() == {'jan24': 10, 'feb24': 0, 'mar24': 10}


def test_historical_valuation_keeps_the_last_month_when_its_day_is_earlier():
    portfolio = make_portfolio(
        [
            trade('buy', '2024-01-20', 'AAA', 1, 10),
            trade('buy', '2024-03-05', 'AAA', 1, 10),
        ]
    )
    history = {'AAA': {'jan24': {'price': 10}, 'feb24': {'price': 11}, 'mar24': {'price': 12}}}
    assert list(portfolio.compute_historical_valuation(history))[-1] == 'mar24'


def test_entry_points_are_the_month_of_the_first_buy():
    portfolio = make_portfolio(
        [
            trade('buy', '2024-03-02', 'AAA', 1, 10),
            trade('sell', '2024-01-05', 'BBB', 1, 10),
            trade('buy', '2024-04-01', 'BBB', 1, 10),
            trade('buy', '2024-02-10', 'AAA', 1, 10),
        ]
    )
    assert portfolio.get_entry_points_months() == {'AAA': 'feb24', 'BBB': 'apr24'}
