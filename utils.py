from datetime import datetime
import pytz

def is_dst(time = datetime.now()):

    x = datetime(datetime.now().year(), 1, 1, 0, 0, 0, tzinfo = pytz.timezone('US/Eastern'))
    y = time(pytz.timezone("US/Eastern"))

    return not (y.utoffset() == x.utcoffset())

def calculate_quantity(amount, price):
    return amount // price + 1