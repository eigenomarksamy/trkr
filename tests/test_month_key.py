from datetime import date

import pytest

from src.market_mngr import MarketData
from src.portfolio_mngr import convert_date_to_short_str, history_key_date

COPIES = [convert_date_to_short_str, MarketData.convert_date_to_short_str]


@pytest.mark.parametrize('convert', COPIES, ids=['portfolio_mngr', 'market_mngr'])
@pytest.mark.parametrize(
    'kwargs, key',
    [
        ({'date': date(2024, 1, 15)}, 'jan24'),
        ({'date': date(2009, 12, 31)}, 'dec09'),
        ({'month': 3, 'year': 2025}, 'mar25'),
        ({'month': 3}, 'mar'),
        ({'year': 2025}, '25'),
        ({'month': 13, 'year': 2025}, ''),
        ({'month': 0}, ''),
        # month and year win over date.
        ({'month': 5, 'year': 2025, 'date': date(2024, 1, 1)}, 'may25'),
    ],
)
def test_month_keys(convert, kwargs, key):
    assert convert(**kwargs) == key


def test_the_copies_differ_without_arguments():
    assert convert_date_to_short_str() is None
    assert MarketData.convert_date_to_short_str() == ''


@pytest.mark.parametrize(
    'key, day',
    [
        ('2024-02-29', date(2024, 2, 29)),
        ('jan24', date(2024, 1, 1)),
        ('dec09', date(2009, 12, 1)),
    ],
)
def test_history_key_date(key, day):
    assert history_key_date(key) == day
