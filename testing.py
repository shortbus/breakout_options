import os
import json
import time
import datetime
import importlib

import requests_cache
import yfinance as yf
import pandas as pd
import numpy as np

from application.app import database
#from application.app import strategies
#from application.app import toolbox

ts = time.time()
db = database.Database()
#df = db.load_data()
te = time.time()
print(te-ts, 'seconds to load db')

# errors
#df = yf.download('AAPL', period='max', interval='1d', group_by='ticker', threads=True)
# load new data
'''
symbols = db.get_symbols_list()
symbols_yf = ' '.join(symbols)
df = yf.download(
    symbols_yf,
    period='100y',
    interval='1d',
    group_by='ticker',
    threads=False,
)
'''

# load module via importlib
'''
strategy = 'breakout'
strategy_module = importlib.import_module(f'strategy_files.{strategy}')
strategy_fn = getattr(strategy_module, strategy)
results = strategy_fn(df)
picks = toolbox.find_todays_breakout(
    df,
    strategy_fn,
    days=strategy_module.days_to_backtest,
)
'''

ref = 'SPY'
t = yf.Ticker(ref)
spy = t.history(period='100y', interval='1d')

spycopy = spy.copy()
spy_adx = spycopy.ta.adx()
spy_rsi = spycopy.ta.stochrsi()

df = db.load_data()
