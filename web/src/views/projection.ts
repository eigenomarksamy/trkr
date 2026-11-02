import type { Context } from '../app';
import { lineChart, tableView } from '../chart';
import { h, mount, type Child } from '../dom';
import { money, monthDate } from '../format';
import { projectionProblem, projectionYaml, projectNetWorth, resolveStartValue } from '../projection';
import type { ProjectionInputs, ProjectionRow, Snapshot } from '../snapshot';

// Used when the config has no projection: block. The form starts with them.
const BLANK: ProjectionInputs = {
  birth_year: Number.NaN,
  retirement_age: 65,
  yearly_return: 7,
  start_net_worth: 'portfolio',
  cash: 0,
  income: 0,
  income_growth: 0,
  invest_percent: 0,
  fees: 0,
  inflation: null,
  deposits_withdrawals: {},
};

// The owner's edits, kept while the same snapshot is open.
let edited: { snapshot: Snapshot; inputs: ProjectionInputs } | null = null;

interface Field {
  key: Exclude<keyof ProjectionInputs, 'start_net_worth' | 'deposits_withdrawals'>;
  label: string;
  hint?: string;
  // Empty means: required (NaN), 0, or not set (null).
  empty: number | null;
}

const FIELDS: Field[] = [
  { key: 'birth_year', label: 'Birth year', empty: Number.NaN },
  { key: 'retirement_age', label: 'Retirement age', empty: Number.NaN },
  { key: 'cash', label: 'Cash', hint: 'Added to the start value', empty: 0 },
  { key: 'income', label: 'Income', hint: 'Yearly', empty: 0 },
  { key: 'income_growth', label: 'Income growth %', hint: 'A year', empty: 0 },
  { key: 'invest_percent', label: 'Invested %', hint: 'Of income', empty: 0 },
  { key: 'yearly_return', label: 'Return %', hint: 'A year, before fees', empty: Number.NaN },
  { key: 'fees', label: 'Fees %', hint: 'A year', empty: 0 },
  { key: 'inflation', label: 'Inflation %', hint: 'Optional: adds today’s money', empty: null },
];

function startYearOf(snapshot: Snapshot): number {
  return snapshot.projection?.start_year ?? new Date(snapshot.generated_at).getFullYear() + 1;
}

function investedLast12Months(snapshot: Snapshot): number {
  if (snapshot.projection) return snapshot.projection.invested_last_12_months;
  const run = new Date(snapshot.generated_at);
  const from = new Date(run.getFullYear(), run.getMonth() - 11, 1).getTime();
  return snapshot.portfolio.monthly_spending
    .filter((m) => monthDate(m.month).getTime() >= from && monthDate(m.month).getTime() <= run.getTime())
    .reduce((sum, m) => sum + m.amount, 0);
}

function planText(plan: Record<string, number>): string {
  return Object.entries(plan)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([year, amount]) => `${year}: ${amount}`)
    .join('\n');
}

/** "2030: -15000" per line; null when a line doesn't read. */
function parsePlan(text: string): Record<string, number> | null {
  const plan: Record<string, number> = {};
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    const match = /^\s*(\d{4})\s*[:=,]?\s*(-?\d+(?:\.\d+)?)\s*$/.exec(line);
    if (!match?.[1] || !match[2]) return null;
    plan[match[1]] = Number(match[2]);
  }
  return plan;
}

export function projectionPage(context: Context): Child[] {
  const { snapshot, currency } = context;
  const original = snapshot.projection?.inputs ?? BLANK;
  if (edited?.snapshot !== snapshot) edited = { snapshot, inputs: structuredClone(original) };
  const startYear = startYearOf(snapshot);
  const portfolioValues: Record<string, number> = { portfolio: snapshot.portfolio.total.value };
  for (const p of snapshot.imaginary) portfolioValues[p.name] = p.total.value;
  const startNames = Object.keys(portfolioValues);

  const inputs = new Map<Field['key'], HTMLInputElement>();
  const startChoice = h(
    'select',
    { id: 'start' },
    h('option', { value: 'portfolio' }, `Real portfolio (${money(portfolioValues.portfolio, currency)})`),
    snapshot.imaginary.map((p) => h('option', { value: p.name }, `${p.name}, imaginary (${money(p.total.value, currency)})`)),
    h('option', { value: '' }, 'A fixed amount'),
  );
  const fixedAmount = h('input', { id: 'start-amount', type: 'number', step: 'any', inputmode: 'decimal' });
  const plan = h('textarea', { id: 'plan', rows: 3, spellcheck: 'false', placeholder: '2030: -15000' });
  const problem = h('p', { class: 'notice error', role: 'alert', hidden: true });
  const results = h('div', { class: 'results' });

  const fill = (values: ProjectionInputs) => {
    for (const field of FIELDS) {
      const value = values[field.key];
      const input = inputs.get(field.key);
      if (input) input.value = value === null || Number.isNaN(value) ? '' : String(value);
    }
    if (typeof values.start_net_worth === 'string') {
      startChoice.value = values.start_net_worth;
      fixedAmount.value = '';
    } else {
      startChoice.value = '';
      fixedAmount.value = String(values.start_net_worth);
    }
    fixedAmount.hidden = startChoice.value !== '';
    plan.value = planText(values.deposits_withdrawals);
  };

  const read = (): ProjectionInputs | string => {
    const values = { ...BLANK };
    for (const field of FIELDS) {
      const text = inputs.get(field.key)?.value.trim() ?? '';
      (values[field.key] as number | null) = text === '' ? field.empty : Number(text);
    }
    values.start_net_worth = startChoice.value || (fixedAmount.value.trim() === '' ? Number.NaN : Number(fixedAmount.value));
    const parsed = parsePlan(plan.value);
    if (!parsed) return 'projection: deposits-withdrawals must map calendar years to amounts, one "year: amount" per line.';
    values.deposits_withdrawals = parsed;
    return values;
  };

  const update = () => {
    fixedAmount.hidden = startChoice.value !== '';
    const values = read();
    const message = typeof values === 'string' ? values : projectionProblem(values, startNames, startYear - 1);
    problem.textContent = message ?? '';
    problem.hidden = message === null;
    // An invalid input keeps the last good result on screen, dimmed.
    results.classList.toggle('stale', message !== null);
    if (message !== null || typeof values === 'string') return;
    edited = { snapshot, inputs: values };
    const startValue = resolveStartValue(values, portfolioValues);
    mount(results, outcome(values, projectNetWorth(values, startValue, startYear), startValue, snapshot, currency));
  };

  const form = h(
    'form',
    { class: 'projection-form', onsubmit: (event: Event) => event.preventDefault(), oninput: update, onchange: update },
    h(
      'div',
      { class: 'field' },
      h('label', { for: 'start' }, 'Start from'),
      startChoice,
      fixedAmount,
    ),
    FIELDS.map((field) => {
      const input = h('input', { id: field.key, type: 'number', step: 'any', inputmode: 'decimal' });
      inputs.set(field.key, input);
      return h(
        'div',
        { class: 'field' },
        h('label', { for: field.key }, field.label),
        input,
        field.hint ? h('span', { class: 'hint' }, field.hint) : null,
      );
    }),
    h(
      'div',
      { class: 'field wide' },
      h('label', { for: 'plan' }, 'Deposits and withdrawals'),
      plan,
      h('span', { class: 'hint' }, 'One "year: amount" per line; negative amounts are withdrawals.'),
    ),
    h(
      'div',
      { class: 'field wide buttons' },
      h(
        'button',
        {
          type: 'button',
          class: 'button quiet',
          onclick: () => {
            fill(original);
            update();
          },
        },
        snapshot.projection ? 'Back to the config’s values' : 'Clear',
      ),
    ),
  );

  fill(edited.inputs);
  update();

  return [
    h('h1', null, 'Projection'),
    h(
      'p',
      { class: 'muted' },
      snapshot.projection
        ? 'Starts from the config’s projection block. Change any input to see what happens; nothing is saved, and the config stays as it is.'
        : 'The config has no projection block, so fill in at least your birth year. Nothing is saved.',
    ),
    h(
      'p',
      { class: 'muted' },
      `Invested in the 12 months to the snapshot: ${money(investedLast12Months(snapshot), currency)}.`,
    ),
    form,
    problem,
    results,
  ];
}

function outcome(
  inputs: ProjectionInputs,
  rows: ProjectionRow[],
  startValue: number,
  snapshot: Snapshot,
  currency: string,
): Node[] {
  const last = rows[rows.length - 1];
  if (!last) return [];
  const real = inputs.inflation !== null;
  const series = [
    { name: 'Net worth', values: rows.map((r) => r.net_worth_before_fees) },
    { name: 'After fees', values: rows.map((r) => r.net_worth_after_fees) },
  ];
  if (real) series.push({ name: 'After fees, today’s money', values: rows.map((r) => r.net_worth_real ?? 0) });
  const yaml = projectionYaml(inputs);
  const copy = h('button', { type: 'button', class: 'button quiet' }, 'Copy');
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(yaml);
      copy.textContent = 'Copied';
    } catch {
      copy.textContent = 'Select the text to copy it';
    }
  });
  return [
    h(
      'p',
      { class: 'headline' },
      `At ${last.age}, in ${last.year}: `,
      h('strong', null, money(last.net_worth_after_fees, currency)),
      ` after fees`,
      real ? `, ${money(last.net_worth_real, currency)} in today’s money` : '',
      `. Before fees: ${money(last.net_worth_before_fees, currency)}.`,
    ),
    h(
      'p',
      { class: 'muted' },
      `Starts at ${money(startValue, currency)} and invests ${money(rows[0]?.contribution, currency)} in ${rows[0]?.year}. Snapshot of ${snapshot.generated_at.slice(0, 10)}.`,
    ),
    h(
      'section',
      { class: 'card' },
      h('h2', null, 'Net worth by year'),
      lineChart({
        label: 'Projected net worth by year',
        x: rows.map((r) => r.year),
        xTick: (year) => String(year),
        xReadout: (year) => `${year}, age ${year - inputs.birth_year}`,
        yTick: (y) => money(y, currency, { compact: true }),
        yReadout: (y) => money(y, currency),
        series,
        zero: true,
      }),
      tableView(
        ['Year', 'Age', 'Income', 'Invested', 'Deposit/withdrawal', 'Return', 'Net worth', 'Return after fees', 'After fees', ...(real ? ['Today’s money'] : [])],
        rows.map((r) => [
          String(r.year),
          String(r.age),
          money(r.income, currency),
          money(r.contribution, currency),
          money(r.deposit_withdrawal, currency, { signed: true }),
          money(r.return_before_fees, currency),
          money(r.net_worth_before_fees, currency),
          money(r.return_after_fees, currency),
          money(r.net_worth_after_fees, currency),
          ...(real ? [money(r.net_worth_real, currency)] : []),
        ]),
      ),
    ),
    h(
      'details',
      { class: 'card yaml' },
      h('summary', null, 'As a projection block for the config'),
      h('pre', null, yaml),
      copy,
    ),
  ];
}
