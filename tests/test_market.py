from datetime import date

import pytest

from conftest import TICKERS, FakeTicker
from src import market_mngr
from src.market_mngr import Interval, MarketDataYahoo

TICKERS_OF_INTEREST = ['AAA.AS', 'BBB', 'USDEUR=X']


class StrictTicker(FakeTicker):
    """FakeTicker that, like Yahoo, has no bars for an empty window."""

    def history(self, period=None, **kwargs):
        if period is None:
            assert kwargs['start'] < kwargs['end'], 'asked Yahoo for an empty window'
        return super().history(period, **kwargs)


def make_market(
    monkeypatch,
    start: str,
    today: date,
    interval: str,
    tickers=TICKERS_OF_INTEREST,
    req_currency='EUR',
) -> MarketDataYahoo:
    class FrozenDate(date):
        @classmethod
        def today(cls):
            return today

    monkeypatch.setattr(market_mngr.yf, 'Ticker', StrictTicker)
    monkeypatch.setattr(market_mngr, 'date', FrozenDate)
    return MarketDataYahoo(
        tickers=list(tickers),
        start_date=start,
        interval=interval,
        req_currency=req_currency,
    )


def weekly_market(monkeypatch, start: str, today: date, **kwargs) -> MarketDataYahoo:
    return make_market(monkeypatch, start, today, Interval.WEEKLY, **kwargs)


def test_a_month_with_bars_keeps_its_last_close(monkeypatch):
    market = weekly_market(monkeypatch, '2024-01-02', date(2024, 6, 30))
    # The fake's last bar is Monday 2024-06-24, week 25: 50 * 1.25.
    assert list(market.history['AAA.AS'])[-1] == 'jun24'
    assert market.history['AAA.AS']['jun24'] == 62.5


def test_the_current_month_without_a_bar_takes_the_current_price(monkeypatch):
    # The fake has no July bar. Yahoo labels weekly bars with their Monday, so a month has
    # none until its first Monday: on 2026-11-01 the latest bar is 2026-10-26.
    market = weekly_market(monkeypatch, '2024-01-02', date(2024, 7, 3))
    assert list(market.history['AAA.AS'])[-2:] == ['jun24', 'jul24']
    assert market.history['AAA.AS']['jul24'] == 62.0
    # USD is converted with the exchange rate's current price too: 130 * 0.92.
    assert market.history['BBB']['jul24'] == 130 * 0.92


def test_a_window_starting_today_needs_no_bars(monkeypatch):
    market = weekly_market(monkeypatch, '2024-07-03', date(2024, 7, 3))
    assert market.history['AAA.AS'] == {'jul24': 62.0}
    assert market.history['BBB'] == {'jul24': 130 * 0.92}
    assert market.current_price['AAA.AS'] == 62.0


def daily_market(monkeypatch, start: str, today: date, **kwargs) -> MarketDataYahoo:
    return make_market(monkeypatch, start, today, Interval.DAILY, **kwargs)


def test_daily_history_is_keyed_by_day_and_today_takes_the_current_price(monkeypatch):
    # Yahoo's end date is exclusive and today's bar only comes with the close, so today
    # has none; on a weekend the last bar is Friday's.
    market = daily_market(monkeypatch, '2024-01-02', date(2024, 6, 30))
    assert list(market.history['AAA.AS'])[-2:] == ['2024-06-28', '2024-06-30']
    assert market.history['AAA.AS']['2024-06-30'] == 62.0
    assert market.history['BBB']['2024-06-30'] == 130 * 0.92


def test_a_daily_window_starting_today_needs_no_bars(monkeypatch):
    market = daily_market(monkeypatch, '2024-07-03', date(2024, 7, 3))
    assert market.history['AAA.AS'] == {'2024-07-03': 62.0}
    assert market.history['BBB'] == {'2024-07-03': 130 * 0.92}


@pytest.fixture
def more_currencies(monkeypatch):
    """A London listing quoted in pence, a Swiss one, and the rates the conversion needs."""
    for ticker, data in {
        'LLL.L': {'currency': 'GBp', 'base': 2000.0, 'current': 2500.0},
        'SSS.SW': {'currency': 'CHF', 'base': 80.0, 'current': 90.0},
        'GBPEUR=X': {'currency': 'EUR', 'base': 1.1, 'current': 1.15},
        'CHFEUR=X': {'currency': 'EUR', 'base': 1.0, 'current': 1.05},
        'EURUSD=X': {'currency': 'USD', 'base': 1.1, 'current': 1.08},
    }.items():
        monkeypatch.setitem(TICKERS, ticker, data)


def test_each_currency_is_converted_with_its_own_rate(monkeypatch, more_currencies):
    # Every non-EUR price used to be multiplied by the one USD rate in the symbol map.
    market = weekly_market(
        monkeypatch,
        '2024-01-02',
        date(2024, 6, 30),
        tickers=['AAA.AS', 'BBB', 'LLL.L', 'SSS.SW'],
    )
    assert market.current_price['AAA.AS'] == 62.0
    assert market.current_price['BBB'] == pytest.approx(130 * 0.92)
    # Pence: 2500 GBp is 25 GBP.
    assert market.current_price['LLL.L'] == pytest.approx(25 * 1.15)
    assert market.current_price['SSS.SW'] == pytest.approx(90 * 1.05)
    # History is converted with the rate's close of the same month: week 25 is 1.25 * base.
    assert market.history['LLL.L']['jun24'] == pytest.approx(2000 * 1.25 / 100 * 1.1 * 1.25)
    assert market.history['SSS.SW']['jun24'] == pytest.approx(80 * 1.25 * 1.0 * 1.25)
    assert {market.currency[t] for t in ('BBB', 'LLL.L', 'SSS.SW')} == {'EUR'}


def test_the_default_currency_can_be_usd(monkeypatch, more_currencies):
    market = weekly_market(
        monkeypatch,
        '2024-01-02',
        date(2024, 6, 30),
        tickers=['AAA.AS', 'BBB'],
        req_currency='USD',
    )
    assert market.current_price['BBB'] == 130.0
    assert market.current_price['AAA.AS'] == pytest.approx(62 * 1.08)


def test_a_price_without_a_currency_is_not_guessed(monkeypatch, capsys):
    monkeypatch.setitem(TICKERS, 'XXX', {'currency': 'NA', 'base': 1.0, 'current': 1.0})
    with pytest.raises(Exception, match='^503$'):
        weekly_market(monkeypatch, '2024-01-02', date(2024, 6, 30), tickers=['XXX'])
    assert 'XXX' in capsys.readouterr().out
