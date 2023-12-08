from connect import connection

database = connection()
cursor = database.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS stock_price_minute (
    id SERIAL PRIMARY KEY, 
    stock_id INTEGER,
    datetime TIMESTAMP NOT NULL,
    open REAL NOT NULL, 
    high REAL NOT NULL,
    low REAL NOT NULL, 
    close REAL NOT NULL, 
    volume REAL NOT NULL,
    FOREIGN KEY (stock_id) REFERENCES stock (id)
)""")

database.commit()