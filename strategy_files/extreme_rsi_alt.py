print(__name__)
import pandas as pd
import pandas_ta as ta

strategy_name = 'Extreme RSI (Alternative)'
days_to_backtest = 1

def extreme_rsi_alt(df):
    symbols = df.columns.get_level_values(0).unique().sort_values(ascending=True)
    rsi = pd.DataFrame()
    rsi_params = {
        'length': 13,
        'rsi_length': 21,
        'k': 8,
        'd': 8,
    }
    rsi_column_name = (
        f'STOCHRSIk'
        f'_{rsi_params["length"]}'
        f'_{rsi_params["rsi_length"]}'
        f'_{rsi_params["k"]}'
        f'_{rsi_params["d"]}'
    )

    for symbol in symbols:
        rsi_single = df[symbol].ta.stochrsi(**rsi_params)
        rsi_single['Ticker'] = symbol
        rsi_single = rsi_single.set_index('Ticker', append=True).unstack('Ticker').swaplevel(axis=1)
        rsi = pd.concat([rsi, rsi_single], axis=1)
    
    close = df.loc[:, df.columns.get_level_values(1).isin(['Close'])].droplevel(1, axis='columns')
    high = df.loc[:, df.columns.get_level_values(1).isin(['High'])].droplevel(1, axis='columns')
    low = df.loc[:, df.columns.get_level_values(1).isin(['Low'])].droplevel(1, axis='columns')
    rsi_14 = rsi.loc[:, rsi.columns.get_level_values(1).isin([rsi_column_name])].droplevel(1, axis='columns')
    
    lt_05 = rsi_14 < 5
    gt_95 = rsi_14 > 95
    
    # crossover
    xo = lt_05
    xu = gt_95
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (close.shift(1) < high)
    puts_hit = xu.shift(1) & (close.shift(1) > low)
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df