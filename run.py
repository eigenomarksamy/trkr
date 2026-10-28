import logging
import os
import pathlib
import sys
from argparse import Namespace
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Tuple, Union

from src.cfg_mngr import CfgManager, ConfigMapUri, Directories, PositionsCfg, create_cfg
from src.csv_mngr import CsvMngr, write_csv_lazy, write_markdown_grid, write_markdown_table
from src.log_mngr import LogManager
from src.market_mngr import (
    Interval,
    MarketDataYahoo,
    MarketSymbol,
    YFinanceSymbMap,
    convertSymbListToDicts,
    get_yfinance_map,
    get_yfinance_map_local,
)
from src.plot_mngr import plot_combined, plot_monthly_stocks, plot_projection
from src.portfolio_mngr import Portfolio
from src.projection import (
    ProjectionCfg,
    invested_last_12_months,
    project_net_worth,
    projection_table,
    resolve_start_value,
)
from src.report_mngr import generate_html_report
from src.transactions import (
    Transactions,
    build_positions,
    build_transactions_object,
    merge_positions,
)
from src.utils import check_internet, get_exception, parse_arguments


@dataclass
class PortfolioRun:
    transactions: Transactions
    portfolio: Portfolio
    portfolio_dict: dict
    total_dict: dict
    entry_points: dict
    historical_valuation: dict
    figs_paths_stocks: list
    figs_paths_stats: list


def exec(cfg_file: os.PathLike) -> None:
    cfg = create_cfg(cfg_file)
    is_quiet = cfg.get_param(ConfigMapUri.QUIET)
    log_level = cfg.get_param(ConfigMapUri.LOG_LEVEL)
    directories = Directories(
        base_dir=cfg.get_param(ConfigMapUri.GENERATION_DIRECTORY),
        log_dir=cfg.get_param(ConfigMapUri.LOG_DIRECTORY),
        local_trans_dir=cfg.get_param(ConfigMapUri.TRANSACTIONS_DIRECTORY)
        if cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local'
        else None,
        local_map_dir=cfg.get_param(ConfigMapUri.SYMBOLS_MAP_DIRECTORY)
        if cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'local'
        else None,
    )
    logger = None
    if LogManager.is_log_active(log_level):
        log_manager = LogManager(
            log_file=f'{directories.log_dir}app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            log_level=log_level,
        )
        logger = log_manager.get_logger()
    if not check_internet():
        if logger:
            logger.error('Failed to connect.')
        if not is_quiet:
            print('Failed to connect.')
        raise Exception('503')
    if not is_quiet:
        print('Connection exists.')
    if logger:
        logger.info('Connection exists.')
    if cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'cloud':
        trans_sheets = cfg.get_param(ConfigMapUri.TRANSACTIONS_SHEET)
    else:
        trans_sheets = cfg.get_param(ConfigMapUri.TRANSACTIONS_DIRECTORY)
    if not is_quiet:
        cfg.print()
    if logger:
        logger.info('Configuration retrieved.')
    yfinance_map_obj = None
    if cfg.get_param(ConfigMapUri.SYMBOLS_STANDARD) == 'custom':
        if cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'cloud':
            yfinance_map_obj = get_yfinance_map(
                cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SHEET), f'{directories.sheets_dir}'
            )
        else:
            yfinance_map_obj = get_yfinance_map_local(
                cfg.get_param(ConfigMapUri.SYMBOLS_MAP_DIRECTORY)
            )
        if not is_quiet:
            print('Yahoo Finance Ticker map:')
            print(yfinance_map_obj.tickerMap)
        if logger:
            logger.info('Ticker map built.')
    portfolio_run = process_portfolio(
        cfg,
        directories,
        cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local',
        trans_sheets,
        yfinance_map_obj,
        is_quiet,
        logger,
        positions=cfg.get_param(ConfigMapUri.POSITIONS),
    )
    imaginary_runs = {}
    for imaginary in cfg.get_param(ConfigMapUri.IMAGINARY_PORTFOLIOS):
        if not is_quiet:
            print(f"Imaginary portfolio '{imaginary.name}':")
        imaginary_dirs = Directories(
            base_dir=f'{directories.imaginary_dir}{imaginary.name}/', log_dir=directories.log_dir
        )
        imaginary_runs[imaginary.name] = process_portfolio(
            cfg,
            imaginary_dirs,
            imaginary.is_local,
            imaginary.location,
            yfinance_map_obj,
            is_quiet,
            logger,
        )
        write_report(
            cfg,
            imaginary_dirs,
            imaginary_runs[imaginary.name],
            yfinance_map_obj,
            title=f'Imaginary Portfolio: {imaginary.name}',
        )
        if logger:
            logger.info(f"Imaginary portfolio '{imaginary.name}' processed.")
    projection = None
    if cfg.get_param(ConfigMapUri.PROJECTION):
        projection = process_projection(
            cfg.get_param(ConfigMapUri.PROJECTION), directories, portfolio_run, imaginary_runs
        )
        if logger:
            logger.info('Projection computed.')
    if not is_quiet:
        print('Generating HTML report..')
    write_report(
        cfg,
        directories,
        portfolio_run,
        yfinance_map_obj,
        imaginary_portfolios=[
            {
                'name': name,
                'total': imaginary_run.total_dict,
                'report': f'{directories.imaginary_dir}{name}/report.html',
            }
            for name, imaginary_run in imaginary_runs.items()
        ],
        projection=projection,
    )
    if logger:
        logger.info('HTMLs created.')
    if not is_quiet:
        print(f'HTML report generated at {f"{directories.base_dir}report.html"}')


def write_report(
    cfg: CfgManager,
    directories: Directories,
    portfolio_run: PortfolioRun,
    yfinance_map_obj: Optional[YFinanceSymbMap],
    **kwargs,
) -> None:
    generate_html_report(
        total_dict=portfolio_run.total_dict,
        entry_points=portfolio_run.entry_points,
        portfolio_dict=portfolio_run.portfolio_dict,
        ticker_map=yfinance_map_obj.tickerMap,
        def_currency=cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
        figs_paths_stocks=portfolio_run.figs_paths_stocks[::-1],
        figs_paths_stats=portfolio_run.figs_paths_stats,
        transactions_list=portfolio_run.transactions.get(),
        historical_valuation=portfolio_run.historical_valuation,
        req_path=f'{directories.base_dir}report.html',
        sub_dir=f'{directories.generated_dir}',
        **kwargs,
    )


def process_projection(
    projection_cfg: ProjectionCfg,
    directories: Directories,
    portfolio_run: PortfolioRun,
    imaginary_runs: dict[str, PortfolioRun],
) -> dict:
    portfolio_values = {'portfolio': portfolio_run.total_dict['value']}
    for name, imaginary_run in imaginary_runs.items():
        portfolio_values[name] = imaginary_run.total_dict['value']
    start_value = resolve_start_value(projection_cfg, portfolio_values)
    today = date.today()
    rows = project_net_worth(projection_cfg, start_value, today.year + 1)
    headers, lines = projection_table(rows, labels=False)
    CsvMngr(pathlib.Path(directories.gen_projection_csv), headers).write(lines)
    labels, _ = projection_table(rows, labels=True)
    write_markdown_grid(
        pathlib.Path(directories.gen_projection_md), 'Net-worth Projection', labels, lines
    )
    series = {
        'Net worth': [row.net_worth_before_fees for row in rows],
        'Net worth (after fees)': [row.net_worth_after_fees for row in rows],
    }
    if projection_cfg.inflation is not None:
        series["Net worth (after fees, today's money)"] = [row.net_worth_real for row in rows]
    fig_path = plot_projection(
        directories.gen_plots_projection,
        [row.year for row in rows],
        projection_cfg.birth_year,
        series,
    )
    if projection_cfg.start_net_worth == 'portfolio':
        start_label = "the real portfolio's current value"
    elif isinstance(projection_cfg.start_net_worth, str):
        start_label = f"the current value of imaginary portfolio '{projection_cfg.start_net_worth}'"
    else:
        start_label = 'a fixed amount from the config'
    if projection_cfg.cash:
        start_label += f' plus {projection_cfg.cash:.2f} cash'
    return {
        'cfg': projection_cfg,
        'start_value': start_value,
        'start_label': start_label,
        'last': rows[-1],
        'contribution': rows[0].contribution,
        'invested_last_12_months': invested_last_12_months(
            portfolio_run.portfolio.compute_spending_history(), today
        ),
        'fig': fig_path,
        'headers': labels,
        'rows': lines,
    }


def process_portfolio(
    cfg: CfgManager,
    directories: Directories,
    is_local: bool,
    trans_sheets: str,
    yfinance_map_obj: Optional[YFinanceSymbMap],
    is_quiet: bool,
    logger: Optional[logging.Logger],
    positions: Optional[PositionsCfg] = None,
) -> PortfolioRun:
    transactions_obj = build_transactions_object(
        is_local, trans_sheets, f'{directories.sheets_dir}', is_quiet, yfinance_map_obj.tickerMap
    )
    if positions:
        dropped = merge_positions(
            transactions_obj,
            build_positions(
                positions.is_local,
                positions.location,
                f'{directories.sheets_dir}',
                is_quiet,
                yfinance_map_obj.tickerMap,
                cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
            ),
        )
        if not is_quiet and dropped:
            print(f'Positions already include {len(dropped)} earlier trades, which are skipped.')
        if logger:
            logger.info(f'Positions retrieved. They include {len(dropped)} earlier trades.')
    if not is_quiet:
        transactions_obj.print()
    if logger:
        logger.info('Transactions retrieved.')
    symbols_of_interest = transactions_obj.get_symbols_of_interest()
    if yfinance_map_obj:
        symbols_of_interest += [
            f'{yfinance_map_obj.tickerMap.get(cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY).lower())}'
        ]
    else:
        symbols_of_interest += [f'{cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY)}']
    if not is_quiet:
        print('Symbols of Interest: ', symbols_of_interest)
    if logger:
        logger.info('Symbols of Interest retrieved.')
    history_variant = cfg.get_param(ConfigMapUri.HISTORY_VARIANT)
    if history_variant == 'full':
        if not is_quiet:
            print('WARNING! Full history variant is not recommended.')
    if cfg.get_param(ConfigMapUri.MARKET_ORIGIN) == 'yahoo':
        start_date = transactions_obj.get_first_transaction_date()
        if not is_quiet:
            print('Start Date:', start_date)
        if logger:
            logger.info(f'Start date: {start_date}')
        market = MarketDataYahoo(
            tickers=symbols_of_interest,
            ticker_map=yfinance_map_obj,
            start_date=start_date,
            interval=Interval.WEEKLY if history_variant == 'lite' else Interval.DAILY,
            req_currency=cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
        )
    else:
        if cfg.get_param(ConfigMapUri.MARKET_ORIGIN) == 'google':
            raise Exception('299')
        else:
            raise Exception('417')
    symbols_obj_list = []
    for symbol in symbols_of_interest:
        symbol_key = symbol
        symbols_obj_list.append(
            MarketSymbol(
                symbol,
                market.history[symbol_key],
                market.current_price[symbol_key],
                market.currency[symbol_key],
            )
        )
    if not is_quiet:
        for symbol in symbols_obj_list:
            symbol.print()
    if logger:
        logger.info('Market data instantiated.')
    prices_dict, history_dict = convertSymbListToDicts(symbols_obj_list)
    portfolio = Portfolio(transactions_obj, prices_dict, is_quiet=is_quiet)
    portfolio_dict, total_dict = portfolio.calculate()
    if logger:
        logger.info('Portfolio calculated.')
        logger.info('Total computed.')
    historical_valuation = portfolio.compute_historical_valuation(history_dict)
    entry_points = portfolio.get_entry_points_months()
    if logger:
        logger.info('History valuated.')
        logger.info('Entry points obtained.')
    if not is_quiet:
        print('Historical Evaluation Dict:')
        for hv in historical_valuation.keys():
            print('\t', hv, historical_valuation[hv])
        print('Entries Dict:')
        for ep in entry_points.keys():
            print('\t', ep, entry_points[ep])
    if not is_quiet:
        print('Generating files..')
    write_csv_lazy(pathlib.Path(f'{directories.gen_portfolio_file}'), portfolio_dict, 'symbol')
    write_markdown_table(
        pathlib.Path(f'{directories.gen_total_file}'), 'Total', 'Metric', 'Value', total_dict
    )
    write_markdown_table(
        pathlib.Path(f'{directories.gen_entries_file}'),
        'Entry Points',
        'Symbol',
        'Date',
        entry_points,
    )
    if not is_quiet:
        print('Files generated.')
    if logger:
        logger.info('Files generated.')
    (
        spending_list,
        profit_percent_list,
        spending_percent_per_month_list,
        symbols_list,
        pp_list,
        months_list,
    ) = portfolio.convert_dicts_to_lists()
    if not is_quiet:
        print('Generating plots..')
    figs_paths_stocks = plot_monthly_stocks(
        fig_path=f'{directories.gen_plots_history}',
        data_dict=history_dict,
        entry_points=entry_points,
    )
    figs_paths_stats = plot_combined(
        fig_path=f'{directories.gen_plots_stats}',
        nums_pie=spending_list,
        nums_bar=profit_percent_list,
        nums_points=spending_percent_per_month_list,
        nums_points_1=list(historical_valuation.values()),
        labels_pie=symbols_list,
        labels_bar=pp_list,
        labels_points=months_list,
        labels_points_1=list(historical_valuation.keys()),
        points_title='Spending Per Month',
        points1_title='Valuation Percent',
        pie_title='Spending Percent',
        bar_title='Profit Percent',
    )
    if logger:
        logger.info('Plots created.')
    if not is_quiet:
        print(f'Check {directories.base_dir} for information.')
    return PortfolioRun(
        transactions=transactions_obj,
        portfolio=portfolio,
        portfolio_dict=portfolio_dict,
        total_dict=total_dict,
        entry_points=entry_points,
        historical_valuation=historical_valuation,
        figs_paths_stocks=figs_paths_stocks,
        figs_paths_stats=figs_paths_stats,
    )


def run_cli(args: Namespace) -> Union[int, Tuple]:
    cfg_file = args.cfg_file
    try:
        exec(cfg_file)
    except Exception as e_num:
        return int(e_num.__str__()), get_exception(int(e_num.__str__()))
    return 0


def run_api(cfg_file: os.PathLike) -> Union[int, Tuple]:
    try:
        exec(cfg_file)
    except Exception as e_num:
        return int(e_num.__str__()), get_exception(int(e_num.__str__()))
    return 0


if __name__ == '__main__':
    ret_tup = run_cli(parse_arguments())
    if isinstance(ret_tup, tuple):
        print(f'Exit text: {ret_tup[1]}')
        exit_code = ret_tup[0]
    else:
        exit_code = ret_tup
    print('Exit code:', exit_code)
    sys.exit(exit_code)
