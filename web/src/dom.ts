// Builds DOM nodes. Text always goes in as text nodes, never as HTML: snapshot values come
// from the owner's sheets and are shown as they are.

export type Child = Node | string | number | null | undefined | false | Child[];
type Props = Record<string, string | number | boolean | EventListener | null | undefined>;

function append(parent: Node, children: Child[]): void {
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (Array.isArray(child)) append(parent, child);
    else parent.appendChild(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

function setProps(element: Element, props: Props | null | undefined): void {
  if (!props) return;
  for (const [name, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) continue;
    if (name.startsWith('on') && typeof value === 'function') {
      element.addEventListener(name.slice(2), value);
    } else if (name === 'style') {
      // A style attribute would need 'unsafe-inline' in the CSP; use a class.
      throw new Error('style props are not allowed');
    } else {
      element.setAttribute(name, value === true ? '' : String(value));
    }
  }
}

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props?: Props | null,
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  setProps(element, props);
  append(element, children);
  return element;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

export function s<K extends keyof SVGElementTagNameMap>(
  tag: K,
  props?: Props | null,
  ...children: Child[]
): SVGElementTagNameMap[K] {
  const element = document.createElementNS(SVG_NS, tag);
  setProps(element, props);
  append(element, children);
  return element;
}

/** Replaces a node's children. */
export function mount(parent: Element, ...children: Child[]): void {
  parent.replaceChildren();
  append(parent, children);
}
