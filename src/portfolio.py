from datetime import datetime
from typing import Tuple, Union
from dateutil.relativedelta import relativedelta
from src.transactions import Transactions

class Portfolio:
    def __init__(self, transactions: Transactions, market_data: dict,
                 is_quiet: bool = False) -> None:
        self.transactions = transactions
        self.portfolio = {}
        self.total = {'value': 0, 'spending': 0, 'profit_net': 0,
                      'profit_percent': 0, 'cash_out': 0,
                      'time_interval_days': 0, 'time_interval_months': 0,
                      'time_interval_years': 0, 'avg_day_roi': 0,
                      'avg_month_roi': 0, 'avg_year_roi': 0}
        self.market_data = market_data
        self.wallet_fees = {}
        self.is_quiet = is_quiet

    def calculate(self) -> Tuple[dict, dict]:
        symbols_dict = {}
        for transaction in self.transactions.get():
            transaction = transaction.__dict__()
            if transaction['symbol'] not in symbols_dict:
                symbols_dict[transaction['symbol']] = {
                    'exchange': f'{transaction["exchange"]}',
                    'amount': 0, 'value': 0, 'spending': 0,
                    'spending_percent': 0, 'profit_net': 0,
                    'profit_percent': 0, 'current_price': 0,
                    'break_even_price': 0, 'price25': 0,
                    'price50': 0, 'price75': 0,
                    'price100': 0, 'price150': 0
                }
            if transaction['type'] == 'buy':
                symbols_dict[transaction['symbol']]['amount'] += transaction['quantity']
                spending = (transaction['price'] * transaction['quantity'] \
                            + transaction['fees'] + transaction['ex_fees']) \
                            / transaction['ex_rate']
                symbols_dict[transaction['symbol']]['spending'] += spending
                self.total['spending'] += spending
                symbols_dict[transaction['symbol']]['current_price'] = self.market_data[transaction['symbol']]['price']
                symbols_dict[transaction['symbol']]['value'] = symbols_dict[transaction['symbol']]['amount'] * symbols_dict[transaction['symbol']]['current_price']
                symbols_dict[transaction['symbol']]['break_even_price'] = symbols_dict[transaction['symbol']]['spending'] / symbols_dict[transaction['symbol']]['amount']
                symbols_dict[transaction['symbol']]['profit_net'] = symbols_dict[transaction['symbol']]['value'] - symbols_dict[transaction['symbol']]['spending']
                symbols_dict[transaction['symbol']]['profit_percent'] = (symbols_dict[transaction['symbol']]['profit_net'] / symbols_dict[transaction['symbol']]['spending']) * 100 if symbols_dict[transaction['symbol']]['spending'] != 0 else 0
                symbols_dict[transaction['symbol']]['price25'] = symbols_dict[transaction['symbol']]['break_even_price'] * 1.25
                symbols_dict[transaction['symbol']]['price50'] = symbols_dict[transaction['symbol']]['break_even_price'] * 1.50
                symbols_dict[transaction['symbol']]['price75'] = symbols_dict[transaction['symbol']]['break_even_price'] * 1.75
                symbols_dict[transaction['symbol']]['price100'] = symbols_dict[transaction['symbol']]['break_even_price'] * 2.00
                symbols_dict[transaction['symbol']]['price150'] = symbols_dict[transaction['symbol']]['break_even_price'] * 2.50
            elif transaction['type'] == 'sell':
                symbols_dict[transaction['symbol']]['amount'] -= transaction['quantity']
                symbols_dict[transaction['symbol']]['value'] = symbols_dict[transaction['symbol']]['amount'] * symbols_dict[transaction['symbol']]['current_price']
                self.total['spending'] -= symbols_dict[transaction['symbol']]['spending']

        for p in list(symbols_dict.keys()):
            if symbols_dict[p]['amount'] == 0:
                del symbols_dict[p]

        for symbol in symbols_dict:
            symbols_dict[symbol]['spending_percent'] = symbols_dict[symbol]['spending'] / self.total['spending'] * 100
            self.portfolio[symbol] = symbols_dict[symbol]
            self.total['value'] += self.portfolio[symbol]['value']

        if not self.is_quiet:
            for p in self.portfolio:
                print(f'{p}:')
                for pp in self.portfolio[p]:
                    print(f'\t{pp}: {self.portfolio[p][pp]}')
        self.total['profit_net'] = self.total['value'] - self.total['spending']
        self.total['profit_percent'] = (self.total['profit_net'] / self.total['spending']) * 100 if self.total['spending'] != 0 else 0
        self.total['cash_out'] = self.total['value'] * 0.95
        transaction_dates = [datetime.strptime(transaction.__dict__()['date'], '%Y-%m-%d') for transaction in self.transactions.get()]
        if transaction_dates:
            min_date = min(transaction_dates)
            max_date = datetime.today()
            self.total['time_interval_days'] = (max_date - min_date).days
            self.total['time_interval_months'] = self.total['time_interval_days'] / 30
            self.total['time_interval_years'] = self.total['time_interval_days'] / 365

        if self.total['time_interval_days'] > 0:
            self.total['avg_day_roi'] = self.total['profit_percent'] / self.total['time_interval_days']
            self.total['avg_month_roi'] = self.total['avg_day_roi'] * 30
            self.total['avg_year_roi'] = self.total['avg_day_roi'] * 365

        if not self.is_quiet:
            print("Portfolio:")
            for tot in self.total:
                print(f'\t\t{tot.capitalize()}: ', self.total[tot])
        return self.portfolio, self.total

    def compute_spending_history(self) -> dict:
        ret_dict = {}
        loc_trans = self.transactions.get()
        loc_trans.sort(key=lambda x: x.__dict__()['date'])
        first_date = datetime.strptime(loc_trans[0].__dict__()['date'], '%Y-%m-%d').date()
        last_date = datetime.strptime(loc_trans[-1].__dict__()['date'], '%Y-%m-%d').date()
        date_tmp = first_date
        while date_tmp <= last_date:
            month_transactions = []
            ret_dict[convert_date_to_short_str(date=date_tmp)] = 0
            month_transactions = self.transactions.get_transactions_month(date_tmp)
            for transaction in month_transactions:
                if transaction['type'] == 'buy':
                    spending = (transaction['price'] * transaction['quantity'] \
                                + transaction['fees'] + transaction['ex_fees']) \
                                / transaction['ex_rate']
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
                entry_points[transaction['symbol']] = convert_date_to_short_str(date=datetime.strptime(transaction['date'], '%Y-%m-%d').date())
        return entry_points

    def compute_historical_valuation(self, historical_dict: dict) -> dict:
        ret_data = {}
        loc_trans = self.transactions.get()
        loc_trans.sort(key=lambda x : x.__dict__()['date'])
        first_date = datetime.strptime(loc_trans[0].__dict__()['date'], '%Y-%m-%d').date()
        last_date = datetime.strptime(loc_trans[-1].__dict__()['date'], '%Y-%m-%d').date()
        acu_valuation = 0
        date_itr = first_date
        while date_itr <= last_date:
            ret_data[convert_date_to_short_str(date=date_itr)] = acu_valuation
            for trans_itr in self.transactions.get_transactions_month(date_itr):
                if trans_itr['type'] == 'buy':
                    acu_valuation += trans_itr['quantity'] * historical_dict[trans_itr['symbol']][convert_date_to_short_str(date=date_itr)]['price']
                    ret_data[convert_date_to_short_str(date=date_itr)] = acu_valuation
                elif trans_itr['type'] == 'sell':
                    acu_valuation += trans_itr['quantity'] * historical_dict[trans_itr['symbol']][convert_date_to_short_str(date=date_itr)]['price']
                    ret_data[convert_date_to_short_str(date=date_itr)] = acu_valuation
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
        spending_per_month_list = [spending_dict[month] \
                                   for month in spending_dict.keys()]
        spending_percent_per_month_list = [100 * euros / sum(spending_per_month_list) \
                                           for euros in spending_per_month_list]
        return spending_list, profit_percent_list, \
            spending_percent_per_month_list, symbols_list, pp_list, months_list

def convert_date_to_short_str(**kwargs) -> str:
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
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
