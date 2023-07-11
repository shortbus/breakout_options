print(__name__)
import pandas as pd

strategy_name = 'Breakout Predict'
days_to_backtest = 1

def breakout_predict(df):
    # assign variables
    high = df.loc[:, df.columns.get_level_values(1).isin(['High'])].droplevel(1, axis='columns')
    low = df.loc[:, df.columns.get_level_values(1).isin(['Low'])].droplevel(1, axis='columns')
    close = df.loc[:, df.columns.get_level_values(1).isin(['Close'])].droplevel(1, axis='columns')
    #
    upper = high * (1 + 4 * (high - low) / (high + low))
    lower = low * (1 - 4 * (high - low) / (high + low))
    upper_band = upper.rolling(20).mean()
    lower_band = lower.rolling(20).mean()
    sma20 = close.rolling(20).mean()
    #
    less_0day_1day = close - close.shift(1)
    xo = (
        (close > close.shift(1))
        & ((less_0day_1day + close) > upper_band)
        & (close > sma20)
    )
    xu = (
        (close < close.shift(1))
        & ((close - less_0day_1day) < lower_band)
        & (close < sma20)
    )
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (high > close.shift(1))
    puts_hit = xu.shift(1) & (low < close.shift(1))
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df