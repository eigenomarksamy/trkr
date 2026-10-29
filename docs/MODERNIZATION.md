# Modernization plan

A living checklist. Tick items as they land and note the commit hash. Order matters: Phase 0 builds the safety net that makes the later phases safe, because the portfolio math has only end-to-end golden coverage and has confirmed bugs.

State as of 2026-10-22: the last code change was 2025-03; the scheduled job ran successfully through 2025-11-04.

2026-10-23: the net-worth projection and imaginary portfolios landed, ahead of the phases, at the owner's request. They brought part of Phase 0 with them: offline test fixtures, the golden end-to-end test and the demo config.

2026-10-23: added a plan for a local web app ("Feature: web app"). Nothing is built yet.

2026-10-24: Phase 0 is done. The work from 2026-10-23 was committed first (`49af3d4`, `e18cdee`). Writing the characterization tests turned up a new bug, added to Phase 1 as bug 12.

2026-10-28: the owner asked for less admin when adding past investments and picked a holdings snapshot: list what you hold now and skip the trade history. It extends opening positions ("Feature: opening positions and holdings snapshot"). Building it turned up bug 13. The owner also asked to plan three more things: a web page for the snapshot, an importer for broker exports, and a sheet generator. They are planned below as "Feature: broker import", "Feature: sheet generator" and web app milestones W7-W9. None of the three is built.

2026-10-29: Phase 1 is done, on branch `phase-1-bugs` (not merged). Each bug is one commit, test first; a follow-up commit puts the monthly charts on a date axis. The fixes needed four decisions, now in the decisions table: what happens on a sell of more than is held, what the valuation chart shows, how currencies are converted, and how the CLI flags combine with the config. Selling the whole fixture turned up bug 14.

## Status (2026-10-29)

| Area | State |
|---|---|
| Phase 0 | Done and committed (last: `88b87d4`). |
| Projection, imaginary portfolios, opening positions | Done and committed (`49af3d4`). |
| Holdings snapshot, bug 13, sheet tab links | Done and committed (`c45f7c3`). 106 tests pass. The demo run and a live run with a snapshot dated today both exit 0. |
| Phase 1, bugs 1-12 | Done on branch `phase-1-bugs` (`bb62641`..`1138a49`), not merged. 163 tests pass, and the demo run exits 0. Bug 14 is open. |
| Phases 2-4 | Not started. |
| Web app, W0-W9 | Not started. W1 and later wait on Phase 2 items and the Phase 3 package. |
| Broker import, sheet generator | Planned only. The importer waits on sample exports from the owner. |

Waiting on the owner:

- a holdings tab in the transactions sheet, and the `positions:` block in `cfg.yml` and `cfg_bat.yml`;
- one export per broker, for the importer;
- the new defaults in the decisions table: web editing of holdings, Google Sheets for the generator, and what "prompts" means.

## Decisions for the owner

Claude assumes the defaults below unless told otherwise.

| Question | Default |
|---|---|
| Environment/lock tool | `uv` (`pyproject.toml` + `uv.lock`), with `requirements.txt` exported from the lock until `run_script.bat` switches over. Needs `winget install astral-sh.uv`. Alternative: plain pip + `pip-compile`. |
| Python floor | `>=3.11`, so the current venv keeps working. |
| Cost basis for sells | Average cost (already implied by `break_even_price`). Realized and unrealized P&L reported separately. |
| Selling more than is held | The run stops with 400 `InvalidInputData` and names the trade, as bad positions rows do. Every figure after such a sell would be wrong, and it usually means a missing buy. A sell within 1e-9 (relative) of the holding counts as selling all of it. |
| "Valuation Percent" chart (bug 6) | The market value of the holdings at the end of each month, from the first trade's month through the current one, as a percentage of the current month's. A month without a close takes the previous close, or today's price. |
| Currency conversion (bug 7) | Each currency with its own Yahoo pair, `<CUR><DEFAULT>=X`. Minor units (GBp, ZAc, ILA) are divided by 100. A ticker Yahoo gives no currency for stops the run with 503 instead of being treated as USD. The symbol map's default-currency row is no longer needed. |
| CLI flags (bug 8) | `--quiet` and `--log-level` override the YAML `cli-exec` block when given, and leave it alone when not. |
| Data sources | Keep Google Sheets (CSV export) and local CSV. Keep Yahoo via `yfinance`. |
| Report format | Keep a static HTML report + PNGs, but make it portable (relative paths). Interactive charts are Phase 4. |
| Projection starting point | The real portfolio's current market value plus a fixed `cash` amount from the config. Expected return and fees are explicit inputs, never derived from past performance. |
| Projection percentages | Whole numbers in the YAML (`7` = 7%), as in the C++ tool. |
| Nominal vs real | Nominal, as in the C++ tool. Setting `inflation` adds real-value columns. |
| Imaginary portfolios | Transactions files in the same format as the real one, priced live from Yahoo through the same pipeline. The C++ model (holdings valued at their purchase price) is not ported. |
| Mortgage calculator in `networth_projection` | Not ported. |
| First projection row | One year after the run (owner, 2026-10-23). A run in October 2026 labels row 1 as 2027, so no year is credited with a full year it hasn't had. |
| Opening positions | One row per investment (quantity, average price or total cost, and a date per row) in a separate optional file or sheet tab, local or cloud. A position is what was held *as of* its date. Trades in that symbol up to and including the date are already in it and are dropped; later trades adjust it (owner, 2026-10-23; as-of rule 2026-10-28). Real portfolio only for now. |
| Web app: where it runs | On the owner's PC only, bound to `127.0.0.1`, with no login. The pages show holdings, and the config holds sheet IDs that anyone with the link can read. Opening it to the LAN or the internet needs auth and HTTPS first, and is a separate decision. |
| Web app: stack | FastAPI + Jinja2 + htmx, rendered on the server, with no Node build step. htmx and `plotly.min.js` are vendored at pinned versions, so the pages work offline. Alternative: Streamlit gets to a first page faster, but it can't share templates or tests with the static report. |
| Web app: charts | Plotly. Figures are built in Python from the run snapshot and drawn in the browser. |
| Web app: how a run executes | The CLI runs as a subprocess, one run at a time, under a lock file that the scheduled job also takes. A crash or a hang can't take the server down, and process-wide state (bugs 5 and 9) stays out of the server. |
| Web app: data contract | Every CLI run writes a versioned `snapshot.json`, the scheduled run included. The server reads snapshots. The only thing it computes itself is projections. |
| Web app: config | Read-only. The server never writes `cfg.yml` or `cfg_bat.yml`. What-ifs live in the URL or under `<gen-dir>/web/`. `run_web.bat` points at `cfg_bat.yml`, so the app opens on the scheduled job's latest run. |
| Web app: dependencies | An optional `web` extra in `pyproject.toml`, so the scheduled job doesn't install FastAPI. |
| Snapshot date | Required on every row. Defaulting it to the run date would move the date every day, and each later trade would be dropped as already counted. In Sheets, fill the column down. |
| Snapshot cost | `cost` is the total paid in the default currency, as broker apps show it, so it needs no `ex_rate`. A row with `average_price` in another currency now requires `ex_rate`, which used to default to 1 without a warning. |
| Web app: editing holdings | The holdings snapshot is the one thing the app edits, and only in a local file (`positions: source: local`). With a Google Sheet source the page shows the rows read-only and links to the sheet. Transactions stay read-only, and the app still never writes the config. |
| Broker import: output | A CSV of new rows in the sheet's column order, to paste into the sheet or append to a local file. The importer never writes to Google. |
| Sheet generator: Google Sheets | It writes one CSV per tab, to import into a new Google Sheet (File > Import), and the matching config blocks. Creating the sheet directly through the Google Sheets API needs a Google Cloud project, OAuth consent on the owner's account and a stored token, so it is a separate decision. |
| Sheet generator: "prompts" | Questions the tool asks, in the terminal and in the web app. Turning free text into rows with an LLM is a different feature: it needs an API key and sends holdings to a third party. Not planned unless the owner asks. |

## Phase 0: Safety net (no behaviour changes)

- [x] `pyproject.toml` with project metadata and runtime deps with lower bounds: pyyaml, requests, matplotlib, numpy, yfinance, jinja2, **python-dateutil** (imported in `portfolio_mngr.py` but undeclared; it arrives transitively via pandas). Drop **markdown2** (never imported). Dev deps: pytest, ruff, and pandas (the tests import it). (`977d6d4`)
- [x] Lock file, with `requirements.txt` regenerated from it so `run_script.bat` installs the same versions. `uv.lock` pins the versions that were already in the venv, so the scheduled job's next `pip install` changes nothing. (`977d6d4`)
- [x] Ruff lint + format config. Do the first format pass as its own commit. The rules are listed explicitly (`E4, E7, E9, F, I, B`), because ruff 0.17's default set is much wider and moves with upgrades. Line length is 100, with single quotes. Config and lint fixes: `1ae21ea`. Format pass: `e09c62a`, skipped by `git blame` via `.git-blame-ignore-revs` (`4b87973`).
- [x] `tests/` with offline fixtures: synthetic transactions CSV, symbol-map CSV, and a stubbed `yfinance.Ticker` returning fixed DataFrames. Also freezes `datetime.today()` in `portfolio_mngr`, and, since 2026-10-28, `date.today()` in `market_mngr`. pytest is configured in `pytest.ini`. (`49af3d4`)
- [x] Characterization tests: `Portfolio.calculate` (buys only, several symbols), `compute_spending_history`, `get_entry_points_months`, `convert_date_to_short_str`, `create_cfg` for each source combination, `CsvMngr.read`, and `get_google_sheet` URL building. (`f9910cc`; `tests/test_portfolio.py`, `test_month_key.py`, `test_csv_mngr.py`, `test_sheets.py`, `test_cfg.py`)
- [x] Golden end-to-end test: `exec()` against a fixture config with the network stubbed. Snapshot `portfolio.csv`, `total.md` and `entries.md`; for PNG/HTML, only assert that they exist. (`tests/test_exec.py`; `TRKR_UPDATE_GOLDEN=1` rewrites the snapshots.) (`49af3d4`)
- [x] Fill in `config/demo-cfg.yml` (currently empty) to point at tracked sample CSVs in `examples/` (`trans-src: local`, `sym-map-src: local`), so a fresh clone can run the tool. It also shows an imaginary portfolio and a projection. (`49af3d4`)
- [x] Fix the README. It documents `sheets.yml`/`settings.yml` and a `--sheets-config-file` flag that no longer exist; the real CLI is `run.py --cfg <file>`. Document the actual YAML schema. (`9e252d5`)
- [x] Once ruff is installed, add a PostToolUse hook in `.claude/settings.json` that formats edited `.py` files. (`1a5a07f`; `.claude/hooks/format_python.py` sorts imports and formats.)

## Phase 1: Known bugs (each fix: failing test first, then the fix)

Ordered by impact. Line numbers are as of commit `c1d28fe`.

1. [x] **Partial sells corrupt totals.** `src/portfolio_mngr.py:51-54`: a sell subtracts the symbol's *entire* spending from the total but leaves the symbol's own spending unchanged. No sale proceeds are recorded either, so realized P&L is lost.
   Reproduced: buy 10 @ 10 of A and of B, then sell 5 of A. Reported: total spending 100 and profit +60%. Correct: remaining cost basis 150, unrealized +6.7%, realized +10. With a single symbol, a partial sell raises `ZeroDivisionError`.
   Related: `amount == 0` float equality (`:57`) keeps dust positions after crypto sells, and a sell seen before any buy of that symbol uses `current_price` 0.
   Fixed: average cost, trades walked by date, `realized_profit` in the total and per symbol (a new last column in `portfolio.csv`), dust closes the position, and selling more than is held is a 400. Value, break-even and targets are derived once at the end. (`5468eef`; `tests/test_portfolio.py`, `test_exec_with_a_snapshot_and_a_later_partial_sell`)
2. [x] **`history-variant: full` crashes.** Daily history is keyed `YYYY-MM-DD`, but `compute_historical_valuation` looks up month keys like `jan24`, which raises `KeyError`. That error then turns into bug 4. The fix must also cover bug 13 for daily bars: today has no bar until the close, and weekends have none. Bug 13's fix only fills the current month for `lite`.
   Fixed: the valuation reduces either key format to month closes (`430586c`), entry markers match by month (`2b66398`), today's daily key gets the current price, and the per-ticker charts use a date axis (`904049a`; `test_exec_with_full_history`, `tests/test_market.py`).
3. [x] **`symbols-standard: yahoo` crashes.** `run.py:69,76,177` dereference `yfinance_map_obj.tickerMap` unconditionally, and `MarketDataYahoo` requires a ticker map for currency conversion (`src/market_mngr.py:161`).
   Fixed: no map means no mapping, and no bogus `'EUR'` or `'None'` ticker is fetched; the conversion needs no map since bug 7. (`853acfc`; `test_exec_with_yahoo_tickers_and_no_symbol_map`)
4. [x] **Error handler crashes on ordinary exceptions.** `run.py:195,202` do `int(str(e))`, so any exception without a numeric message raises `ValueError` inside `except`: a traceback, and exit code 1 only by accident.
   Fixed: `get_exit_status` maps only plain `Exception('<code>')`; anything else prints its traceback and exits 1 as `UnexpectedError`. (`bb62641`; `tests/test_run_cli.py`)
5. [x] **`check_internet` sets a global 3 s socket timeout** (`src/utils.py:20`) for the rest of the process, including every yfinance/requests call after it. It also leaks the socket. Likely source of flaky runs on slow networks.
   Fixed: `socket.create_connection` with a per-call timeout, in a `with` block. (`261d266`; `tests/test_utils.py`)
6. [x] **Historical valuation is not a valuation.** `compute_historical_valuation` *adds* sell quantities (`:136`). It also only prices each lot in the month it was bought and never revalues holdings, so the result is closer to cumulative money invested. Decide what the "Valuation Percent" chart should show, then fix it.
   Fixed: month-end market value of the holdings through the current month (see the decisions table). (`430586c`; `tests/test_portfolio.py`) The monthly charts got a date axis, because the longer range made their labels overlap (`1138a49`).
7. [x] **Currency conversion only supports two currencies.** Every non-default-currency asset is multiplied by the one FX ticker, so a GBP/GBp/CHF listing would be silently mispriced. Convert per currency pair.
   Fixed: per-pair rates fetched on demand, minor units, 503 for a missing currency. USD to EUR is still `USDEUR=X`, so the owner's figures don't change. (`d7d87a1`; `tests/test_market.py`)
8. [x] `--quiet` / `--log-level` CLI flags are ignored (`src/utils.py` parses them; `run.py` never reads them).
   Fixed: they override the config when given; `--log-level` only takes known levels. (`91958d4`; `tests/test_run_cli.py`)
9. [x] Matplotlib figures are never closed (`src/plot_mngr.py`), which warns past ~20 figures and leaks memory in long runs.
   Fixed: each figure is closed once saved. `plot_pie` and `plot_bar` are never called and join the Phase 2 dead-code list. (`4631c79`; `tests/test_plots.py`)
10. [x] `plot_monthly_stocks` locates the entry point with the `names` list from the *previous* symbol (`src/plot_mngr.py:49`). Wrong x position when two series have different dates.
    Fixed: each series is plotted on its own dates on a date axis, so series with different dates line up, and its marker is its own first point in the entry month. (`2b66398`; `tests/test_plots.py`)
11. [x] File I/O has no `encoding=`, so on Windows a non-ASCII character in a sheet (e.g. `€`) breaks reads under cp1252.
    Fixed: CSV and YAML are read as `utf-8-sig`; CSV, Markdown, HTML, templates and the log are written as UTF-8. The owner's configs are ASCII. (`6db4330`; `tests/test_encoding.py`)
12. [x] **Monthly loops drop the last month.** `compute_spending_history` and `compute_historical_valuation` step one month at a time from the *first* transaction's date and stop once past the *last* transaction's date. When the last transaction falls on an earlier day of the month than the first (first 2024-01-20, last 2024-03-05), the final month is never visited, so its buys are missing. This affects the spending chart, the valuation chart and the projection's "invested in the last 12 months". The golden fixture (2024-01-15 → 2024-04-08) and the demo (2024-01-08 → 2025-02-03) both hit it. Found 2026-10-24; pinned by `test_spending_history_drops_the_last_month_when_its_day_is_earlier`. Iterate over month starts instead.
    Fixed: both loops step over month starts. (`a3bb065`; the pinning test, renamed `test_spending_history_keeps_the_last_month_when_its_day_is_earlier`, now pins the fix)
13. [x] **A buy in the current month crashes the run when the month has no weekly bar yet.** `lite` history labels each weekly bar with its Monday. So on the 1st-6th of a month, the month can have no bar yet. A window that starts today has no bars at all, and Yahoo prints "possibly delisted". `compute_historical_valuation` then raises `KeyError`, which becomes bug 4. A snapshot dated today always hit it. Found 2026-10-28 by probing Yahoo with AAPL. Fix: skip the Yahoo call when the window is empty, and give the current month today's price when it has no bar. (`tests/test_market.py`; `c45f7c3`)
14. [ ] **A portfolio with every position sold crashes.** `write_csv_lazy` (`src/csv_mngr.py`) takes its headers from the first row, so an empty portfolio raises `StopIteration` (exit 1 since bug 4). `plot_combined` would then divide by a last valuation of 0 and draw an empty pie. Found 2026-10-29 by selling the whole fixture. It predates the bug 1 fix, which only made the totals right up to that point.

## Phase 2: Structure and cleanup (behaviour-preserving, guarded by Phase 0 tests)

- [ ] Delete dead code: `MarketDataGoogle*`, `MarketReader`, `fetch_histories`, `use_market_google`, `execute_yahoo_finance`, unused parts of `Sheets`, `src/market_tester.py`, unused `TransType`, `Transactions.prepend` (only tests use it since `merge_positions`), and `plot_pie`/`plot_bar` in `plot_mngr.py`.
- [ ] A single month-key helper instead of two copies of `convert_date_to_short_str`. They already differ when called with no arguments: the `portfolio_mngr` copy returns `None`, the `market_mngr` copy `''` (`tests/test_month_key.py`).
- [ ] `Transaction` becomes a `@dataclass`; remove the `__dict__` method; `Transactions.get()` stops exposing the mutable internal list.
- [ ] Config becomes typed dataclasses with validation and clear error messages (same YAML schema). Use `pathlib.Path` for every directory, which removes the trailing-slash requirement.
- [ ] A real exception hierarchy (`TrkrError` → `NoNetworkError`, `UnsupportedConfigError`, …), mapped to exit codes in one place. `get_exit_status` (`src/utils.py`, bug 4) is that place for now.
- [ ] Replace `print` + `is_quiet` threading with `logging` (console level from `quiet`); simplify `LogManager` to stdlib level parsing.
- [ ] `CsvMngr.read` → `csv.DictReader` keyed by the header row. Today it relies on column order and blindly drops the first row.
- [ ] Templates become tracked `.html` files loaded via `PackageLoader`, no longer rewritten at runtime. Un-ignore them, and turn on Jinja autoescape.
- [ ] `Interval` → `StrEnum`; tidy type hints (`Optional[...]` → `X | None`).

## Phase 3: Packaging and performance

- [ ] `src/trkr/` package with a `trkr` console script (`python -m trkr --cfg …`). Keep `run.py` as a thin shim. Point `run_script.bat` at it and stop reinstalling dependencies on every scheduled run.
- [ ] Fetch prices in one batched `yf.download(tickers, …)` call. Today each ticker costs three requests (`history`, `.info`, `history(period="1d")`), and `.info` is the slowest and flakiest. Get currency from `fast_info`. Keep bug 13's behaviour, which `tests/test_market.py` pins: no request for a window that starts today, and the current month filled from the current price.
- [ ] Optional on-disk cache of history, so same-day re-runs need little network.
- [ ] Relative paths in the HTML report, so a `data/<run>/` folder can be moved or zipped.
- [ ] GitHub Actions (`origin` is GitHub): ruff + pytest on push and PRs.
- [ ] Upgrade the locked dependencies. `uv.lock` still pins the venv as of 2025 (yfinance 0.2.59, pandas 2.2.3, numpy 2.1.2, matplotlib 3.10.0). Upgrade with `uv lock --upgrade`, check with the golden test and a demo run, then re-export `requirements.txt`. pandas 3 changes the default string dtype and turns on copy-on-write, so take it as its own step. matplotlib 3.11 removes `plt.cm.get_cmap`, which `plot_monthly_stocks` still calls (a deprecation warning in the tests); switch to `matplotlib.colormaps` first.

## Feature: net-worth projection and imaginary portfolios

A port of the owner's C++ tool at `C:\dev_ws\networth_projection` (`src/networth/`, `src/portfolio/`), which lives outside this repo. Landed 2026-10-23, before Phase 2, so the report sections are inline strings in `report_mngr.py` like the rest; they move with the other templates. Build fixtures from made-up numbers: don't use that project's `gen/` files or its `fillDefaults()` values.

### What the C++ projection computes

One row per year, from the current age to the retirement age inclusive. For year *n*, with return `r`, income growth `g` and fees `f`:

- `income` starts at the configured value and grows by `g` from year 2 on.
- `contribution = income × invest%`.
- `extra` is the deposit (+) or withdrawal (−) planned for year *n*, or 0.
- `return = NW[n−1] × r + (contribution + extra) × r / 2`. New money earns half a year's return (mid-year convention).
- `NW[n] = NW[n−1] + contribution + extra + return`.
- The whole series runs twice: gross with `r`, net with `r − f`.

Output columns: age, year, income, yearly investment, deposit/withdrawal, gross return, gross net worth, net return, net net worth.

C++ defects not to carry over:

- **The year-1 deposit/withdrawal is always dropped.** The constructor reads the plan (`networth.cpp:16`) before `main.cpp:25` calls `setDepWithdrawalPlan`, and the year-1 net-worth formula leaves out the deposit term anyway (`:18`). Also fixed in `networth_projection` on 2026-10-23 (not committed there), and `bin/investor.exe` was rebuilt.
- Plan entries are keyed by year index, where 1 is the first projected year. trkr runs on a schedule, so year 1 moves every January and the plan would drift. Key it by calendar year.
- Values accumulate in 32-bit `float` over ~40 years. Python floats fix this, so any golden values taken from `bin/investor.exe` need a tolerance.
- The projection stops at retirement, with no drawdown phase.

### Projection

- [x] `projection.py`: a pure function, inputs dataclass → list of row dataclasses, with no I/O and no network. Tests come first: a hand-computed 3-year case, `fees: 0` (gross == net), deposits and withdrawals including year 1, and one golden case checked against `bin/investor.exe` run on the same made-up inputs.
- [x] Config: an optional `projection:` block. Absent means the feature is off and output is unchanged. `create_cfg` indexes required keys with `[]`, so read the new keys with `.get()`. Store `birth-year`, not age, so the config doesn't go stale. Validate that retirement is in the future and that percentages are in range. Sketch (made-up values):

  ```yaml
  projection:
    birth-year: 1990
    retirement-age: 65
    start-net-worth: portfolio   # or a fixed number
    cash: 5000                   # added to the start value
    income: 50000
    income-growth: 2             # % per year
    invest-percent: 15           # % of income
    return: 7                    # % per year, before fees
    fees: 0.5                    # % per year
    inflation: 2                 # optional: adds real-value columns
    deposits-withdrawals:        # optional: calendar year -> amount, negative = withdrawal
      2030: -20000
  ```

- [x] `start-net-worth: portfolio` takes `total['value']` from `Portfolio.calculate`, the current market value in the default currency, and adds `cash`.
- [x] Outputs: `generated/projection.csv`, `generated/projection.md`, and `plots/projection.png` with gross and net net worth by age, plus real net worth when `inflation` is set. Close the figure (see bug 9).
- [x] Report: a "Projection" section in `report.html` with the chart and the assumptions. Show the amount actually invested over the last 12 months (from `compute_spending_history`) next to the assumed yearly contribution, so the assumption can be sanity-checked.

### Imaginary portfolios

- [x] Extract the "transactions → market data → `Portfolio` → outputs" part of `exec` (`run.py:19-188`) into a function that takes a transactions source and an output directory. This is behaviour-preserving and guarded by the Phase 0 golden test. (`process_portfolio` → `PortfolioRun`.)
- [x] An optional `imaginary-portfolios:` list in the YAML. Each entry has `name`, `source: local|cloud`, and `transactions-dir` or `shareable-address`, mirroring the real `transactions` block. The files use the same columns as real transactions, and their tickers must be in the symbol map. Outputs go under `<gen-dir>/imaginary/<name>/`, linked from the main report. Each portfolio fetches its own market data, so adding one can't change the real portfolio's history window. The Phase 3 batched download should batch across portfolios too.
- [x] A comparison table in the report: the real portfolio against each imaginary one, showing invested, value, profit and profit %.
- [x] `start-net-worth` can name an imaginary portfolio, to project "what if I had held X instead".

### Later, owner's call

- [ ] Buys without a price: leave `price` empty and fill it from that day's Yahoo close, so a what-if portfolio needs only a date, a ticker and an amount. Needs daily history (bug 2, fixed).
- [ ] Scenarios: several named return/fee sets (e.g. pessimistic, base, optimistic) on one chart.
- [ ] Drawdown after retirement: a withdrawal rate, and how long the money lasts.

## Feature: opening positions and holdings snapshot

For holdings without a full trade history: one row per investment with a quantity, an average buy price or total cost, and a date. It works two ways:

- **Opening balance.** The date is the first buy, and trades after it adjust the position.
- **Snapshot.** The date is the day the numbers were copied from the broker apps, and no trade history is needed.

- [x] `build_positions` (`src/transactions.py`) reads the file by column name. `symbol`, `quantity` and `date` are required, plus `average_price` or `cost` (since 2026-10-28; before that, `average_price`). `currency`, `ex_rate` and `exchange` are optional. It validates each row and exits with 400 `InvalidInputData` on bad data. Each row becomes a `buy` on its date, with platform `positions file`, priced at the average price or at `cost / quantity`.
- [x] Optional `positions:` block (`source: local` with `positions-dir`, or `cloud` with `shareable-address`). Positions go before the transactions, because `Portfolio.calculate` processes the list in order. Since 2026-10-28 that is done by `merge_positions`, which also drops the trades a position already includes (below).
- [x] Tests: reader and validation, config, and an end-to-end run combining positions with trades. The demo config uses `examples/positions.csv`.
- [ ] Positions for imaginary portfolios, which would make "I hold N at price P" what-ifs possible without a transactions file.
- [x] A position followed by a partial sell inherits bug 1 (totals). Fixing bug 1 fixes this too. (`5468eef`; `test_exec_with_a_snapshot_and_a_later_partial_sell`)

### Holdings snapshot (owner, 2026-10-28)

- [x] Bug 13 fixed, so a position dated today doesn't crash the run. Checked live on 2026-10-28 with a snapshot of the demo holdings dated that day: the run starts its history that day and exits 0. (`c45f7c3`)
- [x] `shareable-address` takes a link copied from the browser, including a link to one tab (`#gid=`), so the snapshot can live as a tab in the transactions sheet. Plain IDs, export links and publish-to-web links behave as before. (`sheet_export_url`; `tests/test_sheets.py`; `c45f7c3`)
- [x] `merge_positions` (`src/transactions.py`): positions go first. A trade in a symbol that has a position is dropped when it is dated on or before that position (the latest one, if the symbol has several rows). The run prints how many trades were dropped. Trades in other symbols are untouched. (`tests/test_positions.py`, `test_exec_with_a_holdings_snapshot`; `c45f7c3`)
- [x] A `cost` column (total paid, in the default currency) as an alternative to `average_price`, one or the other per row. The synthetic buy is priced at `cost / quantity`, with `ex_rate` 1. A row with `average_price` in another currency and no `ex_rate` is rejected. (`tests/test_positions.py`; `c45f7c3`)
- [x] README, `examples/positions.csv` (one row with `cost`, same numbers) and CLAUDE.md. (`c45f7c3`)
- [ ] Owner: add a holdings tab to the transactions sheet and a `positions:` block to `cfg.yml` and `cfg_bat.yml`. Keep transactions as the sheet's first tab, or link to that tab as well. Claude doesn't edit those configs without asking.
- [ ] Later, owner's call: a symbol with no older trades has a price chart that starts at the snapshot. An optional `since` column (first-buy date) could start its history earlier without changing the cost.

## Feature: broker import (planned, owner 2026-10-28)

Reads the trade exports from the owner's brokers (Degiro, IBKR and Coinbase) and turns them into trkr transaction rows. The sheet can then be caught up without typing. The same parsers can produce holdings-snapshot rows from each broker's portfolio export.

- [ ] Samples first: the owner provides one real export per broker, kept in `data/` (gitignored). Each parser is written against that file and tested on a made-up file in the same format, in `tests/fixtures/brokers/`. Real rows never go into fixtures.
- [ ] `src/importers/`: one module per broker, each with `detect(header) -> bool` and `parse(path) -> list[Transaction]`. The importer picks the parser from the header row, so the owner doesn't have to name the broker. Check each sample for localized headers, decimal commas, multi-section files (IBKR activity statements) and lines before the header.
- [ ] Fees, `ex_rate` and `ex_fees` come from the export when it has them. A row whose export lacks one is flagged in the output, not guessed.
- [ ] Symbols: Degiro names products by name and ISIN, not by ticker. The symbol map gets an optional `isin` column. ISINs the map doesn't know are listed at the end for the owner to map, with Yahoo search results (`yf.Search`) as suggestions.
- [ ] Duplicates: rows already in the transactions sheet are skipped. Two rows match on date, symbol, type, quantity and rounded price, so a second import of the same file adds nothing.
- [ ] CLI: `trkr import <export>... --cfg <file>` (`run.py import` until the Phase 3 package). It writes `<gen-dir>/import/new_trades.csv` in the sheet's column order, ready to paste, and prints a summary per broker. With `--holdings` it reads portfolio exports and writes snapshot rows instead. A portfolio export without a cost basis gives quantities only, and the owner fills in `cost`.
- [ ] Prerequisites: bug 11 (exports contain `€` and non-ASCII product names) and the `csv.DictReader` item in Phase 2.
- [ ] Tests: each broker on its made-up fixture, header detection, duplicates against an existing sheet, and unmapped ISINs.

## Feature: sheet generator (planned, owner 2026-10-28)

A setup tool that asks a few questions and writes every file trkr reads, so starting or restarting needs no knowledge of the column formats. It is mainly for the web app (W9). A terminal version comes first, and the web wizard reuses its functions.

- [ ] Questions: the default currency and which brokers are used. For each holding, a name or ticker, the quantity, the total cost and the as-of date, or "import from exports" through the broker importer. Last, whether to keep a trade history from now on.
- [ ] Tickers: names are looked up with `yf.Search` (in the locked yfinance 0.2.59), and the owner confirms each match. The exchange-rate row for the default currency goes into the symbol map automatically.
- [ ] Output in `<gen-dir>/setup/`:
  - `transactions.csv`: the header only, or imported rows;
  - `symbols.csv`;
  - `holdings.csv`;
  - `config.yml` with the matching `transactions`, `symbols-map` and `positions` blocks.

  Each CSV has the exact columns trkr reads. The tool never overwrites an existing config.
- [ ] Google Sheets: instructions are printed with the files: create a sheet, import each CSV as its own tab, share it as "Anyone with the link", and paste each tab's link into the config. Links to a tab already work (`sheet_export_url`).
- [ ] CLI: `trkr init` (`run.py init` until Phase 3), with plain `input()` prompts on top of pure functions (answers to rows) that the web wizard calls too.
- [ ] Tests: answers to files for a made-up portfolio, with `yf.Search` stubbed. The generated files then feed an `exec` run on the offline fixture.
- [ ] Owner's call: create the Google Sheet directly through the Sheets API (see the decisions table).

## Feature: web app

A local web app that shows everything the static report shows. It also does what a static page can't: start a run, browse past runs, and recompute the projection as its inputs are edited. It is a second front end on the same core, not a fork. The CLI stays the only code that fetches data and computes portfolios, and the scheduled job keeps working. The defaults are the "Web app" rows in the decisions table.

Prerequisites:

- W0 needs only the Phase 0 tests, because it is a behaviour-preserving refactor guarded by the golden test.
- W1 onward needs these Phase 2 items: the exception hierarchy (the server shows error names, which also retires bug 4), `logging` instead of `print`, tracked templates with autoescape (transactions come from a sheet and are now rendered in a browser), and typed config with `pathlib`. It also needs the Phase 3 package item, so the server can live in `trkr.web`.
- Fix bug 1 before using the app day to day, so the new UI doesn't show wrong totals. (Done, `5468eef`.)
- The Phase 3 batched download and history cache make "Run now" much faster. They are not required.
- W7-W9 (owner, 2026-10-28) need W1. W8 also needs the broker import feature, and W9 the sheet generator.

### Feature parity

Each feature of the CLI, and where it ends up in the app:

| Feature | Today | Web app | Milestone |
| --- | --- | --- | --- |
| Transactions from a local CSV or a public Google Sheet (or one of its tabs), symbol map, positions | YAML config, read by `run.py` | Same config, run by the CLI subprocess | W2 |
| Totals: spending, value, profit, profit %, cash-out, holding period, average ROI | `report.html`, Total | Overview | W1 |
| Per-symbol table with price targets | `report.html`, Portfolio | Holdings (sortable), plus a page per symbol | W1 |
| Stats charts: spending %, profit %, spending per month, valuation % | `plots/gen_stats.png` | Overview: PNGs first, then interactive | W1, W3 |
| Price history per ticker with entry points | `plots/stocks/*.png`, `figs_historical.html` | Symbol pages | W1, W3 |
| Transactions list | `transactions.html` | Transactions, filterable by symbol, type and platform | W1 |
| Symbol map, entry points, historical valuation | `misc_tables.html` | Data | W1 |
| Generated files: `portfolio.csv`, `total.md`, `entries.md`, `projection.csv`, `projection.md` | `generated/` | Downloads on Data | W1 |
| Imaginary portfolios and the comparison table | `imaginary/<name>/report.html`, main report | The same views per portfolio; the comparison on Overview | W1 |
| Net-worth projection | `report.html`, `projection.html` | Projection page, then editable inputs | W1, W4 |
| Scheduled run | `run_script.bat` | Unchanged; its snapshots show up in the app | W0 |
| Logs and exit codes | `log/`, console | Run status with the error name and the log tail | W2 |
| Static HTML report | `report.html` | Still written by the CLI, and linked from Data | none |
| Holdings snapshot | `positions:` file or sheet tab | Holdings page, editable for a local file | W7 |
| Broker import | `trkr import` (planned) | Upload page | W8 |
| Setup | `trkr init` (planned) | Wizard | W9 |

### W0: Core seam (CLI only, no web code)

- [ ] Split computation from output. `process_portfolio` and `process_projection` return data only. Writing the CSV, Markdown and PNG files moves into a separate `write_outputs(run, directories)`. The golden test passes unchanged.
- [ ] A `RunSnapshot` dataclass that holds everything any page needs:
  - run time and a config summary: default currency, history variant, and `local`/`cloud` for each source, but never addresses or sheet IDs;
  - the ticker map, per-symbol rows, totals, monthly spending, entry points and historical valuation;
  - price history per ticker, in the default currency;
  - transactions, with positions marked, and the trades that positions replaced (W7 shows them);
  - each imaginary portfolio, in the same shape;
  - projection inputs, start value and rows.

  It gets `to_json`/`from_json` and a `schema_version`.
- [ ] Every run writes `<gen-dir>/snapshot.json`, plus a copy at `<gen-dir>/snapshots/<YYYYmmdd_HHMMSS>.json`. It writes a temp file and renames it, so a reader never sees half a file. Keep every copy: at tens of KB per run, a year of daily runs is a few MB.
- [ ] Tests: a golden `snapshot.json` for the fixture config (same `TRKR_UPDATE_GOLDEN=1` flow), and a JSON round trip.

### W1: Read-only viewer

- [ ] `trkr web --cfg <file>` starts the server on `127.0.0.1:8765`, using uvicorn and a `create_app(cfg_path)` factory. It shows the latest snapshot from the config's `generation-dir`. When there is no snapshot yet, the page explains how to make one. A snapshot with a different `schema_version` asks for a new run.
- [ ] Layout: navigation, an `as of <run time>` line, and a warning when the snapshot is more than a week old. That warning would have flagged the scheduled job's last run on 2025-11-04 long before 2026-10. The layout works at phone width.
- [ ] Pages, following the parity table:
  - Overview.
  - Holdings, plus one page per symbol with its price history, entry point, break-even and price targets.
  - Transactions.
  - Imaginary: each portfolio gets the same Overview, Holdings and Transactions pages under `/imaginary/<name>/`.
  - Projection.
  - Data: the misc tables, downloads, and a link to the static report.
- [ ] Charts: the existing PNGs. Files are served only from inside `<gen-dir>`, and the resolved path is checked.
- [ ] Read-only JSON at `/api/snapshot` and `/api/snapshot/imaginary/<name>`.
- [ ] Tests with FastAPI's `TestClient` (`httpx` becomes a dev dependency), run on the fixture snapshot:
  - every page returns 200 and shows the fixture values;
  - a made-up sheet ID from the fixture config appears in no response;
  - a request for a file outside `<gen-dir>` gets 404.

### W2: Runs from the browser

- [ ] "Run now": `POST /runs` starts `python -m trkr --cfg <file>` as a subprocess and returns a run id. The page polls the run with htmx and shows the tail of its output. When the run finishes, the page loads the new snapshot.
- [ ] One run at a time per `generation-dir`. The CLI takes `<gen-dir>/.run.lock` and writes its PID into it, so a lock left behind by a dead process can be broken. The scheduled job takes the lock too, so it and a web run never write the same files at once. A second "Run now" gets "already running".
- [ ] A failed run shows the exit code, the error name and the log tail. The last good snapshot stays on screen.
- [ ] Run history: every snapshot with its time, value, profit and profit %, and each one can be opened. A chart of total value across snapshots gives a value-over-time series from the scheduled runs, at each run's current prices. Since bug 6 the "Valuation Percent" chart values the holdings month by month too, but only at month-end closes.
- [ ] Tests: the runner sits behind an interface, and the tests swap in a fake (no subprocess, no network). They cover lock contention and the failure path.

### W3: Interactive charts

- [ ] `trkr/charts.py` holds pure functions that turn a snapshot into a Plotly figure dict, one for each current matplotlib chart: spending %, profit %, spending per month, valuation %, price history per ticker with its entry point, and the projection. The tests check each figure's structure (series, labels, values) on the fixture snapshot, not its pixels.
- [ ] The pages draw the figures with the vendored `plotly.min.js`. Nothing loads from a CDN.
- [ ] Interactions:
  - hover values, legend toggles and date-range zoom;
  - break-even and price-target lines on symbol charts;
  - imaginary portfolios overlaid on the real one.
- [ ] Phase 4's interactive-report item can then reuse these figures in the static report. Until the owner decides on that, the CLI report keeps its PNGs.

### W4: Projection playground

- [ ] A form filled in from the config's `projection:` block. It has every field, including the deposit and withdrawal rows. `start-net-worth` is a choice between the real portfolio, each imaginary portfolio and a fixed amount, with the current values taken from the snapshot.
- [ ] Each change is validated with the same rules as `parse_projection_cfg` and recomputed with `project_net_worth`. That needs no network and takes milliseconds, so htmx can swap in the new table, chart and summary as the owner types. Invalid input shows the message the CLI prints before raising 422.
- [ ] The inputs live in the query string, so a what-if can be bookmarked. "Copy as YAML" gives a `projection:` block to paste into the config; the app never writes the config.
- [ ] When the Scenarios item (projection feature, "Later") lands, each scenario becomes its own set of inputs on a shared chart.
- [ ] Tests: the fixture inputs entered through the form give the same rows as calling `project_net_worth` directly. Each validation error is also tested.

### W5: What-if portfolios from the browser (owner's call)

- [ ] Create an imaginary portfolio by uploading a CSV or typing rows. The same reader that reads the transactions file checks them. The result is saved as `<gen-dir>/web/imaginary/<name>.csv`.
- [ ] A new CLI option, `--imaginary-dir <dir>`, adds every CSV in that directory as an imaginary portfolio named after its file. The web runner passes `<gen-dir>/web/imaginary/`, so portfolios made in the browser join the next run without touching the config.
- [ ] Ticker suggestions come from the symbol map, with a warning for tickers it doesn't contain, since those would fail the run.
- [ ] This builds on two open items: buys without a price (so a row needs only a date, a ticker and an amount) and positions for imaginary portfolios.
- [ ] Tests:
  - upload validation: bad columns, bad dates, unknown symbols, and non-ASCII text (needs bug 11);
  - `--imaginary-dir` end to end with the offline fixture.

### W6: Running it day to day

- [ ] `run_web.bat` runs `-m trkr web --cfg config/cfg_bat.yml` with the venv's Python and opens the browser. Optionally, add a Task Scheduler entry that starts it at logon. `run_script.bat` stays as it is; it gets the run lock through the CLI.
- [ ] A "Web app" section in the README.
- [ ] The GitHub Actions job runs the web tests along with the rest.

### W7: Holdings snapshot from the browser

- [ ] A Holdings page lists the snapshot rows with their current value and P&L, and flags rows more than three months old. Each row shows the trades it replaced, from the run snapshot.
- [ ] With a local positions file, rows can be edited, added and deleted in place:
  - every save goes through `build_positions` before it is written;
  - the previous file is kept as `<file>.bak`;
  - a change to a row's quantity or cost also sets its date to today, unless the owner picks one, because a position is what was held on its date.
- [ ] With a Google Sheet source, the rows are read-only and the page links to the tab.
- [ ] Tests: an edit round trip, a rejected invalid row, and a check that the file path comes only from the config.

### W8: Broker import from the browser

- [ ] Upload one or more exports. The page shows:
  - the parsed rows, with the new ones marked;
  - flagged rows;
  - unmapped ISINs, with Yahoo suggestions.

  It offers `new_trades.csv` for download. With a local transactions file it can also append the rows, after a confirmation.
- [ ] Tests: upload, the preview and the duplicate check, on the made-up broker fixtures.

### W9: Setup wizard

- [ ] The sheet generator's questions as a multi-step form, with ticker search as you type. It ends with the files and the YAML as downloads.
- [ ] Same functions as `trkr init`, so the two can't drift apart. Tests drive the form with the stubbed search.

### Not planned

- Accounts, hosting or a database. There is one user on one machine, and snapshots are files.
- Editing the real transactions. The Google Sheet or the CSV stays the source of truth. The holdings snapshot in a local file is the one exception (W7).
- A separate JavaScript front end (React or similar). It would add a Node build and gain nothing at this size.

## Phase 4: Optional, owner's call

- [ ] pandas-based computation: history as DataFrames, monthly resampling instead of string month keys.
- [ ] Interactive report (e.g. Plotly) instead of PNGs. Web app W3 builds the figures; this item reuses them in the static report.
- [ ] Dividends, deposits/withdrawals, transfers.
- [ ] Money-weighted (XIRR) / time-weighted returns, replacing the linear `profit_percent / days * 365`.
