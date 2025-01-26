import pathlib
from argparse import Namespace
from src.csv_mngr import CsvMngr
from src.portfolio import Portfolio
from src.transactions import Transactions
from src.cfg_mngr import CfgManager, Directories
from src.market_mngr import (MarketDataYahoo, Interval, MarketSymbol,
                             YFinanceSymbMap, convertSymbListToDicts)
from src.sheets_mngr import get_google_sheet
from src.utils import parse_arguments, check_internet, get_yaml_parameter
from src.csv_mngr import write_markdown_table, write_csv_lazy
from src.plot import plot_combined, plot_monthly_stocks
from jinja2 import Environment, FileSystemLoader

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
    sheets_address = get_yaml_parameter('config/sheets.yml')
    cfg_obj.update_cfg(defCurrency=get_yaml_parameter("config/settings.yml",
                                                      "default-currency"))
    if not is_quiet:
        print(cfg_obj.get_cfg())
    yfinance_map_file = get_google_sheet(sheets_address['yfinance-map'],
                                         f'{directories.sheets_dir}',
                                         'yfinance-map.csv')
    yfinance_map_csv_obj = CsvMngr(pathlib.Path(f'{yfinance_map_file}'),
                                   ["symbol", "ticker"])
    yfinance_map_obj = YFinanceSymbMap(CsvMngr.convert_read_list_to_dict(yfinance_map_csv_obj.read()))
    if not is_quiet:
        print("Yahoo Finance Ticker map:")
        print(yfinance_map_obj.tickerMap)
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
    if history_variant == 'full':
        if not is_quiet:
            print("WARNING! Full history variant is not recommended.")
    if get_yaml_parameter('config/settings.yml', 'market-data-origin').lower() == 'yahoo':
        start_date = transactions_obj.get_first_transaction_date()
        if not is_quiet:
            print("Start Date:", start_date)
        market = MarketDataYahoo(tickers=symbols_of_interest,
                                 ticker_map=yfinance_map_obj,
                                 start_date=start_date,
                                 interval=Interval.WEEKLY \
                                    if history_variant == 'lite' \
                                    else Interval.DAILY,
                                 req_currency=cfg_obj.defCurrency)
    else:
        if get_yaml_parameter('config/settings.yml', 'market-data-origin').lower() == 'google':
            raise Exception("Google origin is deprecated.")
        else:
            raise Exception("Not supported market origin.")
    symbols_obj_list = []
    for symbol in symbols_of_interest:
        symbol_key = yfinance_map_obj.tickerMap.get(symbol.lower())
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
        print(f"Exit. Check {directories.base_dir} for information.")
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
    env = Environment(loader=FileSystemLoader('templates'))
    env.filters['abs'] = lambda x: pathlib.Path(x).absolute().as_uri()
    template = env.get_template('report_template.html')
    html_report = template.render(
        total=total_html,
        default_currency=cfg_obj.defCurrency,
        portfolio_dict=portfolio_dict,
        entries=entries_html,
        plots_history=figs_paths_stocks[::-1],
        plots_stats=figs_paths_stats
    )
    report_path = pathlib.Path(f'{directories.base_dir}/report.html')
    report_path.write_text(html_report)
    if not is_quiet:
        print(f"HTML report generated at {report_path}")

if __name__ == '__main__':
    main(parse_arguments())