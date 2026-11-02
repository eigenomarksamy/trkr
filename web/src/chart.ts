// SVG line and column charts with a hover and keyboard readout. Series colours are CSS
// classes (s1-s3, see styles.css), so dark mode restyles them without a redraw.

import { h, s, type Child } from './dom';

export interface LineSeries {
  name: string;
  values: (number | null)[];
}

export interface LineChartOptions {
  // The chart's accessible name.
  label: string;
  // Ascending: timestamps or years.
  x: number[];
  xTick: (x: number) => string;
  xReadout: (x: number) => string;
  yTick: (y: number) => string;
  yReadout: (y: number) => string;
  // At most three: the first three palette slots are the ones validated for any pair.
  series: LineSeries[];
  // A wash under a single series.
  area?: boolean;
  // Start the y axis at zero.
  zero?: boolean;
  // Labelled horizontal lines, such as a break-even price.
  references?: { y: number; label: string }[];
  // Labelled vertical lines, such as the first buy.
  markers?: { x: number; label: string }[];
}

export interface ColumnChartOptions {
  label: string;
  values: number[];
  tick: (index: number) => string;
  readout: (index: number) => string;
  yTick: (y: number) => string;
  yReadout: (y: number) => string;
}

const HEIGHT = 240;
const MARGIN = { top: 14, right: 12, bottom: 28 };

function niceTicks(min: number, max: number, count = 5): number[] {
  if (min === max) {
    const pad = min === 0 ? 1 : Math.abs(min) * 0.1;
    min -= pad;
    max += pad;
  }
  const raw = (max - min) / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normal = raw / magnitude;
  const step = (normal < 1.5 ? 1 : normal < 3 ? 2 : normal < 7 ? 5 : 10) * magnitude;
  const ticks: number[] = [];
  for (let tick = Math.floor(min / step) * step; tick <= max + step * 0.999; tick += step) {
    ticks.push(Math.abs(tick) < step * 1e-9 ? 0 : tick);
  }
  return ticks;
}

/** Evenly spread tick indices that fit the width. */
function tickIndices(count: number, width: number, spacing = 84): number[] {
  const fit = Math.max(2, Math.floor(width / spacing));
  const step = Math.max(1, Math.ceil(count / fit));
  const indices: number[] = [];
  for (let i = 0; i < count; i += step) indices.push(i);
  return indices;
}

interface Frame {
  svg: SVGSVGElement;
  left: number;
  right: number;
  top: number;
  bottom: number;
  y: (value: number) => number;
}

/** The y axis with its gridlines, in an svg sized to the width. */
function frame(width: number, label: string, yValues: number[], zero: boolean, yTick: (y: number) => string): Frame {
  const values = zero ? [0, ...yValues] : yValues;
  const ticks = niceTicks(Math.min(...values), Math.max(...values));
  const lo = ticks[0] ?? 0;
  const hi = ticks[ticks.length - 1] ?? 1;
  const labels = ticks.map(yTick);
  const left = Math.max(...labels.map((text) => text.length)) * 7 + 14;
  const top = MARGIN.top;
  const bottom = HEIGHT - MARGIN.bottom;
  const y = (value: number) => bottom - ((value - lo) / (hi - lo || 1)) * (bottom - top);
  const svg = s('svg', {
    width,
    height: HEIGHT,
    viewBox: `0 0 ${width} ${HEIGHT}`,
    role: 'img',
    'aria-label': label,
  });
  ticks.forEach((tick, i) => {
    const at = y(tick);
    svg.append(
      s('line', { class: i === 0 ? 'axis' : 'grid', x1: left, x2: width - MARGIN.right, y1: at, y2: at }),
      s('text', { class: 'tick', x: left - 8, y: at, 'text-anchor': 'end', 'dominant-baseline': 'middle' }, labels[i]),
    );
  });
  return { svg, left, right: width - MARGIN.right, top, bottom, y };
}

/**
 * Wires the readout: pointer and arrow keys pick an index, show(index) places the marks
 * and returns the readout's content, hide() clears them.
 */
function readout(
  plot: HTMLElement,
  svg: SVGSVGElement,
  count: number,
  indexAt: (x: number) => number,
  anchorX: (index: number) => number,
  show: (index: number) => Node[],
  hide: () => void,
): void {
  // A redraw wires the readout again, so the previous draw's listeners go.
  readouts.get(plot)?.abort();
  const wiring = new AbortController();
  readouts.set(plot, wiring);
  const signal = wiring.signal;
  const tip = h('div', { class: 'readout', hidden: true, 'aria-live': 'polite' });
  plot.append(tip);
  let current = count - 1;
  const place = (index: number) => {
    current = Math.max(0, Math.min(count - 1, index));
    tip.replaceChildren(...show(current));
    tip.hidden = false;
    const x = anchorX(current);
    const width = tip.offsetWidth;
    tip.style.left = `${x + 14 + width > plot.clientWidth ? Math.max(0, x - 14 - width) : x + 14}px`;
  };
  const clear = () => {
    tip.hidden = true;
    hide();
  };
  svg.addEventListener('pointermove', (event) => {
    const box = svg.getBoundingClientRect();
    place(indexAt(event.clientX - box.left));
  });
  svg.addEventListener('pointerleave', clear);
  plot.addEventListener('focus', () => place(current), { signal });
  plot.addEventListener('blur', clear, { signal });
  plot.addEventListener(
    'keydown',
    (event) => {
    const moves: Record<string, number> = { ArrowLeft: current - 1, ArrowRight: current + 1, Home: 0, End: count - 1 };
    if (event.key in moves) {
      event.preventDefault();
      place(moves[event.key] ?? current);
    } else if (event.key === 'Escape') {
      clear();
    }
    },
    { signal },
  );
}

const readouts = new WeakMap<HTMLElement, AbortController>();

function readoutRow(seriesClass: string, value: string, name?: string): HTMLElement {
  return h('div', { class: 'readout-row' }, h('span', { class: `key ${seriesClass}` }), h('strong', null, value), name ? h('span', { class: 'muted' }, name) : null);
}

/** Draws once the container has a width, and again when the width changes. */
function responsive(plot: HTMLElement, draw: (width: number) => void): void {
  let drawn = 0;
  new ResizeObserver((entries) => {
    const width = Math.floor(entries[0]?.contentRect.width ?? 0);
    if (width > 0 && width !== drawn) {
      drawn = width;
      draw(width);
    }
  }).observe(plot);
}

export function lineChart(options: LineChartOptions): HTMLElement {
  const plot = h('div', { class: 'plot', tabindex: 0, 'aria-label': `${options.label}. Use the arrow keys to read the values.` });
  const legend =
    options.series.length > 1
      ? h(
          'ul',
          { class: 'legend' },
          options.series.map((series, i) => h('li', null, h('span', { class: `key s${i + 1}` }), series.name)),
        )
      : null;
  responsive(plot, (width) => drawLines(plot, width, options));
  return h('div', { class: 'chart' }, legend, plot);
}

function drawLines(plot: HTMLElement, width: number, o: LineChartOptions): void {
  const values = o.series.flatMap((series) => series.values.filter((v): v is number => v !== null));
  if (values.length === 0 || o.x.length === 0) {
    plot.replaceChildren(h('p', { class: 'muted empty' }, 'No data to chart.'));
    return;
  }
  const yValues = [...values, ...(o.references ?? []).map((r) => r.y)];
  const f = frame(width, o.label, yValues, o.zero ?? false, o.yTick);
  const first = o.x[0] ?? 0;
  const last = o.x[o.x.length - 1] ?? 0;
  const x = (value: number) => (last === first ? (f.left + f.right) / 2 : f.left + ((value - first) / (last - first)) * (f.right - f.left));

  for (const i of tickIndices(o.x.length, f.right - f.left)) {
    const at = o.x[i] ?? 0;
    f.svg.append(s('text', { class: 'tick', x: x(at), y: f.bottom + 18, 'text-anchor': i === 0 ? 'start' : 'middle' }, o.xTick(at)));
  }
  for (const marker of o.markers ?? []) {
    if (marker.x < first || marker.x > last) continue;
    f.svg.append(
      s('line', { class: 'ref', x1: x(marker.x), x2: x(marker.x), y1: f.top, y2: f.bottom }),
      s('text', { class: 'ref-label', x: x(marker.x) + 4, y: f.top + 10 }, marker.label),
    );
  }
  for (const reference of o.references ?? []) {
    f.svg.append(
      s('line', { class: 'ref', x1: f.left, x2: f.right, y1: f.y(reference.y), y2: f.y(reference.y) }),
      s('text', { class: 'ref-label', x: f.right, y: f.y(reference.y) - 5, 'text-anchor': 'end' }, reference.label),
    );
  }

  o.series.forEach((series, i) => {
    let path = '';
    let open = false;
    series.values.forEach((value, j) => {
      if (value === null) {
        open = false;
        return;
      }
      path += `${open ? 'L' : 'M'}${x(o.x[j] ?? 0).toFixed(1)},${f.y(value).toFixed(1)}`;
      open = true;
    });
    if (o.area && o.series.length === 1) {
      const points = series.values.map((value, j) => [o.x[j] ?? 0, value] as const).filter(([, value]) => value !== null);
      const start = points[0];
      const end = points[points.length - 1];
      if (start && end) {
        f.svg.append(s('path', { class: `area s${i + 1}`, d: `${path}L${x(end[0]).toFixed(1)},${f.bottom}L${x(start[0]).toFixed(1)},${f.bottom}Z` }));
      }
    }
    f.svg.append(s('path', { class: `line s${i + 1}`, d: path }));
  });

  // A single series gets its last value as a direct label.
  if (o.series.length === 1) {
    const series = o.series[0];
    const j = series ? series.values.findLastIndex((v) => v !== null) : -1;
    const value = series?.values[j];
    if (series && value !== null && value !== undefined) {
      const at = x(o.x[j] ?? 0);
      f.svg.append(
        s('circle', { class: 'dot s1', cx: at, cy: f.y(value), r: 4 }),
        s('text', { class: 'end-label', x: at - 8, y: f.y(value) - 10, 'text-anchor': 'end' }, o.yReadout(value)),
      );
    }
  }

  const crosshair = s('line', { class: 'crosshair', y1: f.top, y2: f.bottom, visibility: 'hidden' });
  const dots = o.series.map((_, i) => s('circle', { class: `dot s${i + 1}`, r: 4, visibility: 'hidden' }));
  f.svg.append(crosshair, ...dots);
  plot.replaceChildren(f.svg);
  readout(
    plot,
    f.svg,
    o.x.length,
    (px) => {
      let best = 0;
      o.x.forEach((value, j) => {
        if (Math.abs(x(value) - px) < Math.abs(x(o.x[best] ?? 0) - px)) best = j;
      });
      return best;
    },
    (j) => x(o.x[j] ?? 0),
    (j) => {
      const at = x(o.x[j] ?? 0);
      crosshair.setAttribute('x1', String(at));
      crosshair.setAttribute('x2', String(at));
      crosshair.setAttribute('visibility', 'visible');
      const rows: Node[] = [h('div', { class: 'readout-title' }, o.xReadout(o.x[j] ?? 0))];
      o.series.forEach((series, i) => {
        const value = series.values[j] ?? null;
        const dot = dots[i];
        if (!dot) return;
        if (value === null) {
          dot.setAttribute('visibility', 'hidden');
          return;
        }
        dot.setAttribute('cx', String(at));
        dot.setAttribute('cy', String(f.y(value)));
        dot.setAttribute('visibility', 'visible');
        rows.push(readoutRow(`s${i + 1}`, o.yReadout(value), o.series.length > 1 ? series.name : undefined));
      });
      return rows;
    },
    () => {
      crosshair.setAttribute('visibility', 'hidden');
      for (const dot of dots) dot.setAttribute('visibility', 'hidden');
    },
  );
}

export function columnChart(options: ColumnChartOptions): HTMLElement {
  const plot = h('div', { class: 'plot', tabindex: 0, 'aria-label': `${options.label}. Use the arrow keys to read the values.` });
  responsive(plot, (width) => drawColumns(plot, width, options));
  return h('div', { class: 'chart' }, plot);
}

function drawColumns(plot: HTMLElement, width: number, o: ColumnChartOptions): void {
  if (o.values.length === 0) {
    plot.replaceChildren(h('p', { class: 'muted empty' }, 'No data to chart.'));
    return;
  }
  const f = frame(width, o.label, o.values, true, o.yTick);
  const band = (f.right - f.left) / o.values.length;
  // Columns are at most 24px wide, with at least a 2px gap between neighbours.
  const barWidth = Math.max(1, Math.min(24, band - 2));
  const centre = (i: number) => f.left + band * (i + 0.5);
  for (const i of tickIndices(o.values.length, f.right - f.left)) {
    f.svg.append(s('text', { class: 'tick', x: centre(i), y: f.bottom + 18, 'text-anchor': 'middle' }, o.tick(i)));
  }
  const bars = o.values.map((value, i) => {
    const x0 = centre(i) - barWidth / 2;
    const top = f.y(Math.max(0, value));
    const height = f.bottom - top;
    const r = Math.min(4, barWidth / 2, height);
    // Rounded at the data end, square at the baseline.
    const d =
      height <= 0
        ? ''
        : `M${x0},${f.bottom}V${top + r}Q${x0},${top} ${x0 + r},${top}H${x0 + barWidth - r}Q${x0 + barWidth},${top} ${x0 + barWidth},${top + r}V${f.bottom}Z`;
    const bar = s('path', { class: 'bar s1', d });
    f.svg.append(bar);
    return bar;
  });
  plot.replaceChildren(f.svg);
  let active: SVGPathElement | undefined;
  readout(
    plot,
    f.svg,
    o.values.length,
    (px) => Math.floor((px - f.left) / band),
    centre,
    (i) => {
      active?.classList.remove('active');
      active = bars[i];
      active?.classList.add('active');
      return [h('div', { class: 'readout-title' }, o.readout(i)), readoutRow('s1', o.yReadout(o.values[i] ?? 0))];
    },
    () => active?.classList.remove('active'),
  );
}

/** The chart's numbers as a table, folded away under it. */
export function tableView(headers: string[], rows: Child[][]): HTMLElement {
  return h(
    'details',
    { class: 'table-view' },
    h('summary', null, 'Show as a table'),
    h(
      'div',
      { class: 'scroll' },
      h(
        'table',
        null,
        h('thead', null, h('tr', null, headers.map((header, i) => h('th', { class: i === 0 ? '' : 'num' }, header)))),
        h('tbody', null, rows.map((row) => h('tr', null, row.map((cell, i) => h('td', { class: i === 0 ? '' : 'num' }, cell))))),
      ),
    ),
  );
}
