print(__name__)
import pandas as pd
import pandas_ta as ta

strategy_name = 'ADX Reversal (Alternative)'
days_to_backtest = 1

def adx_reversal_alt(df):
    symbols = df.columns.get_level_values(0).unique().sort_values(ascending=True)
    adx = pd.DataFrame()
    for symbol in symbols:
        adx_single = df[symbol].ta.adx()
        adx_single['Ticker'] = symbol
        adx_single = adx_single.set_index('Ticker', append=True).unstack('Ticker').swaplevel(axis=1)
        adx = pd.concat([adx, adx_single], axis=1)
    
    close = df.loc[:, df.columns.get_level_values(1).isin(['Close'])].droplevel(1, axis='columns')
    high = df.loc[:, df.columns.get_level_values(1).isin(['High'])].droplevel(1, axis='columns')
    low = df.loc[:, df.columns.get_level_values(1).isin(['Low'])].droplevel(1, axis='columns')
    adx_14 = adx.loc[:, adx.columns.get_level_values(1).isin(['ADX_14'])].droplevel(1, axis='columns')
    dmp_14 = adx.loc[:, adx.columns.get_level_values(1).isin(['DMP_14'])].droplevel(1, axis='columns')
    dmn_14 = adx.loc[:, adx.columns.get_level_values(1).isin(['DMN_14'])].droplevel(1, axis='columns')
    
    adx_is_increasing = adx_14 > adx_14.shift(1)
    adx_is_decreasing = adx_14 < adx_14.shift(1)
    adx_gt_40 = adx_14 > 40
    dmp_gt_40 = dmp_14 > 40
    dmn_gt_40 = dmn_14 > 40
    dmp_lt_10 = dmp_14 < 10
    dmn_lt_10 = dmn_14 < 10
    
    # crossover
    xo = adx_is_increasing & adx_gt_40 & dmp_gt_40 & dmn_lt_10
    xu = adx_is_increasing & adx_gt_40 & dmn_gt_40 & dmp_lt_10
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (close.shift(1) < high)
    puts_hit = xu.shift(1) & (close.shift(1) > low)
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df