from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from connect import connection
from psycopg2 import extras

from datetime import date
from dotenv import load_dotenv
import os

from alpaca.data.requests import *
from alpaca.trading.client import TradingClient
from alpaca.trading import *

templates = Jinja2Templates(directory="templates")
app = FastAPI()
load_dotenv()
trading_client = TradingClient(os.getenv("API_KEY"), os.getenv("SECRET_KEY"), paper=True)


@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get("filter", False)

    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("""SELECT max(trade_date) FROM stock_price""")
    show_date = cursor.fetchone()["max"]
    if stock_filter == 'new_closing_highs':
        cursor.execute("""SELECT *
            FROM (
                SELECT symbol, company, stock_price.stock_id, trade_date, max_close FROM stock_price 
                INNER JOIN (SELECT symbol, company, stock_id, MAX(close) AS max_close FROM stock_price JOIN stock ON stock.id = stock_price.stock_id GROUP BY stock_id, symbol, company) 
                AS temp ON stock_price.stock_id = temp.stock_id and stock_price.close = temp.max_close
            ) AS max_close
            WHERE trade_date = (%s) """, (show_date,))
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""SELECT *
            FROM (
                SELECT symbol, company, stock_price.stock_id, trade_date, min_close FROM stock_price 
                INNER JOIN (SELECT symbol, company, stock_id, min(close) AS min_close FROM stock_price JOIN stock ON stock.id = stock_price.stock_id GROUP BY stock_id, symbol, company) 
                AS temp ON stock_price.stock_id = temp.stock_id and stock_price.close = temp.min_close
            ) AS min_close
            WHERE trade_date = (%s) """, (show_date,))
    elif stock_filter == "new_intraday_highs":
        cursor.execute("""SELECT *
            FROM (
                SELECT symbol, company, stock_price.stock_id, trade_date, max_high FROM stock_price 
                INNER JOIN (SELECT symbol, company, stock_id, MAX(high) AS max_high FROM stock_price JOIN stock ON stock.id = stock_price.stock_id GROUP BY stock_id, symbol, company) 
                AS temp ON stock_price.stock_id = temp.stock_id and stock_price.close = temp.max_high
            ) AS new_high
            WHERE trade_date = (%s) """, (show_date,))
    elif stock_filter == "new_intraday_lows":
        cursor.execute("""SELECT *
            FROM (
                SELECT symbol, company, stock_price.stock_id, trade_date, min_low FROM stock_price 
                INNER JOIN (SELECT symbol, company, stock_id, min(low) AS min_low FROM stock_price JOIN stock ON stock.id = stock_price.stock_id GROUP BY stock_id, symbol, company) 
                AS temp ON stock_price.stock_id = temp.stock_id and stock_price.close = temp.min_low
            ) AS new_low
            WHERE trade_date = (%s) """, (show_date,))
    elif stock_filter == "rsi_over_bought":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE rsi_14 > 70 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    elif stock_filter == "rsi_over_sold":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE rsi_14 < 30 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    elif stock_filter == "above_sma_20":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE close > sma_20 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    elif stock_filter == "below_sma_20":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE close < sma_20 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    elif stock_filter == "above_sma_50":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE close > sma_50 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    elif stock_filter == "below_sma_50":
        cursor.execute("""
                SELECT symbol, company, stock_id, trade_date
                FROM stock_price JOIN stock on stock.id = stock_price.stock_id
                WHERE close < sma_50 AND trade_date = (%s)
                ORDER BY symbol
                """, (show_date,))
    else:
        cursor.execute("""
            SELECT id, symbol, company, exchange FROM stock
        """)
    # database.row_factory = custom_row_factory
    
    rows = cursor.fetchall()
    current_date = date.today().isoformat()
    current_date = show_date
    cursor.execute("""
        SELECT symbol, rsi_14, sma_20, sma_50, close FROM stock JOIN stock_price ON stock_price.stock_id = stock.id
        WHERE trade_date = (%s)
    """, (current_date, ))

    indicator_rows = cursor.fetchall()
    indicator_values = {}
    for row in indicator_rows:
        indicator_values[row["symbol"]] = row
    

    database.commit()
    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows, "indicator_values": indicator_values})

@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM strategy
        """)
    strategies = cursor.fetchall()
    cursor.execute("""
        SELECT id, symbol, company, exchange FROM stock WHERE symbol = (%s)
    """, (symbol, ))

    
    # database.row_factory = custom_row_factory
    row = cursor.fetchone()
    cursor.execute("""
        SELECT * FROM stock_price WHERE stock_id = (%s) ORDER BY trade_date DESC
    """, (row['id'], ))

    bars = cursor.fetchall()

    database.commit()
    return templates.TemplateResponse("stock.html", {"request": request, "stock": row, "bars": bars, "strategies": strategies})


@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (%s, %s)
        """, (stock_id, strategy_id))
    
    database.commit()
    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code = 303)


@app.get("/strategies")
def strategies(request: Request):

    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM strategy
        """)
    strategies = cursor.fetchall()
    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": strategies})

@app.get("/order_history")
def order_history(request: Request):
    # database = connection()
    # cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    orders = trading_client.get_orders(GetOrdersRequest(status= "all"))

    return templates.TemplateResponse("order_history.html", {"request": request, "orders": orders})

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    database = connection()
    cursor = database.cursor(cursor_factory=extras.RealDictCursor)

    cursor.execute("""
        SELECT id, name FROM strategy WHERE id = (%s)
        """, (strategy_id,))
    strategy = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, company FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
        WHERE strategy_id = (%s)
        """, (strategy_id,))
    stocks = cursor.fetchall()
    database.commit()
    return templates.TemplateResponse("strategy.html", {"request": request, "stocks": stocks, "strategy": strategy})