// Reads delimited text: a CSV file, or rows pasted from a spreadsheet, which arrive separated
// by tabs (W11b). Quoting as RFC 4180 and Python's csv module read it: a cell that starts with
// a quote can hold the separator, line breaks and a doubled quote. No DOM here.

export interface CsvRow {
  /** The line it starts on, from 1, as an editor or a spreadsheet numbers it. */
  line: number;
  cells: string[];
  /** The row as written, without its line break, to show or to give back. */
  source: string;
  /** False when a quote in it opens and never closes, so it ran to the end of the text. */
  closed: boolean;
}

/** A tab when the first line that isn't blank has one, as rows copied from a spreadsheet do. */
export function separatorOf(text: string): ',' | '\t' {
  const first = text.split(/\r\n|\n|\r/).find((line) => line.trim() !== '') ?? '';
  return first.includes('\t') ? '\t' : ',';
}

/** The rows of the text, without blank ones: a blank line, or one of separators only. */
export function readRows(text: string): CsvRow[] {
  const input = text.startsWith('﻿') ? text.slice(1) : text;
  const separator = separatorOf(input);
  const rows: CsvRow[] = [];
  let at = 0;
  let line = 1;
  while (at < input.length) {
    const start = at;
    const startLine = line;
    const cells: string[] = [];
    let cell = '';
    let fresh = true;
    let quoted = false;
    let end = input.length;
    for (;;) {
      const c = input[at];
      if (c === undefined) {
        cells.push(cell);
        break;
      }
      const breaks = c === '\n' || (c === '\r' && input[at + 1] !== '\n');
      if (quoted) {
        if (c === '"' && input[at + 1] === '"') {
          cell += '"';
          at += 2;
        } else if (c === '"') {
          quoted = false;
          at += 1;
        } else {
          if (breaks) line += 1;
          cell += c;
          at += 1;
        }
      } else if (c === '"' && fresh) {
        quoted = true;
        fresh = false;
        at += 1;
      } else if (c === separator) {
        cells.push(cell);
        cell = '';
        fresh = true;
        at += 1;
      } else if (c === '\r' || c === '\n') {
        cells.push(cell);
        end = at;
        at += c === '\r' && input[at + 1] === '\n' ? 2 : 1;
        line += 1;
        break;
      } else {
        cell += c;
        fresh = false;
        at += 1;
      }
    }
    if (cells.some((value) => value.trim() !== '')) {
      rows.push({ line: startLine, cells, source: input.slice(start, end), closed: !quoted });
    }
  }
  return rows;
}
