import pytest
from conftest import FrozenDatetime
from src import portfolio_mngr
from src.portfolio_mngr import Portfolio
from src.transactions import Transaction, Transactions

# These pin the current behaviour, bugs included, so later refactors can't change it unnoticed.

@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(portfolio_mngr, 'datetime', FrozenDatetime)

def trade(kind, date, symbol, quantity, price, fees=0, ex_rate=1, ex_fees=0):
    return Transaction({'type': kind, 'date': date, 'quantity': quantity, 'fees': fees,
                        'price': price, 'currency': 'EUR', 'symbol': symbol,
                        'exchange': 'XAMS', 'platform': 'broker-x', 'ex_rate': ex_rate,
                        'ex_fees': ex_fees})

def make_portfolio(trades, prices=None):
    transactions = Transactions()
    for t in trades:
        transactions.add(t)
    market_data = {symbol: {'price': price} for symbol, price in (prices or {}).items()}
    return Portfolio(transactions, market_data, is_quiet=True)

def test_calculate_buys_of_several_symbols():
    portfolio, total = make_portfolio([
        trade('buy', '2024-01-10', 'AAA', 10, 20, fees=2),
        trade('buy', '2024-02-20', 'BBB', 4, 50, fees=1, ex_rate=1.25, ex_fees=1),
        trade('buy', '2024-03-05', 'AAA', 5, 30, fees=2),
    ], prices={'AAA': 26, 'BBB': 45}).calculate()

    # AAA: (10*20 + 2) + (5*30 + 2) = 354 for 15 shares. BBB: (4*50 + 1 + 1) / 1.25 = 161.6.
    assert list(portfolio) == ['AAA', 'BBB']
    assert portfolio['AAA'].pop('exchange') == 'XAMS'
    assert portfolio['AAA'] == pytest.approx({
        'amount': 15, 'value': 390, 'spending': 354, 'spending_percent': 354 / 515.6 * 100,
        'profit_net': 36, 'profit_percent': 36 / 354 * 100, 'current_price': 26,
        'break_even_price': 23.6, 'price25': 29.5, 'price50': 35.4, 'price75': 41.3,
        'price100': 47.2, 'price150': 59})
    assert portfolio['BBB'].pop('exchange') == 'XAMS'
    assert portfolio['BBB'] == pytest.approx({
        'amount': 4, 'value': 180, 'spending': 161.6, 'spending_percent': 161.6 / 515.6 * 100,
        'profit_net': 18.4, 'profit_percent': 18.4 / 161.6 * 100, 'current_price': 45,
        'break_even_price': 40.4, 'price25': 50.5, 'price50': 60.6, 'price75': 70.7,
        'price100': 80.8, 'price150': 101})

    # 172 days from the first buy to the frozen today, 2024-06-30.
    profit_percent = 54.4 / 515.6 * 100
    assert total == pytest.approx({
        'value': 570, 'spending': 515.6, 'profit_net': 54.4, 'profit_percent': profit_percent,
        'cash_out': 541.5, 'time_interval_days': 172, 'time_interval_months': 172 / 30,
        'time_interval_years': 172 / 365, 'avg_day_roi': profit_percent / 172,
        'avg_month_roi': profit_percent / 172 * 30, 'avg_year_roi': profit_percent / 172 * 365})

def test_spending_history_sums_buys_per_month_and_ignores_sells():
    portfolio = make_portfolio([
        trade('buy', '2024-03-20', 'BBB', 4, 50, fees=1, ex_rate=1.25, ex_fees=1),
        trade('buy', '2024-01-10', 'AAA', 10, 20, fees=2),
        trade('sell', '2024-03-25', 'AAA', 5, 30),
    ])
    assert portfolio.compute_spending_history() == pytest.approx(
        {'jan24': 202, 'feb24': 0, 'mar24': 161.6})
    # It sorts the shared transactions list in place.
    assert [t.date for t in portfolio.transactions.get()] == [
        '2024-01-10', '2024-03-20', '2024-03-25']

def test_spending_history_drops_the_last_month_when_its_day_is_earlier():
    # Known bug: months are stepped from the first transaction's day of the month,
    # so 2024-03-05 falls after the last step (2024-02-20) and March is never visited.
    portfolio = make_portfolio([
        trade('buy', '2024-01-20', 'AAA', 1, 10),
        trade('buy', '2024-03-05', 'AAA', 1, 10),
    ])
    assert portfolio.compute_spending_history() == {'jan24': 10, 'feb24': 0}

def test_entry_points_are_the_month_of_the_first_buy():
    portfolio = make_portfolio([
        trade('buy', '2024-03-02', 'AAA', 1, 10),
        trade('sell', '2024-01-05', 'BBB', 1, 10),
        trade('buy', '2024-04-01', 'BBB', 1, 10),
        trade('buy', '2024-02-10', 'AAA', 1, 10),
    ])
    assert portfolio.get_entry_points_months() == {'AAA': 'feb24', 'BBB': 'apr24'}
