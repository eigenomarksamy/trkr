from datetime import date

import pytest

from src.projection import (
    ProjectionCfg,
    invested_last_12_months,
    project_net_worth,
    projection_table,
    resolve_start_value,
)


def make_cfg(**kwargs) -> ProjectionCfg:
    params = dict(
        birth_year=1990,
        retirement_age=40,
        yearly_return=10,
        income=20000,
        income_growth=10,
        invest_percent=10,
    )
    params.update(kwargs)
    return ProjectionCfg(**params)


def test_rows_run_from_start_year_to_retirement_year():
    rows = project_net_worth(make_cfg(), start_value=10000, start_year=2027)
    assert [r.year for r in rows] == [2027, 2028, 2029, 2030]
    assert [r.age for r in rows] == [37, 38, 39, 40]


def test_hand_computed_three_years_without_fees():
    rows = project_net_worth(make_cfg(), start_value=10000, start_year=2028)
    # Year 1: 10000*10% + 2000*5% = 1100. Year 2: income +10%, 13100*10% + 2200*5% = 1420.
    assert [r.income for r in rows] == pytest.approx([20000, 22000, 24200])
    assert [r.contribution for r in rows] == pytest.approx([2000, 2200, 2420])
    assert [r.return_before_fees for r in rows] == pytest.approx([1100, 1420, 1793])
    assert [r.net_worth_before_fees for r in rows] == pytest.approx([13100, 16720, 20933])
    assert [r.net_worth_after_fees for r in rows] == pytest.approx([13100, 16720, 20933])
    assert all(r.net_worth_real is None for r in rows)


def test_fees_reduce_the_return_rate():
    rows = project_net_worth(make_cfg(fees=2), start_value=10000, start_year=2029)
    # 8% after fees: 10000*8% + 2000*4% = 880; 12880*8% + 2200*4% = 1118.4.
    assert [r.return_after_fees for r in rows] == pytest.approx([880, 1118.4])
    assert [r.net_worth_after_fees for r in rows] == pytest.approx([12880, 16198.4])
    assert rows[-1].net_worth_before_fees == pytest.approx(16720)


def test_deposit_in_the_first_year_counts():
    # The C++ tool dropped a year-1 deposit; the port must not.
    cfg = make_cfg(deposits_withdrawals={2029: 5000})
    row = project_net_worth(cfg, start_value=10000, start_year=2029)[0]
    assert row.deposit_withdrawal == 5000
    # 10000*10% + (2000 + 5000)*5% = 1350
    assert row.return_before_fees == pytest.approx(1350)
    assert row.net_worth_before_fees == pytest.approx(18350)


def test_withdrawal_lowers_net_worth():
    cfg = make_cfg(deposits_withdrawals={2030: -3000})
    rows = project_net_worth(cfg, start_value=10000, start_year=2029)
    assert rows[1].deposit_withdrawal == -3000
    # 13100*10% + (2200 - 3000)*5% = 1270
    assert rows[1].net_worth_before_fees == pytest.approx(13100 + 2200 - 3000 + 1270)


def test_real_value_discounts_by_years_from_today():
    rows = project_net_worth(make_cfg(inflation=2), start_value=10000, start_year=2028)
    assert rows[0].net_worth_real == pytest.approx(13100 / 1.02)
    assert rows[2].net_worth_real == pytest.approx(20933 / 1.02**3)


def test_no_rows_once_retirement_year_has_passed():
    assert project_net_worth(make_cfg(), start_value=10000, start_year=2031) == []


# Output of the C++ investor.exe (after the year-1 fix) for the same made-up inputs:
# initial 20000, income 40000, +3%/yr, invest 20%, return 6%, fees 1%, ages 30-40,
# deposits/withdrawals in years 1, 4 and 7. Columns: net worth, net worth after fees.
CPP_NET_WORTH = [
    (34590.000000, 34325.000000),
    (45152.601562, 44487.250000),
    (56603.574219, 55410.992188),
    (60763.859375, 58941.902344),
    (73683.882812, 71118.171875),
    (87657.328125, 84180.125000),
    (105845.757812, 101255.359375),
    (122330.664062, 116403.093750),
    (140108.687500, 132610.765625),
    (159266.531250, 149940.437500),
    (179896.390625, 168457.562500),
]


def test_matches_cpp_tool():
    cfg = ProjectionCfg(
        birth_year=1997,
        retirement_age=40,
        yearly_return=6,
        fees=1,
        income=40000,
        income_growth=3,
        invest_percent=20,
        deposits_withdrawals={2027: 5000, 2030: -8000, 2033: 3000},
    )
    rows = project_net_worth(cfg, start_value=20000, start_year=2027)
    actual = [(r.net_worth_before_fees, r.net_worth_after_fees) for r in rows]
    # The C++ tool accumulates in 32-bit floats.
    assert actual == [pytest.approx(row, rel=1e-5) for row in CPP_NET_WORTH]


def test_start_value_from_portfolio_name_or_number_plus_cash():
    values = {'portfolio': 1000.0, 'paper': 2500.0}
    assert resolve_start_value(make_cfg(cash=50), values) == 1050
    assert resolve_start_value(make_cfg(start_net_worth='paper'), values) == 2500
    assert resolve_start_value(make_cfg(start_net_worth=300, cash=50), values) == 350


def test_invested_last_12_months_counts_only_the_trailing_year():
    spending = {'sep23': 999, 'oct23': 100, 'mar24': 50, 'sep24': 25}
    assert invested_last_12_months(spending, date(2024, 9, 15)) == 175


def test_projection_table_drops_real_column_without_inflation():
    rows = project_net_worth(make_cfg(), start_value=10000, start_year=2030)
    headers, lines = projection_table(rows, labels=False)
    assert 'net_worth_real' not in headers
    assert lines[0][:2] == [2030, 40]
    headers, _ = projection_table(
        project_net_worth(make_cfg(inflation=2), 10000, 2030), labels=True
    )
    assert headers[-1] == "Net worth (after fees, today's money)"
