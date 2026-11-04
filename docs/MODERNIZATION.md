# Modernization plan

A living checklist. Tick items as they land and note the commit hash. Order matters: Phase 0 builds the safety net that makes the later phases safe, because the portfolio math has only end-to-end golden coverage and has confirmed bugs.

State as of 2026-10-22: the last code change was 2025-03; the scheduled job ran successfully through 2025-11-04.

2026-10-23: the net-worth projection and imaginary portfolios landed, ahead of the phases, at the owner's request. They brought part of Phase 0 with them: offline test fixtures, the golden end-to-end test and the demo config.

2026-10-23: added a plan for a local web app ("Feature: web app"). Nothing is built yet.

2026-10-24: Phase 0 is done. The work from 2026-10-23 was committed first (`49af3d4`, `e18cdee`). Writing the characterization tests turned up a new bug, added to Phase 1 as bug 12.

2026-10-28: the owner asked for less admin when adding past investments and picked a holdings snapshot: list what you hold now and skip the trade history. It extends opening positions ("Feature: opening positions and holdings snapshot"). Building it turned up bug 13. The owner also asked to plan three more things: a web page for the snapshot, an importer for broker exports, and a sheet generator. They are planned below as "Feature: broker import", "Feature: sheet generator" and web app milestones W7-W9. None of the three is built.

2026-10-29: Phase 1 is done, on branch `phase-1-bugs` (not merged). Each bug is one commit, test first; a follow-up commit puts the monthly charts on a date axis. The fixes needed four decisions, now in the decisions table: what happens on a sell of more than is held, what the valuation chart shows, how currencies are converted, and how the CLI flags combine with the config. Selling the whole fixture turned up bug 14.

Later on 2026-10-29: instead of a live run on the owner's sheets, Phase 1 was validated on a mirror: made-up sheets in the shape of the owner's cached sheet (`tests/test_mirror.py`, `tests/fixtures/mirror/`). Its one sell closes a whole position, and nothing is oversold, so the new 400 rule doesn't fire. Run through `main` and through this branch, the mirror gives the same spending, value and profit, apart from float noise in the last digits. What changes is the new `realized_profit` row, holdings listed in first-trade order instead of sheet order, and the valuation chart. The old chart stopped at the last trade and added the sold position back in; the new one runs to today.

2026-10-31: bug 14 is fixed (`8ff5e1c`), so every Phase 1 item is done. The branch `phase-1-bugs` is still not merged.

Later: `phase-1-bugs` was merged into `main` (`c7bc1fb`).

2026-11-02: the owner asked for the web app to deploy as a Cloudflare Worker on its own domain, to start small and grow, and to publish nothing private. That replaces the local FastAPI plan; the decisions table and "Feature: web app" are rewritten for it. Built, not yet committed: every run writes `snapshot.json` (W0), and `web/` holds a viewer on a Worker (W1) with the projection playground (W4) and a privacy check that guards every build and deploy. 175 Python tests and 16 web tests pass; a local `wrangler dev` and a dry-run deploy both work. The owner deploys.

2026-11-04: the owner asked for all text in the web app to be lower case, except acronyms, trading symbols and words that would confuse. The strings in `web/` were rewritten at the source rather than with CSS `text-transform`, which would lowercase tickers and miss the page title, alerts and `aria-label`s. Months are lowered in `lowerMonth` (`web/src/format.ts`). Snapshot values stay as written. The rule is in `CLAUDE.md`. 18 web tests pass.

2026-11-04: the owner asked for the web app to deploy on push. `.github/workflows/deploy-web.yml` runs `npm ci`, `npm run check` and `npm run deploy` on pushes to `main` that change `web/`. It passes no `--domain`, because the domain attached on 2026-11-02 stays attached, and it hides the `workers.dev` address, because the repo's Actions logs are public. The owner adds the token and account ID as repository secrets.

## Status (2026-11-04)

| Area | State |
|---|---|
| Phase 0 | Done and committed (last: `88b87d4`). |
| Projection, imaginary portfolios, opening positions | Done and committed (`49af3d4`). |
| Holdings snapshot, bug 13, sheet tab links | Done and committed (`c45f7c3`). 106 tests pass. The demo run and a live run with a snapshot dated today both exit 0. |
| Phase 1, bugs 1-14 | Done (`bb62641`..`8ff5e1c`; bug 13 in `c45f7c3`) and merged into `main` (`c7bc1fb`). |
| Phases 2-4 | Not started. |
| Web app | A Cloudflare Worker app in `web/`, committed and deployed by hand on 2026-11-02, with its custom domain attached. W0's snapshot, W1's viewer and most of W4 are done. A push to `main` that changes `web/` deploys it, once the owner adds the secrets. 175 Python tests and 18 web tests pass. |
| Broker import, sheet generator | Planned only. The importer waits on sample exports from the owner. |

Waiting on the owner:

- the deploy workflow's two repository secrets (`web/README.md`, "Deploy"), and whether a hosted app should get the latest snapshot without the file (decisions table);
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
| "Valuation Percent" chart (bug 6) | The market value of the holdings at the end of each month, from the first trade's month through the current one, as a percentage of the current month's. A month without a close takes the previous close, or today's price. When nothing is held this month there is nothing to compare with, so the chart says "Nothing is held." instead of switching to another base (bug 14). |
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
| Web app: where it runs | A Cloudflare Worker on its own domain (owner, 2026-11-02). It serves static files and stores nothing. The owner opens a `snapshot.json` in the browser, which reads it there, so no holdings reach the server. Until 2026-11-02: on the owner's PC only, on `127.0.0.1`. |
| Web app: stack | TypeScript without a UI framework, built by Vite, served as the Worker's static assets; vitest for tests. Exact-pinned dev dependencies only (wrangler, vite, vitest, typescript), each at least two weeks old when pinned, locked in `web/package-lock.json`. Replaces FastAPI + Jinja2 + htmx, which a Worker can't run without a Python runtime and the CLI's dependencies. |
| Web app: charts | Hand-written SVG (`web/src/chart.ts`) on the dataviz palette, drawn from the snapshot. No chart library so far, so nothing to vendor. |
| Web app: how a run executes | The hosted app can't run the CLI. Runs stay with the scheduled job and the CLI; the app shows what they wrote. |
| Web app: data contract | Every CLI run writes a versioned `snapshot.json`, the scheduled run included. The app reads snapshots. The only thing it computes itself is projections, with a port of `project_net_worth` tested against the CLI's rows. |
| Web app: config | The app never sees the config: the snapshot carries only the currency, the history variant and local/cloud per source. What-ifs live in the browser; the projection page gives a YAML block to paste. |
| Web app: dependencies | A separate Node project in `web/`. `pyproject.toml`, `requirements.txt` and the scheduled job don't change. |
| Snapshot date | Required on every row. Defaulting it to the run date would move the date every day, and each later trade would be dropped as already counted. In Sheets, fill the column down. |
| Snapshot cost | `cost` is the total paid in the default currency, as broker apps show it, so it needs no `ex_rate`. A row with `average_price` in another currency now requires `ex_rate`, which used to default to 1 without a warning. |
| Web app: editing holdings | The hosted app can't write the local positions file. Edited rows are checked in the browser and downloaded as a positions CSV, to save over the file or paste into the sheet tab (W7). Transactions stay read-only, and the app never writes the config. |
| Web app: private data | Nothing private is published. The deploy is built only from files git knows, and `web/scripts/check-private.mjs` refuses a build holding a local config's sheet address, the home directory, or any snapshot but the made-up demo. The CSP keeps the page from sending data anywhere; pages are `noindex`. The domain is passed at deploy time, not committed, since the repo is public. Wrangler metrics are off. |
| Web app: getting the snapshot to a hosted app | Open the file, optionally kept in the browser's storage on that device (default). Owner's call, later: the scheduled job uploads each snapshot to R2 or KV behind Cloudflare Access, so a phone opens the latest one. That stores holdings at Cloudflare under the owner's account, and needs Access set up on the domain and an API token on the PC. |
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
14. [x] **A portfolio with every position sold crashes.** `write_csv_lazy` (`src/csv_mngr.py`) takes its headers from the first row, so an empty portfolio raises `StopIteration` (exit 1 since bug 4). `plot_combined` would then divide by a last valuation of 0 and draw an empty pie. Found 2026-10-29 by selling the whole fixture. It predates the bug 1 fix, which only made the totals right up to that point.
    Fixed: `portfolio.csv` takes its columns from `HOLDING_COLUMNS` (`src/portfolio_mngr.py`), which also builds each holding, so an empty portfolio writes the header alone. The spending pie and the valuation chart say "Nothing is held." instead of drawing (see the decisions table). (`8ff5e1c`; `test_exec_with_every_position_sold`, `tests/test_plots.py`)

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

A web page that shows everything the static report shows, and does what a static page can't: recompute the projection as its inputs change, sort and filter, and show any run's snapshot. It is a second front end on the same core, not a fork. The CLI stays the only code that fetches data and computes portfolios, and the scheduled job keeps working. The defaults are the "Web app" rows in the decisions table.

Until 2026-11-02 the plan was a FastAPI server on the owner's PC. The owner then asked for an app that deploys as a Cloudflare Worker on its own domain, starts small and grows, and publishes nothing private. A Worker can't run the CLI or read the owner's files, so the app reads the snapshot the CLI writes, opened in the browser. Milestones that needed the server (runs from the browser, writing files) are marked below.

Prerequisites:

- W0 needs only the Phase 0 tests.
- The Worker app needs none of Phase 2 or the Phase 3 package, because it shares no Python code. Its contract with the CLI is the snapshot, pinned on both sides by tests.
- The Phase 3 batched download and history cache make the scheduled job faster, not the app.
- W7-W9 (owner, 2026-10-28): W8 also needs the broker import feature, and W9 the sheet generator.

### Feature parity

Each feature of the CLI, and where it ends up in the app:

| Feature | Today | Web app | Milestone |
| --- | --- | --- | --- |
| Transactions from a local CSV or a public Google Sheet (or one of its tabs), symbol map, positions | YAML config, read by `run.py` | Unchanged: the CLI reads them; the app shows the result | none |
| Totals: spending, value, profit, profit %, cash-out, holding period, average ROI | `report.html`, Total | Overview | W1, done |
| Per-symbol table with price targets | `report.html`, Portfolio | Holdings (sortable), plus a page per symbol | W1, done |
| Stats charts: spending %, profit %, spending per month, valuation % | `plots/gen_stats.png` | Overview: value at each month end and invested each month are done; spending % and profit % are in the Holdings table, not charted | W1, W3 |
| Price history per ticker with entry points | `plots/stocks/*.png`, `figs_historical.html` | Symbol pages, with the break-even line | W1, done |
| Transactions list | `transactions.html` | Transactions, filterable by symbol, type and platform | W1, done |
| Symbol map, entry points, historical valuation | `misc_tables.html` | Data (symbol map); entry points on symbol charts; valuation as a table under its chart | W1, done |
| Generated files: `portfolio.csv`, `total.md`, `entries.md`, `projection.csv`, `projection.md` | `generated/` | Not in the app: they stay on the PC | none |
| Imaginary portfolios and the comparison table | `imaginary/<name>/report.html`, main report | The same views per portfolio; the comparison on Overview | W1, done |
| Net-worth projection | `report.html`, `projection.html` | Projection page with editable inputs | W4, done in part |
| Scheduled run | `run_script.bat` | Unchanged; each run writes a snapshot to open | W0, done |
| Logs and exit codes | `log/`, console | Not in the app | none |
| Static HTML report | `report.html` | Still written by the CLI | none |
| Holdings snapshot | `positions:` file or sheet tab | Positions are marked in Transactions; editing is W7 | W7 |
| Broker import | `trkr import` (planned) | Upload page, owner's call | W8 |
| Setup | `trkr init` (planned) | Wizard, owner's call | W9 |

### W0: Core seam (CLI only, no web code)

- [x] Every run writes `<gen-dir>/snapshot.json`, plus a copy at `<gen-dir>/snapshots/<YYYYmmdd_HHMMSS>.json`. Each is written to a temp file and renamed, so a reader never sees half a file. Every copy is kept: at tens of KB per run, a year of daily runs is a few MB. (`src/snapshot.py`, called last in `exec`)
- [x] The snapshot holds what any page needs, with `schema` and `schema_version` (1):
  - run time and a config summary: default currency, history variant, and `local`/`cloud` for each source, but never addresses, sheet IDs or paths;
  - the symbol map, per-symbol rows, totals, monthly spending, historical valuation (months as `YYYY-MM`) and entry points;
  - price history per ticker, in the default currency (days as `YYYY-MM-DD`; with lite history a month's 1st stands for its last close);
  - transactions, with positions marked by their platform (`positions file`);
  - each imaginary portfolio, in the same shape;
  - projection inputs, start year, start value and rows.

  It is a plain dict in Python and typed in `web/src/snapshot.ts`; the Python side needs no `from_json`, because only the app reads snapshots. NaN becomes `null`.
- [x] Tests: a golden `tests/golden/exec/snapshot.json` (same `TRKR_UPDATE_GOLDEN=1` flow), months and dates, no paths, the imaginary portfolio and projection against `projection.csv`, NaN, and on the mirror: no sheet address and the same valuation as the report (`tests/test_snapshot.py`, `tests/test_mirror.py`). The web tests parse the golden file.
- [ ] The trades that positions replaced (`merge_positions` returns them), for W7.
- [ ] Split computation from output: `process_portfolio` and `process_projection` return data only, and a separate `write_outputs(run, directories)` writes the files. No longer needed by the app; it would let a test build a snapshot without writing PNGs.

### W1: Viewer on a Worker

- [x] `web/`: TypeScript with no framework, built by Vite into `dist/`, served by a Worker through the `ASSETS` binding with `run_worker_first`, so every response gets the headers: a CSP limiting the page to its own origin (`connect-src 'self'`, no inline script or style), `frame-ancestors 'none'`, `noindex`, `no-referrer`, HSTS. Hashed assets are cached as immutable. `/api/health` reports the snapshot version the app reads.
- [x] Landing page: open `snapshot.json` (picker or drop), "Remember it on this device" (localStorage, off by default), and a made-up demo, also at `/?demo`. A file that is not a snapshot, or of another version, gets a message saying what to do.
- [x] Layout: navigation, `Snapshot of <run time>`, a warning when the snapshot is more than a week old (that would have flagged the scheduled job's last run, 2025-11-04, long before 2026-10), a portfolio switcher for imaginary portfolios. Checked at 390 px wide (no sideways scroll) and in light and dark mode.
- [x] Pages: Overview (tiles, value at each month end, invested each month, comparison table), Holdings (sortable, totals row), a page per symbol (price history with the first buy and break-even, price targets, its trades), Transactions (filters), Projection (W4), Data (snapshot facts, symbol map, forget the stored copy).
- [x] Charts: SVG drawn in the browser, following the dataviz palette (blue, orange, aqua), with a crosshair readout on hover and from the keyboard, and a table view under each.
- [x] Privacy check: `web/scripts/check-private.mjs` ends `npm run build`, which `wrangler dev` and `wrangler deploy` run first. It refuses a build whose inputs git doesn't know, whose output holds a sheet address from the local configs or the home directory, or that holds any snapshot other than the demo made from local files.
- [x] Tests (`npm run check`, vitest): parsing the CLI's golden snapshot and the demo, the error messages, the Worker's headers and routes, and the projection port against the rows the CLI computed for the demo.
- [ ] A symbol table that links sold positions too (only held ones have pages from Holdings today).

### W2: Snapshot history (was: runs from the browser)

A Worker can't start the CLI, so "Run now", run status and the run lock are dropped from the hosted app. The scheduled job and the CLI make the runs.

- [ ] Open several snapshots from `snapshots/` at once and chart total value across them: a value-over-time series at each run's current prices.
- [ ] Owner's call: get the latest snapshot to the app without the file (decisions table, "getting the snapshot to a hosted app").

### W3: Interactive charts

- [x] Hover and keyboard readout on every chart (W1).
- [ ] Spending % and profit % per holding as charts (bars, ranked).
- [ ] Legend toggles and date-range zoom; price targets on symbol charts.
- [ ] Imaginary portfolios overlaid on the real one's value.
- [ ] Phase 4's interactive-report item could reuse these charts in the static report. Until the owner decides on that, the CLI report keeps its PNGs.

### W4: Projection playground

- [x] A form filled in from the snapshot's projection inputs, or blank when the config has none. `start-net-worth` is a choice between the real portfolio, each imaginary one and a fixed amount, with their current values. Deposits and withdrawals are "year: amount" lines.
- [x] Each change is validated with the rules and messages of `parse_projection_cfg` and recomputed by `web/src/projection.ts`, a port of `project_net_worth` checked against the CLI's rows. An invalid input dims the last good result and shows the message.
- [x] "As a projection block for the config" gives the YAML to paste, with a copy button; the app never writes the config.
- [ ] Inputs in the query string, so a what-if can be bookmarked.
- [ ] When the Scenarios item (projection feature, "Later") lands, each scenario becomes its own set of inputs on a shared chart.

### W5: What-if portfolios from the browser (owner's call)

Pricing a typed portfolio needs Yahoo, which the browser can't call (no CORS) and the Worker would have to proxy. Two ways, both for the owner to choose:

- [ ] The app writes a transactions CSV for download, to add to the config as an imaginary portfolio (the CLI prices it on its next run). Needs nothing new on the server.
- [ ] The Worker proxies Yahoo for the tickers asked, and the browser values the portfolio. That puts portfolio math in TypeScript, a second copy of `Portfolio.calculate`, so it needs the same characterization tests.

### W6: Running it day to day

- [x] Build and deploy commands: `npm ci`, `npm run check`, `npm run build`, `npx wrangler login`, `npm run deploy [-- --domain <host>]` (`web/README.md`). Wrangler metrics are off (`send_metrics: false`).
- [x] A "Web app" section in the README.
- [x] Owner: deploy, and attach the domain (its zone must be on the same Cloudflare account). Done 2026-11-02.
- [x] Deploy on push: `.github/workflows/deploy-web.yml` publishes pushes to `main` that change `web/`, after `npm run check`.
- [ ] Owner: add the workflow's `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repository secrets.
- [ ] The GitHub Actions job (Phase 3) runs `npm ci && npm run check` in `web/` along with pytest. The privacy check needs no secrets: in CI it finds no local configs and checks the rest.

### W7: Holdings snapshot from the browser

- [ ] A Holdings page section lists the positions rows with their current value and P&L, and flags rows more than three months old. Each row shows the trades it replaced (W0's open item).
- [ ] Rows can be edited, added and deleted in the browser and downloaded as a positions CSV, checked with the same rules as `build_positions` (ported, with tests against the Python messages). The hosted app can't write the local file, so the owner saves the download over it or pastes it into the sheet tab. A change to a row's quantity or cost also sets its date to today, unless the owner picks one.

### W8: Broker import from the browser (owner's call)

- [ ] The importer is Python (`src/importers/`). In the hosted app it would need a TypeScript copy of each parser, or a Worker running Python. Until the owner decides, the importer stays a CLI command.

### W9: Setup wizard (owner's call)

- [ ] The sheet generator's questions as a multi-step form that ends with the files and the YAML as downloads. Ticker search needs `yf.Search`, so the Worker would proxy Yahoo's search (see W5). Same rows as `trkr init`, checked by shared fixtures.

### Not planned

- Accounts or a database. There is one user, and snapshots are files. If the owner picks the stored-snapshot option, Cloudflare Access does the login.
- Editing the real transactions. The Google Sheet or the CSV stays the source of truth.
- A UI framework (React or similar). The pages are small enough for plain TypeScript and the DOM.

## Phase 4: Optional, owner's call

- [ ] pandas-based computation: history as DataFrames, monthly resampling instead of string month keys.
- [ ] Interactive report instead of PNGs. The web app's SVG charts (`web/src/chart.ts`) could be reused, by shipping a script with the report.
- [ ] Dividends, deposits/withdrawals, transfers.
- [ ] Money-weighted (XIRR) / time-weighted returns, replacing the linear `profit_percent / days * 365`.
