from datetime import date

from conftest import FakeTicker
from src import market_mngr
from src.market_mngr import Interval, MarketDataYahoo, YFinanceSymbMap

TICKER_MAP = YFinanceSymbMap({'aaa': 'AAA.AS', 'bbb': 'BBB', 'eur': 'USDEUR=X'})


class StrictTicker(FakeTicker):
    """FakeTicker that, like Yahoo, has no bars for an empty window."""

    def history(self, period=None, **kwargs):
        if period is None:
            assert kwargs['start'] < kwargs['end'], 'asked Yahoo for an empty window'
        return super().history(period, **kwargs)


def weekly_market(monkeypatch, start: str, today: date) -> MarketDataYahoo:
    class FrozenDate(date):
        @classmethod
        def today(cls):
            return today

    monkeypatch.setattr(market_mngr.yf, 'Ticker', StrictTicker)
    monkeypatch.setattr(market_mngr, 'date', FrozenDate)
    return MarketDataYahoo(
        tickers=['AAA.AS', 'BBB', 'USDEUR=X'],
        ticker_map=TICKER_MAP,
        start_date=start,
        interval=Interval.WEEKLY,
        req_currency='EUR',
    )


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


def daily_market(monkeypatch, start: str, today: date) -> MarketDataYahoo:
    class FrozenDate(date):
        @classmethod
        def today(cls):
            return today

    monkeypatch.setattr(market_mngr.yf, 'Ticker', StrictTicker)
    monkeypatch.setattr(market_mngr, 'date', FrozenDate)
    return MarketDataYahoo(
        tickers=['AAA.AS', 'BBB', 'USDEUR=X'],
        ticker_map=TICKER_MAP,
        start_date=start,
        interval=Interval.DAILY,
        req_currency='EUR',
    )


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
