import pathlib
from argparse import Namespace
from src.csv_mngr import CsvMngr
from src.portfolio import Portfolio
from src.transactions import Transactions
from src.cfg_mngr import CfgManager, Directories
from src.market_mngr import (MarketDataYahoo, Interval, MarketSymbol, YFinanceSymbMap,
                            convertSymbListToDicts, MarketDataGoogleLite, fetch_histories,
                            MarketDataGoogleFull, MarketReader)
from src.sheets_mngr import get_google_sheet
from src.utils import parse_arguments, check_internet, get_yaml_parameter
from src.csv_mngr import write_markdown_table, write_markdown_urls, write_csv_lazy
from src.plot import plot_combined, plot_monthly_stocks

def main(args: Namespace) -> None:
    is_quiet = args.is_quiet
    if not is_quiet:
        print("Checking for internet connection..")
    if not check_internet():
        if not is_quiet:
            print("Failed to connect.")
        return
    if not is_quiet:
        print("Connection exists.")
    cfg_obj = CfgManager()
    gen_dir = get_yaml_parameter('config/settings.yml', 'generation-dir')
    directories = Directories(base_dir=gen_dir)
    if get_yaml_parameter('config/settings.yml', 'use-sheet-of-sheets'):
        sheets_address = get_yaml_parameter('config/king-of-kings.yml')
    else:
        sheets_address = get_yaml_parameter('config/sheets.yml')
    cfg_obj.update_cfg(defCurrency=get_yaml_parameter("config/settings.yml",
                                                      "default-currency"))
    if not is_quiet:
        print(cfg_obj.get_cfg())
    transactions_file = get_google_sheet(sheets_address['transactions'],
                                         f'{directories.sheets_dir}',
                                         'transactions.csv')
    if not is_quiet:
        print('CSV file saved to: {}'.format(transactions_file))
    transactions_obj = Transactions()
    trans_csv_obj = CsvMngr(pathlib.Path(f'{transactions_file}'),
                      ["type", "date", "quantity", "fees", "price",
                       "currency", "symbol", "exchange", "platform",
                       "ex_rate", "ex_fees"])
    transactions_obj.add_list(trans_csv_obj.read())
    if not is_quiet:
        transactions_obj.print()
    symbols_of_interest = transactions_obj.get_symbols_of_interest()
    symbols_of_interest += [f'{cfg_obj.defCurrency.upper()}']
    if not is_quiet:
        print("Symbols of Interest: ", symbols_of_interest)
    history_variant = get_yaml_parameter('config/settings.yml', 'history-variant').lower()
    if get_yaml_parameter('config/settings.yml', 'market-data-origin').lower() == 'yahoo':
        start_date = transactions_obj.get_first_transaction_date()
        if not is_quiet:
            print("Start Date:", start_date)
        if history_variant == 'lite':
            market = MarketDataYahoo(tickers=symbols_of_interest, start_date=start_date, interval=Interval.WEEKLY, req_currency=cfg_obj.defCurrency)
        else:
            market = MarketDataYahoo(tickers=symbols_of_interest, start_date=start_date)
    elif get_yaml_parameter('config/settings.yml', 'market-data-origin').lower() == 'google':
        market_google_file = get_google_sheet(sheets_address['live-market-data'], f'{directories.market_data_dir}', 'market-google.csv')
        if not is_quiet:
            print('CSV file saved to: {}'.format(market_google_file))
        market_csv = MarketReader(market_google_file, symbols_of_interest)
        history_ret_status, history_ret = fetch_histories(sheets_address,
                                                          history_variant,
                                                          directories.history_dir,
                                                          symbols_of_interest, is_quiet)
        if history_variant == 'lite':
            market_history_obj = MarketDataGoogleLite(history_ret, cfg_obj.defCurrency)
        else:
            market_history_obj = MarketDataGoogleFull(history_ret, cfg_obj.defCurrency,
                                                      market_csv.get_usd_conversion_rate() \
                                                      if cfg_obj.defCurrency == 'USD' \
                                                      else market_csv.get_usd_conversion_rate()**-1)
    symbols_obj_list = []
    for symbol in symbols_of_interest:
        symbol_key = YFinanceSymbMap.tickerMap.get(symbol.lower())
        symbols_obj_list.append(MarketSymbol(symbol, market.history[symbol_key], market.current_price[symbol_key], market.currency[symbol_key]))
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
    # write_markdown_urls(pathlib.Path(f'{directories.gen_sheets_urls_file}'),
    #                     'Sheets URLs', sheets_urls)
    if not is_quiet:
        print("Files generated.")
    spending_list, profit_percent_list,\
        spending_percent_per_month_list, \
        symbols_list, pp_list, months_list = \
            portfolio.convert_dicts_to_lists()
    if not is_quiet:
        print("Generating plots..")
    plot_monthly_stocks(fig_path=f'{directories.gen_plots_history}',
                        data_dict=history_dict,
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