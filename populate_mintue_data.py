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
from utils import is_dst, calculate_quantity
import pytz
import csv
load_dotenv()

database = connection()
cursor = database.cursor(cursor_factory=extras.RealDictCursor)

trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)
hisoric_client = StockHistoricalDataClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"))

symbols = []
stock_ids = {}

with open('qqq.csv') as f:
    reader = csv.reader(f)

    for line in reader:
        symbols.append(line[1])

cursor.execute("""
    SELECT * FROM stock
""")

stocks = cursor.fetchall()

for stock in stocks:
    symbol = stock['symbol']
    stock_ids[symbol] = stock['id']

for symbol in symbols:
    format = '%Y-%m-%dT%H:%M:%S%z'
    timeframe = TimeFrame(1, TimeFrameUnit.Minute)  
    start_date = datetime.strptime(f"2023-01-29T00:30:00-05:00", format)
    # end_date = datetime.strptime(f"2023-07-06T16:00:00-05:00", format)

    
    

    # start_date = datetime(2020, 1, 6).date()
    end_date_range = datetime.strptime(f"2023-07-06T16:00:00-05:00", format)

    while start_date < end_date_range:
        end_date = start_date + timedelta(days=4)

        print(f"== Fetching minute bars for {symbol} {start_date} - {end_date} ==")
        # minutes = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=start_date, to=end_date).df
        # minutes = minutes.resample('1min').ffill()
        print(symbol)
        params = StockBarsRequest(symbol_or_symbols = symbol, timeframe=timeframe, start=start_date, end=end_date)
        minutes = hisoric_client.get_stock_bars(params).df.reset_index(level=0, drop=True)
        minutes = minutes.resample('1T').ffill()
        
        for index, row in minutes.iterrows():
            cursor.execute("""
                INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_ids[symbol], index.tz_localize(None).isoformat(), row['open'], row['high'], row['low'], row['close'], row['volume']))

        start_date = start_date + timedelta(days=7)

# format = '%Y-%m-%dT%H:%M:%S%z'
# timeframe = TimeFrame(1, TimeFrameUnit.Minute)  
# start_date = datetime.strptime(f"2023-07-03T09:30:00-05:00", format)
# end_date = datetime.strptime(f"2023-07-06T16:00:00-05:00", format)


# # Define the desired timezone
# desired_timezone = pytz.timezone('America/New_York')

# # Define the time range to fill for each day (start time and end time)
# fill_start_time = pd.Timestamp('09:00:00').time()
# fill_end_time = pd.Timestamp('17:00:00').time()

# # Convert the DatetimeIndex to the desired timezone
# bars = bars.tz_convert(desired_timezone)

# # Iterate over each day and fill the specified time range
# for day in bars.index.date.unique():
#     # Filter the data for the current day
#     day_bars = bars.loc[bars.index.date == day]

#     # Filter the data within the specified time range for the current day
#     time_range_bars = day_bars.between_time(fill_start_time, fill_end_time)

#     # Fill the specified time range with forward-filled values
#     time_range_bars = time_range_bars.ffill()

#     # Update the original DataFrame or Series with the filled values for the current day
#     bars.update(time_range_bars)

# # Convert the DatetimeIndex back to UTC
# bars = bars.tz_convert(pytz.UTC)

# start_date = datetime(2023, 7, 1) 
# end_date =  datetime.today() 
# params = StockBarsRequest(symbol_or_symbols = "AAPL", timeframe=timeframe, start=start_date, end=end_date)
# bars = hisoric_client.get_stock_bars(params).df.reset_index(level=0, drop=True)
# print(bars)
# bars = bars.resample('1T').ffill()
# print(bars)
# for index, row in bars.iterrows():
#     # print(index)
#     # print(row)
#     cursor.execute("""
#         INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume) VALUES 
#         (%s, %s, %s, %s, %s, %s, %s)
#     """, (10465, index.tz_localize(None).isoformat(), row["open"], row["high"], row["low"], row["close"], row["volume"],))

database.commit()
    



