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
