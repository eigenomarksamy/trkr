import pathlib
from os import PathLike
from typing import Optional

from jinja2 import Environment, FileSystemLoader


def generate_misc_tables_html(
    symbols_map: str, entry_points: str, historical_valuation: str, output_path: PathLike
) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'misc_tables_template.html'
    template_file.write_text(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Misc Tables Report</title>
    </head>
    <body>
    <h1>Historical Valuation</h1>
    {{ historical_valuation | safe }}
    <h1>Symbols Map</h1>
    {{ symbols_map | safe }}
    <h1>Entry Points</h1>
    {{ entry_points | safe }}
    </body>
    </html>
    """,
        encoding='utf-8',
    )
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('misc_tables_template.html')
    html_report = template.render(
        symbols_map=symbols_map,
        entry_points=entry_points,
        historical_valuation=historical_valuation,
    )
    report_path = pathlib.Path(f'{output_path}misc_tables.html')
    report_path.write_text(html_report, encoding='utf-8')


def generate_transactions_html(transactions: list[dict], output_path: PathLike) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'transactions_template.html'
    template_file.write_text(
        """
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
    """,
        encoding='utf-8',
    )
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('transactions_template.html')
    html_report = template.render(transactions=transactions)
    report_path = pathlib.Path(f'{output_path}transactions.html')
    report_path.write_text(html_report, encoding='utf-8')


def generate_historical_report(figs_historical: list[PathLike], output_path: PathLike) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'historical_template.html'
    template_file.write_text(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historical Plots</title>
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
    """,
        encoding='utf-8',
    )
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('historical_template.html')
    html_report = template.render(
        plots_history=[str(pathlib.Path(plot).absolute()) for plot in figs_historical]
    )
    report_path = pathlib.Path(f'{output_path}figs_historical.html')
    report_path.write_text(html_report, encoding='utf-8')


def generate_projection_html(headers: list[str], rows: list[list], output_path: PathLike) -> None:
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'projection_template.html'
    template_file.write_text(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Net-worth Projection</title>
    </head>
    <body>
    <h1>Net-worth Projection</h1>
    <table>
        <thead>
            <tr>
                {% for header in headers %}
                <th>{{ header }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr>
                {% for cell in row %}
                <td>{{ '%.2f' % cell if cell is float else cell }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </body>
    </html>
    """,
        encoding='utf-8',
    )
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('projection_template.html')
    html_report = template.render(headers=headers, rows=rows)
    report_path = pathlib.Path(f'{output_path}projection.html')
    report_path.write_text(html_report, encoding='utf-8')


def generate_html_report(
    total_dict: dict,
    entry_points: dict,
    portfolio_dict: dict,
    ticker_map: dict,
    def_currency: str,
    figs_paths_stocks: list[PathLike],
    figs_paths_stats: list[PathLike],
    transactions_list: list,
    historical_valuation: dict,
    req_path: PathLike,
    sub_dir: PathLike,
    title: str = 'Portfolio Report',
    imaginary_portfolios: Optional[list[dict]] = None,
    projection: Optional[dict] = None,
) -> None:
    generate_transactions_html(transactions_list, sub_dir)
    if projection:
        generate_projection_html(projection['headers'], projection['rows'], sub_dir)
    generate_historical_report(figs_paths_stocks[1:], sub_dir)
    entries_html = ''
    for entry in entry_points:
        entries_html += f'{entry}: {entry_points[entry].capitalize()}<br>'
    sym_map_html = ''
    for sym in ticker_map:
        sym_map_html += f'{sym}: {ticker_map[sym]}<br>'
    historical_valuation_html = ''
    for hv in historical_valuation.keys():
        historical_valuation_html += f'{hv}: {historical_valuation[hv]}<br>'
    generate_misc_tables_html(sym_map_html, entries_html, historical_valuation_html, sub_dir)
    template_dir = pathlib.Path('templates')
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / 'report_template.html'
    template_file.write_text(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    </head>
    <body>
    <h1>{{ title }}</h1>
    <p>All values are in {{ default_currency }}.</p>
    <h2>Total</h2>
    {{ total | safe }}
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
    {% if imaginary_portfolios %}
    <h2>Imaginary Portfolios</h2>
    <table>
        <thead>
            <tr>
                <th>Portfolio</th>
                <th>Invested</th>
                <th>Value</th>
                <th>Profit/Loss</th>
                <th>Profit (%)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Real portfolio</td>
                <td>{{ '%.2f' % total_dict['spending'] }}</td>
                <td>{{ '%.2f' % total_dict['value'] }}</td>
                <td>{{ '%.2f' % total_dict['profit_net'] }}</td>
                <td>{{ '%.2f' % total_dict['profit_percent'] }}</td>
            </tr>
            {% for imaginary in imaginary_portfolios %}
            <tr>
                <td><a href="{{ imaginary['report'] | abs }}">{{ imaginary['name'] }}</a></td>
                <td>{{ '%.2f' % imaginary['total']['spending'] }}</td>
                <td>{{ '%.2f' % imaginary['total']['value'] }}</td>
                <td>{{ '%.2f' % imaginary['total']['profit_net'] }}</td>
                <td>{{ '%.2f' % imaginary['total']['profit_percent'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    {% if projection %}
    {% set cfg = projection['cfg'] %}
    {% set last = projection['last'] %}
    <h2>Net-worth Projection</h2>
    <p>
        Starting from {{ '%.2f' % projection['start_value'] }}: {{ projection['start_label'] }}.
        In {{ last.year }}, at age {{ last.age }}, net worth reaches {{ '%.2f' % last.net_worth_before_fees }},
        or {{ '%.2f' % last.net_worth_after_fees }} after fees{% if last.net_worth_real is not none %}
        ({{ '%.2f' % last.net_worth_real }} in today's money){% endif %}.
    </p>
    <table>
        <tbody>
            <tr><td>Yearly return</td><td>{{ cfg.yearly_return }}%</td></tr>
            <tr><td>Fees</td><td>{{ cfg.fees }}%</td></tr>
            <tr><td>Income</td><td>{{ '%.2f' % cfg.income }}, growing {{ cfg.income_growth }}% a year</td></tr>
            <tr><td>Invested</td><td>{{ cfg.invest_percent }}% of income</td></tr>
            {% if cfg.inflation is not none %}
            <tr><td>Inflation</td><td>{{ cfg.inflation }}%</td></tr>
            {% endif %}
            {% for year, amount in cfg.deposits_withdrawals.items() %}
            <tr><td>{{ 'Deposit' if amount >= 0 else 'Withdrawal' }} in {{ year }}</td><td>{{ '%.2f' % amount }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    <p>
        Assumed contribution in the first year: {{ '%.2f' % projection['contribution'] }}.
        Actually bought in the last 12 months: {{ '%.2f' % projection['invested_last_12_months'] }}.
    </p>
    <img src="{{ projection['fig'] | abs }}" alt="Net-worth Projection">
    <br>
    <a href="{{ projection_report_dir | abs }}">View Projection Table</a>
    {% endif %}
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
        <br>
        <a href="{{ history_report_dir | abs }}">View Stocks History</a>
    </div>
    <h2>Transactions</h2>
    <a href="{{ trans_report_dir | abs }}">View Transactions Report</a>
    <h2>Misc Tables</h2>
    <a href="{{ misc_tables_report_dir | abs }}">View Misc Tables Report</a>
    </body>
    </html>
    """,
        encoding='utf-8',
    )
    total_html = ''
    for it in total_dict:
        total_html += f'{it.replace("_", " ").capitalize()}: {total_dict[it]}<br>'
    env = Environment(loader=FileSystemLoader('templates'))
    env.filters['abs'] = lambda x: pathlib.Path(x).absolute().as_uri()
    template = env.get_template('report_template.html')
    html_report = template.render(
        title=title,
        total_dict=total_dict,
        imaginary_portfolios=imaginary_portfolios,
        projection=projection,
        projection_report_dir=f'{sub_dir}projection.html',
        total=total_html,
        default_currency=def_currency,
        portfolio_dict=portfolio_dict,
        history_report_dir=f'{sub_dir}figs_historical.html',
        overview_history_fig=figs_paths_stocks[0],
        plots_stats=figs_paths_stats,
        trans_report_dir=f'{sub_dir}transactions.html',
        misc_tables_report_dir=f'{sub_dir}misc_tables.html',
    )
    report_path = pathlib.Path(req_path)
    report_path.write_text(html_report, encoding='utf-8')
