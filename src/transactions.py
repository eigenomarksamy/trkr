import csv
import os
import pathlib
from datetime import datetime
from typing import List, Optional

from src.csv_mngr import CsvMngr
from src.sheets_mngr import get_google_sheet


class TransType:
    WATCH = 0
    BUY = 1
    SELL = 2
    CONVERT = 3
    TRANSFER = 4
    DEPOSIT = 5
    WITHDRAW = 6


class Transaction:
    def __init__(self, transaction: dict) -> None:
        self.type = transaction['type']
        self.date = transaction['date']
        self.quantity = float(transaction['quantity'])
        self.fees = float(transaction['fees'])
        self.price = float(transaction['price'])
        self.currency = transaction['currency']
        self.symbol = transaction['symbol']
        self.exchange = transaction['exchange']
        try:
            self.wallet = transaction['platform']
        except KeyError:
            self.wallet = transaction['wallet']
        self.ex_rate = float(transaction['ex_rate'])
        self.ex_fees = float(transaction['ex_fees'])

    def __str__(self) -> str:
        return (
            f'{self.type} {self.quantity} {self.exchange}::{self.symbol} '
            + f'at {self.price} {self.currency} '
            + f'with extra {self.fees}, {self.ex_rate} and {self.ex_fees} '
            + f'on {self.date} to {self.wallet}'
        )

    def __dict__(self) -> dict:
        return {
            'type': self.type,
            'date': self.date,
            'quantity': self.quantity,
            'fees': self.fees,
            'price': self.price,
            'currency': self.currency,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'wallet': self.wallet,
            'ex_rate': self.ex_rate,
            'ex_fees': self.ex_fees,
        }


class Transactions:
    def __init__(self) -> None:
        self.transactions = []

    def add(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def add_list(self, transactions: List[Transaction]) -> None:
        for transaction in transactions:
            transaction = Transaction(transaction)
            self.transactions.append(transaction)

    def prepend(self, transactions: List[Transaction]) -> None:
        self.transactions[:0] = transactions

    def get(self) -> list:
        return self.transactions

    def remove(self, index: int) -> None:
        self.transactions.pop(index)

    def clear(self) -> None:
        self.transactions.clear()

    def update(self, index: int, transaction: Transaction) -> None:
        self.transactions[index] = transaction

    def get_transactions_date(self, date: datetime) -> List[Transaction]:
        transactions_date = []
        for transaction in self.transactions:
            if transaction.date == date:
                transactions_date.append(transaction)
        return transactions_date

    def get_transactions_month(self, date: datetime) -> List[dict]:
        transactions_month = []
        for transaction in self.transactions:
            transaction_date = datetime.strptime(transaction.date, '%Y-%m-%d').date()
            if transaction_date.month == date.month and transaction_date.year == date.year:
                transactions_month.append(transaction.__dict__())
        return transactions_month

    def get_symbols_of_interest(self) -> list[str]:
        symbols_of_interest = []
        for transaction in self.transactions:
            if transaction.symbol not in symbols_of_interest:
                symbols_of_interest.append(transaction.symbol)
        return symbols_of_interest

    def get_first_transaction_date(self, date_format: str = '%Y-%m-%d') -> str:
        first_transaction = min(
            self.transactions, key=lambda t: datetime.strptime(t.date, '%Y-%m-%d')
        )
        return datetime.strptime(first_transaction.date, '%Y-%m-%d').strftime(date_format)

    def match_symbols_standard(self, std_map: dict) -> None:
        for transaction in self.transactions:
            transaction.symbol = std_map.get(transaction.symbol.lower(), transaction.symbol.lower())

    def print(self) -> None:
        print('Transactions:')
        for transaction in self.transactions:
            print(transaction)


def build_transactions_object(
    is_local: bool,
    address: str,
    directory: Optional[os.PathLike],
    is_quiet: bool,
    std_map: Optional[dict],
) -> Transactions:
    if is_local:
        transactions_file = address
    else:
        transactions_file = get_google_sheet(address, f'{directory}', 'transactions.csv')
        if not is_quiet:
            print('CSV file saved to: {}'.format(transactions_file))
    transactions_obj = Transactions()
    trans_csv_obj = CsvMngr(
        pathlib.Path(f'{transactions_file}'),
        [
            'type',
            'date',
            'quantity',
            'fees',
            'price',
            'currency',
            'symbol',
            'exchange',
            'platform',
            'ex_rate',
            'ex_fees',
        ],
    )
    transactions_obj.add_list(trans_csv_obj.read())
    if std_map:
        transactions_obj.match_symbols_standard(std_map)
    return transactions_obj


POSITION_COLUMNS = ['symbol', 'quantity', 'average_price', 'date']


def input_error(message: str) -> Exception:
    print(f'Input error: {message}')
    return Exception('400')


def build_positions(
    is_local: bool,
    address: str,
    directory: Optional[os.PathLike],
    is_quiet: bool,
    std_map: Optional[dict],
) -> List[Transaction]:
    """Reads opening positions, one row per investment, as buys at the average price.

    Required columns: symbol, quantity, average_price, date (YYYY-MM-DD).
    Optional: currency, ex_rate (default 1, same meaning as in transactions), exchange.
    """
    if is_local:
        positions_file = address
    else:
        positions_file = get_google_sheet(address, f'{directory}', 'positions.csv')
        if not is_quiet:
            print('CSV file saved to: {}'.format(positions_file))
    with open(positions_file, 'r', newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames or []]
        missing = [column for column in POSITION_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise input_error(f'{positions_file}: missing columns: {", ".join(missing)}.')
        rows = list(reader)
    positions = Transactions()
    for line, row in enumerate(rows, start=2):
        if not any(isinstance(value, str) and value.strip() for value in row.values()):
            continue
        where = f'{positions_file} line {line}'
        try:
            quantity = float(row['quantity'])
            average_price = float(row['average_price'])
            ex_rate = float(row.get('ex_rate') or 1)
        except ValueError:
            raise input_error(
                f'{where}: quantity, average_price and ex_rate must be numbers.'
            ) from None
        try:
            datetime.strptime(row['date'].strip(), '%Y-%m-%d')
        except ValueError:
            raise input_error(f'{where}: date must be YYYY-MM-DD, not {row["date"]!r}.') from None
        if not row['symbol'].strip():
            raise input_error(f'{where}: symbol is empty.')
        if quantity <= 0:
            raise input_error(f'{where}: quantity must be positive.')
        if average_price < 0:
            raise input_error(f'{where}: average_price must not be negative.')
        if ex_rate <= 0:
            raise input_error(f'{where}: ex_rate must be positive.')
        positions.add(
            Transaction(
                {
                    'type': 'buy',
                    'date': row['date'].strip(),
                    'quantity': quantity,
                    'fees': 0,
                    'price': average_price,
                    'currency': (row.get('currency') or '').strip(),
                    'symbol': row['symbol'].strip(),
                    'exchange': (row.get('exchange') or '').strip(),
                    'platform': 'positions file',
                    'ex_rate': ex_rate,
                    'ex_fees': 0,
                }
            )
        )
    if std_map:
        positions.match_symbols_standard(std_map)
    return positions.get()
