import os
import csv
import requests
from typing import Any, Tuple, Union
from datetime import datetime

def get_google_sheet(spreadsheet_id: str, outDir: str,
                     outFile: str) -> os.PathLike:
    os.makedirs(outDir, exist_ok = True)
    url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv'
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join(outDir, outFile)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    else:
        print(f'Error downloading Google Sheet: {response.status_code}')
        raise Exception(f'Error downloading Google Sheet: {response.status_code}')

class MarketReader:
    def __init__(self, file: os.PathLike,
                 symbols_of_interest: list[str]) -> None:
        self.csv_file = file
        self.market_data = self.load_market_data()
        self.missing_symbols = []
        self.market_symbols = []
        self.market_verification = self.verify_symbols(symbols_of_interest)

    def load_market_data(self) -> list:
        market_data = []
        with open(self.csv_file, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                market_data.append(row)
        return market_data

    def verify_symbols(self, symbols_of_interest: list[str]) -> bool:
        for data in self.market_data:
            if data['symbol'] not in self.market_symbols:
                self.market_symbols.append(data['symbol'])
        for symbol in symbols_of_interest:
            if symbol not in self.market_symbols:
                if symbol not in self.missing_symbols:
                    self.missing_symbols.append(symbol)
        if len(self.missing_symbols) > 0:
            return False
        return True

    def get_current_price(self, symbol: str, currency: str) -> float:
        for data in self.market_data:
            if data['symbol'] == symbol and data['currency'] == currency:
                return float(data['price'])
        return 0.0

    def get_usd_conversion_rate(self) -> float:
        for data in self.market_data:
            if data['symbol'] == 'USD':
                return float(data['price'])
        return 0.0

    def align_data(self, def_currency: str, is_quiet: bool = False) -> dict:
        data_aligned = {}
        for entry in self.market_data:
            data_aligned[entry['symbol']] = {'price' : float(entry['price']),
                                             'currency' : entry['currency']}
        for entry in data_aligned.keys():
            if def_currency == 'EUR':
                if data_aligned[entry]['currency'] == 'USD':
                    data_aligned[entry]['price'] *= self.get_usd_conversion_rate()
                    data_aligned[entry]['currency'] = 'EUR'
            elif def_currency == 'USD':
                if data_aligned[entry]['currency'] == 'EUR':
                    data_aligned[entry]['price'] /= self.get_usd_conversion_rate()
                    data_aligned[entry]['currency'] = 'USD'
            if not is_quiet:
                print(f'{entry}: {data_aligned[entry]["price"]}, ' +
                      f'currency: {data_aligned[entry]["currency"]}')
        return data_aligned

class MarketHistory:

    def __init__(self, files_dict: dict, def_currency: str) -> None:
        self.data = {}
        self.data_aligned = {}
        self.def_currency = def_currency
        for file in files_dict:
            self.data[file.upper()] = self.load_market_data(files_dict[file])
        self.align_data()

    @staticmethod
    def load_market_data(csv_file: os.PathLike) -> list:
        market_data = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                market_data.append(row)
        return market_data

    @staticmethod
    def format_date(raw_date: str) -> datetime:
        raw_date = raw_date.split()[0]
        return datetime.strptime(raw_date, '%m/%d/%Y').date()

    @staticmethod
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
            else:
                return ''
        elif month is not None and year is None:
            return months[month - 1][:3].lower()
        elif month is None and year is not None:
            return str(year)[2:]
        else:
            return months[month - 1][:3].lower() + str(year)[2:]

    def get_historical_data(self) -> dict:
        return self.data_aligned

    def align_data(self) -> None:
        pass

class MarketHistoryFull(MarketHistory):

    def __init__(self, files_dict: dict, def_currency: str, currency_conv_rate: float) -> None:
        self.currency_conv_rate = currency_conv_rate
        super().__init__(files_dict, def_currency)

    def align_data(self) -> None:
        for elm in self.data:
            self.data_aligned[elm] = {}
            for i in self.data[elm]:
                self.data_aligned[elm][i['Date'].split()[0]] = {'price': float(i['Close']), 'currency': i['Currency']}
        for elm in self.data_aligned:
            if elm == 'USD':
                continue
            for date in self.data_aligned[elm]:
                if self.def_currency == 'EUR' and self.data_aligned[elm][date]['currency'] == 'USD':
                    try:
                        self.data_aligned[elm][date]['price'] *= self.data_aligned['USD'][date]['price']
                    except KeyError:
                        self.data_aligned[elm][date]['price'] *= self.currency_conv_rate
                    self.data_aligned[elm][date]['currency'] = 'EUR'
                elif self.def_currency == 'USD' and self.data_aligned[elm][date]['currency'] == 'EUR':
                    try:
                        self.data_aligned[elm][date]['price'] /= self.data_aligned['USD'][date]['price']
                    except KeyError:
                        self.data_aligned[elm][date]['price'] /= self.currency_conv_rate
                    self.data_aligned[elm][date]['currency'] = 'USD'

class MarketHistoryLite(MarketHistory):

    def __init__(self, files_dict: dict, def_currency: str):
        super().__init__(files_dict, def_currency)

    def align_data(self) -> None:
        for elm in self.data:
            self.data_aligned[elm] = {}
            for i in self.data[elm]:
                self.data_aligned[elm][super().convert_date_to_short_str(date=super().format_date(i['Date']))] = {'price': float(i['Close']), 'currency': i['Currency']}
        for elm in self.data_aligned:
            if elm == 'USD':
                continue
            for date in self.data_aligned[elm]:
                if self.def_currency == 'EUR' and self.data_aligned[elm][date]['currency'] == 'USD':
                    self.data_aligned[elm][date]['price'] *= self.data_aligned['USD'][date]['price']
                    self.data_aligned[elm][date]['currency'] = 'EUR'
                elif self.def_currency == 'USD' and self.data_aligned[elm][date]['currency'] == 'EUR':
                    self.data_aligned[elm][date]['price'] /= self.data_aligned['USD'][date]['price']
                    self.data_aligned[elm][date]['currency'] = 'USD'

def fetch_histories(addresses: dict, suffix: str, destination: str,
                    symbols_of_interest: list[str],
                    is_quiet: bool) -> Tuple[bool, Union[dict, list[str]]]:
    history_files = {}
    history_symbols = []
    missing_history_symbols = []
    for elm in addresses[f'history-{suffix}']:
        history_files[elm] = get_google_sheet(addresses[f'history-{suffix}'][elm], f'{destination + suffix + "/"}', f'{elm}.csv')
        if not is_quiet:
            print(f'CSV history of {elm} saved to file {history_files[elm]}')
        if elm.upper() not in history_symbols:
            history_symbols.append(elm.upper())
    for symbol in symbols_of_interest:
        if symbol not in history_symbols:
            if symbol not in missing_history_symbols:
                missing_history_symbols.append(symbol)
    if len(missing_history_symbols) > 0:
        return False, missing_history_symbols
    else:
        return True, history_files
