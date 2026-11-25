import { describe, expect, it } from 'vitest';
import { readRows, separatorOf } from '../src/csv';

const cells = (text: string) => readRows(text).map((row) => row.cells);

describe('reading delimited text', () => {
  it('reads commas, or tabs as a spreadsheet copies its rows', () => {
    expect(cells('a,b,c\r\n1,2,3\r\n')).toEqual([
      ['a', 'b', 'c'],
      ['1', '2', '3'],
    ]);
    expect(cells('a\tb,c\t3\n')).toEqual([['a', 'b,c', '3']]);
    expect(separatorOf('\n\n a\tb')).toBe('\t');
    expect(separatorOf('a,b')).toBe(',');
    expect(separatorOf('')).toBe(',');
  });

  it('reads quotes as RFC 4180 and Python do', () => {
    expect(cells('"a, b","say ""hi""",c\n')).toEqual([['a, b', 'say "hi"', 'c']]);
    expect(cells('"two\r\nlines",x\nnext,y')).toEqual([
      ['two\r\nlines', 'x'],
      ['next', 'y'],
    ]);
    // A quote inside a cell is a quote, and so are the cells after a closing one.
    expect(cells('a"b,"c"d\n')).toEqual([['a"b', 'cd']]);
    expect(cells('"",x')).toEqual([['', 'x']]);
  });

  it('skips a byte order mark and blank rows, and keeps empty cells', () => {
    expect(cells('﻿a,b\n\n  \n,,\nc,\n')).toEqual([
      ['a', 'b'],
      ['c', ''],
    ]);
    expect(cells('')).toEqual([]);
  });

  it('numbers each row by the line it starts on, and keeps its text', () => {
    const rows = readRows('a,b\r\n\r\n"x\ny",z\rlast,1');
    expect(rows.map((row) => row.line)).toEqual([1, 3, 5]);
    expect(rows.map((row) => row.source)).toEqual(['a,b', '"x\ny",z', 'last,1']);
    expect(rows.every((row) => row.closed)).toBe(true);
  });

  it('says when a quote never closes', () => {
    const rows = readRows('a,b\n"open,c\nd,e\n');
    expect(rows).toHaveLength(2);
    expect(rows[1]).toMatchObject({ line: 2, cells: ['open,c\nd,e\n'], closed: false });
  });
});
