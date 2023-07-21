print(__name__)
import os
import json
import datetime

import requests

import pandas as pd
import yfinance as yf
#import pandas_ta as ta

from bs4 import BeautifulSoup as bs

class Database:
    def __init__(self):
        self.data_dir = 'data'
        self.filename = 'sp500.h5'
        self.full_path = os.path.join(
            self.data_dir,
            self.filename,
        )
        if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)
        self.df = pd.DataFrame()
        self.last_pull = 0.0
        self.last_pull_pretty = 'n/a'
        self.file_exists = False
        try:
            open(self.full_path)
            self.file_exists = True
            self.last_pull = os.path.getmtime(self.full_path)
            last_pull_dt = datetime.datetime.fromtimestamp(self.last_pull)
            self.last_pull_pretty = last_pull_dt.strftime(f'(%a) %B %d, %Y @ %H:%M:%S')
        except:
            pass
        return
    
    def get_symbols_list(self):
        filename = 'sp500.js'
        full_path = os.path.join(
            self.data_dir,
            filename,
        )
        try:
            with open(full_path, 'r') as f:
                fr = f.read()
            return json.loads(fr)
        except:
            pass
        html = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        soup = bs(html.text, 'lxml')
        table = soup.find('table', {'class': 'wikitable sortable'})
        output = {}
        for row in table.findAll('tr')[1:]:
                td = row.findAll('td')
                ticker = td[0].text
                name = td[1].text
                sector = td[2].text
                sub_industry = td[3].text
                hq = td[4].text
                added = td[5].text
                cik = td[6].text
                founded = td[7].text
                ticker = ticker[:-1]
                ticker = ticker.replace('.', '-')
                output[ticker] = {
                    'symbol': ticker,
                    'security': name,
                    'sector': sector,
                    'industry': sub_industry,
                    'hq': hq,
                    'added': added,
                    'cik': cik,
                    'founded': founded,
                }
        with open(full_path, 'w') as f:
            f.write(
                json.dumps(
                    output,
                    indent=2,
                )
            )
        return output
    
    def get_historic_data(self):
        symbols = self.get_symbols_list()
        symbols_yf = ' '.join(symbols)
        df = yf.download(
            symbols_yf,
            period='100y',
            interval='1d',
            group_by='ticker',
            threads=True,
        )
        df.to_hdf(self.full_path, key='data')
        return
    
    def load_data(self):
        try:
            open(self.full_path)
        except:
            self.get_historic_data()
        df = pd.read_hdf(self.full_path)
        return df
    
    def update_historic_data(self):
        now = datetime.datetime.now()
        last_pull_dt = datetime.datetime.utcfromtimestamp(self.last_pull)
        days = (now - last_pull_dt).days
        if days >= 50:
            self.get_historic_data()
            return self.load_data()
        symbols = self.get_symbols_list()
        symbols_yf = ' '.join(symbols)
        # today - today == -1
        # +2 covers missing day and last known day
        # for worst case scenario
        df = yf.download(
            symbols_yf,
            #period=f'{days+2}d',
            period='5d',
            interval='1d',
            group_by='ticker',
            threads=True,
        )
        historic = self.load_data()
        duplicates = df.index.intersection(historic.index)
        for date in duplicates:
            if historic.loc[date].sort_index().equals(df.loc[date].sort_index()):
                duplicates = duplicates.drop(date)
                df.drop(date, inplace=True)
            else:
                # volume changes after hours
                print(f'outdated entry for {date} in historic')
                historic = historic.drop(date)
        if len(df) > 0:
            print(f'adding {len(df)} entries')
            #historic.drop(duplicates, inplace=True)
            both = pd.concat([historic, df])
            both.sort_index(inplace=True)
            try:
                os.remove(self.full_path + '.bak')
            except:
                pass
            os.rename(self.full_path, self.full_path + '.bak')
            both.to_hdf(self.full_path, key='data')
            self.last_pull = os.path.getmtime(self.full_path)
            last_pull_dt = datetime.datetime.fromtimestamp(self.last_pull)
            self.last_pull_pretty = last_pull_dt.strftime(f'(%a) %B %d, %Y @ %H:%M:%S')
            return
        else:
            print('nothing to add')
        return
    
    def _(self):
        return

if __name__ == '__main__':
    db = Database()
    