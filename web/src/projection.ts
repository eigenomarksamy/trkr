// A port of src/projection.py and the projection checks in src/cfg_mngr.py, so the
// projection can be recomputed in the browser as its inputs change. Keep the two in step:
// test/projection.test.ts checks this port against rows the CLI computed.

import type { ProjectionInputs, ProjectionRow } from './snapshot';

/** One row per year, from startYear to the year of retirement (project_net_worth). */
export function projectNetWorth(
  inputs: ProjectionInputs,
  startValue: number,
  startYear: number,
): ProjectionRow[] {
  const rows: ProjectionRow[] = [];
  let income = inputs.income;
  let netWorthBeforeFees = startValue;
  let netWorthAfterFees = startValue;
  const rateBeforeFees = inputs.yearly_return / 100;
  const rateAfterFees = (inputs.yearly_return - inputs.fees) / 100;
  const retirementYear = inputs.birth_year + inputs.retirement_age;
  for (let year = startYear, n = 1; year <= retirementYear; year++, n++) {
    if (n > 1) income *= 1 + inputs.income_growth / 100;
    const contribution = (income * inputs.invest_percent) / 100;
    const depositWithdrawal = inputs.deposits_withdrawals[String(year)] ?? 0;
    const newMoney = contribution + depositWithdrawal;
    // New money arrives through the year, so it earns half a year's return.
    const returnBeforeFees = netWorthBeforeFees * rateBeforeFees + (newMoney * rateBeforeFees) / 2;
    const returnAfterFees = netWorthAfterFees * rateAfterFees + (newMoney * rateAfterFees) / 2;
    netWorthBeforeFees += newMoney + returnBeforeFees;
    netWorthAfterFees += newMoney + returnAfterFees;
    rows.push({
      year,
      age: year - inputs.birth_year,
      income,
      contribution,
      deposit_withdrawal: depositWithdrawal,
      return_before_fees: returnBeforeFees,
      net_worth_before_fees: netWorthBeforeFees,
      return_after_fees: returnAfterFees,
      net_worth_after_fees: netWorthAfterFees,
      net_worth_real:
        inputs.inflation === null ? null : netWorthAfterFees / (1 + inputs.inflation / 100) ** n,
    });
  }
  return rows;
}

/** The start value: a portfolio's value or a fixed amount, plus cash (resolve_start_value). */
export function resolveStartValue(
  inputs: ProjectionInputs,
  portfolioValues: Record<string, number>,
): number {
  const start =
    typeof inputs.start_net_worth === 'string'
      ? (portfolioValues[inputs.start_net_worth] ?? Number.NaN)
      : inputs.start_net_worth;
  return start + inputs.cash;
}

/**
 * The first problem with the inputs, worded as the CLI words it (parse_projection_cfg), or
 * null. portfolioNames holds 'portfolio' and each imaginary portfolio's name.
 */
export function projectionProblem(
  inputs: ProjectionInputs,
  portfolioNames: string[],
  currentYear: number,
): string | null {
  const numbers: [string, number | null][] = [
    ['birth-year', inputs.birth_year],
    ['retirement-age', inputs.retirement_age],
    ['return', inputs.yearly_return],
    ['cash', inputs.cash],
    ['income', inputs.income],
    ['income-growth', inputs.income_growth],
    ['invest-percent', inputs.invest_percent],
    ['fees', inputs.fees],
    ['inflation', inputs.inflation],
  ];
  for (const [key, value] of numbers) {
    if (key === 'inflation' && value === null) continue;
    if (value === null || !Number.isFinite(value)) {
      return ['birth-year', 'retirement-age', 'return'].includes(key)
        ? `projection: ${key} is required.`
        : `projection: ${key} must be a number.`;
    }
  }
  for (const [key, value] of [
    ['birth-year', inputs.birth_year],
    ['retirement-age', inputs.retirement_age],
  ] as const) {
    if (!Number.isInteger(value)) return `projection: ${key} must be a whole number.`;
  }
  const start = inputs.start_net_worth;
  if (typeof start === 'string' ? !portfolioNames.includes(start) : !Number.isFinite(start)) {
    return "projection: start-net-worth must be a number, 'portfolio' or an imaginary portfolio's name.";
  }
  if (inputs.invest_percent < 0 || inputs.invest_percent > 100) {
    return 'projection: invest-percent must be between 0 and 100.';
  }
  if (inputs.fees < 0) return 'projection: fees must not be negative.';
  for (const [key, value] of [
    ['return', inputs.yearly_return],
    ['income-growth', inputs.income_growth],
    ['inflation', inputs.inflation ?? 0],
  ] as const) {
    if (value <= -100) return `projection: ${key} must be above -100.`;
  }
  for (const [year, amount] of Object.entries(inputs.deposits_withdrawals)) {
    if (!/^\d+$/.test(year) || !Number.isFinite(amount)) {
      return 'projection: deposits-withdrawals must map calendar years to amounts.';
    }
  }
  if (inputs.birth_year + inputs.retirement_age <= currentYear) {
    return 'projection: retirement-age is reached this year or earlier, so there is nothing to project.';
  }
  return null;
}

/** The inputs as a projection: block to paste into the config. */
export function projectionYaml(inputs: ProjectionInputs): string {
  const start =
    typeof inputs.start_net_worth === 'number' || inputs.start_net_worth === 'portfolio'
      ? String(inputs.start_net_worth)
      : `'${inputs.start_net_worth}'`;
  const lines = [
    'projection:',
    `  birth-year: ${inputs.birth_year}`,
    `  retirement-age: ${inputs.retirement_age}`,
    `  start-net-worth: ${start}`,
    `  cash: ${inputs.cash}`,
    `  income: ${inputs.income}`,
    `  income-growth: ${inputs.income_growth}`,
    `  invest-percent: ${inputs.invest_percent}`,
    `  return: ${inputs.yearly_return}`,
    `  fees: ${inputs.fees}`,
  ];
  if (inputs.inflation !== null) lines.push(`  inflation: ${inputs.inflation}`);
  const plan = Object.entries(inputs.deposits_withdrawals).sort(([a], [b]) => Number(a) - Number(b));
  if (plan.length > 0) {
    lines.push('  deposits-withdrawals:');
    for (const [year, amount] of plan) lines.push(`    ${year}: ${amount}`);
  }
  return lines.join('\n') + '\n';
}
