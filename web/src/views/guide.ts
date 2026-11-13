// How to make a snapshot.json: the page the landing links to, for someone who has none yet.
// It needs no snapshot, so the router shows it before anything is open.

import { type Child, h } from '../dom';

export const GUIDE_PAGE = 'make-a-snapshot';
export const GUIDE_HREF = `#/${GUIDE_PAGE}`;

const REPO = 'https://github.com/eigenomarksamy/trkr';

const INSTALL = [
  'git clone https://github.com/eigenomarksamy/trkr.git',
  'cd trkr',
  'python -m venv .venv',
  '.venv/Scripts/python.exe -m pip install -r requirements.txt',
].join('\n');

const TRADES = [
  'type,date,quantity,fees,price,currency,symbol,exchange,platform,ex_rate,ex_fees',
  'buy,2024-01-08,10,1,105.20,EUR,VWCE.DE,XETRA,broker-a,1,0',
  'buy,2024-03-04,2,1,175.10,USD,AAPL,NASDAQ,broker-b,1.08,2',
].join('\n');

const CONFIG = [
  'market-data-origin: yahoo',
  'comp:',
  '  default-currency: EUR       # every value is shown in it',
  '  history-variant: lite       # weekly prices; full is daily and slower',
  'directories:                  # each one must end with /',
  '  generation-dir: data/me/',
  '  log-dir: log/me/',
  '  transactions-dir: data/transactions.csv',
  'transactions:',
  '  source: local',
  '  symbols-standard: yahoo     # symbols are yahoo tickers',
  'cli-exec:',
  '  quiet: true',
  '  log-level: info',
].join('\n');

const RUN = '.venv/Scripts/python.exe run.py --cfg config/cfg.yml';
const DEMO = '.venv/Scripts/python.exe run.py --cfg config/demo-cfg.yml';

const code = (text: string) => h('code', null, text);
// Focusable, so a block that scrolls sideways can be scrolled from the keyboard.
const block = (text: string) => h('pre', { tabindex: 0 }, text);

function step(title: string, ...body: Child[]): HTMLElement {
  return h('li', null, h('h2', null, title), ...body);
}

export function guide(): HTMLElement {
  return h(
    'main',
    { class: 'guide' },
    h('a', { class: 'back', href: '#/' }, '← back'),
    h('h1', null, 'how to make a snapshot.json'),
    h(
      'p',
      { class: 'lede' },
      'trkr is a python tool that runs on your computer. it prices your trades with yahoo finance and writes ',
      code('snapshot.json'),
      ', the file this page opens. a first one takes five steps.',
    ),
    h(
      'ol',
      { class: 'steps' },
      step(
        'install trkr',
        h('p', null, 'you need python 3.11 or newer and git. in a terminal:'),
        block(INSTALL),
        h(
          'p',
          { class: 'hint' },
          'on a mac or on linux, write ',
          code('.venv/bin/python'),
          ' instead of ',
          code('.venv/Scripts/python.exe'),
          ', here and below.',
        ),
      ),
      step(
        'list your trades',
        h(
          'p',
          null,
          'save them as ',
          code('data/transactions.csv'),
          ', one row per trade. the columns are read by position, so keep this order:',
        ),
        block(TRADES),
        h(
          'ul',
          null,
          h('li', null, code('type'), ' is buy or sell, and ', code('date'), ' is YYYY-MM-DD.'),
          h('li', null, code('symbol'), ' is the ticker as yahoo finance writes it.'),
          h('li', null, code('price'), ', ', code('fees'), ' and ', code('ex_fees'), " are in the trade's currency."),
          h(
            'li',
            null,
            code('ex_rate'),
            " is how many units of the trade's currency one unit of your default currency buys: 1 when they are the same.",
          ),
          h('li', null, code('exchange'), ' and ', code('platform'), ' are only shown.'),
        ),
      ),
      step(
        'write a config',
        h('p', null, 'save this as ', code('config/cfg.yml'), ':'),
        block(CONFIG),
        h(
          'p',
          { class: 'hint' },
          'git ignores ',
          code('config/cfg.yml'),
          ', ',
          code('data/'),
          ' and ',
          code('log/'),
          ', so your trades stay out of the repo.',
        ),
      ),
      step(
        'run it',
        block(RUN),
        h(
          'p',
          null,
          'it needs the internet for prices and takes a few seconds. it writes ',
          code('data/me/snapshot.json'),
          ' next to ',
          code('report.html'),
          ', and keeps a copy of every run in ',
          code('data/me/snapshots/'),
          '.',
        ),
        h('p', { class: 'hint' }, 'to try it before typing your trades, run the made-up demo:'),
        block(DEMO),
        h('p', { class: 'hint' }, 'it writes ', code('data/demo-run/snapshot.json'), '.'),
      ),
      step(
        'open it here',
        h(
          'p',
          null,
          'go ',
          h('a', { href: '#/' }, 'back to the start'),
          ', choose open snapshot.json and pick the file, or drop it on the page. it is read in this browser and never uploaded.',
        ),
        h(
          'p',
          null,
          'run trkr again whenever you want new prices. the page warns when a snapshot is more than a week old.',
        ),
      ),
    ),
    h(
      'p',
      { class: 'hint' },
      'a google sheet instead of a CSV file, holdings instead of a trade history, imaginary portfolios and a projection are all in the ',
      h('a', { href: `${REPO}#configuration`, target: '_blank', rel: 'noopener noreferrer' }, 'README'),
      '.',
    ),
  );
}
