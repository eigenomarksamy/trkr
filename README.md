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

## Demo

**To run the demo execute the following command in the home directory terminal for the project:**

``$ python -m venv .venv``

``$ .venv/Scripts/activate``

``$ python -m pip install --upgrade pip``

``$ pip install -r requirements.txt``

``$ python run.py --sheets-config-file config/demo-sheets.yml --settings-config-file config/demo-settings.yml``

Then check the directory `data/demo/`
