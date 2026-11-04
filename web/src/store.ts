// Where the open snapshot comes from, and the copy kept on this device when the owner asks.
// Nothing here leaves the browser: the snapshot is read from a local file or from the demo.

import { parseSnapshot, type Snapshot } from './snapshot';

const REMEMBERED = 'trkr.snapshot';

export interface Loaded {
  snapshot: Snapshot;
  // 'demo' for the made-up demo, otherwise the file's name.
  origin: 'demo' | 'file';
  name: string;
  remembered: boolean;
}

export async function loadDemo(): Promise<Loaded> {
  const response = await fetch('/demo-snapshot.json');
  if (!response.ok) throw new Error(`the demo could not be loaded (${response.status}).`);
  return { snapshot: parseSnapshot(await response.text()), origin: 'demo', name: 'demo', remembered: false };
}

export async function loadFile(file: File, remember: boolean): Promise<Loaded> {
  const text = await file.text();
  const snapshot = parseSnapshot(text);
  let remembered = false;
  if (remember) {
    try {
      localStorage.setItem(REMEMBERED, JSON.stringify({ name: file.name, text }));
      remembered = true;
    } catch {
      // Storage is full or blocked; the snapshot is still open for this visit.
    }
  }
  return { snapshot, origin: 'file', name: file.name, remembered };
}

/** The snapshot kept on this device, if any and if it still reads. */
export function loadRemembered(): Loaded | null {
  try {
    const stored = localStorage.getItem(REMEMBERED);
    if (!stored) return null;
    const { name, text } = JSON.parse(stored) as { name: string; text: string };
    return { snapshot: parseSnapshot(text), origin: 'file', name, remembered: true };
  } catch {
    forget();
    return null;
  }
}

export function forget(): void {
  try {
    localStorage.removeItem(REMEMBERED);
  } catch {
    // Nothing was stored.
  }
}
