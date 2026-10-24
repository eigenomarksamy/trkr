from datetime import date
from dataclasses import dataclass, field, fields
from typing import Optional, Union
from dateutil.relativedelta import relativedelta
from src.portfolio_mngr import convert_date_to_short_str

# Ported from the owner's C++ networth_projection tool. Percentages are whole
# numbers (7 means 7%), as there.

@dataclass
class ProjectionCfg:
    birth_year: int
    retirement_age: int
    yearly_return: float
    # A number, 'portfolio' (the real portfolio's value) or an imaginary portfolio's name.
    start_net_worth: Union[float, str] = 'portfolio'
    cash: float = 0
    income: float = 0
    income_growth: float = 0
    invest_percent: float = 0
    fees: float = 0
    inflation: Optional[float] = None
    # Calendar year -> amount; negative amounts are withdrawals.
    deposits_withdrawals: dict[int, float] = field(default_factory=dict)

@dataclass
class ProjectionRow:
    year: int
    age: int
    income: float
    contribution: float
    deposit_withdrawal: float
    return_before_fees: float
    net_worth_before_fees: float
    return_after_fees: float
    net_worth_after_fees: float
    net_worth_real: Optional[float]

ROW_LABELS = {
    'year': 'Year',
    'age': 'Age',
    'income': 'Income',
    'contribution': 'Contribution',
    'deposit_withdrawal': 'Deposit/Withdrawal',
    'return_before_fees': 'Return',
    'net_worth_before_fees': 'Net worth',
    'return_after_fees': 'Return (after fees)',
    'net_worth_after_fees': 'Net worth (after fees)',
    'net_worth_real': "Net worth (after fees, today's money)",
}

def project_net_worth(cfg: ProjectionCfg, start_value: float,
                      start_year: int) -> list[ProjectionRow]:
    """One row per year, from start_year to the year of retirement.

    Row n is the state n years after start_value was measured, so the first
    row is a full year away and the real value is discounted by n years.
    """
    rows = []
    income = cfg.income
    net_worth_before_fees = start_value
    net_worth_after_fees = start_value
    rate_before_fees = cfg.yearly_return / 100
    rate_after_fees = (cfg.yearly_return - cfg.fees) / 100
    retirement_year = cfg.birth_year + cfg.retirement_age
    for n, year in enumerate(range(start_year, retirement_year + 1), start=1):
        if n > 1:
            income *= 1 + cfg.income_growth / 100
        contribution = income * cfg.invest_percent / 100
        deposit_withdrawal = cfg.deposits_withdrawals.get(year, 0)
        new_money = contribution + deposit_withdrawal
        # New money arrives through the year, so it earns half a year's return.
        return_before_fees = net_worth_before_fees * rate_before_fees + new_money * rate_before_fees / 2
        return_after_fees = net_worth_after_fees * rate_after_fees + new_money * rate_after_fees / 2
        net_worth_before_fees += new_money + return_before_fees
        net_worth_after_fees += new_money + return_after_fees
        net_worth_real = None
        if cfg.inflation is not None:
            net_worth_real = net_worth_after_fees / (1 + cfg.inflation / 100) ** n
        rows.append(ProjectionRow(year=year, age=year - cfg.birth_year,
                                  income=income, contribution=contribution,
                                  deposit_withdrawal=deposit_withdrawal,
                                  return_before_fees=return_before_fees,
                                  net_worth_before_fees=net_worth_before_fees,
                                  return_after_fees=return_after_fees,
                                  net_worth_after_fees=net_worth_after_fees,
                                  net_worth_real=net_worth_real))
    return rows

def resolve_start_value(cfg: ProjectionCfg, portfolio_values: dict[str, float]) -> float:
    if isinstance(cfg.start_net_worth, str):
        start_value = portfolio_values[cfg.start_net_worth]
    else:
        start_value = cfg.start_net_worth
    return start_value + cfg.cash

def invested_last_12_months(spending_history: dict, today: date) -> float:
    """Sums Portfolio.compute_spending_history over this month and the 11 before it."""
    months = [convert_date_to_short_str(date=today - relativedelta(months=i)) for i in range(12)]
    return sum(spending_history.get(month, 0) for month in months)

def projection_table(rows: list[ProjectionRow], labels: bool) -> tuple[list[str], list[list]]:
    """Headers and rows for writing out, money rounded to cents.

    The real-value column is left out when no inflation was configured.
    """
    names = [f.name for f in fields(ProjectionRow)]
    if not rows or rows[0].net_worth_real is None:
        names.remove('net_worth_real')
    headers = [ROW_LABELS[name] for name in names] if labels else names
    lines = []
    for row in rows:
        line = []
        for name in names:
            value = getattr(row, name)
            line.append(value if name in ('year', 'age') else round(float(value), 2))
        lines.append(line)
    return headers, lines
