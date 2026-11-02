import { describe, expect, it } from 'vitest';
import demo from '../public/demo-snapshot.json?raw';
import { projectionProblem, projectionYaml, projectNetWorth, resolveStartValue } from '../src/projection';
import { parseSnapshot, type ProjectionInputs } from '../src/snapshot';

function inputs(overrides: Partial<ProjectionInputs> = {}): ProjectionInputs {
  return {
    birth_year: 1990,
    retirement_age: 40,
    yearly_return: 10,
    start_net_worth: 'portfolio',
    cash: 0,
    income: 20000,
    income_growth: 10,
    invest_percent: 10,
    fees: 0,
    inflation: null,
    deposits_withdrawals: {},
    ...overrides,
  };
}

const close = (values: number[]) => values.map((value) => expect.closeTo(value, 6));

describe('projectNetWorth', () => {
  // The same cases as tests/test_projection.py.
  it('runs from the start year to the retirement year', () => {
    const rows = projectNetWorth(inputs(), 10000, 2027);
    expect(rows.map((r) => r.year)).toEqual([2027, 2028, 2029, 2030]);
    expect(rows.map((r) => r.age)).toEqual([37, 38, 39, 40]);
  });

  it('matches three years computed by hand', () => {
    const rows = projectNetWorth(inputs(), 10000, 2028);
    // Year 1: 10000*10% + 2000*5% = 1100. Year 2: income +10%, 13100*10% + 2200*5% = 1420.
    expect(rows.map((r) => r.income)).toEqual(close([20000, 22000, 24200]));
    expect(rows.map((r) => r.return_before_fees)).toEqual(close([1100, 1420, 1793]));
    expect(rows.map((r) => r.net_worth_after_fees)).toEqual(close([13100, 16720, 20933]));
    expect(rows.every((r) => r.net_worth_real === null)).toBe(true);
  });

  it('takes the fees off the return rate', () => {
    const rows = projectNetWorth(inputs({ fees: 2 }), 10000, 2029);
    // 8% after fees: 10000*8% + 2000*4% = 880; 12880*8% + 2200*4% = 1118.4.
    expect(rows.map((r) => r.return_after_fees)).toEqual(close([880, 1118.4]));
    expect(rows.at(-1)?.net_worth_before_fees).toBeCloseTo(16720, 6);
  });

  it('gives the rows the CLI gave for the demo', () => {
    const projection = parseSnapshot(demo).projection;
    if (!projection) throw new Error('The demo has no projection.');
    const rows = projectNetWorth(projection.inputs, projection.start_value, projection.start_year);
    expect(rows.length).toBe(projection.rows.length);
    rows.forEach((row, i) => {
      for (const [key, value] of Object.entries(projection.rows[i] ?? {})) {
        const ours = row[key as keyof typeof row];
        if (value === null) {
          expect(ours).toBeNull();
        } else {
          // Python and JavaScript may round a power differently in the last bit.
          expect(Math.abs((ours as number) - value)).toBeLessThanOrEqual(1e-9 * Math.max(1, Math.abs(value)));
        }
      }
    });
  });
});

describe('resolveStartValue', () => {
  it('adds cash to a portfolio value or a fixed amount', () => {
    expect(resolveStartValue(inputs({ cash: 100 }), { portfolio: 2392 })).toBe(2492);
    expect(resolveStartValue(inputs({ start_net_worth: 'paper', cash: 1 }), { portfolio: 5, paper: 9 })).toBe(10);
    expect(resolveStartValue(inputs({ start_net_worth: 50, cash: 1 }), {})).toBe(51);
  });
});

describe('projectionProblem', () => {
  const names = ['portfolio', 'paper'];

  it('accepts good inputs', () => {
    expect(projectionProblem(inputs(), names, 2026)).toBeNull();
  });

  it('words problems as the CLI does', () => {
    expect(projectionProblem(inputs({ birth_year: Number.NaN }), names, 2026)).toBe('projection: birth-year is required.');
    expect(projectionProblem(inputs({ retirement_age: 40.5 }), names, 2026)).toBe(
      'projection: retirement-age must be a whole number.',
    );
    expect(projectionProblem(inputs({ start_net_worth: 'other' }), names, 2026)).toMatch(/start-net-worth/);
    expect(projectionProblem(inputs({ invest_percent: 101 }), names, 2026)).toBe(
      'projection: invest-percent must be between 0 and 100.',
    );
    expect(projectionProblem(inputs({ fees: -1 }), names, 2026)).toBe('projection: fees must not be negative.');
    expect(projectionProblem(inputs({ inflation: -100 }), names, 2026)).toBe('projection: inflation must be above -100.');
    expect(projectionProblem(inputs(), names, 2030)).toMatch(/nothing to project/);
  });
});

describe('projectionYaml', () => {
  it('writes a block in the config schema', () => {
    const yaml = projectionYaml(
      inputs({ start_net_worth: 'paper', inflation: 2, deposits_withdrawals: { '2031': 5, '2030': -15000 } }),
    );
    expect(yaml).toBe(
      [
        'projection:',
        '  birth-year: 1990',
        '  retirement-age: 40',
        "  start-net-worth: 'paper'",
        '  cash: 0',
        '  income: 20000',
        '  income-growth: 10',
        '  invest-percent: 10',
        '  return: 10',
        '  fees: 0',
        '  inflation: 2',
        '  deposits-withdrawals:',
        '    2030: -15000',
        '    2031: 5',
        '',
      ].join('\n'),
    );
  });
});
