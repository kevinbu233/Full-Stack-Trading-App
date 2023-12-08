from connect import connection
import psycopg2

from alpaca.trading.client import TradingClient
from alpaca.trading import *
from alpaca.trading.enums import *
from dotenv import load_dotenv
import os
from psycopg2 import extras

def createTable():
    database = connection()
    cursor = database.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL UNIQUE,
            company TEXT NOT NULL,
            exchange TEXT NOT NULL,
            shortable BOOLEAN NOT NULL
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_price (
            id SERIAL PRIMARY KEY,
            stock_id INTEGER,
            trade_date DATE NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            sma_20 REAL NOT NULL,
            sma_50 REAL NOT NULL,
            rsi_14 REAL NOT NULL,

            FOREIGN KEY (stock_id) REFERENCES stock (id)
        )
        """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_strategy (
            stock_id INTEGER NOT NULL,
            strategy_id INTEGER NOT NULL,
            FOREIGN KEY (stock_id) REFERENCES stock (id),
            FOREIGN KEY (strategy_id) REFERENCES strategy (id)
        )
    """)


    strategies = ['opening_range_breakout', 'opening_range_breakdown']

    for strategy in strategies:
        cursor.execute("""
            INSERT INTO strategy (name) VALUES (%s)
        """, (strategy, ))

    database.commit()

def getKeys():
    load_dotenv()

def custom_row_factory(cursor, row):
    # Convert the row into a dictionary
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

def initalizeDatabase():
    database = connection()
    cursor = database.cursor()
    trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)
    search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

    assets = trading_client.get_all_assets(search_params)
    for asset in assets:
        try:
            if asset.status == "active":
                cursor.execute("INSERT INTO stock (symbol, company, exchange, shortable) VALUES (%s, %s, %s, %s)", (asset.symbol, asset.name, asset.exchange, asset.shortable))
        except Exception as e:
            print(asset.symbol)
            print(e)
    # account = trading_client.get_account()
    # for property_name, value in account:
    #     print(f"\"{property_name}\": {value}")

    database.commit()

def checkNewSymbol():
    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    cursor.execute("""
        SELECT symbol, company FROM stock
    """)
    # database.row_factory = custom_row_factory
    rows = cursor.fetchall()
    symbols = [row['symbol'] for row in rows]

    trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)
    search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

    assets = trading_client.get_all_assets(search_params)
    for asset in assets:
        try:
            if asset.status == "active" and asset.tradable and asset.symbol not in symbols:
                print(f"Added a new stock {asset.symbol} {asset.name}")
                cursor.execute("INSERT INTO stock (symbol, company) VALUES (%s, %s)", (asset.symbol, asset.name))
        except Exception as e:
            print(asset.symbol)
            print(e)

def main():
    getKeys()
    createTable()
    # initalizeDatabase()

main()