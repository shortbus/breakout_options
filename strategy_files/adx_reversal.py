print(__name__)
import pandas as pd
import pandas_ta as ta

strategy_name = 'ADX Reversal'
days_to_backtest = 1

def adx_reversal(df):
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
    
    gt_0day_1day = adx_14 > adx_14.shift(1)
    lt_0day_1day = adx_14 < adx_14.shift(1)
    lt_1day_2day = adx_14.shift(1) < adx_14.shift(2)
    gt_1day_2day = adx_14.shift(1) > adx_14.shift(2)
    dmp_gt_0day_1day = dmp_14 > dmp_14.shift(1)
    dmn_gt_0day_1day = dmn_14 > dmn_14.shift(1)
    
    # crossover
    xo = gt_0day_1day & lt_1day_2day & dmp_gt_0day_1day
    xu = lt_0day_1day & gt_1day_2day & dmn_gt_0day_1day
    # find out if previous day was successful
    calls_hit = xo.shift(1) & (close.shift(1) < high)
    puts_hit = xu.shift(1) & (close.shift(1) > low)
    df = pd.concat([xo,xu,calls_hit,puts_hit], axis=1, keys=['xo','xu','calls_hit','puts_hit']).swaplevel(axis=1)
    return df