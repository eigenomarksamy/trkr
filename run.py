import os
import sys
import pathlib
from argparse import Namespace
from datetime import datetime
from typing import Union, Tuple, Optional
from src.portfolio_mngr import Portfolio
from src.market_mngr import MarketDataYahoo, Interval, MarketSymbol
from src.cfg_mngr import Directories, ConfigMapUri
from src.log_mngr import LogManager
from src.cfg_mngr import create_cfg
from src.transactions import build_transactions_object
from src.market_mngr import get_yfinance_map, convertSymbListToDicts, get_yfinance_map_local
from src.utils import parse_arguments, check_internet, get_exception
from src.csv_mngr import write_markdown_table, write_csv_lazy
from src.plot_mngr import plot_combined, plot_monthly_stocks
from src.report_mngr import generate_html_report

def exec(cfg_file: os.PathLike, quiet_arg: Optional[bool],
         log_level: Optional[str]) -> None:
    is_quiet = quiet_arg if quiet_arg is not None else True
    cfg = create_cfg(cfg_file)
    directories = Directories(base_dir=cfg.get_param(ConfigMapUri.GENERATION_DIRECTORY),
                            log_dir=cfg.get_param(ConfigMapUri.LOG_DIRECTORY),
                            local_trans_dir=cfg.get_param(ConfigMapUri.TRANSACTIONS_DIRECTORY) \
                                if cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local' \
                                    else None,
                            local_map_dir=cfg.get_param(ConfigMapUri.SYMBOLS_MAP_DIRECTORY) \
                                if cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'local' \
                                    else None)
    logger = None
    if log_level:
        log_manager = LogManager(log_file=f'{directories.log_dir}app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                                log_level=log_level)
        logger = log_manager.get_logger()
    if not check_internet():
        if logger:
            logger.error('Failed to connect.')
        if not is_quiet:
            print("Failed to connect.")
        raise Exception("503")
    if not is_quiet:
        print("Connection exists.")
    if logger:
        logger.info('Connection exists.')
    if cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'cloud':
        trans_sheets = cfg.get_param(ConfigMapUri.TRANSACTIONS_SHEET)
    else:
        trans_sheets = cfg.get_param(ConfigMapUri.TRANSACTIONS_DIRECTORY)
    if not is_quiet:
        print(cfg.print())
    if logger:
        logger.info(cfg.to_str())
    yfinance_map_obj = None
    if cfg.get_param(ConfigMapUri.SYMBOLS_STANDARD) == 'custom':
        if cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'cloud':
            yfinance_map_obj = get_yfinance_map(cfg.get_param(ConfigMapUri.SYMBOLS_MAP_SHEET),
                                                f'{directories.sheets_dir}')
        else:
            yfinance_map_obj = get_yfinance_map_local(cfg.get_param(ConfigMapUri.SYMBOLS_MAP_DIRECTORY))
        if not is_quiet:
            print("Yahoo Finance Ticker map:")
            print(yfinance_map_obj.tickerMap)
    transactions_obj = build_transactions_object(True if cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local' else False,
                                                 trans_sheets,
                                                 f'{directories.sheets_dir}',
                                                 is_quiet, yfinance_map_obj.tickerMap)
    if not is_quiet:
        transactions_obj.print()
    symbols_of_interest = transactions_obj.get_symbols_of_interest()
    if yfinance_map_obj:
        symbols_of_interest += [f'{yfinance_map_obj.tickerMap.get(cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY).lower())}']
    else:
        symbols_of_interest += [f'{cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY)}']
    if not is_quiet:
        print("Symbols of Interest: ", symbols_of_interest)
    history_variant = cfg.get_param(ConfigMapUri.HISTORY_VARIANT)
    if history_variant == 'full':
        if not is_quiet:
            print("WARNING! Full history variant is not recommended.")
    if cfg.get_param(ConfigMapUri.MARKET_ORIGIN) == 'yahoo':
        start_date = transactions_obj.get_first_transaction_date()
        if not is_quiet:
            print("Start Date:", start_date)
        market = MarketDataYahoo(tickers=symbols_of_interest,
                                 ticker_map=yfinance_map_obj,
                                 start_date=start_date,
                                 interval=Interval.WEEKLY \
                                    if history_variant == 'lite' \
                                    else Interval.DAILY,
                                 req_currency=cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY))
    else:
        if cfg.get_param(ConfigMapUri.MARKET_ORIGIN)  == 'google':
            raise Exception("299")
        else:
            raise Exception("417")
    symbols_obj_list = []
    for symbol in symbols_of_interest:
        symbol_key = symbol
        symbols_obj_list.append(MarketSymbol(symbol, market.history[symbol_key],
                                             market.current_price[symbol_key],
                                             market.currency[symbol_key]))
    if not is_quiet:
        for symbol in symbols_obj_list:
            symbol.print()
    prices_dict, history_dict = convertSymbListToDicts(symbols_obj_list)
    portfolio = Portfolio(transactions_obj, prices_dict, is_quiet=is_quiet)
    portfolio_dict, total_dict = portfolio.calculate()
    historical_valuation = portfolio.compute_historical_valuation(history_dict)
    entry_points = portfolio.get_entry_points_months()
    if not is_quiet:
        print("Historical Evaluation Dict:")
        for hv in historical_valuation.keys():
            print('\t', hv, historical_valuation[hv])
        print("Entries Dict:")
        for ep in entry_points.keys():
            print('\t', ep, entry_points[ep])
    if not is_quiet:
        print("Generating files..")
    write_csv_lazy(pathlib.Path(f'{directories.gen_portfolio_file}'),
                   portfolio_dict, 'symbol')
    write_markdown_table(pathlib.Path(f'{directories.gen_total_file}'), 'Total',
                         'Metric', 'Value', total_dict)
    write_markdown_table(pathlib.Path(f'{directories.gen_entries_file}'), 'Entry Points',
                         'Symbol', 'Date', entry_points)
    if not is_quiet:
        print("Files generated.")
    spending_list, profit_percent_list,\
        spending_percent_per_month_list, \
        symbols_list, pp_list, months_list = \
            portfolio.convert_dicts_to_lists()
    if not is_quiet:
        print("Generating plots..")
    figs_paths_stocks = plot_monthly_stocks(fig_path=f'{directories.gen_plots_history}',
                                     data_dict=history_dict,
                                     entry_points=entry_points)
    figs_paths_stats = plot_combined(fig_path=f'{directories.gen_plots_stats}',
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
                                    bar_title='Profit Percent')
    if not is_quiet:
        print(f"Check {directories.base_dir} for information.")
    if not is_quiet:
        print("Generating HTML report..")
    generate_html_report(total_dict=total_dict,
                         entry_points=entry_points,
                         portfolio_dict=portfolio_dict,
                         ticker_map=yfinance_map_obj.tickerMap,
                         def_currency=cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
                         figs_paths_stocks=figs_paths_stocks[::-1],
                         figs_paths_stats=figs_paths_stats,
                         req_path=f'{directories.base_dir}report.html')
    if not is_quiet:
        print(f'HTML report generated at {f"{directories.base_dir}report.html"}')

def run_cli(args: Namespace) -> Union[int, Tuple]:
    is_quiet = args.is_quiet
    log_level = args.log_level.upper()
    cfg_file = args.cfg_file
    try:
        exec(cfg_file, is_quiet, log_level)
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
        print(f"Exit text: {ret_tup[1]}")
        exit_code = ret_tup[0]
    else:
        exit_code = ret_tup
    print("Exit code:", exit_code)
    sys.exit(exit_code)
