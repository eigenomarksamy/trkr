from datetime import date
import yfinance as yf
import sys

def get_iwda(ticker, interval):

    ticker_n = ticker
    ticker_n = 'VUSA.AS'
    print(ticker)
    print(type(ticker_n))
    obj = yf.Ticker(ticker_n)
    current_price = obj.history(period="1d")['Close'].iloc[-1]
    print(current_price)
    print("Current Price:", current_price)
    history = obj.history(start="2023-01-01", end=date.today(), interval=interval)
    print(history)
    history_dict = {}
    history_dict[ticker_n] = {date.strftime('%Y-%m-%d'): float(row['Close']) for date, row in history.iterrows()}
    print(history_dict)
    sys.exit(0)

# currency = etf.info.get("currency", "Currency information not available")
# print(f"Currency: {currency}")


# stock = yf.Ticker("NVDA")

# # Current price
# current_price = stock.history(period="1d")['Close'].iloc[-1]
# print("Current Price:", current_price)

# # Historical data
# history = stock.history(start="2023-01-01", end=date.today(), interval="1wk")
# print(history)

# currency = stock.info.get("currency", "Currency information not available")
# print(f"Currency: {currency}")


# stock = yf.Ticker("BTC-EUR")

# # Current price
# current_price = stock.history(period="1d")['Close'].iloc[-1]
# print("Current Price:", current_price)

# # Historical data
# history = stock.history(start="2023-01-01", end=date.today(), interval="1wk")
# print(history)

# currency = stock.info.get("currency", "Currency information not available")
# print(f"Currency: {currency}")


# ticker = "EURUSD=X"

# # Fetch the currency pair data
# currency_pair = yf.Ticker(ticker)

# # Get the current exchange rate
# current_rate = currency_pair.history(period="1d")['Close'].iloc[-1]
# print(f"EUR to USD exchange rate: {current_rate}")

# # Historical data
# history = currency_pair.history(start="2023-01-01", end=date.today(), interval="1wk")
# print(history)


def get_stats(ticker):
    obj = yf.Ticker(ticker)
    rate = obj.history(period="1d")['Close'].iloc[-1]
    history = obj.history(start="2023-01-01", end=date.today(), interval="1wk")
    history_dict = {}
    history_dict[ticker] = {date.strftime('%Y-%m-%d'): float(row['Close']) for date, row in history.iterrows()}
    currency = obj.info.get("currency", "")
    print('ticker', ticker)
    print(" ")
    print('rate', rate)
    print(" ")
    print('history', history)
    print(" ")
    print('history_dict', history_dict)
    print(" ")
    print('currency', currency)
    print(" ")

get_iwda("VUSA.AS", '1wk')
# get_stats('IWDA.AMS')
# get_stats('VEUR.AMS')
get_stats('NVDA')