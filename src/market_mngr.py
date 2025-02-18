import os
import csv
import pathlib
import yfinance as yf
from typing import Union, Optional, Tuple
from datetime import date, datetime
from src.sheets_mngr import get_google_sheet
from src.csv_mngr import CsvMngr

class Interval:
    DAILY = '1d'
    MONTHLY = '1mo'
    WEEKLY = '1wk'

class YFinanceSymbMap:

    def __init__(self, tickers_map: dict) -> None:
        self.tickerMap = tickers_map

class MarketData:

    def __init__(self) -> None:
        pass

    def get_market_history(self) -> dict:
        return self.fetch_history()

    @staticmethod
    def format_date(raw_date: str, date_format: str) -> datetime:
        raw_date = raw_date.split()[0]
        return datetime.strptime(raw_date, date_format).date()

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

class MarketDataGoogle(MarketData):

    def __init__(self, def_currency: str, files_dict: dict) -> None:
        super().__init__()
        self.data = {}
        self.data_aligned = {}
        self.def_currency = def_currency
        for file in files_dict:
            self.data[file.upper()] = self.load_market_data_csv(files_dict[file])
        self.align_data()

    def fetch_history(self) -> dict:
        return self.get_historical_data()

    @staticmethod
    def load_market_data_csv(csv_file: os.PathLike) -> list:
        market_data = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                market_data.append(row)
        return market_data

    def get_historical_data(self) -> dict:
        return self.data_aligned

    def align_data(self) -> None:
        pass

class MarketDataGoogleLite(MarketDataGoogle):

    def __init__(self, files_dict: dict, def_currency: str):
        super().__init__(files_dict, def_currency)

    def align_data(self) -> None:
        for elm in self.data:
            self.data_aligned[elm] = {}
            for i in self.data[elm]:
                self.data_aligned[elm][MarketData.convert_date_to_short_str(date=MarketData.format_date(i['Date']))] = {'price': float(i['Close']), 'currency': i['Currency']}
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

class MarketDataGoogleFull(MarketDataGoogle):

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

class MarketDataYahoo(MarketData):

    def __init__(self, tickers: list[str],
                 ticker_map: Optional[YFinanceSymbMap],
                 start_date: Union[str, date],
                 end_date: Optional[Union[str, date]]=None,
                 date_format: str='%Y-%m-%d',
                 interval: Interval=Interval.DAILY,
                 auto_convert_currency: bool=True,
                 **kwargs) -> None:
        super().__init__()
        self.tickers = tickers
        self.interval = interval
        self.date_format = date_format
        self.start_date = self.assign_date(start_date, self.date_format)
        if end_date:
            self.end_date = self.assign_date(end_date, self.date_format)
        else:
            self.end_date = date.today()
        self.history = {}
        self.currency = {}
        self.current_price = {}
        self.formulate_history()
        if auto_convert_currency:
            req_currency = kwargs.get('req_currency', 'NA')
            self.currency_key = ticker_map.tickerMap.get(req_currency.lower(), None)
            if not self.currency_key:
                raise Exception("Currency conversion required, no currency provided.")
            else:
                self.convert_currencies(req_currency)

    @staticmethod
    def get_current_price_ticker(ticker: str) -> float:
        return float(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1])

    @staticmethod
    def assign_date(work_date: Union[str, date],
                    date_format: str) -> date:
        if isinstance(work_date, str):
            ret_date = datetime.strptime(work_date, date_format).date()
        else:
            ret_date = work_date
        return ret_date

    def formulate_history(self) -> None:
        for ticker in self.tickers:
            yf_ticker = yf.Ticker(ticker)
            history_data_frame = yf_ticker.history(start=self.start_date,
                                                    end=self.end_date,
                                                    interval=self.interval)
            if self.interval == Interval.DAILY:
                self.history[ticker] = {date.strftime(self.date_format): float(row['Close']) for date, row in history_data_frame.iterrows()}
            else:
                self.history[ticker] = {MarketData.convert_date_to_short_str(date=dater.date()): float(row['Close']) for dater, row in history_data_frame.iterrows()}
            self.currency[ticker] = yf_ticker.info.get("currency", 'NA')
            self.current_price[ticker] = self.get_current_price_ticker(ticker)

    def convert_currencies(self, req_currency: str) -> None:
        for ticker in self.tickers:
            if ticker == self.currency_key:
                continue
            if self.currency[ticker] != req_currency.upper():
                self.current_price[ticker] *= self.current_price[self.currency_key]
                self.currency[ticker] = req_currency.upper()
                for d in self.history[ticker]:
                        try:
                            self.history[ticker][d] *= self.history[self.currency_key][d]
                        except KeyError:
                            self.history[ticker][d] *= self.current_price[self.currency_key]

    def fetch_history(self) -> dict:
        return self.history

class MarketHistory:

    def __init__(self, market_data: MarketData) -> None:
        self.history = market_data.get_market_history()

class MarketSymbol:

    def __init__(self, symbol: str, history: dict, price: float,
                 currency: str) -> None:
        self.symbol = symbol
        self.history = history
        self.currency = currency
        self.price = price

    def print(self) -> None:
        print("Symbol:", self.symbol)
        print("Currency:", self.currency)
        print("Price:", self.price)
        print("History:")
        for h in self.history:
            print("\t", h, self.history[h])

class MarketReader:
    def __init__(self, file: os.PathLike,
                 symbols_of_interest: list[str]) -> None:
        self.csv_file = file
        self.market_data = MarketDataGoogle.load_market_data_csv()
        self.missing_symbols = []
        self.market_symbols = []
        self.market_verification = self.verify_symbols(symbols_of_interest)

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
            try:
                data_aligned[entry['symbol']] = {'price' : float(entry['price']),
                                                'currency' : entry['currency']}
            except ValueError as verr:
                if not is_quiet:
                    raise ValueError(f"Exception raised!\n\t--> {verr}.\n" +
                                     f"In other words,\n\t" +
                                     f'GOOGLEFINANCE is down for {entry["symbol"]}.' +
                                     '\n\tPossibly more')
                raise verr
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

def convertSymbListToDicts(symbols: list[MarketSymbol]) -> Tuple[dict, dict]:
    price_dict = {}
    history_dict = {}
    for symbol in symbols:
        price_dict[symbol.symbol] = {'price': symbol.price}
        history_dict[symbol.symbol] = {}
        for dater in symbol.history:
            history_dict[symbol.symbol][dater] = {'price' : symbol.history[dater]}
    return price_dict, history_dict

def get_yfinance_map(sheet_address: str, directory: os.PathLike,
                     file_name: str='yfinance-map.csv') -> YFinanceSymbMap:
    return YFinanceSymbMap(
            CsvMngr.convert_read_list_to_dict(
                CsvMngr(
                    pathlib.Path(
                        get_google_sheet(sheet_address,
                                         directory,
                                         file_name)),
                    ["symbol", "ticker"]).read()))

def get_yfinance_map_local(sheet_location: str) -> YFinanceSymbMap:
    return YFinanceSymbMap(
            CsvMngr.convert_read_list_to_dict(
                CsvMngr(
                    pathlib.Path(sheet_location),
                    ["symbol", "ticker"]).read()))

def use_market_google():
    market = MarketDataGoogleLite({}, 'SSSS')
    history_obj = MarketHistory(market, '2023-01-01')
    symbol = MarketSymbol('sss', history_obj.history, 1212, 'ssss')

def execute_yahoo_finance():
    symbols_of_interest = ['META', 'NVDA', 'btceur', 'pfe', 'usd', 'iwda', 'vwce', "VEUR", 'vusa']
    market = MarketDataYahoo(tickers=symbols_of_interest, start_date='2023-12-01', interval=Interval.WEEKLY)
    symbols_obj_list = []
    for symbol in symbols_of_interest:
        symbol_key = YFinanceSymbMap.tickerMap.get(symbol.lower())
        symbols_obj_list.append(MarketSymbol(symbol, market.history[symbol_key], market.current_price[symbol_key],market.currency[symbol_key]))
    for symbol in symbols_obj_list:
        symbol.print()

# execute_yahoo_finance()