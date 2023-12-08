import yfinance
import psycopg2
from config import config

def connection():
    connection = None
    try:
        params = config()
        print("Connecting to database")
        connection = psycopg2.connect(**params)
        return connection
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)

def connect():
    connection = None
    try:
        params = config()
        print("Connecting to database")
        connection = psycopg2.connect(**params)

        crsr = connection.cursor()
        crsr.execute("SELECT version()")
        db_version = crsr.fetchone()
        print(db_version)
        crsr.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:

        if connection is not None:
            connection.close()
            print("Terminated!")

if __name__ == "__main__":
    connect()

# df = yfinance.download("AAPL", start="2022-12-07", end="2022-12-31")
# df.to_csv("AAPL_data.csv")