import os

os.environ.setdefault('MPLBACKEND', 'Agg')

import pathlib
from datetime import date, datetime

import pandas as pd
import pytest

FIXTURES = pathlib.Path(__file__).parent / 'fixtures'
GOLDEN = pathlib.Path(__file__).parent / 'golden'

# Made-up market. Weekly closes rise 1% a week from 'base', daily closes 0.2% a weekday;
# 'current' is today's price.
TICKERS = {
    'AAA.AS': {'currency': 'EUR', 'base': 50.0, 'current': 62.0},
    'BBB': {'currency': 'USD', 'base': 100.0, 'current': 130.0},
    'USDEUR=X': {'currency': 'EUR', 'base': 0.9, 'current': 0.92},
}


class FakeTicker:
    def __init__(self, ticker: str) -> None:
        self.data = TICKERS[ticker]
        self.info = {'currency': self.data['currency']}

    def history(self, period=None, **kwargs) -> pd.DataFrame:
        if period == '1d':
            return pd.DataFrame(
                {'Close': [self.data['current']]}, index=pd.to_datetime(['2024-06-28'])
            )
        if kwargs.get('interval') == '1d':
            # Yahoo's end is exclusive, so the frozen today (a Sunday) has no bar.
            index = pd.bdate_range('2024-01-01', '2024-06-28')
            step = 0.002
        else:
            index = pd.date_range('2024-01-01', '2024-06-24', freq='W-MON')
            step = 0.01
        closes = [self.data['base'] * (1 + step * bar) for bar in range(len(index))]
        return pd.DataFrame({'Close': closes}, index=index)


class FrozenDatetime(datetime):
    @classmethod
    def today(cls):
        return cls(2024, 6, 30)


class FrozenDate(date):
    @classmethod
    def today(cls):
        return cls(2024, 6, 30)


def _no_network(*args, **kwargs):
    raise AssertionError('Tests must not touch the network.')


@pytest.fixture
def offline(monkeypatch, tmp_path) -> pathlib.Path:
    """Stubs Yahoo, Google Sheets, the connectivity check and today's date."""
    import run
    from src import portfolio_mngr

    monkeypatch.setattr('src.market_mngr.yf.Ticker', FakeTicker)
    monkeypatch.setattr('src.sheets_mngr.requests.get', _no_network)
    monkeypatch.setattr(run, 'check_internet', lambda: True)
    monkeypatch.setattr(portfolio_mngr, 'datetime', FrozenDatetime)
    monkeypatch.setattr('src.market_mngr.date', FrozenDate)
    # report_mngr writes its templates/ directory relative to the cwd.
    monkeypatch.chdir(tmp_path)
    return tmp_path


def make_cfg(tmp_path: pathlib.Path, extra_yaml: str = '') -> pathlib.Path:
    """Writes a config that reads the fixture CSVs and generates into tmp_path/out/."""
    cfg = (
        f"""
market-data-origin: yahoo
comp:
  default-currency: EUR
  history-variant: lite
directories:
  generation-dir: {(tmp_path / 'out').as_posix()}/
  log-dir: {(tmp_path / 'log').as_posix()}/
  transactions-dir: {(FIXTURES / 'transactions.csv').as_posix()}
  symbols-map-dir: {(FIXTURES / 'symbols.csv').as_posix()}
transactions:
  source: local
  symbols-standard: custom
symbols-map:
  source: local
cli-exec:
  quiet: true
  log-level: notset
"""
        + extra_yaml
    )
    path = tmp_path / 'cfg.yml'
    path.write_text(cfg, encoding='utf-8')
    return path


def check_golden(actual: pathlib.Path, name: str) -> None:
    """Compares a generated file with tests/golden/<name>; TRKR_UPDATE_GOLDEN=1 rewrites it."""
    golden = GOLDEN / name
    if os.environ.get('TRKR_UPDATE_GOLDEN') == '1':
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_bytes(actual.read_bytes())
    assert actual.read_text(encoding='utf-8') == golden.read_text(encoding='utf-8')
