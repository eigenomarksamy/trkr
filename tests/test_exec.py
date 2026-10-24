import csv
from datetime import date

import pytest

import run
from conftest import FIXTURES, check_golden, make_cfg


def check_real_portfolio_outputs(out):
    generated = out / 'generated'
    for name in ('portfolio.csv', 'total.md', 'entries.md'):
        check_golden(generated / name, f'exec/{name}')
    for path in (
        'report.html',
        'generated/transactions.html',
        'generated/misc_tables.html',
        'generated/figs_historical.html',
        'generated/plots/stocks/history.png',
        'generated/plots/stocks/history_aaa.as.png',
        'generated/plots/gen_stats_pie_spending_percent.png',
        'generated/plots/gen_stats_points_valuation_percent.png',
    ):
        assert (out / path).exists(), path


def test_exec_matches_golden(offline):
    run.exec(make_cfg(offline))
    out = offline / 'out'
    check_real_portfolio_outputs(out)
    report = (out / 'report.html').read_text()
    assert 'Imaginary Portfolios' not in report
    assert 'Net-worth Projection' not in report
    assert not (out / 'imaginary').exists()
    assert not (out / 'generated' / 'projection.csv').exists()


def test_exec_with_imaginary_portfolio_and_projection(offline):
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
    check_real_portfolio_outputs(out)

    paper = out / 'imaginary' / 'paper'
    with open(paper / 'generated' / 'portfolio.csv', newline='') as file:
        holdings = list(csv.DictReader(file))
    assert [h['symbol'] for h in holdings] == ['BBB']
    # 20 shares at 130 USD, converted at 0.92
    assert float(holdings[0]['value']) == pytest.approx(2392)
    assert 'Imaginary Portfolio: paper' in (paper / 'report.html').read_text()

    generated = out / 'generated'
    with open(generated / 'projection.csv', newline='') as file:
        rows = list(csv.DictReader(file))
    assert [int(r['year']) for r in rows] == list(range(year + 1, year + 6))
    assert float(rows[1]['deposit_withdrawal']) == -500
    # Starts from paper's 2392 plus 100 cash: 2492 + 3000 + 2492*6% + 3000*3%
    assert float(rows[0]['net_worth_before_fees']) == pytest.approx(5731.52)
    assert 'net_worth_real' in rows[0]
    for path in ('projection.md', 'projection.html', 'plots/projection.png'):
        assert (generated / path).exists(), path

    report = (out / 'report.html').read_text()
    assert 'Imaginary Portfolios' in report
    assert 'imaginary/paper/report.html' in report
    assert 'Net-worth Projection' in report
    assert "imaginary portfolio 'paper' plus 100.00 cash" in report


def test_exec_with_opening_positions(offline):
    run.exec(
        make_cfg(
            offline,
            f"""
positions:
  source: local
  positions-dir: {(FIXTURES / 'positions.csv').as_posix()}
""",
        )
    )
    generated = offline / 'out' / 'generated'
    with open(generated / 'portfolio.csv', newline='') as file:
        holdings = {row['symbol']: row for row in csv.DictReader(file)}
    # Opening 20 @ 40 plus the fixture trades (10 @ 50 + 1 fee, 4 @ 55 + 1 fee)
    assert float(holdings['AAA.AS']['amount']) == 34
    assert float(holdings['AAA.AS']['spending']) == pytest.approx(800 + 722)
    assert float(holdings['AAA.AS']['break_even_price']) == pytest.approx(1522 / 34)
    # Opening 3 @ 90 USD at ex_rate 1.2, plus the fixture trade
    assert float(holdings['BBB']['amount']) == 8
    assert float(holdings['BBB']['spending']) == pytest.approx(225 + 501.5 / 1.1)
    assert 'positions file' in (generated / 'transactions.html').read_text()
