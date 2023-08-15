print(__name__)
import pandas as pd

strategy_name = 'Momentum Quick'
days_to_backtest = 1

def momentum_quick(df):
    close = df.loc[:, df.columns.get_level_values(1).isin(['Close'])].droplevel(1, axis='columns')
    high = df.loc[:, df.columns.get_level_values(1).isin(['High'])].droplevel(1, axis='columns')
    low = df.loc[:, df.columns.get_level_values(1).isin(['Low'])].droplevel(1, axis='columns')
    sma20 = close.rolling(20).mean()
    less_0day_1day = close - close.shift(1)
    # crossover
    xo = (
        (close > close.shift(1))
        & ((less_0day_1day + close) > sma20)
        & (close < sma20)
    )
    xu = (
        (close < close.shift(1))
        & ((close - less_0day_1day) < sma20)
        & (close > sma20)
    )
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (close.shift(1) < high)
    puts_hit = xu.shift(1) & (close.shift(1) > low)
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df