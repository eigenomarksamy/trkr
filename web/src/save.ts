// Hands a download to the browser, and the menus that offer them (W12). The file is made
// in the page and saved through an object URL: nothing is uploaded.

import { h } from './dom';
import type { Download } from './download';

export function save(file: Pick<Download, 'name' | 'mime' | 'data'>): void {
  const url = URL.createObjectURL(new Blob([file.data as BlobPart], { type: file.mime }));
  const link = h('a', { href: url, download: file.name, hidden: true });
  document.body.append(link);
  link.click();
  link.remove();
  // Revoked once the browser has started the download.
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export interface MenuEntry {
  label: string;
  make: () => Download;
}

/** A "download" menu with a button per entry. Each file is made when its button is pressed. */
export function downloadMenu(entries: () => MenuEntry[], label = 'download'): HTMLElement {
  const list = h('ul', { class: 'download-list' });
  const menu = h('details', { class: 'downloads' }, h('summary', { class: 'button quiet' }, label), list);
  menu.addEventListener('toggle', () => {
    if (!menu.open) return;
    const items = entries();
    list.replaceChildren(
      ...items.map((entry) =>
        h('li', null, h('button', { type: 'button', class: 'button link', onclick: () => save(entry.make()) }, entry.label)),
      ),
    );
    if (items.length === 0) list.append(h('li', { class: 'muted' }, 'nothing to download here.'));
  });
  return menu;
}

/**
 * A menu of a page's files. They are made again when a button is pressed, so a download has
 * the page's current sort, filters and inputs.
 */
export function filesMenu(files: () => Download[]): HTMLElement {
  return downloadMenu(() =>
    files().map((file) => ({
      label: file.label,
      make: () => files().find((f) => f.name === file.name) ?? file,
    })),
  );
}
