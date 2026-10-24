# Tracker

## Description

### YAML Files

- *cfg.yml*: includes the configurations.

## Usage

To use the program there are a few required steps.

### Sheets

There are some google sheets required to be used as source of data.

#### Transactions

1. Please create a google sheet that has the transactions to be used by the tool.

    With the following headers:

    - type
    - date *(Written in YYYY-MM-DD fashion)*
    - quantity
    - fees
    - price
    - currency
    - symbol
    - exchange
    - platform
    - ex_rate
    - ex_fees

    **Example:**

    | type | date | quantity | fees | price | currency | symbol | exchange | platform | ex_rate | ex_fees |
    |--------|-------|--------|-------|--------|-------|--------|-------|--------|-------|--------|
    | buy | 2023-12-04 | 5 | 1 | 36.02 | EUR | VEUR | AMS | Degiro | 1 | 0 |
    | buy | 2023-12-02 | 0.00269324 | 2.99 | 36019.81 | EUR | BTCEUR | NA | Coinbase | 1 | 0 |
    | buy | 2024-06-25 | 0.5 | 0 | 124.21 | USD | NVDA | NASDAQ | IBKR | 1.07055 | 2 |
    | sell | 2024-12-27 | 21 | 1 | 39.1809524 | EUR | VEUR | AMS | Degiro | 1 | 0 |

2. Share the sheet and copy the link, don't forget to change the sharing settings to 'Anyone with link'.

3. Paste the link in *config/sheets.yml*, then strip everything in the sheet to just the ID.

    Example:
    <https://docs.google.com/spreadsheets/d/1Hgk5htL_6VlO8byEGJjLkD2a0XZoVXjWdoWRbWJyxVI/edit?usp=drive_link> --> `1Hgk5htL_6VlO8byEGJjLkD2a0XZoVXjWdoWRbWJyxVI`

    sheets.yml:
    `transactions: 1Hgk5htL_6VlO8byEGJjLkD2a0XZoVXjWdoWRbWJyxVI`

    ***Please note that this is just an example and not an actual sheet.***

***Pro-tip: you can import your transactions as a CSV file from any platform you use (IBKR, CoinBase, Degiro, etc.).***

#### Symbol Map

Since we migrated from `GOOGLEFINANCE` to `YFinance` we need to add symbols' map for the symbols of interest.

1. Create a sheet similar to the  `transactions` sheet created in the previous step
with a map between the symbols of interest and how they're represented on yahoo-finance.

    With the following headers:

    - symbol
    - ticker

    **Example:**

    | symbol | ticker |
    |--------|-------|
    | btceur | BTC-EUR |
    | meta | META |
    | usd | EURUSD=X |
    | vwce | VWCE.AS |

2. Share the sheet and copy the link, don't forget to change the sharing settings to 'Anyone with link'.

3. Paste the link in *config/sheets.yml*, then strip everything in the sheet to just the ID.

    Example:
    <https://docs.google.com/spreadsheets/d/1RZ_NBdxaFfT-ElmmaaQdouxoeVKLuT2r0inuvxFX8n4/edit?usp=drive_link> --> `1RZ_NBdxaFfT-ElmmaaQdouxoeVKLuT2r0inuvxFX8n4`

    sheets.yml:

    ``
`yfinance-map: 1RZ_NBdxaFfT-ElmmaaQdouxoeVKLuT2r0inuvxFX8n4`
    ``

    ***Please note that this is just an example and not an actual sheet.***

### Settings

The settings are fairly simple.

`default-currency:` That's either 'EUR' or 'USD' without the quotes.

`history-variant:` That's either 'full' or 'lite' without the quotes.

`generation-dir:` That's the directory that will have the output of the program, for example: 'data/user/' without the quotes.

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

## Demo

`config/demo-cfg.yml` runs on the made-up transactions in `examples/`, with live prices from Yahoo. **To run it, execute the following commands in the project's home directory:**

``$ python -m venv .venv``

``$ .venv/Scripts/activate``

``$ python -m pip install --upgrade pip``

``$ pip install -r requirements.txt``

``$ python run.py --cfg config/demo-cfg.yml``

Then open `data/demo-run/report.html`.

## Tests

``$ .venv/Scripts/python.exe -m pytest``

The tests run offline. When a change to the output is intended, regenerate the golden files in `tests/golden/` with `TRKR_UPDATE_GOLDEN=1` and review the diff.
