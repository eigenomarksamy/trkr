// Markup as plain data, so a file can be built without a DOM: the charts are drawn as these
// nodes and turned into DOM for the page (chart.ts) or into text for a download. Text and
// attribute values are always escaped, since snapshot values come from the owner's sheets.

export type Attrs = Record<string, string | number | null | undefined | false>;

export interface MNode {
  tag: string;
  attrs: Attrs;
  children: (MNode | string)[];
}

export type Content = MNode | string | number | null | undefined | false | Content[];

function flatten(children: Content[], into: (MNode | string)[]): (MNode | string)[] {
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (Array.isArray(child)) flatten(child, into);
    else into.push(typeof child === 'number' ? String(child) : child);
  }
  return into;
}

export function m(tag: string, attrs?: Attrs | null, ...children: Content[]): MNode {
  return { tag, attrs: attrs ?? {}, children: flatten(children, []) };
}

const VOID = new Set(['meta', 'link', 'br', 'hr', 'img', 'input', 'col', 'wbr']);

export function escapeText(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function escapeAttr(text: string): string {
  return escapeText(text).replace(/"/g, '&quot;');
}

/** The node as markup text, valid both as HTML and, for SVG, as XML. */
export function toMarkup(node: MNode): string {
  const attrs = Object.entries(node.attrs)
    .filter(([, value]) => value !== null && value !== undefined && value !== false)
    .map(([name, value]) => ` ${name}="${escapeAttr(String(value))}"`)
    .join('');
  if (VOID.has(node.tag)) return `<${node.tag}${attrs}>`;
  const inner = node.children
    .map((child) => {
      if (typeof child !== 'string') return toMarkup(child);
      // A stylesheet is raw text in HTML, so it is written as it is; only our own CSS goes in one.
      if (node.tag === 'style') {
        if (/[<&]/.test(child)) throw new Error('a stylesheet may not hold < or &');
        return child;
      }
      return escapeText(child);
    })
    .join('');
  return `<${node.tag}${attrs}>${inner}</${node.tag}>`;
}
