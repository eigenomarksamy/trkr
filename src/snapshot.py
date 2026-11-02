"""The run snapshot: what the web app shows, as one JSON file per run.

The web app (web/) opens it in the browser. It holds no sheet address, sheet ID or file path:
the config summary only says whether each source is local or cloud.
"""

import json
import math
import os
import pathlib
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

from src.cfg_mngr import CfgManager, ConfigMapUri
from src.portfolio_mngr import HOLDING_COLUMNS, history_key_date

SCHEMA = 'trkr-snapshot'
# Bump on a change that a reader of the old shape would get wrong, and update web/src/snapshot.ts.
SCHEMA_VERSION = 1


def month_of(key: str) -> str:
    """A month key ('jan24') or a day ('2024-01-15') as 'YYYY-MM'."""
    return history_key_date(key).strftime('%Y-%m')


def portfolio_snapshot(run) -> dict:
    """The figures of one PortfolioRun (run.py), the real portfolio or an imaginary one."""
    transactions = sorted(run.transactions.get(), key=lambda t: t.date)
    return {
        'holdings': [
            {'symbol': symbol} | {column: holding[column] for column in HOLDING_COLUMNS}
            for symbol, holding in run.portfolio_dict.items()
        ],
        'total': dict(run.total_dict),
        'monthly_spending': [
            {'month': month_of(key), 'amount': amount}
            for key, amount in run.portfolio.compute_spending_history().items()
        ],
        'valuation': [
            {'month': month_of(key), 'value': value}
            for key, value in run.historical_valuation.items()
        ],
        'entry_points': {symbol: month_of(key) for symbol, key in run.entry_points.items()},
        'transactions': [
            {
                'type': t.type,
                'date': t.date,
                'quantity': t.quantity,
                'fees': t.fees,
                'price': t.price,
                'currency': t.currency,
                'symbol': t.symbol,
                'exchange': t.exchange,
                'platform': t.wallet,
                'ex_rate': t.ex_rate,
                'ex_fees': t.ex_fees,
            }
            for t in transactions
        ],
        # Closes in the default currency. With lite history a month's date is its 1st, and its
        # close is the month's last weekly close.
        'prices': {
            ticker: [
                {'date': day.isoformat(), 'close': close}
                for day, close in sorted(
                    (history_key_date(key), point['price']) for key, point in history.items()
                )
            ]
            for ticker, history in run.history.items()
        },
    }


def projection_snapshot(projection: dict) -> dict:
    """The inputs and rows of process_projection (run.py)."""
    inputs = asdict(projection['cfg'])
    inputs['deposits_withdrawals'] = {
        str(year): amount for year, amount in inputs['deposits_withdrawals'].items()
    }
    return {
        'inputs': inputs,
        'start_year': projection['start_year'],
        'start_value': projection['start_value'],
        'start_label': projection['start_label'],
        'invested_last_12_months': projection['invested_last_12_months'],
        'rows': [asdict(row) for row in projection['projection_rows']],
    }


def build_snapshot(
    cfg: CfgManager,
    portfolio_run,
    imaginary_runs: dict,
    projection: Optional[dict],
    ticker_map: Optional[dict],
    generated_at: Optional[datetime] = None,
) -> dict:
    """portfolio_run and imaginary_runs' values are run.py's PortfolioRun."""
    positions = cfg.get_param(ConfigMapUri.POSITIONS)
    positions_source = None
    if positions is not None:
        positions_source = 'local' if positions.is_local else 'cloud'
    symbols_map_source = None
    if cfg.get_param(ConfigMapUri.SYMBOLS_STANDARD) == 'custom':
        symbols_map_source = cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SOURCE)
    return {
        'schema': SCHEMA,
        'schema_version': SCHEMA_VERSION,
        'generated_at': (generated_at or datetime.now()).isoformat(timespec='seconds'),
        'config': {
            'default_currency': cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
            'history_variant': cfg.get_param(ConfigMapUri.HISTORY_VARIANT),
            'sources': {
                'transactions': cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE),
                'symbols_map': symbols_map_source,
                'positions': positions_source,
            },
        },
        'symbol_map': dict(ticker_map or {}),
        'portfolio': portfolio_snapshot(portfolio_run),
        'imaginary': [
            {'name': name} | portfolio_snapshot(run) for name, run in imaginary_runs.items()
        ],
        'projection': projection_snapshot(projection) if projection else None,
    }


def finite(value: Any) -> Any:
    """NaN and infinity become null: JSON has neither, and Yahoo sometimes gives NaN closes."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [finite(item) for item in value]
    return value


def write_snapshot(snapshot: dict, path: os.PathLike, history_dir: os.PathLike) -> pathlib.Path:
    """Writes path, and a copy named after the run time in history_dir.

    Each file is written under a temporary name and then renamed, so a reader never sees half
    a file. Returns the copy's path.
    """
    text = json.dumps(finite(snapshot), indent=1, ensure_ascii=False, allow_nan=False) + '\n'
    run_time = datetime.fromisoformat(snapshot['generated_at']).strftime('%Y%m%d_%H%M%S')
    copy = pathlib.Path(history_dir) / f'{run_time}.json'
    for target in (pathlib.Path(path), copy):
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.tmp')
        temporary.write_text(text, encoding='utf-8')
        os.replace(temporary, target)
    return copy
