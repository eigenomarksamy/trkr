from datetime import datetime
from src.transactions import Transactions, Transaction

def get_transaction_data(default_currency: str) -> dict:
    print("Enter transaction details:")
    type = input("Type (Watch, Buy, Sell, Convert, Transfer, Deposit or Withdraw): ").lower()
    date_raw = input("Date (DD-MM-YYYY) or TODAY: ")
    if date_raw == 'TODAY':
        date_raw = datetime.today().strftime('%d-%m-%Y')
    date = datetime.strptime(date_raw, '%d-%m-%Y').date()
    quantity = input("Quantity: ")
    fees = input("Fees: ")
    price = input("Price: ")
    currency = input("Currency: ").upper()
    symbol = input("Symbol: ").upper()
    exchange = input("Exchange: ").upper()
    wallet = input("Wallet: ")
    ex_rate = 1.0
    ex_fees = 0.0
    if currency != default_currency:
        ex_rate = input("Exchange rate: ")
        ex_fees = input("Exchange fees: ")

    transaction_data = {
        "type": type,
        "date": date,
        "quantity": quantity,
        "fees": fees,
        "price": price,
        "currency": currency,
        "symbol": symbol,
        "exchange": exchange,
        "wallet": wallet,
        "ex_rate": ex_rate,
        "ex_fees": ex_fees
    }

    return transaction_data

def execute_ui(default_currency: str, transactions_obj: Transactions) -> list:
    while True:
        print("\nTransaction Data Entry")
        print("1. Compute")
        print("2. Enter new transaction")
        print("3. Edit transaction")
        print("4. View transactions")
        print("5. Delete transaction")
        choice = input("Choose an option: ")

        if choice == '1':
            print("Starting Calculations...")
            break
        elif choice == '2':
            transaction_data = get_transaction_data(default_currency)
            print("\nTransaction Data:")
            for key, value in transaction_data.items():
                print(f"{key}: {value}")
            transactions_obj.add(Transaction(transaction_data))
        elif choice == '3':
            print("Edit transaction")
            transactions = transactions_obj.get()
            for transaction in transactions:
                print(f"{transactions.index(transaction)}: {transaction.__dict__()}")
            index = int(input("Enter the index of the transaction to edit: "))
            transaction_data = get_transaction_data(default_currency)
            print("\nTransaction Data:")
            for key, value in transaction_data.items():
                print(f"{key}: {value}")
            transactions_obj.remove(index)
            transactions_obj.add(transaction_data)
        elif choice == '4':
            print("Transactions:")
            print(transactions_obj.get())
        elif choice == '5':
            print("Delete transaction")
            transactions = transactions_obj.get()
            for transaction in transactions:
                print(f"{transactions.index(transaction)}: {transaction.__dict__()}")
            index = int(input("Enter the index of the transaction to edit: "))
            transaction_data = get_transaction_data(default_currency)
            print("\nTransaction Data:")
            for key, value in transaction_data.items():
                print(f"{key}: {value}")
            transactions_obj.remove(index)
        else:
            print("Invalid choice. Please try again.")
    return transactions_obj.get()
