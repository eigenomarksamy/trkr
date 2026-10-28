# trkr

Personal investment-portfolio tracker. Reads a transactions CSV (local file or a public Google Sheet), pulls prices from Yahoo Finance via `yfinance`, computes per-symbol and total P&L, and writes CSV/Markdown tables, matplotlib PNGs and a static HTML report. Single user, Windows, run on a schedule via `run_script.bat`.

**Modernization is in progress.** The plan, the known-bug list and progress live in `docs/MODERNIZATION.md`. Read it before starting work, and tick items there as they land.

## Running

- Python 3.11 venv at `.venv/`. Call it directly, no activation needed: `.venv/Scripts/python.exe`.
- `.venv/Scripts/python.exe run.py --cfg config/cfg.yml`. Needs network (Google Sheets + Yahoo), ~10-15 s.
- `run_script.bat` is the owner's scheduled job: activates the venv, runs `pip install -r requirements.txt`, then runs with `config/cfg_bat.yml` → `data/bat_script/`, `log/bat_script/`. Keep it working.
- The `--quiet` and `--log-level` CLI flags are parsed but ignored; the `cli-exec` block in the YAML is what counts.
- Tests: `.venv/Scripts/python.exe -m pytest` (offline, ~3 s).
- Lint and format: `.venv/Scripts/python.exe -m ruff check .` and `... -m ruff format .` (config in `pyproject.toml`). A PostToolUse hook (`.claude/hooks/format_python.py`) already sorts imports and formats each `.py` file Claude edits, so an Edit's `old_string` may need re-reading after a reformat.
- Dependencies: declared in `pyproject.toml`, locked in `uv.lock`. `requirements.txt` is generated from the lock (`uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`), so never edit it by hand. To change dependencies, edit `pyproject.toml` (or `uv add --no-sync`), run `uv lock`, then re-export. Never run plain `uv sync` or `uv add` on `.venv`: an exact sync removes packages the owner installed outside the lock. Use `uv sync --inexact` to install. uv is installed by winget and may be missing from an older shell's PATH; it lives at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`.
- `tests/test_exec.py` snapshots the fixture portfolio's `portfolio.csv`, `total.md` and `entries.md` in `tests/golden/`. When an output change is intended, rerun with `TRKR_UPDATE_GOLDEN=1` and review the golden diff.
- `config/demo-cfg.yml` runs on made-up data in `examples/` plus live Yahoo prices, writing to `data/demo-run/`. It doesn't touch the owner's sheets, so it is safe to run.

## Private data

`config/*.yml` (except `demo-cfg.yml`), `data/` and `log/` are gitignored and hold the owner's real portfolio: Google Sheet IDs readable by anyone with the link, transaction history, generated reports.

- Never copy real values (sheet IDs, holdings, quantities, prices) into tracked files, test fixtures, commit messages or PR text. Build fixtures from made-up data.
- Don't edit `config/cfg.yml` or `config/cfg_bat.yml` without asking.
- A real end-to-end run hits the owner's live sheets. Ask before running it.

## Pipeline (`run.py` → `exec`)

1. `create_cfg` (`src/cfg_mngr.py`) flattens the nested YAML into `ConfigMapUri` keys. `Directories` builds every output path by string concatenation, so directory values in the YAML **must end with `/`**. The optional `imaginary-portfolios` and `projection` blocks are parsed into dataclasses and validated; an invalid block prints the reason and raises `"422"`.
2. Symbol map (when `transactions.symbols-standard: custom`): CSV `symbol,ticker` mapping lowercase local symbols to Yahoo tickers (`vwce → VWCE.AS`). It must also contain the default currency's key: with EUR as default, `eur → USDEUR=X` is the FX ticker every non-EUR series is **multiplied** by. That only works for exactly two currencies.
3. `build_transactions_object` (`src/transactions.py`) downloads/reads the transactions CSV and rewrites each symbol to its Yahoo ticker. With the optional `positions:` block, `build_positions` reads holdings as of a date (one row per investment: quantity, `average_price` or a total `cost` in the default currency, and a date) as synthetic `buy`s with platform `positions file`. `merge_positions` puts them first, because `Portfolio.calculate` walks the list in order and later sells must see them. It also drops each trade in the same symbol dated on or before the position, since the position already includes it. That is what lets a snapshot replace the trade history.
4. `MarketDataYahoo` (`src/market_mngr.py`) fetches history, current price and currency for each ticker, then converts currencies.
5. `Portfolio` (`src/portfolio_mngr.py`) computes per-symbol and total figures, monthly spending, entry points and historical valuation.
6. `csv_mngr`, `plot_mngr` and `report_mngr` write `<gen-dir>/generated/…` and `<gen-dir>/report.html`.

Steps 3-5 and the files/plots of step 6 live in `process_portfolio`, which returns a `PortfolioRun`. It runs once for the real portfolio and once per imaginary portfolio (output in `<gen-dir>/imaginary/<name>/`, with its own report). Then `process_projection` runs `src/projection.py`, a pure year-by-year net-worth projection ported from the owner's C++ tool `C:\dev_ws\networth_projection`. Last, `write_report` renders the main report with the comparison table and the projection section.

Errors are signalled as `raise Exception("503")`; `run_cli` turns the message into an int exit code and a name via `get_exception` (`src/utils.py`). Any other exception crashes inside that handler with a `ValueError`.

## Non-obvious conventions

- Transaction dates are `YYYY-MM-DD` strings everywhere. Monthly buckets use short keys like `jan24` from `convert_date_to_short_str`, which is duplicated in `market_mngr.py` and `portfolio_mngr.py`. The copies differ only when called with no arguments (`None` vs `''`, pinned in `tests/test_month_key.py`); keep them otherwise identical until they're merged.
- `history-variant: lite` (weekly bars) keys history by those month keys, so weeks collapse and the last close of the month wins. Yahoo labels each weekly bar with its Monday, so the current month can have no bar yet, and `formulate_history` then fills it with the current price (bug 13). `full` keys by `YYYY-MM-DD`, which the monthly code in `Portfolio` can't look up (known bug).
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
