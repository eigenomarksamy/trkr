# trkr

Personal investment-portfolio tracker. Reads a transactions CSV (local file or a public Google Sheet), pulls prices from Yahoo Finance via `yfinance`, computes per-symbol and total P&L, and writes CSV/Markdown tables, matplotlib PNGs, a static HTML report and a `snapshot.json` for the web app in `web/`. Single user, Windows, run on a schedule via `run_script.bat`.

**Modernization is in progress.** The plan, the known-bug list and progress live in `docs/MODERNIZATION.md`. Read it before starting work, and tick items there as they land.

## Running

- Python 3.11 venv at `.venv/`. Call it directly, no activation needed: `.venv/Scripts/python.exe`.
- `.venv/Scripts/python.exe run.py --cfg config/cfg.yml`. Needs network (Google Sheets + Yahoo), ~10-15 s.
- `run_script.bat` is the owner's scheduled job: activates the venv, runs `pip install -r requirements.txt`, then runs with `config/cfg_bat.yml` → `data/bat_script/`, `log/bat_script/`. Keep it working.
- The `--quiet` and `--log-level` CLI flags override the YAML `cli-exec` block when given. `run_script.bat` passes neither, so the scheduled job follows `cfg_bat.yml`.
- Tests: `.venv/Scripts/python.exe -m pytest` (offline, ~3 s).
- Lint and format: `.venv/Scripts/python.exe -m ruff check .` and `... -m ruff format .` (config in `pyproject.toml`). A PostToolUse hook (`.claude/hooks/format_python.py`) already sorts imports and formats each `.py` file Claude edits, so an Edit's `old_string` may need re-reading after a reformat.
- Dependencies: declared in `pyproject.toml`, locked in `uv.lock`. `requirements.txt` is generated from the lock (`uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`), so never edit it by hand. To change dependencies, edit `pyproject.toml` (or `uv add --no-sync`), run `uv lock`, then re-export. Never run plain `uv sync` or `uv add` on `.venv`: an exact sync removes packages the owner installed outside the lock. Use `uv sync --inexact` to install. uv is installed by winget and may be missing from an older shell's PATH; it lives at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`.
- `tests/test_exec.py` snapshots the fixture portfolio's `portfolio.csv`, `total.md` and `entries.md` in `tests/golden/`. When an output change is intended, rerun with `TRKR_UPDATE_GOLDEN=1` and review the golden diff.
- `tests/test_mirror.py` runs the CLI the way the scheduled job does (cloud sheets, custom map, EUR, lite, not quiet, log INFO) on `tests/fixtures/mirror/`: made-up sheets in the shape of the owner's, as of its 2025-11-04 download. Every value in them is invented. Snapshots are in `tests/golden/mirror/`. Use it instead of a live run to check a change against owner-like data. If the owner's sheet changes shape, rebuild the mirror from a profile of the cached sheet (counts and categories only), never from its values.
- `config/demo-cfg.yml` runs on made-up data in `examples/` plus live Yahoo prices, writing to `data/demo-run/`. It doesn't touch the owner's sheets, so it is safe to run.
- Web app: `cd web`, then `npm run check` (tsc + vitest, offline), `npm run build`, `npm run preview` (Worker on 127.0.0.1:8787, `/?demo` opens the demo). Details in `web/README.md`.

## Private data

`config/*.yml` (except `demo-cfg.yml`), `data/` and `log/` are gitignored and hold the owner's real portfolio: Google Sheet IDs readable by anyone with the link, transaction history, generated reports.

- Never copy real values (sheet IDs, holdings, quantities, prices) into tracked files, test fixtures, commit messages or PR text. Build fixtures from made-up data.
- Don't edit `config/cfg.yml` or `config/cfg_bat.yml` without asking.
- A real end-to-end run hits the owner's live sheets. Ask before running it.
- A `snapshot.json` holds holdings and transactions. Never copy one into `web/`; the only snapshot there is `web/public/demo-snapshot.json`, made from `config/demo-cfg.yml`.
- Deploying the web app (`npm run deploy`, `wrangler deploy`) publishes it. Leave that to the owner unless asked, and never write the owner's domain into tracked files: the repo is public.

## Pipeline (`run.py` → `exec`)

1. `create_cfg` (`src/cfg_mngr.py`) flattens the nested YAML into `ConfigMapUri` keys. `Directories` builds every output path by string concatenation, so directory values in the YAML **must end with `/`**. The optional `imaginary-portfolios` and `projection` blocks are parsed into dataclasses and validated; an invalid block prints the reason and raises `"422"`.
2. Symbol map (when `transactions.symbols-standard: custom`): CSV `symbol,ticker` mapping lowercase local symbols to Yahoo tickers (`vwce → VWCE.AS`). With `yahoo` there is no map (`yfinance_map_obj` is `None`) and symbols are used as written. A default-currency entry (`eur → USDEUR=X`) is optional; it only adds that rate to the charted symbols.
3. `build_transactions_object` (`src/transactions.py`) downloads/reads the transactions CSV and rewrites each symbol to its Yahoo ticker. With the optional `positions:` block, `build_positions` reads holdings as of a date (one row per investment: quantity, `average_price` or a total `cost` in the default currency, and a date) as synthetic `buy`s with platform `positions file`. `merge_positions` puts them first, because `Portfolio.calculate` walks the list in order and later sells must see them. It also drops each trade in the same symbol dated on or before the position, since the position already includes it. That is what lets a snapshot replace the trade history.
4. `MarketDataYahoo` (`src/market_mngr.py`) fetches history, current price and currency for each ticker, then converts each currency with its own Yahoo pair `<CUR><DEFAULT>=X`, fetched on demand. Minor units (GBp, ZAc, ILA) are divided by 100. A ticker without a currency fails the run with 503.
5. `Portfolio` (`src/portfolio_mngr.py`) computes per-symbol and total figures, monthly spending, entry points and historical valuation. `calculate` walks trades by date with average cost: `spending`, `profit_net` and `profit_percent` cover what is still held, `realized_profit` what sells made, and a sell of more than is held raises 400. The historical valuation is the holdings' market value at each month end, through the current month.
6. `csv_mngr`, `plot_mngr` and `report_mngr` write `<gen-dir>/generated/…` and `<gen-dir>/report.html`.
7. `src/snapshot.py` writes `<gen-dir>/snapshot.json` and a copy in `<gen-dir>/snapshots/`, both through a temp file and a rename. It holds everything the web app shows: no sheet address and no path, only whether each source is `local` or `cloud`. Months are `YYYY-MM`, days `YYYY-MM-DD`, and NaN becomes `null`.

Steps 3-5 and the files/plots of step 6 live in `process_portfolio`, which returns a `PortfolioRun`. It runs once for the real portfolio and once per imaginary portfolio (output in `<gen-dir>/imaginary/<name>/`, with its own report). Then `process_projection` runs `src/projection.py`, a pure year-by-year net-worth projection ported from the owner's C++ tool `C:\dev_ws\networth_projection`. Then `write_report` renders the main report with the comparison table and the projection section. Last, `write_snapshot` writes the snapshot of the whole run.

Errors are signalled as `raise Exception("503")`; `run_cli` turns the message into an int exit code and a name via `get_exit_status` (`src/utils.py`). Any other exception prints its traceback and exits 1 as `UnexpectedError`.

## Non-obvious conventions

- Transaction dates are `YYYY-MM-DD` strings everywhere. Monthly buckets use short keys like `jan24` from `convert_date_to_short_str`, which is duplicated in `market_mngr.py` and `portfolio_mngr.py`. The copies differ only when called with no arguments (`None` vs `''`, pinned in `tests/test_month_key.py`); keep them otherwise identical until they're merged.
- `history-variant: lite` (weekly bars) keys history by those month keys, so weeks collapse and the last close of the month wins. Yahoo labels each weekly bar with its Monday, so the current month can have no bar yet, and `formulate_history` then fills it with the current price (bug 13). `full` keys by `YYYY-MM-DD`, and today, which never has a daily bar, gets the current price. `history_key_date` (`portfolio_mngr.py`) turns either kind of key into a date: the valuation reduces both to month closes, and the charts use a date axis.
- `Transaction.__dict__` is a *method* returning a dict, so callers write `t.__dict__()`. `vars(t)` won't do what you expect.
- `Transactions.get()` returns the internal list, and several `Portfolio` methods `.sort()` it in place.
- `report_mngr.py` rewrites the Jinja templates in `templates/` from inline strings on every run, and that directory is gitignored. Edit the strings in `report_mngr.py`, not the `.html` files.
- The HTML report links images and sub-pages with absolute `file://` URIs, so a report only works on the machine that generated it.
- Dead code: `MarketDataGoogle*`, `MarketReader`, `fetch_histories`, `use_market_google`, `execute_yahoo_finance`, most of `Sheets` (only `Sheets.is_url` is used), and `src/market_tester.py`, a scratch script that hits the network on import. Never import it.

## Working rules

- The money math has known bugs and only end-to-end golden coverage. Before changing `portfolio_mngr.py`, the currency conversion in `market_mngr.py`, or `transactions.py`, first add a test with synthetic transactions. The test pins either the current behaviour or, when fixing a bug, the corrected behaviour.
- Tests never touch the network: stub `yfinance.Ticker` and `requests.get`.
- One concern per commit. Keep formatting-only changes in their own commits, apart from logic changes.
- Keep the YAML config schema backward compatible: the owner's existing `cfg.yml` and `cfg_bat.yml` must keep working.

## Web app (`web/`)

A TypeScript page with no framework, built by Vite and served by a Cloudflare Worker (`web/src/worker.ts`) with a strict CSP. It reads a `snapshot.json` that the owner opens in the browser. The Worker stores nothing and receives no portfolio data. The plan and its decisions are in `docs/MODERNIZATION.md`, "Feature: web app".

- The snapshot is a contract between `src/snapshot.py` and `web/src/snapshot.ts`. Change both and bump `SCHEMA_VERSION` in both when its shape changes. `tests/golden/exec/snapshot.json` pins the Python side, and the web tests parse it.
- `web/src/projection.ts` ports `project_net_worth` and the projection checks of `parse_projection_cfg`. A change to either Python function needs the same change there. `web/test/projection.test.ts` compares the port with the rows in the demo snapshot.
- `npm run build` ends with `web/scripts/check-private.mjs`, and `wrangler dev`/`deploy` run that build first. It refuses files under `web/index.html`, `web/src/` or `web/public/` that git doesn't know, so `git add` new files before building.
- Build DOM with `h()`/`s()` from `web/src/dom.ts`, which only inserts text. No `innerHTML`, no inline styles (the CSP blocks them), no CDN or third-party requests.
- Charts follow the dataviz palette: up to three series in slots 1-3, a legend for two or more, a table view under each chart.
