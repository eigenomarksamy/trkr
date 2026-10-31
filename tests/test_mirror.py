"""The scheduled job's run on a mirror of the owner's sheet.

tests/fixtures/mirror/ holds made-up sheets in the shape of the owner's, as of the scheduled
job's last download (2025-11-04): the same row and symbol counts, currencies, exchanges,
platforms and decimal places, the one sell (a full close, listed last), rows out of date order,
several trades on one day, and CRLF line endings. Every value is invented: tickers, quantities,
prices and dates. The config has the shape of cfg_bat.yml: both sheets from Google (the download
is stubbed), a custom symbol map with eur and usd exchange-rate rows, EUR, lite history, not
quiet, log level INFO.
"""

import csv
import logging
from argparse import Namespace
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import run
from conftest import FIXTURES, check_golden
from src import portfolio_mngr

MIRROR = FIXTURES / 'mirror'
SHEETS = {
    'mirror-transactions-sheet': MIRROR / 'transactions.csv',
    'mirror-symbols-sheet': MIRROR / 'symbols.csv',
}
# About eight months after the last trade, as with the scheduled job's last run.
TODAY = date(2024, 10, 11)

# Made-up market: currency, close on EPOCH, growth per week. A ticker that isn't here (such as
# EURUSD=X, which the map lists but EUR as default never needs) fails the run.
EPOCH = date(2022, 10, 31)
MARKET = {
    'ETFA.AS': ('EUR', 70.0, 0.002),
    'ETFB.AS': ('EUR', 98.0, 0.0015),
    'ETFC.AS': ('EUR', 33.0, 0.001),
    'ETFD.AS': ('EUR', 45.0, 0.0025),
    'ETFE.AS': ('EUR', 24.0, 0.0005),
    'NYSA': ('USD', 150.0, 0.001),
    'NASA': ('USD', 180.0, 0.002),
    'NASB': ('USD', 90.0, 0.004),
    'COIN-EUR': ('EUR', 15000.0, 0.012),
    'USDEUR=X': ('EUR', 0.95, -0.0003),
}


def close(ticker: str, day: date) -> float:
    _, base, growth = MARKET[ticker]
    return base * (1 + growth) ** ((day - EPOCH).days / 7)


def in_eur(ticker: str, day: date) -> float:
    price = close(ticker, day)
    return price * close('USDEUR=X', day) if MARKET[ticker][0] == 'USD' else price


class MirrorTicker:
    """Weekly bars on Mondays from the start's week up to the (exclusive) end, as Yahoo gives."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.info = {'currency': MARKET[ticker][0]}

    def history(self, period=None, start=None, end=None, interval=None) -> pd.DataFrame:
        if period == '1d':
            return pd.DataFrame(
                {'Close': [close(self.ticker, TODAY)]}, index=pd.to_datetime([TODAY])
            )
        assert interval == '1wk'
        mondays = pd.date_range(
            start - timedelta(days=start.weekday()), end, freq='W-MON', inclusive='left'
        )
        return pd.DataFrame(
            {'Close': [close(self.ticker, day.date()) for day in mondays]}, index=mondays
        )


class MirrorDatetime(datetime):
    @classmethod
    def today(cls):
        return cls(TODAY.year, TODAY.month, TODAY.day)


class MirrorDate(date):
    @classmethod
    def today(cls):
        return cls(TODAY.year, TODAY.month, TODAY.day)


def download(url: str) -> SimpleNamespace:
    """Stands in for requests.get on a sheet's CSV export URL."""
    sheet_id = url.split('/d/')[1].split('/')[0]
    return SimpleNamespace(status_code=200, content=SHEETS[sheet_id].read_bytes())


def write_cfg(tmp) -> str:
    cfg = tmp / 'cfg_bat.yml'
    cfg.write_text(
        f"""
market-data-origin: yahoo
comp:
  default-currency: EUR
  history-variant: lite
directories:
  generation-dir: {(tmp / 'out').as_posix()}/
  log-dir: {(tmp / 'log').as_posix()}/
  # Set but unused with cloud sources, as in the owner's config.
  transactions-dir: {(tmp / 'unused' / 'transactions.csv').as_posix()}
  symbols-map-dir: {(tmp / 'unused' / 'symbols.csv').as_posix()}
transactions:
  source: cloud
  symbols-standard: custom
  shareable-address: mirror-transactions-sheet
symbols-map:
  source: cloud
  shareable-address: mirror-symbols-sheet
cli-exec:
  quiet: false
  log-level: INFO
""",
        encoding='utf-8',
    )
    return cfg


@pytest.fixture(scope='module')
def mirror(tmp_path_factory) -> SimpleNamespace:
    """Runs the CLI once on the mirror, the way run_script.bat does, minus pip."""
    tmp = tmp_path_factory.mktemp('mirror')
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr('src.market_mngr.yf.Ticker', MirrorTicker)
        patch.setattr('src.sheets_mngr.requests.get', download)
        patch.setattr(run, 'check_internet', lambda: True)
        patch.setattr(portfolio_mngr, 'datetime', MirrorDatetime)
        patch.setattr('src.market_mngr.date', MirrorDate)
        # report_mngr writes its templates/ directory relative to the cwd.
        patch.chdir(tmp)
        plt.close('all')
        exit_code = run.run_cli(Namespace(cfg_file=write_cfg(tmp), is_quiet=None, log_level=None))
        open_figures = plt.get_fignums()
    logger = logging.getLogger('LogManager')
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)
    return SimpleNamespace(exit_code=exit_code, out=tmp / 'out', log=tmp / 'log', figs=open_figures)


def read_csv(path) -> list[dict]:
    with open(path, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


def read_total(path) -> dict:
    total = {}
    for line in path.read_text(encoding='utf-8').splitlines()[4:]:
        _, metric, value, _ = line.split('|')
        total[metric.strip()] = float(value)
    return total


def read_valuation(path) -> dict:
    html = path.read_text(encoding='utf-8')
    section = html.split('<h1>Historical Valuation</h1>')[1].split('<h1>')[0]
    lines = [line.strip() for line in section.split('<br>') if ':' in line]
    return {key: float(value) for key, value in (line.split(': ') for line in lines)}


def holdings(until: str) -> dict:
    """Held quantity per ticker after the trades up to and including a date."""
    tickers = {row['symbol']: row['ticker'] for row in read_csv(MIRROR / 'symbols.csv')}
    held = {}
    for row in read_csv(MIRROR / 'transactions.csv'):
        if row['date'] <= until:
            sign = 1 if row['type'] == 'buy' else -1
            ticker = tickers[row['symbol'].lower()]
            held[ticker] = held.get(ticker, 0) + sign * float(row['quantity'])
    return {ticker: quantity for ticker, quantity in held.items() if quantity}


def test_the_scheduled_job_runs_cleanly(mirror):
    assert mirror.exit_code == 0
    assert mirror.figs == []
    # The sheets were "downloaded" byte for byte.
    sheets = mirror.out / 'sheets'
    assert (sheets / 'transactions.csv').read_bytes() == SHEETS[
        'mirror-transactions-sheet'
    ].read_bytes()
    assert b'\r\n' in (sheets / 'transactions.csv').read_bytes()
    logs = list(mirror.log.glob('app_*.log'))
    assert len(logs) == 1
    log = logs[0].read_text(encoding='utf-8')
    for step in ('Transactions retrieved.', 'Portfolio calculated.', 'HTMLs created.'):
        assert step in log
    for path in ('report.html', 'generated/plots/stocks/history.png', 'generated/misc_tables.html'):
        assert (mirror.out / path).exists(), path


def test_the_outputs_match_golden(mirror):
    for name in ('portfolio.csv', 'total.md', 'entries.md'):
        check_golden(mirror.out / 'generated' / name, f'mirror/{name}')


def test_the_figures_match_a_calculation_by_hand(mirror):
    # The only sell closes ETFA, so every other holding cost the sum of its buys:
    # (price * quantity + fees + ex_fees) / ex_rate.
    tickers = {row['symbol']: row['ticker'] for row in read_csv(MIRROR / 'symbols.csv')}
    cost = {}
    for row in read_csv(MIRROR / 'transactions.csv'):
        if row['type'] == 'buy':
            ticker = tickers[row['symbol'].lower()]
            cost[ticker] = cost.get(ticker, 0) + (
                float(row['price']) * float(row['quantity'])
                + float(row['fees'])
                + float(row['ex_fees'])
            ) / float(row['ex_rate'])
    held = holdings(until=TODAY.isoformat())
    portfolio = {row['symbol']: row for row in read_csv(mirror.out / 'generated' / 'portfolio.csv')}

    assert sorted(portfolio) == sorted(held)
    assert 'ETFA.AS' not in portfolio
    for ticker, quantity in held.items():
        assert float(portfolio[ticker]['amount']) == pytest.approx(quantity)
        assert float(portfolio[ticker]['spending']) == pytest.approx(cost[ticker])
        assert float(portfolio[ticker]['value']) == pytest.approx(quantity * in_eur(ticker, TODAY))
        assert float(portfolio[ticker]['realized_profit']) == 0

    total = read_total(mirror.out / 'generated' / 'total.md')
    assert total['spending'] == pytest.approx(sum(cost[ticker] for ticker in held))
    assert total['value'] == pytest.approx(sum(q * in_eur(t, TODAY) for t, q in held.items()))
    # ETFA: 45 sold at 78.64 less a fee of 2, for six buys that cost 3302.158 with their fees.
    assert cost['ETFA.AS'] == pytest.approx(3302.158)
    assert total['realized_profit'] == pytest.approx(45 * 78.64 - 2 - 3302.158)


def test_the_valuation_is_each_month_ends_holdings_at_market_prices(mirror):
    valuation = read_valuation(mirror.out / 'generated' / 'misc_tables.html')
    # Every month from the first trade's through this one, none skipped.
    months = pd.period_range('2022-11', TODAY.strftime('%Y-%m'), freq='M')
    assert list(valuation) == [month.strftime('%b%y').lower() for month in months]

    def month_end_value(until: str, last_monday: date) -> float:
        return sum(q * in_eur(t, last_monday) for t, q in holdings(until).items())

    # February 2024, when ETFA was sold: its last weekly close is Monday the 26th.
    assert valuation['feb24'] == pytest.approx(month_end_value('2024-02-29', date(2024, 2, 26)))
    # This month: the latest bar is Monday 2024-10-07.
    assert valuation['oct24'] == pytest.approx(month_end_value('2024-10-31', date(2024, 10, 7)))
