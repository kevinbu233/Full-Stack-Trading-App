from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading import *

from dotenv import load_dotenv
import os
from connect import connection
from alpaca.data.requests import *

trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)

response = trading_client.close_all_positions(cancel_orders=True)

print(response)