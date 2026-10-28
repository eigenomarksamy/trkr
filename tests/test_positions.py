import pytest

from conftest import FIXTURES
from src.transactions import Transaction, Transactions, build_positions, merge_positions

SYMBOLS = {'aaa': 'AAA.AS', 'bbb': 'BBB'}


def write_positions(tmp_path, text):
    path = tmp_path / 'positions.csv'
    path.write_text(text, encoding='utf-8')
    return str(path)


def test_positions_become_buys_at_the_average_price():
    aaa, bbb = build_positions(True, str(FIXTURES / 'positions.csv'), None, True, SYMBOLS)
    assert aaa.__dict__() == {
        'type': 'buy',
        'date': '2024-01-02',
        'quantity': 20.0,
        'fees': 0.0,
        'price': 40.0,
        'currency': 'EUR',
        'symbol': 'AAA.AS',
        'exchange': 'AMS',
        'wallet': 'positions file',
        'ex_rate': 1.0,
        'ex_fees': 0.0,
    }
    assert (bbb.symbol, bbb.price, bbb.ex_rate) == ('BBB', 90.0, 1.2)


def test_only_four_columns_are_required(tmp_path):
    path = write_positions(
        tmp_path, '﻿Symbol, Quantity ,average_price,date\naaa,5,12.5,2023-03-01\n,,,\n'
    )
    [position] = build_positions(True, path, None, True, None)
    assert (position.symbol, position.quantity, position.price) == ('aaa', 5.0, 12.5)
    assert (position.ex_rate, position.currency, position.exchange) == (1.0, '', '')


def test_cost_is_the_total_paid_in_the_default_currency(tmp_path):
    path = write_positions(
        tmp_path, 'symbol,quantity,cost,date,currency\nbbb,4,500,2024-06-28,USD\n'
    )
    [position] = build_positions(True, path, None, True, SYMBOLS, 'EUR')
    assert (position.symbol, position.quantity, position.price) == ('BBB', 4.0, 125.0)
    assert (position.ex_rate, position.currency) == (1.0, 'EUR')


def test_rows_can_mix_average_price_and_cost(tmp_path):
    path = write_positions(
        tmp_path,
        'symbol,quantity,average_price,cost,date,currency,ex_rate\n'
        'aaa,5,12,,2023-03-01,eur,\n'
        'bbb,2,,300,2023-03-01,,\n',
    )
    aaa, bbb = build_positions(True, path, None, True, None, 'EUR')
    assert (aaa.price, aaa.ex_rate, aaa.currency) == (12.0, 1.0, 'eur')
    assert (bbb.price, bbb.ex_rate, bbb.currency) == (150.0, 1.0, 'EUR')


@pytest.mark.parametrize(
    'text, message',
    [
        ('symbol,quantity,date\naaa,5,2023-03-01\n', 'missing columns: average_price or cost.'),
        (
            'symbol,quantity,average_price,cost,date\naaa,5,12,60,2023-03-01\n',
            'average_price or cost, not both',
        ),
        (
            'symbol,quantity,average_price,cost,date\naaa,5,,,2023-03-01\n',
            'average_price or cost is required',
        ),
        ('symbol,quantity,cost,date\naaa,5,-1,2023-03-01\n', 'cost must not be negative'),
        (
            'symbol,quantity,cost,date,ex_rate\naaa,5,60,2023-03-01,1.1\n',
            'cost is already in EUR, so leave ex_rate empty',
        ),
        (
            'symbol,quantity,average_price,date,currency\naaa,5,12,2023-03-01,USD\n',
            'average_price is in USD, so ex_rate is required',
        ),
        ('symbol,quantity,average_price,date\naaa,five,12,2023-03-01\n', 'line 2'),
        ('symbol,quantity,average_price,date\naaa,5,12,01-03-2023\n', 'YYYY-MM-DD'),
        ('symbol,quantity,average_price,date\naaa,0,12,2023-03-01\n', 'quantity must be positive'),
        (
            'symbol,quantity,average_price,date,ex_rate\naaa,5,12,2023-03-01,0\n',
            'ex_rate must be positive',
        ),
        ('symbol,quantity,average_price,date\n,5,12,2023-03-01\n', 'symbol is empty'),
    ],
)
def test_invalid_positions_exit_with_400(tmp_path, capsys, text, message):
    path = write_positions(tmp_path, text)
    with pytest.raises(Exception, match='^400$'):
        build_positions(True, path, None, True, None, 'EUR')
    assert message in capsys.readouterr().out


def test_prepend_puts_opening_positions_before_trades():
    def buy(date):
        return Transaction(
            {
                'type': 'buy',
                'date': date,
                'quantity': 1,
                'fees': 0,
                'price': 1,
                'currency': 'EUR',
                'symbol': 'aaa',
                'exchange': '',
                'platform': '',
                'ex_rate': 1,
                'ex_fees': 0,
            }
        )

    transactions = Transactions()
    transactions.add(buy('2024-05-01'))
    transactions.prepend([buy('2023-01-01'), buy('2023-02-01')])
    assert [t.date for t in transactions.get()] == ['2023-01-01', '2023-02-01', '2024-05-01']


def trade(symbol, date, platform='broker-x'):
    return Transaction(
        {
            'type': 'buy',
            'date': date,
            'quantity': 1,
            'fees': 0,
            'price': 1,
            'currency': 'EUR',
            'symbol': symbol,
            'exchange': '',
            'platform': platform,
            'ex_rate': 1,
            'ex_fees': 0,
        }
    )


def test_a_position_replaces_the_trades_it_already_includes():
    transactions = Transactions()
    for t in (
        trade('aaa', '2024-01-15'),
        trade('bbb', '2024-02-12'),
        trade('aaa', '2024-06-28'),
        trade('aaa', '2024-07-01'),
    ):
        transactions.add(t)
    dropped = merge_positions(transactions, [trade('aaa', '2024-06-28', 'positions file')])
    # Up to and including the position's date: those trades are already in it.
    assert [(t.symbol, t.date) for t in dropped] == [('aaa', '2024-01-15'), ('aaa', '2024-06-28')]
    assert [(t.symbol, t.date, t.wallet) for t in transactions.get()] == [
        ('aaa', '2024-06-28', 'positions file'),
        ('bbb', '2024-02-12', 'broker-x'),
        ('aaa', '2024-07-01', 'broker-x'),
    ]


def test_a_symbol_with_several_positions_is_covered_until_the_latest():
    transactions = Transactions()
    for t in (trade('aaa', '2024-03-01'), trade('aaa', '2024-05-01'), trade('aaa', '2024-5-2')):
        transactions.add(t)
    positions = [trade('aaa', '2024-04-30', 'positions file'), trade('aaa', '2024-05-01', 'p')]
    dropped = merge_positions(transactions, positions)
    assert [t.date for t in dropped] == ['2024-03-01', '2024-05-01']
    assert [t.date for t in transactions.get()] == ['2024-04-30', '2024-05-01', '2024-5-2']


def test_without_positions_nothing_is_dropped():
    transactions = Transactions()
    transactions.add(trade('aaa', '2024-03-01'))
    assert merge_positions(transactions, []) == []
    assert [t.date for t in transactions.get()] == ['2024-03-01']
