from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading import *
from alpaca.trading.enums import *
from dotenv import load_dotenv
import os
from connect import connection
from alpaca.data.requests import *
import alpaca_trade_api as tradeapi
from alpaca.data.timeframe import *
from psycopg2 import extras
import pandas as pd
from .utils import is_dst, calculate_quantity

from datetime import date

load_dotenv()

database = connection()
cursor = database.cursor(cursor_factory=extras.RealDictCursor)

cursor.execute("""
    SELECT id FROM strategy WHERE name = 'opening_range_breakout'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    SELECT symbol, company FROM stock join stock_strategy 
    ON stock_strategy.stock_id = stock.id
    WHERE stock_strategy.strategy_id = (%s)
""", (strategy_id, ))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]

trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)
hisoric_client = StockHistoricalDataClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"))
# current_date = date.today().isoformat()
current_date = "2023-06-22"

orders = trading_client.get_orders(GetOrdersRequest(status= "all", after=current_date))
existing_orders_symbols = [order.symbol for order in orders if order.status != "canceled"]
print(current_date)
for symbol in symbols:

    timeframe = TimeFrame(1, TimeFrameUnit.Minute)  
    
    format = '%Y-%m-%dT%H:%M:%S%z'
    print(symbol)
# converting the timestamp string to datetime object
    if is_dst():
        start_minute_bar = datetime.strptime(f"{current_date}T09:30:00-05:00", format)
        end_minute_bar = datetime.strptime(f"{current_date}T09:45:00-05:00", format)
    else:
        start_minute_bar = datetime.strptime(f"{current_date}T09:30:00-04:00", format)
        end_minute_bar = datetime.strptime(f"{current_date}T09:45:00-04:00", format)

    print(start_minute_bar)
    params = StockBarsRequest(symbol_or_symbols = symbol, timeframe=timeframe, start=datetime(2023, 6, 22), end=datetime(2023, 6, 23))
    bars = hisoric_client.get_stock_bars(params).df
    bars = bars.droplevel(0)
    # opening_range_mask = (bars.index.datetime >= start_minute_bar) & (bars.index.datetime <= end_minute_bar)
    opening_range_bars = bars.loc[start_minute_bar:end_minute_bar]
    print(opening_range_bars)
    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['high'].max()

    opening_range = opening_range_high - opening_range_low

    print(opening_range_high)
    print(opening_range_low)
    print(opening_range)

    after_opening_range_bars = bars.loc[end_minute_bar:]

    print(after_opening_range_bars)
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

    if not after_opening_range_breakout.empty:
        if symbol not in existing_orders_symbols:
            print(after_opening_range_breakout)
            limit_price_stuff = after_opening_range_breakout.iloc[0]['close']
            print(limit_price_stuff)

            print(f"placing buy order for {symbol} at {limit_price_stuff}, closed_above {opening_range_high} at {after_opening_range_breakout.index.time[0]}")
            take_profit_req = TakeProfitRequest(limit_price= limit_price_stuff)
            stop_loss_req = StopLossRequest(limit_price= limit_price_stuff + opening_range, stop_price=limit_price_stuff - opening_range)
            try:
                order = LimitOrderRequest(symbol = symbol, side=OrderSide.BUY, type=OrderType.LIMIT, limit_price = limit_price_stuff, qty = calculate_quantity(10000, limit_price_stuff), time_in_force= TimeInForce.DAY,  stop_loss=stop_loss_req, take_profit=take_profit_req)
                submitted_order = trading_client.submit_order(order)
                print(submitted_order)
            except Exception as e:
                print(f"could not submit order {e}")
        else:
            print(f"Already placed an order for {symbol}")
        
        
        
        
        
        
        
        