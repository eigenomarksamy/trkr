# trkr

A personal investment-portfolio tracker. It reads your transactions from a CSV file or a public Google Sheet, prices them with Yahoo Finance, and computes profit and loss per investment and in total. The results are written as CSV and Markdown tables, charts, and an HTML report.

## Setup

Python 3.11 or newer. From the project's home directory:

``$ python -m venv .venv``

``$ .venv/Scripts/python.exe -m pip install -r requirements.txt``

`requirements.txt` pins the versions locked in `uv.lock`. Then run:

``$ .venv/Scripts/python.exe run.py --cfg config/cfg.yml``

`--cfg` defaults to `config/cfg.yml`. The `--quiet` and `--log-level` flags are accepted but ignored; set `quiet` and `log-level` in the config instead. `config/*.yml` is gitignored except the demo, so your own configs stay local. To try the tool on made-up data first, see [Demo](#demo).

## Configuration

One YAML file holds everything. The required part:

```yaml
market-data-origin: yahoo        # the only supported source
comp:
  default-currency: EUR          # EUR or USD: every value is reported in it
  history-variant: lite          # lite (weekly prices); full (daily) currently crashes
directories:                     # every directory must end with '/'
  generation-dir: data/me/       # where the outputs go
  log-dir: log/me/
  transactions-dir: data/transactions.csv   # only for transactions source: local
  symbols-map-dir: data/symbols.csv         # only for symbols-map source: local
transactions:
  source: cloud                  # local (a CSV file) or cloud (a Google Sheet)
  shareable-address: <sheet id>  # only for source: cloud
  symbols-standard: custom       # custom: use the symbol map below
symbols-map:
  source: cloud                  # local or cloud
  shareable-address: <sheet id>  # only for source: cloud
cli-exec:
  quiet: false                   # true hides the detailed console output
  log-level: info                # debug, info, warning, error, critical or notset
```

The optional `positions`, `imaginary-portfolios` and `projection` blocks are described below.

For a Google Sheet, set its sharing to "Anyone with the link". Then put the sheet ID in `shareable-address`: that's the part of the link between `/d/` and `/edit`. The sheet is downloaded as CSV into `<generation-dir>sheets/` on every run.

### Transactions

One row per trade. The columns are read **by position**, so keep them in this order. The first row is always skipped as the header.

| type | date       | quantity | fees | price  | currency | symbol | exchange | platform | ex_rate | ex_fees |
|------|------------|----------|------|--------|----------|--------|----------|----------|---------|---------|
| buy  | 2024-01-08 | 10       | 1    | 105.20 | EUR      | vwce   | XETRA    | broker-a | 1       | 0       |
| buy  | 2024-03-04 | 2        | 1    | 175.10 | USD      | aapl   | NASDAQ   | broker-b | 1.08    | 2       |

- `type` is `buy` or `sell`. `date` is YYYY-MM-DD.
- `price`, `fees` and `ex_fees` (currency exchange fees) are in the trade's own currency.
- `ex_rate` is how many units of the trade's currency one unit of the default currency buys, so 1 when they are the same. The cost in the default currency is `(price × quantity + fees + ex_fees) / ex_rate`.
- `currency`, `exchange` and `platform` are only shown.

Most brokers (IBKR, Degiro, Coinbase, …) can export trades as CSV, which you can rearrange into these columns.

### Symbol map

Maps the symbols in your transactions to Yahoo Finance tickers. Two columns, `symbol` then `ticker`, with the first row skipped as the header. Symbols are matched case-insensitively. A symbol missing from the map goes to Yahoo as it is, in lower case.

| symbol | ticker   |
|--------|----------|
| vwce   | VWCE.DE  |
| aapl   | AAPL     |
| eur    | USDEUR=X |

The map must also contain the default currency, lower-cased, mapped to the exchange-rate ticker for the other currency: `eur → USDEUR=X` with EUR as default, `usd → EURUSD=X` with USD. Every price that isn't in the default currency is multiplied by that rate, so only two currencies are supported.

### Positions (opening balances)

Optional. When you don't have every past trade, list what you hold instead: one row per investment with the quantity, your average buy price and a date (e.g. when you first bought it). Each row counts as a single buy on that date, before the trades in the transactions sheet, so later buys and sells adjust it. Charts and monthly spending start at that date.

```yaml
positions:
  source: local                 # a local CSV file...
  positions-dir: data/positions.csv
  # source: cloud               # ...or a shared Google Sheet
  # shareable-address: <sheet id>
```

| symbol | quantity | average_price | date       | currency | ex_rate | exchange |
|--------|----------|---------------|------------|----------|---------|----------|
| vwce   | 12       | 92.40         | 2023-03-06 | EUR      | 1       | XETRA    |
| aapl   | 4        | 150.20        | 2023-05-08 | USD      | 1.09    | NASDAQ   |

`symbol`, `quantity`, `average_price` and `date` (YYYY-MM-DD) are required. The average price is in the investment's own currency, and `ex_rate` converts it to the default currency the same way as in transactions (default 1). `currency` and `exchange` are only shown. Symbols go through the symbol map like transactions.

### Imaginary portfolios

Optional. An imaginary portfolio is a transactions file in the same format as the real one. It is priced from Yahoo like the real portfolio and gets its own report under `<generation-dir>imaginary/<name>/`. The main report compares it with the real portfolio. Its symbols must be in the symbol map.

```yaml
imaginary-portfolios:
  - name: all-world-only        # letters, digits, '-' and '_'
    source: local               # a local CSV file...
    transactions-dir: examples/transactions-all-world.csv
  - name: tech-heavy
    source: cloud               # ...or a shared Google Sheet
    shareable-address: <sheet id>
```

### Net-worth projection

Optional. Projects net worth year by year until retirement and adds a section, a chart and a full table to the report. It also writes `generated/projection.csv` and `generated/projection.md`. Percentages are whole numbers: `7` means 7%.

```yaml
projection:
  birth-year: 1992              # required
  retirement-age: 60            # required
  return: 7                     # required: yearly, before fees
  start-net-worth: portfolio    # 'portfolio' (default), an imaginary portfolio's name, or a number
  cash: 5000                    # added to the start value (default 0)
  income: 45000                 # yearly (default 0)
  income-growth: 2              # default 0
  invest-percent: 15            # share of income invested each year (default 0)
  fees: 0.3                     # yearly, taken off the return (default 0)
  inflation: 2                  # optional: adds a today's-money column
  deposits-withdrawals:         # optional: calendar year -> amount, negative = withdrawal
    2030: -15000
```

Each row is one year from the day of the run, so the first row is next calendar year. Contributions and deposits arrive through the year and earn half a year's return.

## Output

Everything goes under `generation-dir`:

- `report.html`: the report. It links its charts and pages with absolute paths, so it only works on the machine that generated it.
- `generated/portfolio.csv`, `generated/total.md`, `generated/entries.md`: per-investment figures, totals, and the month of each first buy.
- `generated/plots/`: the charts.
- `imaginary/<name>/`: one report per imaginary portfolio.

Known bugs, including wrong totals after a partial sell, are listed in [docs/MODERNIZATION.md](docs/MODERNIZATION.md).

## Demo

`config/demo-cfg.yml` runs on the made-up transactions in `examples/`, with live prices from Yahoo. After [Setup](#setup):

``$ .venv/Scripts/python.exe run.py --cfg config/demo-cfg.yml``

Then open `data/demo-run/report.html`.

## Development

``$ .venv/Scripts/python.exe -m pip install pytest ruff pandas`` (or ``uv sync --inexact``)

``$ .venv/Scripts/python.exe -m pytest``

``$ .venv/Scripts/python.exe -m ruff check .``

``$ .venv/Scripts/python.exe -m ruff format .``

The tests run offline. When a change to the output is intended, regenerate the golden files in `tests/golden/` with `TRKR_UPDATE_GOLDEN=1` and review the diff.

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. After changing them, run `uv lock`, then regenerate `requirements.txt` with:

``$ uv export --no-dev --no-hashes --no-emit-project -o requirements.txt``
