// Number and date formatting, in the viewer's locale. Missing numbers print as a dash.

type Num = number | null | undefined;

const DASH = '–';
const moneyFormats = new Map<string, Intl.NumberFormat>();

function moneyFormat(currency: string, compact: boolean): Intl.NumberFormat {
  const key = `${currency}|${compact}`;
  let format = moneyFormats.get(key);
  if (!format) {
    try {
      format = new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency,
        notation: compact ? 'compact' : 'standard',
        maximumFractionDigits: compact ? 1 : 2,
      });
    } catch {
      // Not an ISO currency code: a plain number, with the code after it in money().
      format = new Intl.NumberFormat(undefined, {
        notation: compact ? 'compact' : 'standard',
        maximumFractionDigits: compact ? 1 : 2,
      });
    }
    moneyFormats.set(key, format);
  }
  return format;
}

function isNumber(value: Num): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

export function money(value: Num, currency: string, options: { signed?: boolean; compact?: boolean } = {}): string {
  if (!isNumber(value)) return DASH;
  const format = moneyFormat(currency, options.compact ?? false);
  const text = format.resolvedOptions().style === 'currency' ? format.format(Math.abs(value)) : `${format.format(Math.abs(value))} ${currency}`;
  return sign(value, options.signed ?? false) + text;
}

/** A percentage given in percent units: 12.5 -> "12.5%". */
export function percent(value: Num, options: { signed?: boolean; digits?: number } = {}): string {
  if (!isNumber(value)) return DASH;
  const digits = options.digits ?? 1;
  const text = Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return `${sign(value, options.signed ?? false)}${text}%`;
}

export function number(value: Num, maxDigits = 2): string {
  if (!isNumber(value)) return DASH;
  return value.toLocaleString(undefined, { maximumFractionDigits: maxDigits });
}

/** Quantities: crypto needs up to 8 decimals, shares usually none. */
export function quantity(value: Num): string {
  return number(value, 8);
}

function sign(value: number, signed: boolean): string {
  if (value < 0 && Math.abs(value) >= 0.005) return '−';
  return signed && value > 0 ? '+' : '';
}

/** Up, down or flat, for colouring a figure. Tiny values count as flat. */
export function direction(value: Num): 'up' | 'down' | 'flat' {
  if (!isNumber(value) || Math.abs(value) < 0.005) return 'flat';
  return value > 0 ? 'up' : 'down';
}

/** 'YYYY-MM' -> the first of that month, at local midnight. */
export function monthDate(month: string): Date {
  const [year, monthNumber] = month.split('-').map(Number);
  return new Date(year ?? 1970, (monthNumber ?? 1) - 1, 1);
}

/** 'YYYY-MM-DD' -> that day, at local midnight. */
export function dayDate(day: string): Date {
  const [year, month, date] = day.split('-').map(Number);
  return new Date(year ?? 1970, (month ?? 1) - 1, date ?? 1);
}

/** A date as the format writes it, with the month in lower case like the rest of the page. AM and PM keep their case. */
export function lowerMonth(format: Intl.DateTimeFormat, date: Date): string {
  return format
    .formatToParts(date)
    .map((part) => (part.type === 'month' ? part.value.toLocaleLowerCase() : part.value))
    .join('');
}

export function monthLabel(month: string | Date, style: 'short' | 'long' = 'short'): string {
  const date = typeof month === 'string' ? monthDate(month) : month;
  return lowerMonth(new Intl.DateTimeFormat(undefined, { month: style, year: 'numeric' }), date);
}

export function dayLabel(day: string | Date): string {
  const date = typeof day === 'string' ? dayDate(day) : day;
  return lowerMonth(new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' }), date);
}

/** The snapshot's local run time, 'YYYY-MM-DDTHH:MM:SS'. */
export function runTime(isoLocal: string): string {
  return lowerMonth(new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }), new Date(isoLocal));
}

/** Whole days from a snapshot's run time to now. */
export function ageInDays(isoLocal: string, now: Date = new Date()): number {
  return Math.floor((now.getTime() - new Date(isoLocal).getTime()) / 86_400_000);
}
