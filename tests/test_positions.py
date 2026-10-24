import pytest
from conftest import FIXTURES
from src.transactions import Transaction, Transactions, build_positions

SYMBOLS = {'aaa': 'AAA.AS', 'bbb': 'BBB'}

def write_positions(tmp_path, text):
    path = tmp_path / 'positions.csv'
    path.write_text(text, encoding='utf-8')
    return str(path)

def test_positions_become_buys_at_the_average_price():
    aaa, bbb = build_positions(True, str(FIXTURES / 'positions.csv'), None, True, SYMBOLS)
    assert aaa.__dict__() == {'type': 'buy', 'date': '2024-01-02', 'quantity': 20.0,
                              'fees': 0.0, 'price': 40.0, 'currency': 'EUR',
                              'symbol': 'AAA.AS', 'exchange': 'AMS',
                              'wallet': 'positions file', 'ex_rate': 1.0, 'ex_fees': 0.0}
    assert (bbb.symbol, bbb.price, bbb.ex_rate) == ('BBB', 90.0, 1.2)

def test_only_four_columns_are_required(tmp_path):
    path = write_positions(tmp_path, '﻿Symbol, Quantity ,average_price,date\n'
                                     'aaa,5,12.5,2023-03-01\n'
                                     ',,,\n')
    [position] = build_positions(True, path, None, True, None)
    assert (position.symbol, position.quantity, position.price) == ('aaa', 5.0, 12.5)
    assert (position.ex_rate, position.currency, position.exchange) == (1.0, '', '')

@pytest.mark.parametrize('text, message', [
    ('symbol,quantity,date\naaa,5,2023-03-01\n', 'missing columns: average_price'),
    ('symbol,quantity,average_price,date\naaa,five,12,2023-03-01\n', 'line 2'),
    ('symbol,quantity,average_price,date\naaa,5,12,01-03-2023\n', 'YYYY-MM-DD'),
    ('symbol,quantity,average_price,date\naaa,0,12,2023-03-01\n', 'quantity must be positive'),
    ('symbol,quantity,average_price,date,ex_rate\naaa,5,12,2023-03-01,0\n', 'ex_rate must be positive'),
    ('symbol,quantity,average_price,date\n,5,12,2023-03-01\n', 'symbol is empty'),
])
def test_invalid_positions_exit_with_400(tmp_path, capsys, text, message):
    path = write_positions(tmp_path, text)
    with pytest.raises(Exception, match='^400$'):
        build_positions(True, path, None, True, None)
    assert message in capsys.readouterr().out

def test_prepend_puts_opening_positions_before_trades():
    def buy(date):
        return Transaction({'type': 'buy', 'date': date, 'quantity': 1, 'fees': 0,
                            'price': 1, 'currency': 'EUR', 'symbol': 'aaa', 'exchange': '',
                            'platform': '', 'ex_rate': 1, 'ex_fees': 0})
    transactions = Transactions()
    transactions.add(buy('2024-05-01'))
    transactions.prepend([buy('2023-01-01'), buy('2023-02-01')])
    assert [t.date for t in transactions.get()] == ['2023-01-01', '2023-02-01', '2024-05-01']
