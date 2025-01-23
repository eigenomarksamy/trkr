import yaml
import socket
import pathlib
import argparse
from typing import Union, Optional
from src.cfg_mngr import CfgManager, Directories, Sheets
from src.portfolio import Portfolio
from src.transactions import Transactions
from src.market import (MarketReader, MarketHistoryFull,
                        MarketHistoryLite, fetch_histories)
from src.csv_mngr import (CsvMngr, write_markdown_table,
                          write_markdown_urls, write_csv_lazy)
from src.market import get_google_sheet
from src.plot import plot_combined, plot_monthly_stocks

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Tracker info')
    parser.add_argument('--quiet', '-q', action='store_true', dest='is_quiet',
                        help='Hide detailed output')
    return parser.parse_args()

def check_internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False

def get_yaml_parameter(yaml_path: pathlib.Path,
                       parameter: Optional[str]=None) -> Union[str, dict]:
    param_val = None
    param_dict = {}
    with open(yaml_path, 'r') as stream:
        try:
            param_dict = yaml.safe_load(stream)
            if parameter:
                param_val = param_dict[parameter]
        except yaml.YAMLError as exc:
            print(exc)
    if not parameter:
        return param_dict
    return param_val

def main(args: argparse.Namespace) -> None:
    is_quiet = args.is_quiet
    cfg_obj = CfgManager()
    transactions_obj = Transactions()
    gen_dir = get_yaml_parameter('config/settings.yml', 'generation-dir')
    directories = Directories(base_dir=gen_dir)
    if not is_quiet:
        print(f'Generation at: {gen_dir}')
    if get_yaml_parameter('config/settings.yml', 'use-sheet-of-sheets'):
        sheets_address = get_yaml_parameter('config/king-of-kings.yml')
    else:
        sheets_address = get_yaml_parameter('config/sheets.yml')
    sheets_obj = Sheets(sheets_address, get_yaml_parameter('config/settings.yml', 'use-sheet-of-sheets'))
    sheets_urls = sheets_obj.get_sheets_links()
    sheets_address = sheets_obj.get_sheets_ids()
    transactions_file = get_google_sheet(sheets_address['transactions'],
                                         f'{directories.sheets_dir}',
                                         'transactions.csv')
    if not is_quiet:
        print('CSV file saved to: {}'.format(transactions_file))
    trans_csv_obj = CsvMngr(pathlib.Path(f'{transactions_file}'),
                      ["type", "date", "quantity", "fees", "price",
                       "currency", "symbol", "exchange", "platform",
                       "ex_rate", "ex_fees"])
    cfg_obj.update_cfg(defCurrency=get_yaml_parameter("config/settings.yml", "default-currency"))
    cfg_obj.update_cfg(platformCfg=get_yaml_parameter("config/platforms.yml", "platforms"))
    if not is_quiet:
        print("Checking for internet connection..")
    if not check_internet():
        if not is_quiet:
            print("Failed to connect.")
        return
    if not is_quiet:
        print("Connection exists.")
    if not is_quiet:
        print(cfg_obj.get_cfg())
    transactions_obj.add_list(trans_csv_obj.read())
    if not is_quiet:
        transactions_obj.print()
    symbols_of_interest = transactions_obj.get_symbols_of_interest()
    if cfg_obj.defCurrency.lower() == 'eur':
        symbols_of_interest += ['USD']
    else:
        symbols_of_interest += ['EUR']
    if not is_quiet:
        print("Symbols of Interest: ", symbols_of_interest)
        print("Downloading Live Market Data..")
    market_google_file = get_google_sheet(sheets_address['live-market-data'], f'{directories.market_data_dir}', 'market-google.csv')
    if not is_quiet:
        print('CSV file saved to: {}'.format(market_google_file))
    market_csv = MarketReader(market_google_file, symbols_of_interest)
    if not market_csv.market_verification:
        if not is_quiet:
            print("Market data doesn't include all symbols of interest.")
            print("Missing symbols: ", market_csv.missing_symbols)
        return
    market_data_aligned = market_csv.align_data(cfg_obj.defCurrency, is_quiet)
    history_variant = get_yaml_parameter("config/settings.yml", "history-variant")
    history_ret_status, history_ret = fetch_histories(sheets_address,
                                                      history_variant,
                                                      directories.history_dir,
                                                      symbols_of_interest, is_quiet)
    if history_ret_status:
        if history_variant == 'lite':
            market_history_obj = MarketHistoryLite(history_ret, cfg_obj.defCurrency)
        else:
            market_history_obj = MarketHistoryFull(history_ret, cfg_obj.defCurrency,
                                                   market_csv.get_usd_conversion_rate() \
                                                    if cfg_obj.defCurrency == 'USD' \
                                                    else market_csv.get_usd_conversion_rate()**-1)
    else:
        if not is_quiet:
            print("Missing market history symbols: ", history_ret)
        return
    historical_data_dict = market_history_obj.get_historical_data()
    if not is_quiet:
        print(f'$1 = €{market_csv.get_usd_conversion_rate()}')
        print(f'€1 = ${1 / market_csv.get_usd_conversion_rate()}')
    portfolio = Portfolio(transactions_obj, market_data_aligned, is_quiet=is_quiet)
    portfolio_dict, total_dict = portfolio.calculate()
    historical_valuation = portfolio.compute_historical_valuation(historical_data_dict)
    entry_points = portfolio.get_entry_points_months()
    if not is_quiet:
        print("Generating files..")
    write_csv_lazy(pathlib.Path(f'{directories.gen_portfolio_file}'),
                   portfolio_dict, 'symbol')
    write_markdown_table(pathlib.Path(f'{directories.gen_total_file}'), 'Total',
                         'Metric', 'Value', total_dict)
    write_markdown_table(pathlib.Path(f'{directories.gen_entries_file}'), 'Entry Points',
                         'Symbol', 'Date', entry_points)
    write_markdown_urls(pathlib.Path(f'{directories.gen_sheets_urls_file}'),
                        'Sheets URLs', sheets_urls)
    if not is_quiet:
        print("Files generated.")
    spending_list, profit_percent_list,\
        spending_percent_per_month_list, \
        symbols_list, pp_list, months_list = \
            portfolio.convert_dicts_to_lists()
    if not is_quiet:
        print("Generating plots..")
    plot_monthly_stocks(fig_path=f'{directories.gen_plots_history}',
                        data_dict=historical_data_dict,
                        entry_points=entry_points)
    plot_combined(fig_path=f'{directories.gen_plots_stats}', nums_pie=spending_list,
                  nums_bar=profit_percent_list, nums_points=spending_percent_per_month_list,
                  nums_points_1=list(historical_valuation.values()),
                  labels_pie=symbols_list,
                  labels_bar=pp_list, labels_points=months_list,
                  labels_points_1=list(historical_valuation.keys()),
                  points_title='Spending Per Month',
                  points1_title='Valuation Percent',
                  pie_title='Spending Percent',
                  bar_title='Profit Percent')
    if not is_quiet:
        print(f"Exit. Check {directories.base_dir} for information.")

if __name__ == '__main__':
    main(parse_arguments())
