// Reads back a stored (uncompressed) zip, for the tests: from the central directory, as an
// unzip tool does, checking each local header against it.

export interface Entry {
  path: string;
  text: string;
  crc: number;
  time: number;
  date: number;
  flags: number;
}

export function unzip(bytes: Uint8Array): Entry[] {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const decoder = new TextDecoder();
  const end = bytes.length - 22;
  if (view.getUint32(end, true) !== 0x06054b50) throw new Error('no end of central directory');
  const count = view.getUint16(end + 10, true);
  let at = view.getUint32(end + 16, true);
  const entries: Entry[] = [];
  for (let i = 0; i < count; i++) {
    if (view.getUint32(at, true) !== 0x02014b50) throw new Error(`no central entry ${i}`);
    const flags = view.getUint16(at + 8, true);
    const method = view.getUint16(at + 10, true);
    const time = view.getUint16(at + 12, true);
    const date = view.getUint16(at + 14, true);
    const crc = view.getUint32(at + 16, true);
    const size = view.getUint32(at + 20, true);
    const nameLength = view.getUint16(at + 28, true);
    const offset = view.getUint32(at + 42, true);
    const path = decoder.decode(bytes.subarray(at + 46, at + 46 + nameLength));
    if (method !== 0) throw new Error(`${path} is compressed`);
    if (view.getUint32(offset, true) !== 0x04034b50) throw new Error(`no local header for ${path}`);
    if (view.getUint32(offset + 14, true) !== crc) throw new Error(`${path}: local crc differs`);
    const localName = view.getUint16(offset + 26, true);
    const extra = view.getUint16(offset + 28, true);
    const start = offset + 30 + localName + extra;
    entries.push({ path, text: decoder.decode(bytes.subarray(start, start + size)), crc, time, date, flags });
    at += 46 + nameLength;
  }
  return entries;
}
