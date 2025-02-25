import os
import sys
import pathlib
from argparse import Namespace
from datetime import datetime
from typing import Union, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from src.portfolio import Portfolio
from src.transactions import build_transactions_object
from src.cfg_mngr import Directories, create_cfg, ConfigMapUri
from src.market_mngr import MarketDataYahoo, Interval, MarketSymbol
from src.market_mngr import get_yfinance_map, convertSymbListToDicts, get_yfinance_map_local
from src.utils import parse_arguments, check_internet, get_exception
from src.csv_mngr import write_markdown_table, write_csv_lazy
from src.plot import plot_combined, plot_monthly_stocks
from src.log_mngr import LogManager

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
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'report_template.html'
    template_file.write_text("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Report</title>
    </head>
    <body>
    <h1>Portfolio Report</h1>
    <p>All values are in {{ default_currency }}.</p>
    <h2>Total</h2>
    {{ total | safe }}
    <h2>Symbols Map</h2>
    {{ symbols_map | safe }}
    <h2>Entry Points</h2>
    {{ entries | safe }}
    <h2>Portfolio</h2>
    {{ portfolio | safe }}
    <table>
        <thead>
            <tr>
                <th>Exchange</th>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Average Price</th>
                <th>Current Price</th>
                <th>Value</th>
                <th>Profit/Loss</th>
                <th>Profit (%)</th>
                <th>Price 25%</th>
                <th>Price 50%</th>
                <th>Price 75%</th>
                <th>Price 100%</th>
                <th>Price 150%</th>
            </tr>
        </thead>
        <tbody>
            {% for symbol, data in portfolio_dict.items() %}
            <tr>
                <td>{{ data['exchange' ]}} </td>
                <td>{{ symbol }}</td>
                <td>{{ '%.4f' % data['amount'] }}</td>
                <td>{{ '%.4f' % data['break_even_price'] }}</td>
                <td>{{ '%.4f' % data['current_price'] }}</td>
                <td>{{ '%.4f' % data['value'] }}</td>
                <td>{{ '%.4f' % data['profit_net'] }}</td>
                <td>{{ '%.4f' % data['profit_percent'] }}</td>
                <td>{{ '%.4f' % data['price25'] }}</td>
                <td>{{ '%.4f' % data['price50'] }}</td>
                <td>{{ '%.4f' % data['price75'] }}</td>
                <td>{{ '%.4f' % data['price100'] }}</td>
                <td>{{ '%.4f' % data['price150'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <h2>Plots</h2>
    <div>
        <h3>Statistics Plots</h3>
        {% for plot in plots_stats %}
            <img src="{{ plot | abs }}" alt="Statistics Plot">
        {% endfor %}
    </div>
    <div>
        <h3>Historical Plots</h3>
        {% for plot in plots_history %}
            <img src="{{ plot | abs }}" alt="Historical Plot">
        {% endfor %}
    </div>
    </body>
    </html>
    """)
    total_html = ''
    for it in total_dict:
        total_html += f'{it.replace("_", " ").capitalize()}: {total_dict[it]}<br>'
    entries_html = ''
    for entry in entry_points:
        entries_html += f'{entry}: {entry_points[entry].capitalize()}<br>'
    sym_map_html = ''
    for sym in yfinance_map_obj.tickerMap:
        sym_map_html += f'{sym}: {yfinance_map_obj.tickerMap[sym]}<br>'
    env = Environment(loader=FileSystemLoader('templates'))
    env.filters['abs'] = lambda x: pathlib.Path(x).absolute().as_uri()
    template = env.get_template('report_template.html')
    html_report = template.render(
        total=total_html,
        default_currency=cfg.get_param(ConfigMapUri.DEFAULT_CURRENCY),
        portfolio_dict=portfolio_dict,
        symbols_map=sym_map_html,
        entries=entries_html,
        plots_history=figs_paths_stocks[::-1],
        plots_stats=figs_paths_stats
    )
    report_path = pathlib.Path(f'{directories.base_dir}/report.html')
    report_path.write_text(html_report)
    if not is_quiet:
        print(f"HTML report generated at {report_path}")

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

