print(__name__)
import pandas as pd
import pandas_ta as ta

strategy_name = 'RSI Reversal'
days_to_backtest = 1

def rsi_reversal(df):
    symbols = df.columns.get_level_values(0).unique().sort_values(ascending=True)
    rsi = pd.DataFrame()
    for symbol in symbols:
        rsi_single = df[symbol].ta.stochrsi()
        rsi_single['Ticker'] = symbol
        rsi_single = rsi_single.set_index('Ticker', append=True).unstack('Ticker').swaplevel(axis=1)
        rsi = pd.concat([rsi, rsi_single], axis=1)
    
    close = df.loc[:, df.columns.get_level_values(1).isin(['Close'])].droplevel(1, axis='columns')
    high = df.loc[:, df.columns.get_level_values(1).isin(['High'])].droplevel(1, axis='columns')
    low = df.loc[:, df.columns.get_level_values(1).isin(['Low'])].droplevel(1, axis='columns')
    rsi_14 = rsi.loc[:, rsi.columns.get_level_values(1).isin(['STOCHRSId_14_14_3_3'])].droplevel(1, axis='columns')
    
    gt_0day_1day = rsi_14 > rsi_14.shift(1)
    lt_0day_1day = rsi_14 < rsi_14.shift(1)
    lt_1day_2day = rsi_14.shift(1) < rsi_14.shift(2)
    gt_1day_2day = rsi_14.shift(1) > rsi_14.shift(2)
    
    # crossover
    xo = gt_0day_1day & lt_1day_2day
    xu = lt_0day_1day & gt_1day_2day
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (close.shift(1) < high)
    puts_hit = xu.shift(1) & (close.shift(1) > low)
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df