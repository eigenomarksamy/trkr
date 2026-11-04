import { describe, expect, it } from 'vitest';
import { dayLabel, lowerMonth, monthLabel, runTime } from '../src/format';

describe('date labels', () => {
  it('writes months in lower case and leaves AM and PM alone', () => {
    const format = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' });
    const afternoon = new Date(2026, 10, 4, 15, 45);
    expect(lowerMonth(format, afternoon).replace(/\s/g, ' ')).toBe('nov 4, 2026, 3:45 PM');
  });

  // The viewer's locale decides the words, so these only check the case of the month.
  it('applies to every label on the page', () => {
    const month = new Intl.DateTimeFormat(undefined, { month: 'short' }).format(new Date(2024, 0, 1));
    const lower = month.toLocaleLowerCase();
    expect(monthLabel('2024-01')).toContain(lower);
    expect(dayLabel('2024-01-15')).toContain(lower);
    expect(runTime('2024-01-15T15:45:00')).toContain(lower);
  });
});
