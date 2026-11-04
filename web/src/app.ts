// The page shell and the hash router: #/<page>[/<arg>] for the real portfolio,
// #/imaginary/<name>/<page>[/<arg>] for an imaginary one.

import { h, mount } from './dom';
import { ageInDays, runTime } from './format';
import { portfolioNamed, type Portfolio, type Snapshot } from './snapshot';
import { forget, loadDemo, loadRemembered, type Loaded } from './store';
import { dataPage } from './views/data';
import { holdingsPage } from './views/holdings';
import { landing, openFileButton } from './views/landing';
import { overviewPage } from './views/overview';
import { projectionPage } from './views/projection';
import { symbolPage } from './views/symbol';
import { transactionsPage } from './views/transactions';

export type Page = 'overview' | 'holdings' | 'symbol' | 'transactions' | 'projection' | 'data';

// The projection and the data page are about the whole snapshot, not one portfolio.
const GLOBAL_PAGES: Page[] = ['projection', 'data'];
const PAGES: Page[] = ['overview', 'holdings', 'symbol', 'transactions', 'projection', 'data'];
const STALE_AFTER_DAYS = 7;

export interface Context {
  loaded: Loaded;
  snapshot: Snapshot;
  // '' for the real portfolio.
  portfolioName: string;
  portfolio: Portfolio;
  currency: string;
  // The open snapshot changed: render again.
  reload: (loaded: Loaded | null) => void;
}

interface Route {
  portfolio: string;
  page: Page;
  arg?: string;
}

function parseRoute(hash: string): Route {
  const parts = hash
    .replace(/^#\/?/, '')
    .split('/')
    .filter(Boolean)
    .map((part) => decodeURIComponent(part));
  let portfolio = '';
  if (parts[0] === 'imaginary' && parts[1]) {
    portfolio = parts[1];
    parts.splice(0, 2);
  }
  const page = PAGES.find((name) => name === parts[0]) ?? 'overview';
  return { portfolio: GLOBAL_PAGES.includes(page) ? '' : portfolio, page, arg: parts[1] };
}

export function href(portfolio: string, page: Page, arg?: string): string {
  const parts = portfolio && !GLOBAL_PAGES.includes(page) ? ['imaginary', portfolio] : [];
  if (page !== 'overview' || arg) parts.push(page);
  if (arg) parts.push(arg);
  return `#/${parts.map(encodeURIComponent).join('/')}`;
}

export function start(root: HTMLElement): void {
  let loaded = loadRemembered();
  const reload = (next: Loaded | null) => {
    loaded = next;
    if (next === null) forget();
    render();
    window.scrollTo(0, 0);
  };
  const render = () => {
    if (!loaded) {
      document.title = 'trkr';
      mount(root, landing(reload));
      return;
    }
    let route = parseRoute(location.hash);
    let portfolio = portfolioNamed(loaded.snapshot, route.portfolio);
    if (!portfolio) {
      route = { portfolio: '', page: route.page };
      portfolio = loaded.snapshot.portfolio;
    }
    const context: Context = {
      loaded,
      snapshot: loaded.snapshot,
      portfolioName: route.portfolio,
      portfolio,
      currency: loaded.snapshot.config.default_currency,
      reload,
    };
    mount(root, shell(context, route));
  };
  window.addEventListener('hashchange', () => {
    render();
    window.scrollTo(0, 0);
  });
  render();
  // ?demo opens the made-up demo, so it can be linked to.
  if (!loaded && new URLSearchParams(location.search).has('demo')) {
    loadDemo().then(reload, () => undefined);
  }
}

function shell(context: Context, route: Route): Node[] {
  const { snapshot, loaded } = context;
  const days = ageInDays(snapshot.generated_at);
  const pages: [Page, string][] = [
    ['overview', 'overview'],
    ['holdings', 'holdings'],
    ['transactions', 'transactions'],
    ['projection', 'projection'],
    ['data', 'data'],
  ];
  const current = route.page === 'symbol' ? 'holdings' : route.page;
  const titles: Record<Page, string> = {
    overview: 'overview',
    holdings: 'holdings',
    symbol: route.arg ?? 'symbol',
    transactions: 'transactions',
    projection: 'projection',
    data: 'data',
  };
  document.title = `${titles[route.page]} · trkr`;

  const switcher =
    snapshot.imaginary.length > 0 && !GLOBAL_PAGES.includes(route.page)
      ? h(
          'label',
          { class: 'switcher' },
          h('span', { class: 'visually-hidden' }, 'portfolio'),
          (() => {
            const select = h(
              'select',
              {
                onchange: (event: Event) => {
                  const name = (event.target as HTMLSelectElement).value;
                  location.hash = href(name, route.page === 'symbol' ? 'holdings' : route.page);
                },
              },
              h('option', { value: '' }, 'real portfolio'),
              snapshot.imaginary.map((p) => h('option', { value: p.name }, `${p.name} (imaginary)`)),
            );
            select.value = route.portfolio;
            return select;
          })(),
        )
      : null;

  const view = (() => {
    switch (route.page) {
      case 'holdings':
        return holdingsPage(context);
      case 'symbol':
        return symbolPage(context, route.arg ?? '');
      case 'transactions':
        return transactionsPage(context);
      case 'projection':
        return projectionPage(context);
      case 'data':
        return dataPage(context);
      default:
        return overviewPage(context);
    }
  })();

  return [
    h(
      'header',
      { class: 'top' },
      h(
        'div',
        { class: 'bar' },
        h('a', { class: 'brand', href: href('', 'overview') }, 'trkr'),
        h(
          'p',
          { class: 'asof' },
          loaded.origin === 'demo' ? h('span', { class: 'badge' }, 'made-up demo data') : null,
          `snapshot of ${runTime(snapshot.generated_at)}`,
        ),
        h(
          'div',
          { class: 'actions' },
          openFileButton(context.reload, loaded.remembered, 'open another'),
          h('button', { class: 'button quiet', type: 'button', onclick: () => context.reload(null) }, 'close'),
        ),
      ),
      days > STALE_AFTER_DAYS && loaded.origin !== 'demo'
        ? h(
            'p',
            { class: 'notice warn', role: 'status' },
            `this snapshot is ${days} days old, so its prices are too. run trkr again for a new one.`,
          )
        : null,
      h(
        'nav',
        { class: 'tabs', 'aria-label': 'pages' },
        h(
          'ul',
          null,
          pages.map(([page, label]) =>
            h(
              'li',
              null,
              h(
                'a',
                { href: href(route.portfolio, page), 'aria-current': page === current ? 'page' : null },
                label,
              ),
            ),
          ),
        ),
        switcher,
      ),
    ),
    h(
      'main',
      { class: 'page' },
      route.portfolio ? h('p', { class: 'notice' }, `imaginary portfolio: ${route.portfolio}`) : null,
      view,
    ),
  ];
}
