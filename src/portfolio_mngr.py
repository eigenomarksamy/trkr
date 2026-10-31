import math
from datetime import date, datetime
from typing import Tuple

from dateutil.relativedelta import relativedelta

from src.transactions import Transactions, input_error

# Price target -> multiple of the break-even price.
PRICE_TARGETS = {
    'price25': 1.25,
    'price50': 1.50,
    'price75': 1.75,
    'price100': 2.00,
    'price150': 2.50,
}

# A holding's figures, in the order portfolio.csv lists them.
HOLDING_COLUMNS = [
    'exchange',
    'amount',
    'value',
    'spending',
    'spending_percent',
    'profit_net',
    'profit_percent',
    'current_price',
    'break_even_price',
    *PRICE_TARGETS,
    'realized_profit',
]


class Portfolio:
    def __init__(
        self, transactions: Transactions, market_data: dict, is_quiet: bool = False
    ) -> None:
        self.transactions = transactions
        self.portfolio = {}
        self.total = {
            'value': 0,
            'spending': 0,
            'profit_net': 0,
            'profit_percent': 0,
            'realized_profit': 0,
            'cash_out': 0,
            'time_interval_days': 0,
            'time_interval_months': 0,
            'time_interval_years': 0,
            'avg_day_roi': 0,
            'avg_month_roi': 0,
            'avg_year_roi': 0,
        }
        self.market_data = market_data
        self.wallet_fees = {}
        self.is_quiet = is_quiet

    def calculate(self) -> Tuple[dict, dict]:
        symbols_dict = {}
        # Average cost depends on the order of the trades, so walk them by date. The sort is
        # stable: trades on the same day keep their order in the sheet.
        for transaction in sorted(self.transactions.get(), key=lambda t: t.date):
            transaction = transaction.__dict__()
            if transaction['symbol'] not in symbols_dict:
                symbols_dict[transaction['symbol']] = dict.fromkeys(HOLDING_COLUMNS, 0) | {
                    'exchange': f'{transaction["exchange"]}'
                }
            holding = symbols_dict[transaction['symbol']]
            if transaction['type'] == 'buy':
                holding['amount'] += transaction['quantity']
                holding['spending'] += (
                    transaction['price'] * transaction['quantity']
                    + transaction['fees']
                    + transaction['ex_fees']
                ) / transaction['ex_rate']
            elif transaction['type'] == 'sell':
                held = holding['amount']
                # Selling all of 0.1 + 0.2 bought sells 0.3, which is not quite the sum.
                if math.isclose(transaction['quantity'], held, rel_tol=1e-9):
                    cost = holding['spending']
                    holding['amount'] = 0
                elif transaction['quantity'] < held:
                    cost = holding['spending'] * transaction['quantity'] / held
                    holding['amount'] -= transaction['quantity']
                else:
                    raise input_error(
                        f'the sell of {transaction["quantity"]} {transaction["symbol"]} '
                        + f'on {transaction["date"]} is more than the {held} held.'
                    )
                holding['spending'] -= cost
                proceeds = (
                    transaction['price'] * transaction['quantity']
                    - transaction['fees']
                    - transaction['ex_fees']
                ) / transaction['ex_rate']
                holding['realized_profit'] += proceeds - cost

        for symbol, holding in symbols_dict.items():
            self.total['realized_profit'] += holding['realized_profit']
            if holding['amount'] == 0:
                continue
            holding['current_price'] = self.market_data[symbol]['price']
            holding['value'] = holding['amount'] * holding['current_price']
            holding['break_even_price'] = holding['spending'] / holding['amount']
            holding['profit_net'] = holding['value'] - holding['spending']
            holding['profit_percent'] = (
                holding['profit_net'] / holding['spending'] * 100 if holding['spending'] != 0 else 0
            )
            for target, factor in PRICE_TARGETS.items():
                holding[target] = holding['break_even_price'] * factor
            self.portfolio[symbol] = holding
            self.total['value'] += holding['value']
            self.total['spending'] += holding['spending']

        for holding in self.portfolio.values():
            holding['spending_percent'] = (
                holding['spending'] / self.total['spending'] * 100
                if self.total['spending'] != 0
                else 0
            )

        if not self.is_quiet:
            for p in self.portfolio:
                print(f'{p}:')
                for pp in self.portfolio[p]:
                    print(f'\t{pp}: {self.portfolio[p][pp]}')
        self.total['profit_net'] = self.total['value'] - self.total['spending']
        self.total['profit_percent'] = (
            (self.total['profit_net'] / self.total['spending']) * 100
            if self.total['spending'] != 0
            else 0
        )
        self.total['cash_out'] = self.total['value'] * 0.95
        transaction_dates = [
            datetime.strptime(transaction.__dict__()['date'], '%Y-%m-%d')
            for transaction in self.transactions.get()
        ]
        if transaction_dates:
            min_date = min(transaction_dates)
            max_date = datetime.today()
            self.total['time_interval_days'] = (max_date - min_date).days
            self.total['time_interval_months'] = self.total['time_interval_days'] / 30
            self.total['time_interval_years'] = self.total['time_interval_days'] / 365

        if self.total['time_interval_days'] > 0:
            self.total['avg_day_roi'] = (
                self.total['profit_percent'] / self.total['time_interval_days']
            )
            self.total['avg_month_roi'] = self.total['avg_day_roi'] * 30
            self.total['avg_year_roi'] = self.total['avg_day_roi'] * 365

        if not self.is_quiet:
            print('Portfolio:')
            for tot in self.total:
                print(f'\t\t{tot.capitalize()}: ', self.total[tot])
        return self.portfolio, self.total

    def compute_spending_history(self) -> dict:
        ret_dict = {}
        loc_trans = self.transactions.get()
        loc_trans.sort(key=lambda x: x.__dict__()['date'])
        first_date = datetime.strptime(loc_trans[0].__dict__()['date'], '%Y-%m-%d').date()
        last_date = datetime.strptime(loc_trans[-1].__dict__()['date'], '%Y-%m-%d').date()
        # Step over month starts, or a last day of the month earlier than the first is skipped.
        date_tmp = first_date.replace(day=1)
        while date_tmp <= last_date:
            month_transactions = []
            ret_dict[convert_date_to_short_str(date=date_tmp)] = 0
            month_transactions = self.transactions.get_transactions_month(date_tmp)
            for transaction in month_transactions:
                if transaction['type'] == 'buy':
                    spending = (
                        transaction['price'] * transaction['quantity']
                        + transaction['fees']
                        + transaction['ex_fees']
                    ) / transaction['ex_rate']
                    ret_dict[convert_date_to_short_str(date=date_tmp)] += spending
            date_tmp += relativedelta(months=1)
        return ret_dict

    def get_entry_points_months(self) -> dict:
        entry_points = {}
        loc_trans = self.transactions.get()
        loc_trans.sort(key=lambda x: x.__dict__()['date'])
        for transaction in loc_trans:
            transaction = transaction.__dict__()
            if transaction['symbol'] not in entry_points and transaction['type'] == 'buy':
                entry_points[transaction['symbol']] = convert_date_to_short_str(
                    date=datetime.strptime(transaction['date'], '%Y-%m-%d').date()
                )
        return entry_points

    def compute_historical_valuation(self, historical_dict: dict) -> dict:
        """The market value of the holdings at the end of each month, up to this month.

        A month is priced at its last close in historical_dict, which is keyed by month (lite)
        or by day (full). A month without a close takes the close before it, or else today's
        price.
        """
        month_closes = {
            symbol: {
                convert_date_to_short_str(date=history_key_date(key)): point['price']
                for key, point in history.items()
            }
            for symbol, history in historical_dict.items()
        }
        ret_data = {}
        loc_trans = self.transactions.get()
        loc_trans.sort(key=lambda x: x.__dict__()['date'])
        held = {}
        last_close = {}
        next_trade = 0
        date_itr = datetime.strptime(loc_trans[0].date, '%Y-%m-%d').date().replace(day=1)
        while date_itr <= datetime.today().date():
            month = convert_date_to_short_str(date=date_itr)
            month_end = (date_itr + relativedelta(months=1, days=-1)).strftime('%Y-%m-%d')
            while next_trade < len(loc_trans) and loc_trans[next_trade].date <= month_end:
                trade = loc_trans[next_trade]
                if trade.type == 'buy':
                    held[trade.symbol] = held.get(trade.symbol, 0) + trade.quantity
                elif trade.type == 'sell':
                    held[trade.symbol] = held.get(trade.symbol, 0) - trade.quantity
                next_trade += 1
            for symbol, closes in month_closes.items():
                if month in closes:
                    last_close[symbol] = closes[month]
            ret_data[month] = sum(
                quantity
                * (
                    last_close[symbol]
                    if symbol in last_close
                    else self.market_data[symbol]['price']
                )
                for symbol, quantity in held.items()
            )
            date_itr += relativedelta(months=1)
        return ret_data

    def convert_dicts_to_lists(self) -> Tuple[list, list, list, list, list, list]:
        spending_list = []
        profit_percent_list = []
        symbols_list = []
        for entry in self.portfolio:
            spending_list.append(self.portfolio[entry]['spending_percent'])
            profit_percent_list.append(self.portfolio[entry]['profit_percent'])
            symbols_list.append(entry)
        profit_percent_list.append(self.total['profit_percent'])
        pp_list = symbols_list.copy()
        pp_list.append('Total')
        spending_dict = self.compute_spending_history()
        months_list = [month for month in spending_dict.keys()]
        spending_per_month_list = [spending_dict[month] for month in spending_dict.keys()]
        spending_percent_per_month_list = [
            100 * euros / sum(spending_per_month_list) for euros in spending_per_month_list
        ]
        return (
            spending_list,
            profit_percent_list,
            spending_percent_per_month_list,
            symbols_list,
            pp_list,
            months_list,
        )


def history_key_date(key: str) -> date:
    """The day a price-history key stands for.

    Full (daily) history is keyed YYYY-MM-DD. Lite history is keyed by month keys like 'jan24',
    which stand for the 1st of their month.
    """
    try:
        return datetime.strptime(key, '%Y-%m-%d').date()
    except ValueError:
        month = [convert_date_to_short_str(month=m) for m in range(1, 13)].index(key[:3]) + 1
        return date(2000 + int(key[3:]), month, 1)


def convert_date_to_short_str(**kwargs) -> str:
    months = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
    ]
    month = kwargs.get('month', None)
    year = kwargs.get('year', None)
    date = kwargs.get('date', None)
    if month is not None and (month < 1 or month > 12):
        return ''
    if month is None and year is None:
        if date is not None:
            month = date.month
            year = date.year
            if month < 1 or month > 12:
                return ''
            return months[month - 1][:3].lower() + str(year)[2:]
    elif month is not None and year is None:
        return months[month - 1][:3].lower()
    elif month is None and year is not None:
        return str(year)[2:]
    else:
        return months[month - 1][:3].lower() + str(year)[2:]
