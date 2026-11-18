// The files the app offers for download (W12): CSV, file names and a zip. Nothing here
// touches the DOM or the network; save.ts hands the result to the browser.

export type Cell = string | number | null;

export interface Download {
  // The file name the browser saves it as.
  name: string;
  // Its path inside the combined zip.
  path: string;
  // What the download menu calls it.
  label: string;
  mime: string;
  data: string | Uint8Array;
}

// A cell that starts with one of these is a formula to a spreadsheet, so it gets a ' in front
// (OWASP's advice for CSV injection). Numbers are written as numbers, so a negative one stays.
const FORMULA_START = /^[=+\-@\t\r]/;

function csvCell(cell: Cell): string {
  if (cell === null) return '';
  if (typeof cell === 'number') return Number.isFinite(cell) ? String(cell) : '';
  const text = FORMULA_START.test(cell) ? `'${cell}` : cell;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** RFC 4180 CSV: a header row, then one row per entry, each line ending in CRLF. */
export function toCsv(headers: string[], rows: Cell[][]): string {
  return [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
}

/** Lower case, with anything but letters, digits and dots turned into single dashes. */
export function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9.]+/g, '-')
    .replace(/^[-.]+|[-.]+$/g, '');
}

// CRC-32 (IEEE), the checksum a zip entry carries.
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

export function crc32(data: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of data) crc = (CRC_TABLE[(crc ^ byte) & 0xff] ?? 0) ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

/** 'YYYY-MM-DDTHH:MM:SS' as a zip entry's DOS time and date. */
function dosTime(isoLocal: string): { time: number; date: number } {
  const [day = '', clock = ''] = isoLocal.split('T');
  const [year = 1980, month = 1, date = 1] = day.split('-').map(Number);
  const [hours = 0, minutes = 0, seconds = 0] = clock.split(':').map(Number);
  return {
    time: (hours << 11) | (minutes << 5) | Math.floor(seconds / 2),
    date: ((Math.max(1980, year) - 1980) << 9) | (month << 5) | date,
  };
}

/**
 * A zip of the files, stored without compression: the files are small, and storing needs no
 * library. Names are UTF-8 (flag bit 11). Every entry is dated with the snapshot's run time.
 */
export function zip(files: { path: string; data: string | Uint8Array }[], isoLocal: string): Uint8Array {
  const encoder = new TextEncoder();
  const { time, date } = dosTime(isoLocal);
  const local: Uint8Array[] = [];
  const central: Uint8Array[] = [];
  let offset = 0;
  for (const file of files) {
    const name = encoder.encode(file.path);
    const data = typeof file.data === 'string' ? encoder.encode(file.data) : file.data;
    const crc = crc32(data);
    const header = new Uint8Array(30 + name.length);
    const h = new DataView(header.buffer);
    h.setUint32(0, 0x04034b50, true);
    h.setUint16(4, 20, true);
    h.setUint16(6, 0x0800, true);
    h.setUint16(8, 0, true);
    h.setUint16(10, time, true);
    h.setUint16(12, date, true);
    h.setUint32(14, crc, true);
    h.setUint32(18, data.length, true);
    h.setUint32(22, data.length, true);
    h.setUint16(26, name.length, true);
    h.setUint16(28, 0, true);
    header.set(name, 30);
    local.push(header, data);

    const entry = new Uint8Array(46 + name.length);
    const c = new DataView(entry.buffer);
    c.setUint32(0, 0x02014b50, true);
    c.setUint16(4, 20, true);
    c.setUint16(6, 20, true);
    c.setUint16(8, 0x0800, true);
    c.setUint16(10, 0, true);
    c.setUint16(12, time, true);
    c.setUint16(14, date, true);
    c.setUint32(16, crc, true);
    c.setUint32(20, data.length, true);
    c.setUint32(24, data.length, true);
    c.setUint16(28, name.length, true);
    c.setUint32(42, offset, true);
    entry.set(name, 46);
    central.push(entry);
    offset += header.length + data.length;
  }
  const centralSize = central.reduce((sum, part) => sum + part.length, 0);
  const end = new Uint8Array(22);
  const e = new DataView(end.buffer);
  e.setUint32(0, 0x06054b50, true);
  e.setUint16(8, files.length, true);
  e.setUint16(10, files.length, true);
  e.setUint32(12, centralSize, true);
  e.setUint32(16, offset, true);
  const parts = [...local, ...central, end];
  const out = new Uint8Array(parts.reduce((sum, part) => sum + part.length, 0));
  let at = 0;
  for (const part of parts) {
    out.set(part, at);
    at += part.length;
  }
  return out;
}
