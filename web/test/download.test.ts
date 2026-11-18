import { describe, expect, it } from 'vitest';
import { crc32, slug, toCsv, zip } from '../src/download';
import { toMarkup, m } from '../src/markup';
import { unzip } from './unzip';

describe('toCsv', () => {
  it('writes a header and rows, each line ending in CRLF', () => {
    expect(toCsv(['a', 'b'], [[1, 'x'], [2.5, 'y']])).toBe('a,b\r\n1,x\r\n2.5,y\r\n');
  });

  it('keeps numbers raw, and leaves missing ones empty', () => {
    expect(toCsv(['n'], [[0.000012345], [-1250.5], [null], [Number.NaN]])).toBe('n\r\n0.000012345\r\n-1250.5\r\n\r\n\r\n');
  });

  it('quotes commas, quotes and line breaks', () => {
    expect(toCsv(['t'], [['a,b'], ['say "hi"'], ['two\nlines']])).toBe('t\r\n"a,b"\r\n"say ""hi"""\r\n"two\nlines"\r\n');
  });

  it('defuses text a spreadsheet would run as a formula', () => {
    expect(toCsv(['t'], [['=SUM(A1)'], ['+1'], ['-2'], ['@x'], ['=a,b']])).toBe("t\r\n'=SUM(A1)\r\n'+1\r\n'-2\r\n'@x\r\n\"'=a,b\"\r\n");
  });
});

describe('slug', () => {
  it('makes file-name parts from tickers and titles', () => {
    expect(slug('BTC-EUR')).toBe('btc-eur');
    expect(slug('USDEUR=X')).toBe('usdeur-x');
    expect(slug('VWCE.AS')).toBe('vwce.as');
    expect(slug('^GSPC')).toBe('gspc');
    expect(slug('value at each month end')).toBe('value-at-each-month-end');
    expect(slug('profit %')).toBe('profit');
  });
});

describe('zip', () => {
  it('computes the standard CRC-32', () => {
    expect(crc32(new TextEncoder().encode('123456789'))).toBe(0xcbf43926);
    expect(crc32(new Uint8Array())).toBe(0);
  });

  it('stores files that read back with their names, contents and checksums', () => {
    const files = [
      { path: 'trkr/portfolio/holdings.csv', data: 'symbol,value\r\nAAA,1\r\n' },
      { path: 'trkr/überall.svg', data: '<svg></svg>' },
      { path: 'trkr/bytes.bin', data: new Uint8Array([0, 1, 2, 255]) },
    ];
    const entries = unzip(zip(files, '2026-11-18T07:30:10'));
    expect(entries.map((e) => e.path)).toEqual(files.map((f) => f.path));
    expect(entries[0]?.text).toBe(files[0]?.data);
    expect(entries[1]?.text).toBe('<svg></svg>');
    for (const entry of entries) {
      // UTF-8 names, and the snapshot's run time: 07:30:10, 18 november 2026.
      expect(entry.flags & 0x0800).toBe(0x0800);
      expect(entry.time).toBe((7 << 11) | (30 << 5) | 5);
      expect(entry.date).toBe(((2026 - 1980) << 9) | (11 << 5) | 18);
    }
    expect(entries[0]?.crc).toBe(crc32(new TextEncoder().encode(files[0]?.data as string)));
  });

  it('makes an empty zip that is still a zip', () => {
    expect(unzip(zip([], '2026-11-18T00:00:00'))).toEqual([]);
  });
});

describe('toMarkup', () => {
  it('escapes text and attribute values', () => {
    expect(toMarkup(m('p', { title: 'a "b" <c>' }, '<b>x</b> & y'))).toBe('<p title="a &quot;b&quot; &lt;c&gt;">&lt;b&gt;x&lt;/b&gt; &amp; y</p>');
  });

  it('leaves out empty attributes, and writes void elements without a close', () => {
    expect(toMarkup(m('div', { class: null, id: undefined, hidden: false }, m('meta', { charset: 'utf-8' }), 1))).toBe('<div><meta charset="utf-8">1</div>');
  });

  it('refuses a stylesheet that could end its element', () => {
    expect(() => toMarkup(m('style', null, 'a { } </style><script>'))).toThrow(/stylesheet/);
  });
});
