# Modernization plan

A living checklist. Tick items as they land and note the commit hash. This repo is public, so confidential work never goes in this file; the ecosystem's shared rules, which `CLAUDE.md` imports, say where it goes. Order matters: Phase 0 builds the safety net that makes the later phases safe, because the portfolio math has only end-to-end golden coverage and has confirmed bugs.

Each open ticket's heading ends in its size, the same value as its issue's `Size` in the ecosystem's GitHub Project, on the ecosystem's scale: xxs takes minutes, xs under an hour, s an hour or two, m about a session, l two or three, xl four to six and xxl more. tbd means an owner's call, a decision or work not yet planned decides it. A change to one is made to the other in the same session.

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

2026-11-04: the owner asked for the web app to deploy on push. `.github/workflows/deploy-web.yml` runs `npm ci`, `npm run check` and `npm run deploy` on pushes to `main` that change `web/`. It passes no `--domain`, because the domain attached on 2026-11-02 stays attached, and it hides the `workers.dev` address, because the repo's Actions logs are public. The owner adds the token and account ID as repository secrets. The push that added the workflow (`c49b1a0`) started no run, though Actions was on and the path filter matched; no cause was found. A manual run then deployed `c49b1a0`, and the domain stayed attached. The next push that changed `web/` (`485d732`) started the workflow and deployed.

2026-11-04: the owner asked for a button in the web app's footer that goes to eigenomar.com. W10 plans it, and nothing is built yet.

2026-11-07: the web app is committed and deployed. It has been on `main` since 2026-11-02 (`d3b7cab`), and the owner deployed it by hand that day, with its domain attached. Since 2026-11-04, a push to `main` that changes `web/` deploys it. From `1050c64` to `c49b1a0`, the Status table said it was neither committed nor deployed. "Built, not yet committed" in the 2026-11-02 note was true when written. Checked on 2026-11-07: the app, its demo and its health route answer, and 175 Python tests and 18 web tests pass.

2026-11-13: the owner asked for a page that shows how to make a `snapshot.json` (W1), then for snapshots made in the web app itself, with nothing to install: old trades entered by hand, one at a time or in bulk, fees included, and later each trade's price fetched for its date. It is planned as W11, in slices that ship one at a time. It needs the Worker to fetch prices, so the Worker will see tickers, never quantities, prices paid or fees, and a second copy of the money math in TypeScript, pinned to the CLI's golden snapshot. It replaces W5's open choice. Slice 1, the math, is built and not yet committed.

2026-11-13: trkr is being onboarded to the eigenomar ecosystem, whose contract lives in `meta-eigenomar`. That changes nothing in how trkr is built, tested or deployed. The owner's target capabilities and release gate are planned as X1-X3 ("Release gate"), and the onboarding steps as EO1-EO10 ("Ecosystem onboarding"). `project.yaml` and the shared import on `CLAUDE.md`'s first line are added, not yet committed.

2026-11-14: the onboarding's first steps are in `c8fcf62`, and W11's slice 1 and W1's guide page, which the 2026-11-13 notes call not yet committed, are in `382507c`, pushed and deployed that day. The owner answered the onboarding's questions: no standing approval for commits (EO3), EO10's priorities, and W5 closed, since W11 does its work. EO6-EO9 close the portability gaps: LF line endings, `npm run check` from either spelling of the drive letter, the venv's Python on Linux, and the C++ tool by its repository. 175 Python tests and 36 web tests pass.

2026-11-18: the owner asked for trkr to adopt two standards the ecosystem is adding, once each is designed in `meta-eigenomar`: the documents every repository keeps, and its SCM strategy. They are planned as DOC1 and SCM1 ("Ecosystem standards"), and nothing is built yet.

2026-11-20: the owner asked for every app under eigenomar.com to share one tab icon, eigenomar.com's lambda with its colors swapped. W13 replaces the web app's chart line with it, and nothing is built yet.

2026-11-25: X1's audit is done, not yet committed. Of the fifteen target capabilities, eight are covered, five in part, and dividends and deposits and withdrawals stay the owner's call. Its four gaps became items in W1, W3 and X2, and grouping holdings joins the owner's calls. One of them is new to this plan: Yahoo's prices are split-adjusted and the trades aren't.

2026-11-24: W11's slices 2 and 3 are built and not yet committed: the Worker's price route, and "make a snapshot here", the first slice anyone can see. A push to `main` deploys them, and the first check after that deploy is whether Yahoo answers Cloudflare's servers (W11). 175 Python tests and 87 web tests pass.

2026-11-25: the owner split W11 so each part is picked on its own. Slices 1-3 are W11a, done, and slices 4-6 are W11b-W11d, each `m` and with its own issue, W11b on W11's. Slice 7's items stay under W11 without ids. W11c fills in a trade's price as traded, not adjusted (X1, gap 4).

2026-11-26: renamed, since the ecosystem's lanes are numbered across its repositories: W19 from `W1`, W20 from `W2`, W21 from `W3`, W22 from `W4`, W23 from `W5`, X12 from `X2`, DOC3 from `DOC1` and SCM3 from `SCM1`. Their anchors, headings, references and issues changed with them, and the notes above keep the ids they were written with.

2026-11-27: the owner asked for trkr's tickets to move into their GitHub issues once the ecosystem's third standard, `meta-eigenomar` ST3, is built: its decisions were made that day. MIG3 ("Ecosystem standards") is the cutover, and nothing is built yet.

## Status (2026-11-07)

| Area | State |
|---|---|
| Phase 0 | Done and committed (last: `88b87d4`). |
| Projection, imaginary portfolios, opening positions | Done and committed (`49af3d4`). |
| Holdings snapshot, bug 13, sheet tab links | Done and committed (`c45f7c3`). 106 tests pass. The demo run and a live run with a snapshot dated today both exit 0. |
| Phase 1, bugs 1-14 | Done (`bb62641`..`8ff5e1c`; bug 13 in `c45f7c3`) and merged into `main` (`c7bc1fb`). |
| Phases 2-4 | Not started. |
| Web app | A Cloudflare Worker app in `web/`, committed (`d3b7cab`) and deployed by hand on 2026-11-02, with its custom domain attached. W0's snapshot (`1050c64`), W19's viewer and most of W22 are done. A push to `main` that changes `web/` deploys it through `.github/workflows/deploy-web.yml`. 175 Python tests and 18 web tests pass. |
| Broker import, sheet generator | Planned only. The importer waits on sample exports from the owner. |

Waiting on the owner:

- whether a hosted app should get the latest snapshot without the file (decisions table);
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
| Web app: how a run executes | The hosted app can't run the CLI. Runs stay with the scheduled job and the CLI; the app shows what they wrote. From 2026-11-13 the app also makes snapshots itself, from trades typed into it (W11). |
| Web app: data contract | Every CLI run writes a versioned `snapshot.json`, the scheduled run included. The app reads snapshots. It computes projections, with a port of `project_net_worth` tested against the CLI's rows, and, for W11, whole portfolios, with a port of the money math tested against the CLI's golden snapshot. |
| Web app: snapshots made in the browser | Anyone can make a snapshot in the app with nothing to install (owner, 2026-11-13). Trades are typed in or pasted, kept in the browser's storage on that device, and download as a transactions CSV in trkr's column order, which the CLI reads too. They are never sent anywhere. Lite (weekly) history only, and symbols are Yahoo tickers, with no symbol map. |
| Web app: prices for the browser | The browser can't call Yahoo (no CORS, and the CSP allows only the app's own origin), so the Worker fetches prices for the tickers the page asks for (W11a, slice 2). It sees tickers and dates, never quantities, prices paid or fees. It keeps no copy beyond Cloudflare's cache of public prices. It answers only the app's own pages and takes only ticker-shaped input, so it isn't a general Yahoo proxy. If Yahoo refuses Cloudflare's servers, the fallback is a price provider with a free API key, held as a Worker secret. |
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

A port of the owner's C++ tool, the public repo `eigenomarksamy/networth_projection` (`src/networth/`, `src/portfolio/`), which lives outside this repo. Landed 2026-10-23, before Phase 2, so the report sections are inline strings in `report_mngr.py` like the rest; they move with the other templates. Build fixtures from made-up numbers: don't use that project's `gen/` files or its `fillDefaults()` values.

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
| Totals: spending, value, profit, profit %, cash-out, holding period, average ROI | `report.html`, Total | Overview | W19, done |
| Per-symbol table with price targets | `report.html`, Portfolio | Holdings (sortable), plus a page per symbol | W19, done |
| Stats charts: spending %, profit %, spending per month, valuation % | `plots/gen_stats.png` | Overview: value at each month end and invested each month are done; spending % and profit % are in the Holdings table, not charted | W19, W21 |
| Price history per ticker with entry points | `plots/stocks/*.png`, `figs_historical.html` | Symbol pages, with the break-even line | W19, done |
| Transactions list | `transactions.html` | Transactions, filterable by symbol, type and platform | W19, done |
| Symbol map, entry points, historical valuation | `misc_tables.html` | Data (symbol map); entry points on symbol charts; valuation as a table under its chart | W19, done |
| Generated files: `portfolio.csv`, `total.md`, `entries.md`, `projection.csv`, `projection.md` | `generated/` | The files stay on the PC; each page's tables download as CSV and its charts as SVG | W12 |
| Imaginary portfolios and the comparison table | `imaginary/<name>/report.html`, main report | The same views per portfolio; the comparison on Overview | W19, done |
| Net-worth projection | `report.html`, `projection.html` | Projection page with editable inputs | W22, done in part |
| Scheduled run | `run_script.bat` | Unchanged; each run writes a snapshot to open | W0, done |
| Logs and exit codes | `log/`, console | Not in the app | none |
| Static HTML report | `report.html` | Still written by the CLI; the app downloads a self-contained combined report | W12 |
| Holdings snapshot | `positions:` file or sheet tab | Positions are marked in Transactions; editing is W7 | W7 |
| Broker import | `trkr import` (planned) | Upload page, owner's call | W8 |
| Setup | `trkr init` (planned) | Wizard, owner's call | W9 |

<a id="w0"></a>

### W0: Core seam (CLI only, no web code) · s

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

<a id="w19"></a>

### W19: Viewer on a Worker · s

- [x] `web/`: TypeScript with no framework, built by Vite into `dist/`, served by a Worker through the `ASSETS` binding with `run_worker_first`, so every response gets the headers: a CSP limiting the page to its own origin (`connect-src 'self'`, no inline script or style), `frame-ancestors 'none'`, `noindex`, `no-referrer`, HSTS. Hashed assets are cached as immutable. `/api/health` reports the snapshot version the app reads.
- [x] Landing page: open `snapshot.json` (picker or drop), "Remember it on this device" (localStorage, off by default), and a made-up demo, also at `/?demo`. A file that is not a snapshot, or of another version, gets a message saying what to do.
- [x] Layout: navigation, `Snapshot of <run time>`, a warning when the snapshot is more than a week old (that would have flagged the scheduled job's last run, 2025-11-04, long before 2026-10), a portfolio switcher for imaginary portfolios. Checked at 390 px wide (no sideways scroll) and in light and dark mode.
- [x] Pages: Overview (tiles, value at each month end, invested each month, comparison table), Holdings (sortable, totals row), a page per symbol (price history with the first buy and break-even, price targets, its trades), Transactions (filters), Projection (W22), Data (snapshot facts, symbol map, forget the stored copy).
- [x] Charts: SVG drawn in the browser, following the dataviz palette (blue, orange, aqua), with a crosshair readout on hover and from the keyboard, and a table view under each.
- [x] Privacy check: `web/scripts/check-private.mjs` ends `npm run build`, which `wrangler dev` and `wrangler deploy` run first. It refuses a build whose inputs git doesn't know, whose output holds a sheet address from the local configs or the home directory, or that holds any snapshot other than the demo made from local files.
- [x] Tests (`npm run check`, vitest): parsing the CLI's golden snapshot and the demo, the error messages, the Worker's headers and routes, and the projection port against the rows the CLI computed for the demo.
- [ ] A symbol table that links sold positions too (only held ones have pages from Holdings today).
- [ ] Realized profit and fees paid per symbol, sold positions included, and the fees paid in total (X1, gap 3). The snapshot lists only held positions, so a closed position's realized profit shows only in the total today.
- [x] A page on how to make a `snapshot.json` (owner, 2026-11-13): `#/make-a-snapshot`, in `web/src/views/guide.ts`, linked under the landing's open button. It needs no snapshot, so the router shows it before anything else. Five steps: install, a transactions CSV, a minimal `config/cfg.yml` (Yahoo tickers, so no symbol map), run, open. That config was checked with a run on made-up trades, which wrote a snapshot. Checked at 390 px wide (no sideways scroll) and in light and dark mode. Committed in `382507c`.

<a id="w20"></a>

### W20: Snapshot history (was: runs from the browser) · m

A Worker can't start the CLI, so "Run now", run status and the run lock are dropped from the hosted app. The scheduled job and the CLI make the runs.

- [ ] Open several snapshots from `snapshots/` at once and chart total value across them: a value-over-time series at each run's current prices.
- [ ] Owner's call: get the latest snapshot to the app without the file (decisions table, "getting the snapshot to a hosted app").

<a id="w21"></a>

### W21: Interactive charts · m

- [x] Hover and keyboard readout on every chart (W19).
- [ ] Spending % and profit % per holding as charts (bars, ranked), with each holding's share of the current value beside its share of the cost, in the Holdings table too (X1, gap 2).
- [ ] The money put in less what sells took out, as a total on Overview and as a second line on "value at each month end", so the chart tells gains from new money (X1, gap 1). The snapshot's trades are enough to work it out.
- [ ] Legend toggles and date-range zoom; price targets on symbol charts.
- [ ] Imaginary portfolios overlaid on the real one's value.
- [ ] Phase 4's interactive-report item could reuse these charts in the static report. Until the owner decides on that, the CLI report keeps its PNGs.

<a id="w22"></a>

### W22: Projection playground · s

- [x] A form filled in from the snapshot's projection inputs, or blank when the config has none. `start-net-worth` is a choice between the real portfolio, each imaginary one and a fixed amount, with their current values. Deposits and withdrawals are "year: amount" lines.
- [x] Each change is validated with the rules and messages of `parse_projection_cfg` and recomputed by `web/src/projection.ts`, a port of `project_net_worth` checked against the CLI's rows. An invalid input dims the last good result and shows the message.
- [x] "As a projection block for the config" gives the YAML to paste, with a copy button; the app never writes the config.
- [ ] Inputs in the query string, so a what-if can be bookmarked.
- [ ] When the Scenarios item (projection feature, "Later") lands, each scenario becomes its own set of inputs on a shared chart.

### W23: What-if portfolios from the browser (owner's call)

Decided 2026-11-13: the second way, through W11. The owner wants every snapshot to be possible in the app, so the Worker fetches prices and the browser values the portfolio. A what-if portfolio is then a second trade list (W11's later items).

Pricing a typed portfolio needs Yahoo, which the browser can't call (no CORS) and the Worker would have to proxy. Two ways, both for the owner to choose:

- [ ] The app writes a transactions CSV for download, to add to the config as an imaginary portfolio (the CLI prices it on its next run). Needs nothing new on the server.
- [x] The Worker proxies Yahoo for the tickers asked, and the browser values the portfolio. Chosen 2026-11-13; the work is W11, so W23 has nothing left of its own. That puts portfolio math in TypeScript, a second copy of `Portfolio.calculate`, so it needs the same characterization tests.

<a id="w6"></a>

### W6: Running it day to day · xs

- [x] Build and deploy commands: `npm ci`, `npm run check`, `npm run build`, `npx wrangler login`, `npm run deploy [-- --domain <host>]` (`web/README.md`). Wrangler metrics are off (`send_metrics: false`).
- [x] A "Web app" section in the README.
- [x] Owner: deploy, and attach the domain (its zone must be on the same Cloudflare account). Done 2026-11-02.
- [x] Deploy workflow: `.github/workflows/deploy-web.yml` runs `npm run check`, then deploys. A manual run deployed `c49b1a0` on 2026-11-04.
- [x] Owner: add the workflow's `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repository secrets.
- [x] See a push to `main` that changes `web/` start the workflow: `485d732` did, on 2026-11-04. The push that added the workflow did not, and the cause is unknown.
- [ ] The GitHub Actions job (Phase 3) runs `npm ci && npm run check` in `web/` along with pytest. The privacy check needs no secrets: in CI it finds no local configs and checks the rest.

<a id="w7"></a>

### W7: Holdings snapshot from the browser · l

- [ ] A Holdings page section lists the positions rows with their current value and P&L, and flags rows more than three months old. Each row shows the trades it replaced (W0's open item).
- [ ] Rows can be edited, added and deleted in the browser and downloaded as a positions CSV, checked with the same rules as `build_positions` (ported, with tests against the Python messages). The hosted app can't write the local file, so the owner saves the download over it or pastes it into the sheet tab. A change to a row's quantity or cost also sets its date to today, unless the owner picks one.

<a id="w8"></a>

### W8: Broker import from the browser (owner's call) · tbd

- [ ] The importer is Python (`src/importers/`). In the hosted app it would need a TypeScript copy of each parser, or a Worker running Python. Until the owner decides, the importer stays a CLI command.

<a id="w9"></a>

### W9: Setup wizard (owner's call) · tbd

- [ ] The sheet generator's questions as a multi-step form that ends with the files and the YAML as downloads. Ticker search needs `yf.Search`, so the Worker would proxy Yahoo's search (see W23). Same rows as `trkr init`, checked by shared fixtures.

<a id="w10"></a>

### W10: Button to eigenomar.com (owner, 2026-11-04) · xs

- [ ] A footer with a link to `https://eigenomar.com`, labelled `eigenomar.com` and styled with `.button`. The app has no footer yet: `shell()` in `web/src/app.ts` has a header and a main, and `landing()` in `web/src/views/landing.ts` stands in for them until a snapshot is open, so both need it.
- [ ] It opens in a new tab (`target="_blank" rel="noopener"`). An open snapshot stays in the page unless the owner chose to remember it, so leaving in the same tab would drop it.
- [ ] It stays a link, not a form, because the CSP has `form-action 'none'`. A link needs no change to the CSP in `web/src/worker.ts`.

<a id="w11"></a>

### W11a-W11d: Make a snapshot in the app (owner, 2026-11-13)

Anyone can make their snapshot in the web app, with nothing to install. They enter old trades by hand, one at a time or in bulk, with their fees, and later can fetch a trade's price for its date. Each slice ships on its own; the defaults are the "Web app: snapshots made in the browser" and "prices for the browser" rows in the decisions table.

Split on 2026-11-25 by the owner, so each part is picked on its own: W11a is slices 1-3, done, W11b took W11's issue, and W11c and W11d have issues of their own. Until then W11 was one ticket, `xl`, with its slices as its list. None of the three needs another: W11b goes first, and W11d after it, since both load many trades into the editor at once. The later items at the end have no id until each is scoped, and W7 and W9 decide two of them.

<a id="w11a"></a>

#### W11a: The money math, prices from the Worker, and trades by hand

Slices 1-3, done by 2026-11-24 and deployed in `0724797`.

- [x] **1. The money math in the browser** (no visible change). `web/src/market.ts` ports `MarketDataYahoo`'s lite history and `convert_currencies`: the last weekly close of each month, today's price for a month with no bar yet (bug 13), minor units, and each currency's own pair. `web/src/portfolio.ts` ports `Portfolio.calculate`, `compute_spending_history`, `get_entry_points_months` and `compute_historical_valuation`, and builds a snapshot's portfolio. Same order of trades and sums as the Python, so the figures match to the last digit. `web/test/portfolio.test.ts` rebuilds `tests/conftest.py`'s made-up market and checks the port against `tests/golden/exec/snapshot.json`, exactly. The golden has no sells, so a second case pins the figures the CLI's `Portfolio` printed for made-up partial sells with fees and exchange rates, one closing only through `isclose`. A change in the order of a sell's arithmetic fails it. The cases of `tests/test_portfolio.py` and `tests/test_market.py` are repeated: oversells, dust, pence, each currency's pair, a missing pair. One deliberate difference: a weekly bar with no close is skipped, where the CLI carries the NaN into its figures. Committed in `382507c`.
- [x] **2. Prices from the Worker.** `GET /api/prices?ticker=<t>&from=<YYYY-MM-DD>` answers `{currency, price, closes}`, weekly closes in the ticker's own currency: the input `market.ts` takes. Yahoo's chart API, split- and dividend-adjusted like `yfinance`. Only same-origin requests (`Sec-Fetch-Site`), a ticker pattern, a cap on the date range, and an hour in Cloudflare's cache. The landing's privacy note and `web/README.md` change with it. Built 2026-11-24 in `web/src/yahoo.ts`, with the page's side in `web/src/prices.ts`. Like `yfinance`, it asks for weekly bars from the given day to today, today not included, takes the adjusted close, and dates each bar in its exchange's time zone; a history that starts today has no closes, as in the CLI. It refuses anything a browser doesn't mark `same-origin` (403), other methods (405), a ticker outside the pattern shared with the trade form, a day that isn't one, after today or more than 50 years back (400). Yahoo's 404 is a 404, any other failure a 502 that names Yahoo's status, and only 2xx and 404 answers are cached. Tests (13, vitest): the route on a made-up Yahoo answer, the time zones, the fallbacks, every refusal, and the page's parsing. Checked under `npm run preview` against Yahoo on 2026-11-24: a quote, a currency pair, an unknown ticker and a request without the header, and VWCE.DE's 65 weekly closes from 2025-09-01 are the dates and values `yfinance` gives. The landing's privacy note changed with slice 3, the first page that asks for prices.
  - [x] After the deploy: does Yahoo answer the Worker from Cloudflare's servers? `web/README.md` ("Deploy") has the `curl`. If not, the fallback in the decisions table. Yes, checked on 2026-11-24 after `0724797` deployed: AAPL, VWCE.DE, IWDA.L and USDEUR=X answered with their weekly closes in under half a second, an unknown ticker 404 and a request without the header 403. The same walk-through as slice 3's, on the deployed app, made a snapshot with live prices.
- [x] **3. Trades by hand, and a snapshot from them** (the first visible slice). A "make a snapshot" page: default currency, a form for one trade with all eleven columns, checked as the CLI reads them, and a table to edit and delete. Trades are kept on this device. "Make snapshot" fetches each ticker and currency pair, computes, and opens the result in the viewer, with downloads of `snapshot.json` and `transactions.csv`. The landing links to it next to the guide. Built 2026-11-24: `#/trades` ("make a snapshot here", `web/src/views/trades.ts`), which, like the guide, opens with or without a snapshot, and `web/src/trades.ts` with no DOM. A trade is checked as `Transaction` reads it and as the money math needs it: buy or sell, a real day not after today, numbers as `float()` reads them but finite, quantity and ex_rate above 0, price and fees not negative, a three-letter currency, a ticker, and exchange and platform at most 40 characters, on one line, not starting like a spreadsheet formula. Each problem is listed and its field marked. Empty fees and ex_fees are 0, an empty ex_rate 1, and symbols and currencies are upper-cased. Trades and the default currency are kept in local storage (`trkr.trades`), with a warning when the browser refuses. "make snapshot" fetches each ticker from the first trade's day, then each currency pair the quotes need, four at a time, and opens the result as a snapshot "made in this browser" (`config.sources.transactions: browser`, a value only the app writes, so the format version stays 1). The header then links back to the trades, and the data page downloads `snapshot.json` and `transactions.csv`, which the trades page also offers. Tests (10, vitest): every check, the CSV, storage, and `makeSnapshot` on the golden snapshot's own trades and `tests/conftest.py`'s market gives the golden portfolio exactly. Checked on 2026-11-24 in headless Chrome against `npm run preview`, with made-up trades in public tickers: adding, a bad row's messages, editing, the trades after a reload, making the snapshot with live prices, its overview, holdings and data pages, and the back button, with no console error or CSP report, and no sideways scroll at 390 px in light and dark mode.
<a id="w11b"></a>

#### W11b: Trades in bulk (was slice 4) · m

- [x] Paste rows or open a CSV file in trkr's column order, header optional, as the sheet or a broker export rearranged. A preview flags each bad row with the reason, then the good rows are added. Built 2026-11-25: "add trades in bulk" on `#/trades`, a box to paste into and "open a CSV file", which reads the file into the box. "check the rows" previews them: how many rows, how many to add, whether the first row was read as a header, each bad row with its line, its text and its reasons, and the good rows as a table. "add" adds the good rows and leaves the bad ones in the box, to fix and check again. `web/src/csv.ts` reads the text: commas, or tabs when the first line has one, as rows copied from a spreadsheet are; quoting as Python's `csv` reads it; a byte order mark and blank rows skipped; each row numbered by the line it starts on.
- [x] Each row is checked as W11a's form checks one trade (`web/src/trades.ts`), so a `transactions.csv` the trades page downloaded opens again here. Duplicates aren't detected: that is X3's. `readTrades` takes the first row as a header when its type, date and quantity cells none of them read as a trade's, so a header with other names, such as a sheet's, is left out too, and a bad first trade is still flagged. A row needs eleven columns: empty cells after them are allowed, as a spreadsheet adds them, but a value there is flagged, since the CLI would ignore it and it usually means another column order. A quote that never closes is flagged too. Tests (11, vitest, 98 in all): the reader's quoting, separators, blank rows and line numbers; rows with and without a header, from a spreadsheet, every kind of bad row, the page's own CSV back as the same trades, and `examples/transactions.csv`. Checked on 2026-11-25 in headless Chrome against `npm run preview`, with made-up trades in public tickers: pasted rows without a header and spreadsheet rows with one, a CSV file with a header and one without, bad rows flagged and left in the box, the trades after a reload, the downloaded `transactions.csv` opened again as the same five trades, and a snapshot made from them with live prices, with no console error or CSP report, and no sideways scroll at 390 px in light and dark mode.
- Done when: pasted rows and an opened CSV file, each with and without a header, add their good rows to the trades; each bad row is listed with its reasons and isn't added; the trades page's own `transactions.csv` reads back as the same trades; and `npm run check` passes.

<a id="w11c"></a>

#### W11c: A trade's price (was slice 5) · m

- [ ] In the form, "fetch price" fills in the close on the trade's date and its currency, and `ex_rate` from the currency pair that day. Fees stay typed in.
- [ ] The price route answers daily closes for a short window, beside the weekly history it gives now, with the same refusals and cache.
- [ ] The close it fills in is as traded, not adjusted for later splits and dividends like the history's (X1, gap 4), since it stands for what was paid.
- Done when: "fetch price" fills a made-up trade in a public ticker with that day's close, currency and `ex_rate`, as `yfinance` gives them unadjusted; the route's tests cover the daily window and its refusals; and `npm run check` passes.

<a id="w11d"></a>

#### W11d: Keep it current (was slice 6) · m

- [ ] A snapshot carries its trades, all eleven columns, so "refresh prices" makes a snapshot made here again, which also answers the stale-snapshot warning.
- [ ] A snapshot the CLI wrote can be opened in the editor to continue in the browser. Its trades include the positions file's rows, as buys with the platform `positions file` (`merge_positions`), so the editor shows them as trades.
- Done when: "refresh prices" on a snapshot made here gives the same trades with today's prices and clears the stale-snapshot warning; the golden snapshot opens in the editor with its trades, and making it again gives the golden portfolio for the same market; and `npm run check` passes.

Later, with no id until each is scoped:

- [ ] Holdings rows instead of a trade history (a port of `build_positions` and `merge_positions`, with W7, which can read a positions CSV with `web/src/csv.ts`), imaginary portfolios as further trade lists (W23), projection inputs, ticker search (W9), daily history.

<a id="w12"></a>

### W12: Export and download reports (owner, 2026-11-18)

The app shows every report but can't hand one out. Today the only exports are the CLI's files on the owner's PC, and its `report.html` links its images with `file://` URIs, so it opens only on the machine that wrote it. W12 lets the viewer download what the app shows, one report at a time or all of them together. Each file is built in the browser from the open snapshot: nothing is uploaded, and the Worker receives nothing.

- [x] **Separately.** Every page with a report has a "download" menu next to its heading: Overview, Holdings, each symbol page, Transactions, Projection and Data. A table downloads as CSV, with the columns shown on screen, and with plain numbers and dates (`YYYY-MM-DD`), not the formatted numbers on screen. Holdings has its current sort, and its totals row stays out of the CSV. A chart downloads as SVG, with its legend inside and light colours. Transactions downloads the rows its filters show, and Projection the rows for its current inputs.
- [x] **Combined.** "download report" in the header offers both formats: one HTML file, and a zip of the separate files in a folder per portfolio. Both hold every portfolio in the open snapshot, imaginary ones too, and the projection for the inputs on the Projection page this session. The HTML file has the styles and SVG charts inline, light and dark, a contents list, its own CSP that allows no scripts and no requests, and nothing that points outside it, so it opens offline on any machine.
- [x] **Print.** A print stylesheet hides the header, menus and readouts and switches to light colours, and the app unfolds each chart's table while printing, so "save as PDF" gives a clean copy of a page. The combined HTML file prints without its contents list.
- [x] Built with the app's rules: no third-party code or requests, text in lower case except tickers, currency codes and acronyms, and names like `trkr-holdings-2026-11-18.csv` (an imaginary portfolio adds `imaginary-<name>-`; the date is the snapshot's run date). Each page's report is data in `web/src/reports.ts`, and the pages take their charts from it, so a downloaded chart is the one on screen. The files are written without a DOM: charts are drawn as markup data (`web/src/markup.ts`), turned into DOM on the page and into escaped text for a file, and the zip is stored with a CRC-32 in `web/src/download.ts`. A file is saved through an object URL and a link with the `download` attribute (`web/src/save.ts`). The Worker's CSP didn't change.
- [x] Tests (vitest, 25 new, 64 in all): CSV quoting and formula-injection guard, file names, the zip read back entry by entry, escaping, each report against the golden and demo snapshots, the projection against the CLI's rows, and the combined file: every report, no script, link, source or URL. Checked on 2026-11-18 in headless Chrome against `npm run preview` with the demo: every menu's 21 files downloaded, no CSP violation or console error, the HTML file opened from disk with the network off and made no request, and it has no sideways scroll at 390 px.
- [x] Owner's call, decided 2026-11-18: both formats, offered side by side; every portfolio in the open snapshot, as the session has it; no change to the CLI.
- Done when: every page listed above downloads its tables and charts, the combined report opens offline in a browser on another machine with every page and chart, printing a page gives no navigation, and `npm run check` passes.

<a id="w13"></a>

### W13: The ecosystem's tab icon (owner, 2026-11-20) · xs

Every app under eigenomar.com shows the same tab icon: eigenomar.com's lambda with its two colors swapped, a light-blue tile and a near-black lambda (shared decision SD5).

- [ ] Replace `web/public/favicon.svg`, the chart line, with it. `web/index.html` already links that file, so nothing else changes. The file is already tracked, so `check-private.mjs` lets the build through.
- [ ] The icon is served by the Worker like any other asset, so the CSP in `web/src/worker.ts` doesn't change.
- Done when: the deployed app's tab shows the icon in a light and a dark browser theme, the demo's too, and `npm run check` and `npm run build` pass.

### Not planned

- Accounts or a database. There is one user, and snapshots are files. If the owner picks the stored-snapshot option, Cloudflare Access does the login.
- Editing the real transactions. The Google Sheet or the CSV stays the source of truth.
- A UI framework (React or similar). The pages are small enough for plain TypeScript and the DOM.

## Phase 4: Optional, owner's call

- [ ] pandas-based computation: history as DataFrames, monthly resampling instead of string month keys.
- [ ] Interactive report instead of PNGs. The web app's SVG charts (`web/src/chart.ts`) could be reused, by shipping a script with the report.
- [ ] Dividends, deposits/withdrawals, transfers.
- [ ] Money-weighted (XIRR) / time-weighted returns, replacing the linear `profit_percent / days * 365`.

## Release gate: X1, X12 and X3 (owner)

What trkr should cover, and the gate it passes before it counts as released. X1, X12 and X3 check trkr against both. They were written before this plan, for an app that holds the data itself, so much of them is done here already or planned another way: "Where they meet this plan" maps each part. Don't rebuild what already works. Planned here on 2026-11-13.

- **Target capabilities:** total value, contributions, realized and unrealized gains, allocation and a performance timeline; positions, transactions, dividends, fees, deposits and withdrawals, FX; manual entry, CSV import, export and backups.
- **Release gate:** calculations are verified, imports are tested, there is no personal data in public builds, and exports work. It holds once X12 and X3 are done: X12 verifies the calculations, and X3 covers the imports, the builds and the exports.

The done-whens below were written on 2026-11-13 from each ticket's own text, adding no work, and the owner approved them on 2026-11-14.

<a id="x1"></a>

### X1: Audit against the target capabilities · s

- [x] List what the repo already does against the target capabilities, and record the gaps under this heading. Name the gaps only, and leave what is done to the rest of this plan. "Where they meet this plan" compares plan with plan, so this checks the code and the app themselves. Done 2026-11-25, from `src/` and `web/src/` as of `68ed062`: the table and the gaps below.
- Done when: every target capability is listed here as covered (and where), planned (and by which item), or a gap, and each gap is an item in this plan or one of the owner's calls below.

| Capability | State | Where |
| --- | --- | --- |
| Total value | Covered | `Portfolio.calculate`'s `total['value']`, at today's prices in the default currency: the report's Total and the Overview's value tile. |
| Contributions | Covered in part, gap 1 | "Invested" is what the holdings still held cost (`total['spending']`), and each month's buys with their fees are `compute_spending_history` (Overview, "invested each month"). Nothing adds up the money put in over time, less what sells took out. |
| Realized and unrealized gains | Covered, gap 3 | `profit_net` and `profit_percent` for what is held, `realized_profit` for what sells made, on average cost with fees (bug 1): Overview's tiles, Holdings and `portfolio.csv`. The snapshot lists only held positions, so a closed position's realized profit shows only in the total. |
| Allocation | Covered in part, gap 2 | Each holding's share of the cost (`spending_percent`): Holdings' "weight" and the report's spending pie. Nothing shows each holding's share of the current value, or groups holdings. |
| Performance timeline | Covered in part, gaps 1 and 4 | The holdings' value at each month end (`compute_historical_valuation`: the report's valuation chart and Overview's "value at each month end"), and each symbol's price history with its first buy. New money lifts the value line as much as gains do, and nothing beside it shows what was put in. The only return figure is the profit % spread evenly over the years (`avg_year_roi`). XIRR or time-weighted returns are Phase 4's. |
| Positions | Covered, gap 4 | The Holdings table and a page per symbol, and the CLI's holdings snapshot and opening positions (`build_positions`, `merge_positions`). Planned: pages for sold positions (W19), editing positions rows (W7), and positions in the app's own snapshots (W11's later items). |
| Transactions | Covered | The transactions CSV or sheet for the CLI, the Transactions page with its filters (W19), and the app's trades page (W11a). |
| Dividends | Gap, owner's call | No transaction type records one. The CLI reads any `type` and skips every row that isn't `buy` or `sell` without a word, and the app's trade form refuses one. Phase 4 and the owner's call below. |
| Fees | Covered, gap 3 | Each trade's `fees` and `ex_fees` are added to its cost or taken off its proceeds, and Transactions shows them. Nothing adds up the fees paid: `Portfolio.wallet_fees` is set and never used. |
| Deposits and withdrawals | Gap, owner's call | trkr tracks investments, not cash, so there is no cash balance. `TransType.DEPOSIT` and `WITHDRAW` are unused (Phase 2's dead code), and the projection's `deposits-withdrawals` are planned amounts, not records. Phase 4 and the owner's call below. |
| FX | Covered | Each currency with its own Yahoo pair, history at each date's rate, and minor units (bug 7: `convert_currencies`, and `web/src/market.ts`), and each trade's cost at its own `ex_rate`. A trade's `currency` column is read but no figure uses it, and nothing checks it against the currency Yahoo gives the ticker: X3's import validation. |
| Manual entry | Covered | The sheet or CSV for the CLI. In the app, the trades page, one trade at a time with all eleven columns, checked as the CLI reads them (W11a). |
| CSV import | Covered in part, planned | The CLI reads the transactions CSV or sheet, and the positions file by column name with its checks (400). The transactions reader goes by column order and drops the first row whatever it holds (Phase 2's `csv.DictReader` item), and it checks nothing: a mistyped `type` is skipped, and a bad number or date stops the run with a traceback (exit 1). Nothing detects duplicates. Planned: pasting or opening a CSV in the app with bad rows flagged (W11b), validation and duplicate detection (X3), and broker exports (broker import). |
| Export | Covered | The CLI's files (`generated/`, `report.html`, `snapshot.json`), and in the app each page's tables and charts and the combined report (W12). |
| Backups | Covered in part, planned | The CLI keeps every snapshot in `snapshots/`, and the sheet or CSV is the record. The app downloads `snapshot.json` and `transactions.csv` (W11a), and a snapshot opens again in the viewer. A downloaded `transactions.csv` can't be loaded back into the trades page yet: W11b opens one, and W11d continues a snapshot in the browser. |

The gaps, each now an item in this plan:

1. **Contributions over time.** The money put in less what sells took out, as a total and as a line beside the value at each month end, so the timeline tells gains from new money. A W21 item.
2. **Allocation by value.** Each holding's share of the current value, beside its share of the cost. Part of W21's ranked bars. Grouping holdings, by currency, platform or exchange, is the owner's call below: trkr has no asset classes.
3. **Realized profit and fees per symbol.** Sold positions included, and the fees paid in total. A W19 item, beside its sold positions.
4. **Splits and adjusted prices.** Yahoo's prices are split- and dividend-adjusted, as `yfinance` gives them by default and as the Worker's route asks for them, but each trade keeps its quantity and price as traded, and nothing records a split. A split after a buy values that holding at the old quantity times the new price, and a dividend payer's past month-end values read lower than they were. An X12 item, for the ledger and the performance parts.

<a id="x12"></a>

### X12: Tested calculation core (needs X1) · l

- [ ] Separate the ledger, positions, cost basis (with the method stated explicitly), performance and currency conversion.
- [ ] Test each against independently checked reference examples.
- [ ] Splits and adjusted prices (X1, gap 4): a split recorded in the ledger, or the trades' quantities and prices adjusted to match the prices, so a split after a buy changes neither the value nor the cost. State whether past values use adjusted or as-traded closes.
- Done when: each of the five is its own part with its method written down, and each has tests against reference examples worked out independently of trkr (by hand or with another tool), passing in `pytest`.

<a id="x3"></a>

### X3: Synthetic demo and privacy boundary (needs X12) · tbd

- [ ] A synthetic demo portfolio that loads by default.
- [ ] Real data stored locally only (local-first), and never shipped in a build.
- [ ] CSV import with validation and duplicate detection.
- [ ] Export and backup.
- Done when: the demo opens without a snapshot (unless the owner drops that, below), real data stays on the device and the privacy check refuses a build that holds it, an import rejects bad rows and skips rows it already has, and an export can be opened again as a backup.

### Where they meet this plan

Compared on 2026-11-04, with W11 (2026-11-13) added. trkr is a Python CLI that reads a Google Sheet or CSV, and its web app shows the `snapshot.json` each run writes; since W11 it can also make a snapshot from trades typed into it.

- **X12** is Phases 0-2. Phase 0's tests and Phase 1's fixes are done, with average cost as the stated method ("Cost basis for sells" in the decisions table) and each currency converted with its own pair (bug 7). Phase 2's structure is not started.
- **X3's demo** is at `/?demo` (W19), and the landing page asks for a snapshot first, so it doesn't load by default.
- **X3's local-first storage:** an opened snapshot stays in the browser, on that device only when the owner asks (W19), and W11's trades are kept in the browser's storage on that device. The privacy check keeps everything but the made-up demo out of every build (W19).
- **X3's CSV import** is the CLI reading the sheet or file, and W11b adds pasting rows or opening a CSV in the app, with each bad row flagged. Duplicate detection is part of the planned broker import.
- **X3's export and backup** are the files each run writes on the owner's PC, which this plan keeps out of the app. W11a downloads `snapshot.json` and `transactions.csv`, the backup that can be opened again. W12 downloads the reports, each page on its own or all of them combined.
- **Manual entry:** the real transactions stay in the sheet ("Not planned": editing the real transactions). W11a adds trades typed into the app, for snapshots made there.
- **Dividends, deposits and withdrawals** are in Phase 4, optional and the owner's call, so nothing commits to them yet.
- **The release gate's imports**, for broker exports, wait on a sample export from each broker (broker import).

### Owner's call

- [ ] Whether the demo should load by default.
- [ ] Whether allocation groups holdings, by currency, platform or exchange, beyond each holding's own share (X1, gap 2).
- [ ] Whether manual entry in the app, and dividends, deposits and withdrawals, stay target capabilities. W11's typed trades may answer the first. Drop from the target capabilities whatever doesn't stay.

## Ecosystem standards: DOC3 and SCM3 (owner, 2026-11-18)

The ecosystem's contract, in `meta-eigenomar`, is adding two standards that every repository adopts: the documents each one keeps, and how each one manages its source and delivers it. DOC3 and SCM3 adopt them here, each once its standard is designed. Until then, their issues stay in the backlog. Both revisit what the onboarding kept as it was, at the owner's request.

A third standard, `meta-eigenomar` ST3, makes GitHub's issues the home of every repository's backlog, and its decisions were made on 2026-11-27. MIG3 moves this plan's tickets there, once ST3 is built.

<a id="doc3"></a>

### DOC3: The product's documents (needs the ecosystem's document standard) · tbd

- [ ] Write or gather trkr's product vision, architecture, design, testing strategy, and verification and validation (V&V) documents, in the shape the ecosystem's document standard (`meta-eigenomar` ST1) sets. Where a file or section already covers one, name it rather than copy it. Today the architecture is `CLAUDE.md`'s pipeline, `web/README.md`'s "How it fits together" and "Feature: web app" above. The target capabilities and release gate (X1, X12 and X3) are the nearest thing to a vision and a V&V plan. The tests are pytest, with the golden and mirror snapshots, and the web app's Vitest suite, with its privacy check on every build.
- Done when: each of the five documents exists, or names the file or section that holds it, and follows the standard's outline. `project.yaml` names them under the standard's keys, and the ecosystem's validator passes. Nothing in them is confidential, since this repo is public.

<a id="scm3"></a>

### SCM3: The ecosystem's SCM strategy (needs the ecosystem's SCM strategy) · tbd

- [ ] Adopt the ecosystem's SCM strategy (`meta-eigenomar` ST2) through its adoption checklist: CI, branching, protection of `main`, versioning and releases, the health report and dependency updates. Today `.github/workflows/deploy-web.yml` runs `npm run check` and deploys on pushes to `main` that change `web/`, nothing runs pytest or ruff in CI, work goes to `main` or a working branch, and there are no releases. Phase 3's GitHub Actions item, ruff and pytest on pushes and PRs, is done by this ticket if the strategy's CI covers it. The repo and its Actions logs are public, so no workflow writes the owner's domain or real data.
- Done when: every item on the checklist is applied here, or recorded here as an exception the strategy allows, with its reason. `project.yaml`'s `delivery` and `CLAUDE.md` say what runs, every workflow passes on `main`, and the ecosystem's validator passes.

<a id="mig3"></a>

### MIG3: The backlog moves into GitHub issues (needs GitHub as the home of the backlog) · m

- [ ] Move this plan's planning to GitHub all at once, following the cutover steps of the ecosystem's standard `meta-eigenomar` ST3. Each open ticket's content moves into its issue's body, keeping its id and its issue's `<id>: <title>`. A work package's slices, such as W11's, become sub-issues where each is tracked on its own and checklists where it isn't. Ideas not yet tickets become draft items in the Project with status `idea`, hard needs are blocked-by links, and size, status and priority live only in the Project. Done, dropped and moved items stay here as a frozen archive, with the known-bug list, and each open ticket's anchor stays, linking its issue. The owner's calls and the release gate stay as files, or move into the documents DOC3 writes. A push to `main` that changes `web/` deploys, and this ticket changes nothing there.
- Needs: GitHub as the home of the backlog (`meta-eigenomar` ST3), which includes the ecosystem's own cutover first and the backlog's backup. DOC3 is a planning need: the target capabilities move into the vision before this plan retires.
- Done when: every open ticket's content is in its issue, and this file holds only the archive, the anchors and what stays a file. `project.yaml`'s `documents.plan` is `null` and `planning.source` names GitHub, the ecosystem's validator passes, nothing confidential is in any issue, since this repo is public, and the owner approved the cutover. Bringing tickets up to the ecosystem's ticket standard (`meta-eigenomar` ST4) isn't part of it: each ticket follows it when it is picked up.

## Ecosystem onboarding (2026-11-13)

**Goal:** make trkr discoverable and coordinated in the eigenomar ecosystem without changing how it is built or delivered. The contract is in `meta-eigenomar`. `project.yaml` says where this repo's documents are, and `CLAUDE.md` imports the ecosystem's shared rules.

**Stays as it is:** the venv, `pyproject.toml`, `uv.lock` and the exported `requirements.txt`; `run_script.bat` and the scheduled job; pytest, ruff and the format hook; the web app's `npm` scripts and privacy check; `.github/workflows/deploy-web.yml`, so a push to `main` that changes `web/` still deploys; work on `main` or a working branch, as now; no releases; and the documents where they are: this plan, `CLAUDE.md`, `README.md` and `web/README.md`.

Each step is small and lands between feature work. Each says what it waits on.

- [x] <a id="eo1"></a>**EO1: `project.yaml`.** At the repo root, pointing at the documents above, and checked with the ecosystem's validator (0 errors, 0 warnings). `links.deployment` is `null`: the app is deployed, but its domain stays out of tracked files (owner, 2026-11-13). `c8fcf62`.
- [x] <a id="eo2"></a>**EO2: The shared rules.** `CLAUDE.md`'s first line imports the ecosystem's shared rules, and nothing else in it moved, so it still says how to build and test without the import. `c8fcf62`.
- [x] <a id="eo3"></a>**EO3: Standing approval for commits.** None (owner, 2026-11-14): every commit waits for the owner, and `CLAUDE.md` grants nothing. Sessions here committed Phase 1 on the working branch `phase-1-bugs`, but work since 2026-11-02 goes straight to `main`, which a grant never covers. If the owner grants it later, `CLAUDE.md` gets a "Commits" section: commit on a working branch once the work is verified, never on `main`, and never push, merge or deploy without the owner. A push to `main` that changes `web/` deploys, so the merge stays the owner's.
- [x] <a id="eo4"></a>**EO4: X1-X3.** The owner's target capabilities and release gate, with X1-X3, are in "Release gate" above. Their done-whens are new, and the owner approved them on 2026-11-14. `c8fcf62`.
- [x] <a id="eo5"></a>**EO5: Confidential work.** This plan's opening says confidential work never goes in this file, and the shared rules say where. Nothing in this plan is marked confidential (owner, 2026-11-13).
- [x] <a id="eo6"></a>**EO6: `.gitattributes` with LF line endings.** `* text=auto eol=lf` is its first rule, above the mirror's `-text` line, so the mirror's CSVs keep their CRLF. Every other text file was already LF in the index (`git ls-files --eol`, 2026-11-14), so `git add --renormalize .` has nothing to stage.
- [x] <a id="eo7"></a>**EO7: `npm run check` from a lowercase drive letter.** VS Code opens the folder as `c:\`. Vitest's worker loaded its runner from the spelling the command started in, `c:`, while each test file resolved `vitest` to `C:`, so a run from `c:` had two runners and every file failed with no test run. On Windows, `web/vite.config.ts` now points the tests' `vitest` at the copy under the working directory, so there is one. Checked on 2026-11-14 with `cmd /c "cd /d c:\<path>\trkr\web && ..."` and the same from `C:\`: `npm run check` and `npm test` pass from both (36 tests), and `npm run build` passes. pytest passes from both (175 tests).
- [x] <a id="eo8"></a>**EO8: The Python commands on Linux.** The README's Setup gives the Linux spelling, `python3 -m venv .venv` and `.venv/bin/python` wherever it writes `.venv/Scripts/python.exe`, and Development points there. `CLAUDE.md` keeps the Windows spelling, the owner's machine. Linux coverage: the deploy workflow runs `npm run check` on `ubuntu-latest`, which covers the web app, and nothing runs pytest on Linux until Phase 3's GitHub Actions item does.
- [x] <a id="eo9"></a>**EO9: The C++ tool by its repository.** `CLAUDE.md` and "Feature: net-worth projection" name it as the public repo `eigenomarksamy/networth_projection`, and no tracked file gives a local path for it.
- [x] <a id="eo10"></a>**EO10: An issue for every open ticket.** On the ecosystem's GitHub Project, only with the owner's approval, and with each issue's text shown first, since the repo is public. Each ticket has a stable anchor above its heading (W0-W4 and W6-W11 since 2026-11-14). The issue's title starts with the ticket's id, its body links the ticket's section, and each need becomes a blocked-by link (X2 on X1, X3 on X2). The open tickets on 2026-11-14 are 14: W0-W4, W6-W11 and X1-X3. W5 closes without one, since W11 does its work, and W11 is one issue, with its slices as its list (owner, 2026-11-14). A W milestone is done when every item in its list is ticked or dropped. Priorities (owner, 2026-11-14): W11 P1; W8 and W9, the owner's calls, P3; the rest P2. Items without an id (Phases 2-4, the projection's "Later", the broker import, the sheet generator) aren't tickets, so they get no issue unless they get an id. Done 2026-11-14, with the owner's approval of each text: W0-W4 are #1-#5, W6-W11 #6-#11 and X1-X3 #12-#14, each in the Project with its status, priority and work type, and #13 (X2) is blocked by #12 (X1), and #14 (X3) by #13 (X2).

No documents are planned beyond this one: `CLAUDE.md`, the README and `web/README.md` already cover the architecture and the engineering.

Open questions, answered by the owner on 2026-11-14:

- EO3: no standing approval for commits (EO3).
- EO10: W11 P1; W8 and W9 P3; the rest P2 (EO10).
- EO10: W5 closes without an issue, since W11 does its work (W5, EO10).
- X1-X3: the new done-whens are approved, with EO10's issue texts (X1-X3).
