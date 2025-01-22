# Tracker

## Description

### YAML Files

- *platforms.yml*: Includes the configurations for the used platforms (unused).
- *settings.yml*: Includes the general settings for the program.
- *sheets.yml*: Includes the addresses of the used sheets in the program.

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
    <https://docs.google.com/spreadsheets/d/1S04AVxZ7vKS3_7G5hJzeclkg2M8p69UghOMMfqPh-AE/edit?usp=drive_link> --> `1S04AVxZ7vKS3_7G5hJzeclkg2M8p69UghOMMfqPh-AE`

    sheets.yml:
    `transactions: 1S04AVxZ7vKS3_7G5hJzeclkg2M8p69UghOMMfqPh-AE`

    ***Please note that this is just an example and not an actual sheet.***

#### Market Data

1. Same as step 1 in 'Transactions'

    With the following headers:

    - symbol
    - price
    - currency

    Fill the sheet with the data of the symbols you're interested in, for example:

    | symbol | price | currency |
    | ------ | ----- | ---------|
    | BTCEUR | `=GOOGLEFINANCE("BTCEUR")` | EUR |
    | NVDA | `=GOOGLEFINANCE("NASDAQ:NVDA")` | USD |
    | PFE | `=GOOGLEFINANCE("NYSE:PFE")` | USD |
    | VEUR | `=GOOGLEFINANCE("AMS:VEUR")` | EUR |

2. Same as step '2' that you did with 'Transactions'

3. Same as step '3' that you did with 'Transactions'

    Use the `live-market-data` instead of 'transactions' this time.

4. While still with the google sheet open, do the following procedure:
   1. Go to 'File'
   2. Go to 'Settings'
   3. Go to 'Calculation'
   4. Under 'Recalculation', change the selection to 'On change and every minute'.
   5. Make sure the sheet is synced to the drive.
   6. Voila!

#### Market History

1. Same as step '1' in 'Market Data'

    With no headers of your own.

    Just paste the following formula in the `A1` cell:
    `=GOOGLEFINANCE("<symbolOfInterest>","price",DATE(<YYYY-MM-DD>),TODAY(),"<interval>")`

    - Replace the `<YYYY-MM-DD>` with the actual date of interest (first date), e.g., 2023-12-03.
    - Replace the `<symbolOfInterest>` with the actual symbol you're interested in, e.g., `AMS:VUSA`
    - Replace the `<interval>` with the interval of interest, either `daily` or `weekly`, weekly is used for the lite version and daily used for the full version, check the Settings section, to configure that variation.

    After doing that a table will be generated, you need to create a column with the same size of the current table, the column title's is 'Currency' then you enter the currency or use the '`GOOGLEFINANCE`' API to do so.

2. Same as step '2' from 'Market Data'.
3. Same as step '3' from 'Market Data'.

    ``
    history-full:
    ``

    ``
    btceur: 1V7BHFocUnTAMENoY8FkYtyug7597z5sPpRUQsGb_Y6Y
    ``

    Or

    ``
    history-full:
    ``

    ``
        btceur: 1V7BHFocUnTAMENoY8FkYtyug7597z5sPpRUQsGb_Y6Y
    ``

    ***Please note that this is just an example and not an actual sheet.***

**Repeat the previous steps for all the symbols you're interested in.**

### Settings

The settings are fairly simple.

`default-currency:` That's either 'EUR' or 'USD' without the quotes.

`history-variant:` That's either 'full' or 'lite' without the quotes.

`generation-dir:` That's the directory that will have the output of the program, for example: 'data/user/' without the quotes.
