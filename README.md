# trkr

A personal investment-portfolio tracker. It reads your transactions from a CSV file or a public Google Sheet, prices them with Yahoo Finance, and computes profit and loss per investment and in total. The results are written as CSV and Markdown tables, charts, and an HTML report.

## Setup

Python 3.11 or newer. From the project's home directory:

``$ python -m venv .venv``

``$ .venv/Scripts/python.exe -m pip install -r requirements.txt``

`requirements.txt` pins the versions locked in `uv.lock`. Then run:

``$ .venv/Scripts/python.exe run.py --cfg config/cfg.yml``

`--cfg` defaults to `config/cfg.yml`. `--quiet` and `--log-level <level>` override `quiet` and `log-level` in the config; without them, the config decides. `config/*.yml` is gitignored except the demo, so your own configs stay local. To try the tool on made-up data first, see [Demo](#demo).

## Configuration

One YAML file holds everything. The required part:

```yaml
market-data-origin: yahoo        # the only supported source
comp:
  default-currency: EUR          # every value is reported in it
  history-variant: lite          # lite (weekly prices) or full (daily prices, slower)
directories:                     # every directory must end with '/'
  generation-dir: data/me/       # where the outputs go
  log-dir: log/me/
  transactions-dir: data/transactions.csv   # only for transactions source: local
  symbols-map-dir: data/symbols.csv         # only for symbols-map source: local
transactions:
  source: cloud                  # local (a CSV file) or cloud (a Google Sheet)
  shareable-address: <sheet id>  # only for source: cloud
  symbols-standard: custom       # custom: use the symbol map below; yahoo: symbols are tickers
symbols-map:                     # only for symbols-standard: custom
  source: cloud                  # local or cloud
  shareable-address: <sheet id>  # only for source: cloud
cli-exec:
  quiet: false                   # true hides the detailed console output
  log-level: info                # debug, info, warning, error, critical or notset
```

The optional `positions`, `imaginary-portfolios` and `projection` blocks are described below.

For a Google Sheet, set its sharing to "Anyone with the link". Then put the sheet ID in `shareable-address`: that's the part of the link between `/d/` and `/edit`. A sheet ID reads the first tab. To read another tab, paste the link to that tab from the address bar instead (it ends in `#gid=<number>`). The sheet is downloaded as CSV into `<generation-dir>sheets/` on every run.

### Transactions

One row per trade. The columns are read **by position**, so keep them in this order. The first row is always skipped as the header.

| type | date       | quantity | fees | price  | currency | symbol | exchange | platform | ex_rate | ex_fees |
|------|------------|----------|------|--------|----------|--------|----------|----------|---------|---------|
| buy  | 2024-01-08 | 10       | 1    | 105.20 | EUR      | vwce   | XETRA    | broker-a | 1       | 0       |
| buy  | 2024-03-04 | 2        | 1    | 175.10 | USD      | aapl   | NASDAQ   | broker-b | 1.08    | 2       |

- `type` is `buy` or `sell`. `date` is YYYY-MM-DD. Rows don't have to be in date order.
- `price`, `fees` and `ex_fees` (currency exchange fees) are in the trade's own currency.
- `ex_rate` is how many units of the trade's currency one unit of the default currency buys, so 1 when they are the same. The cost in the default currency is `(price × quantity + fees + ex_fees) / ex_rate`.
- `currency`, `exchange` and `platform` are only shown.
- A sell uses the average cost: it removes its share of what the holding cost, and the proceeds, `(price × quantity − fees − ex_fees) / ex_rate`, minus that share are realized profit. Selling more than you hold stops the run with an input error that names the trade.

Most brokers (IBKR, Degiro, Coinbase, …) can export trades as CSV, which you can rearrange into these columns.

### Symbol map

Maps the symbols in your transactions to Yahoo Finance tickers. Two columns, `symbol` then `ticker`, with the first row skipped as the header. Symbols are matched case-insensitively. A symbol missing from the map goes to Yahoo as it is, in lower case. The map is only used with `symbols-standard: custom`; with `yahoo`, write Yahoo tickers in the transactions and leave the map out.

| symbol | ticker   |
|--------|----------|
| vwce   | VWCE.DE  |
| aapl   | AAPL     |
| eur    | USDEUR=X |

Prices are converted to the default currency with Yahoo's rate for each currency: `USDEUR=X` for USD with EUR as default, `GBPEUR=X` for GBP, and so on. London listings quoted in pence (GBp) are divided by 100 first. The map needs no exchange-rate row; an entry for the default currency, like `eur` above, only adds that rate to the charts.

### Positions (holdings snapshot or opening balances)

Optional. You don't have to enter every past trade. List what you hold instead: one row per investment with the quantity, what you paid and a date. A position is what you held **on its date**. Trades in that symbol up to and including the date are already in it, so they are skipped. Later trades in the transactions sheet add on top.

There are two ways to use it:

- **Snapshot.** Copy each holding's quantity and total cost from your broker apps, and date every row today. No trade history is needed. To update it later, change the rows and their date, or enter new trades in the transactions sheet.
- **Opening balance.** Date each row with your first buy, and enter the trades after it in the transactions sheet.

Charts and monthly spending for a symbol start at its earliest row or trade.

```yaml
positions:
  source: local                 # a local CSV file...
  positions-dir: data/positions.csv
  # source: cloud               # ...or a Google Sheet: its ID, or a link to one tab
  # shareable-address: https://docs.google.com/spreadsheets/d/<sheet id>/edit#gid=<tab id>
```

| symbol | quantity | average_price | cost   | date       | currency | ex_rate | exchange |
|--------|----------|---------------|--------|------------|----------|---------|----------|
| vwce   | 12       | 92.40         |        | 2023-03-06 | EUR      | 1       | XETRA    |
| aapl   | 4        |               | 551.19 | 2023-05-08 | USD      |         | NASDAQ   |

- Required: `symbol`, `quantity`, `date` (YYYY-MM-DD), and either `average_price` or `cost` on each row.
- `cost` is the total you paid, in the default currency. Broker apps show it as cost basis or amount invested. This is the simplest choice, because it needs no exchange rate.
- `average_price` is per unit, in the investment's own currency. `ex_rate` converts it the same way as in transactions. It defaults to 1, and it is required when `currency` isn't the default currency.
- Fill in `date` on every row. In Sheets, fill the column down. It can't default to the day of the run, or every trade made after the snapshot would be skipped as already counted.
- `currency` and `exchange` are only shown. Symbols go through the symbol map like transactions.
- In Google Sheets, the positions can be a tab of the transactions sheet. Link `shareable-address` to that tab, and keep the transactions on the first tab, or link to their tab too.

The run prints how many trades the positions skipped.

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
- `generated/portfolio.csv`, `generated/total.md`, `generated/entries.md`: per-investment figures, totals, and the month of each first buy. `spending`, `profit_net` and `profit_percent` are about what you still hold; `realized_profit` is what sells made.
- `generated/plots/`: the charts. "Valuation Percent" is the market value of your holdings at the end of each month, as a percentage of this month's.
- `imaginary/<name>/`: one report per imaginary portfolio.

Known bugs are listed in [docs/MODERNIZATION.md](docs/MODERNIZATION.md).

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
