"""The snapshot each run writes for the web app (src/snapshot.py)."""

import csv
import json
from datetime import date, datetime

import pytest

import run
from conftest import FIXTURES, check_golden, make_cfg
from src.snapshot import SCHEMA_VERSION, write_snapshot


def read_json(path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def test_snapshot_matches_golden(offline):
    run.exec(make_cfg(offline))
    out = offline / 'out'
    check_golden(out / 'snapshot.json', 'exec/snapshot.json')
    # The run's own copy is named after its (frozen) run time.
    copy = out / 'snapshots' / '20240630_120000.json'
    assert copy.read_bytes() == (out / 'snapshot.json').read_bytes()
    assert not list(out.rglob('*.tmp'))


def test_snapshot_has_iso_months_and_dates(offline):
    run.exec(make_cfg(offline))
    snapshot = read_json(offline / 'out' / 'snapshot.json')
    assert snapshot['schema'] == 'trkr-snapshot'
    assert snapshot['schema_version'] == SCHEMA_VERSION
    assert snapshot['generated_at'] == '2024-06-30T12:00:00'
    portfolio = snapshot['portfolio']
    assert [h['symbol'] for h in portfolio['holdings']] == ['AAA.AS', 'BBB']
    assert portfolio['entry_points'] == {'AAA.AS': '2024-01', 'BBB': '2024-02'}
    assert [m['month'] for m in portfolio['valuation']] == [
        '2024-01',
        '2024-02',
        '2024-03',
        '2024-04',
        '2024-05',
        '2024-06',
    ]
    assert [m['month'] for m in portfolio['monthly_spending']] == [
        '2024-01',
        '2024-02',
        '2024-03',
        '2024-04',
    ]
    # 10 @ 50 + 1, (5 @ 100 + 1 + 0.5) / 1.1, 4 @ 55 + 1
    assert sum(m['amount'] for m in portfolio['monthly_spending']) == pytest.approx(
        501 + 501.5 / 1.1 + 221
    )
    assert [t['date'] for t in portfolio['transactions']] == [
        '2024-01-15',
        '2024-02-12',
        '2024-04-08',
    ]
    assert portfolio['transactions'][0]['platform'] == 'broker-x'
    # Lite history: one close per month, dated the 1st. June's is its last weekly close, on
    # Monday the 24th, the 26th bar: 50 * 1.25.
    closes = portfolio['prices']['AAA.AS']
    assert [c['date'] for c in closes][:2] == ['2024-01-01', '2024-02-01']
    assert closes[-1] == {'date': '2024-06-01', 'close': 62.5}


def test_snapshot_holds_no_paths(offline):
    run.exec(make_cfg(offline))
    text = (offline / 'out' / 'snapshot.json').read_text(encoding='utf-8')
    for path in (offline, FIXTURES):
        assert path.as_posix() not in text
        assert str(path) not in text
    assert read_json(offline / 'out' / 'snapshot.json')['config'] == {
        'default_currency': 'EUR',
        'history_variant': 'lite',
        'sources': {'transactions': 'local', 'symbols_map': 'local', 'positions': None},
    }


def test_snapshot_with_imaginary_portfolio_and_projection(offline):
    year = date.today().year
    run.exec(
        make_cfg(
            offline,
            f"""
imaginary-portfolios:
  - name: paper
    source: local
    transactions-dir: {(FIXTURES / 'transactions_imaginary.csv').as_posix()}
projection:
  birth-year: {year - 30}
  retirement-age: 35
  start-net-worth: paper
  cash: 100
  income: 30000
  invest-percent: 10
  return: 6
  fees: 0.5
  inflation: 2
  deposits-withdrawals:
    {year + 2}: -500
""",
        )
    )
    out = offline / 'out'
    snapshot = read_json(out / 'snapshot.json')
    [paper] = snapshot['imaginary']
    assert paper['name'] == 'paper'
    assert [h['symbol'] for h in paper['holdings']] == ['BBB']
    assert paper['total']['value'] == pytest.approx(2392)

    projection = snapshot['projection']
    assert projection['start_year'] == year + 1
    assert projection['start_value'] == pytest.approx(2492)
    assert projection['inputs']['start_net_worth'] == 'paper'
    assert projection['inputs']['deposits_withdrawals'] == {str(year + 2): -500}
    with open(out / 'generated' / 'projection.csv', newline='', encoding='utf-8') as file:
        table = list(csv.DictReader(file))
    assert len(projection['rows']) == len(table)
    for row, line in zip(projection['rows'], table, strict=True):
        for column, value in line.items():
            assert row[column] == pytest.approx(float(value), abs=0.005), column


def test_write_snapshot_turns_nan_into_null(tmp_path):
    snapshot = {'generated_at': datetime(2024, 1, 2, 3, 4, 5).isoformat(), 'close': float('nan')}
    copy = write_snapshot(snapshot, tmp_path / 'snapshot.json', tmp_path / 'snapshots')
    assert copy == tmp_path / 'snapshots' / '20240102_030405.json'
    assert read_json(tmp_path / 'snapshot.json')['close'] is None
