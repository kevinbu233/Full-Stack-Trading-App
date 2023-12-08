from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading import *
from alpaca.trading.enums import *
from dotenv import load_dotenv
import os
from connect import connection
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from psycopg2 import extras
import tulipy
import numpy as np


def checkPrice(timeframe = TimeFrame(1, TimeFrameUnit.Day), start_date = datetime.today):
    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    print(start_date)
    cursor.execute("""
        SELECT id, symbol, company FROM stock
    """)
    rows = cursor.fetchall()
    
    stock_dict= {}
    symbols = []
    for row in rows:
        symbol = row['symbol'] 
        symbols.append(symbol)
        stock_dict[symbol] = row["id"]

    hisoric_client = StockHistoricalDataClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"))
    chunk_size = 200
    end_date =  datetime.today() 
    for i in range(0, len(symbols), 200):

        symbol_chunk = symbols[i: i+chunk_size]

        timeframe = TimeFrame(1, TimeFrameUnit.Day)  


       
        params = StockBarsRequest(symbol_or_symbols = symbol_chunk, timeframe=timeframe, start=start_date, end=end_date)
        bars = hisoric_client.get_stock_bars(params)

        for i, symbol in enumerate(bars.data):
            print(f"Processing {symbol}")
            sma_20, sma_50, rsi_14 = 0, 0, 0
            recent_closes = [bar.close for bar in bars[symbol]]
            if len(recent_closes)> 50:
                sma_50 = tulipy.sma(np.array(recent_closes), period=50)[-1]
                
            if len(recent_closes) > 20:
                sma_20 = tulipy.sma(np.array(recent_closes), period=20)[-1]
            if len(recent_closes) > 14 :
                rsi_14 = tulipy.rsi(np.array(recent_closes), period=14)[-1]
            for bar in bars[symbol]:
                stock_id = stock_dict[symbol]


                cursor.execute(
                    "INSERT INTO stock_price (stock_id, trade_date, open, high, low, close, volume, sma_20, sma_50, rsi_14)" +
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (stock_id, bar.timestamp, bar.open, bar.high, bar.low, bar.close, bar.volume, sma_20, sma_50, rsi_14)
                )
        database.commit()
    filename = "last_date_queried.txt" 

    with open(filename, "w") as file:
        file.write(str(end_date.date()) + "\n")



if __name__ == '__main__':
    load_dotenv()
    filename = "last_date_queried.txt"  
    timestamp = ""
    with open(filename, "r") as file:
        for line in file:
            timestamp_str = line.strip()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
            print(timestamp)
    checkPrice(start_date=timestamp)

