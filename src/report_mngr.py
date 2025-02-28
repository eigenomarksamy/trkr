import pathlib
from os import PathLike
from jinja2 import Environment, FileSystemLoader

def generate_transactions_html(transactions: list[dict],
                               output_path: PathLike) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'transactions_template.html'
    template_file.write_text("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transactions Report</title>
    </head>
    <body>
    <h1>Transactions Report</h1>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Exchange</th>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Platform</th>
            </tr>
        </thead>
        <tbody>
            {% for transaction in transactions %}
            <tr>
                <td>{{ transaction['date'] }}</td>
                <td>{{ transaction['type'] }}</td>
                <td>{{ transaction['exchange'] }}</td>
                <td>{{ transaction['symbol'] }}</td>
                <td>{{ '%.4f' % transaction['quantity'] }}</td>
                <td>{{ '%.4f' % transaction['price'] }}</td>
                <td>{{ transaction['wallet'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </body>
    </html>
    """)
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('transactions_template.html')
    html_report = template.render(transactions=transactions)
    report_path = pathlib.Path(f'{output_path}transactions.html')
    report_path.write_text(html_report)

def generate_historical_report(figs_historical: list[PathLike],
                               output_path: PathLike) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'historical_template.html'
    template_file.write_text("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plots</title>
    </head>
    <body>
    <h1>Historical Plots</h1>
    <div>
        {% for plot in plots_history %}
            <img src="{{ plot }}" alt="Historical Plot">
        {% endfor %}
    </div>
    </body>
    </html>
    """)
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('historical_template.html')
    html_report = template.render(plots_history=[str(pathlib.Path(plot).absolute()) for plot in figs_historical])
    report_path = pathlib.Path(f'{output_path}figs_historical.html')
    report_path.write_text(html_report)

def generate_html_report(total_dict: dict, entry_points: dict,
                         portfolio_dict: dict, ticker_map: dict,
                         def_currency: str, figs_paths_stocks: list[PathLike],
                         figs_paths_stats: list[PathLike],
                         transactions_list: list, req_path: PathLike,
                         sub_dir: PathLike) -> None:
    generate_transactions_html(transactions_list, sub_dir)
    generate_historical_report(figs_paths_stocks[1:], sub_dir)
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
        <img src="{{ overview_history_fig | abs }}" alt="Combined Monthly Stocks"/>
        <a href="{{ history_report_dir | abs }}">View Stocks History</a>
    </div>
    <h2>Transactions</h2>
    <a href="{{ trans_report_dir | abs }}">View Transactions Report</a>
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
    for sym in ticker_map:
        sym_map_html += f'{sym}: {ticker_map[sym]}<br>'
    env = Environment(loader=FileSystemLoader('templates'))
    env.filters['abs'] = lambda x: pathlib.Path(x).absolute().as_uri()
    template = env.get_template('report_template.html')
    html_report = template.render(
        total=total_html,
        default_currency=def_currency,
        portfolio_dict=portfolio_dict,
        symbols_map=sym_map_html,
        entries=entries_html,
        history_report_dir=f'{sub_dir}figs_historical.html',
        overview_history_fig=figs_paths_stocks[0],
        plots_stats=figs_paths_stats,
        trans_report_dir=f'{sub_dir}transactions.html'
    )
    report_path = pathlib.Path(req_path)
    report_path.write_text(html_report)
