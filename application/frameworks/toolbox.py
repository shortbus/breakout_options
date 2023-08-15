print(__name__)
import mibian
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

rsi_params = {
    'length': 13,
    'rsi_length': 21,
    'k': 8,
    'd': 8,
}
rsi_column_name = (
    f'STOCHRSId'
    f'_{rsi_params["length"]}'
    f'_{rsi_params["rsi_length"]}'
    f'_{rsi_params["k"]}'
    f'_{rsi_params["d"]}'
)

def run_backtest(db, results, days=1):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    df = db.join(results)
    strike_float = float(df['Close'].iloc[-1])
    strike = f'{strike_float:.02f}'
    df['Profit+'] = (df['High'].shift(-days).rolling(days).max() - df['Close']).where(df['xo'] == True)
    df['Profit-'] = (df['Close'] - df['Low'].shift(-days)).where(df['xu'] == True)
    df[~df['Profit+'].isnull()]
    df[~df['Profit-'].isnull()]
    # mean for crossovers
    xo_avg = df['Profit+'].median()
    xo_days = df['Profit+'].count()
    # mean for crossunders
    xu_avg = df['Profit-'].median()
    xu_days = df['Profit-'].count()
    # total median
    avg = pd.concat([df['Profit+'].dropna(), df['Profit-'].dropna()]).median()
    # total
    xo_days_win = df[df['Profit+'] >= 0]['Profit+'].count()
    xu_days_win = df[df['Profit-'] >= 0]['Profit-'].count()
    xo_days_loss = df[df['Profit+'] < 0]['Profit+'].count()
    xu_days_loss = df[df['Profit-'] < 0]['Profit-'].count()
    xo_days_total = xo_days_win + xo_days_loss
    xu_days_total = xu_days_win + xo_days_loss
    xo_ratio = (xo_days_win / xo_days_total) * 100 if xo_days_total != 0 else 0
    xu_ratio = (xu_days_win / xu_days_total) * 100 if xu_days_total != 0 else 0
    xo_profit = (xo_avg / strike_float) * 100
    xu_profit = (xu_avg / strike_float) * 100
    message_dict = {
        'call_ratio': f'{xo_ratio:.2f}%',
        'call_diff': f'{xo_avg:.2f}',
        'call_profit': f'{xo_profit:.2f}',
        'call_fraction': f'{xo_days_win}/{xo_days_total}',
        'put_ratio': f'{xu_ratio:.2f}%',
        'put_diff': f'{xu_avg:.2f}',
        'put_profit': f'{xu_profit:.2f}',
        'put_fraction': f'{xu_days_win}/{xu_days_total}',
    }
    return message_dict

def find_todays_breakout(db, fn, days=1):
    global rsi_params
    global rsi_column_name
    results = fn(db)
    symbols = results.columns.get_level_values(0).unique().sort_values(ascending=True)
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    picks = []
    for symbol in symbols:
        if results[symbol].tail(1)['xo'].bool():
            contract_type = 'call'
            cross = 'xo'
        elif results[symbol].tail(1)['xu'].bool():
            contract_type = 'put'
            cross = 'xu'
        else:
            continue
        # ignore multiple breakouts within 4 days
        if list(results[symbol][cross].tail(4)).count(True) > 1: continue
        data_copy = db[symbol].copy()
        strike_float = float(data_copy['Close'].iloc[-1])
        strike = f'{strike_float:.02f}'
        adx = data_copy.ta.adx()
        stochrsi = data_copy.ta.stochrsi(**rsi_params)
        adx_uptrend = (adx.tail(1)['ADX_14'] > adx.shift(1).tail(1)['ADX_14']).bool()
        adx_uptrend_readable = 'Up' if adx_uptrend else 'Down'
        dmi_uptrend = (adx.tail(1)['DMP_14'] > adx.tail(1)['DMN_14']).bool()
        dmi_uptrend_readable = 'Up' if dmi_uptrend else 'Down'
        rsi_uptrend = (stochrsi.tail(1)[rsi_column_name] > stochrsi.shift(1)[rsi_column_name].tail(1)).bool()
        rsi_uptrend_readable = 'Up' if rsi_uptrend else 'Down'
        pick = all([dmi_uptrend, adx_uptrend, rsi_uptrend]) or all([not dmi_uptrend, adx_uptrend, not rsi_uptrend])
        bt = run_backtest(data_copy, results[symbol].copy(), days=days)
        picks.append({
                'symbol': symbol,
                'strike': strike,
                'type': contract_type,
                'dmi': dmi_uptrend_readable,
                'rsi': rsi_uptrend_readable,
                'adx': adx_uptrend_readable,
                'pick': pick,
                'bt': bt,
            })
    return picks

def find_yesterdays_breakout(fn, grab_new: bool=False):
    if grab_new:
        data = update_historic()
    else:
        data = load_historic()
    symbols = data.columns.get_level_values(0).unique().sort_values(ascending=True)
    print('\n\n### Previous day\'s results! ###')
    for symbol in symbols:
        data_copy = data[symbol].copy()
        #data_copy.dropna(inplace=True)
        df = fn(data_copy, symbol).tail(2)
        close_yest = float(df.shift(1)['Close'].tail(1))
        high_today = float(df['High'].tail(1))
        low_today = float(df['Low'].tail(1))
        diff_call = close_yest - high_today
        diff_put = low_today - close_yest
        if df.shift(1)['xo'].tail(1).bool():
            if df.tail(1)['calls_hit'].bool():
                print(symbol, f'(CALL) hit!\t(+${abs(diff_call):.02f})')
            else:
                #print(symbol, '(CALL) fail,', f'{close_yest:.02f} > {high_today:.02f} by {diff_call:.02f}')
                print(symbol, f'(PUT) fail,\tby {diff_call:.02f}')
        elif df.shift(1)['xu'].tail(1).bool():
            if df.tail(1)['puts_hit'].bool():
                print(symbol, f'(PUT) hit!\t(-${abs(diff_put):.02f})')
            else:
                #print(symbol, '(PUT) fail,', f'{close_yest:.02f} < {low_today:.02f} by {diff_put:.02f}')
                print(symbol, f'(PUT) fail,\tby {diff_put:.02f}')

def get_pricing(symbol, pick_type, gain):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    anticipated_gain = float(gain)
    t = yf.Ticker(symbol)
    e = t.options
    df = t.history(period='1d', interval='1d')
    s = float(df['Close'].iloc[-1])
    output = []
    for exp in e:
        msg = {
            'date': exp,
            'strike': 'n/a',
            'iv': 'n/a',
            'delta': 'n/a',
            'gamma': 'n/a',
            'theta': 'n/a',
            'gain_percent': 'n/a',
            'buy_price': 'n/a',
            'sell_price': 'n/a',
            'unit_price': 'n/a',
            'oi': 'n/a',
            'bid': 'n/a',
            'ask': 'n/a',
            'bid-ask': 'n/a',
            'msg': '',
        }
        c = t.option_chain(exp)
        #anticipated_gain = 0.77
        est = float(s) + anticipated_gain
        if pick_type == 'call':
            strikes = c.calls.strike.values
        else:
            strikes = c.puts.strike.values
        # Skip empty option chains
        if len(strikes) == 0:
            #print(f'{exp} exp.\tEMPTY CHAIN')
            msg['msg'] = 'EMPTY CHAIN'
            output.append(msg)
            continue
        near_idx = min(range(len(strikes)),key = lambda i: abs(strikes[i]-float(s)))
        nearest = strikes[near_idx]
        if pick_type == 'call':
            nearest_strike = c.calls[c.calls.strike == nearest]
        else:
            nearest_strike = c.puts[c.puts.strike == nearest]
        oi = nearest_strike.openInterest.iloc[-1]
        msg['oi'] = float(oi)
        unit_price = float(nearest_strike.lastPrice.iloc[-1]) * 100
        msg['unit_price'] = f'{unit_price:.2f}'
        # Skip wide bid-ask spread, by $0.10
        bid = nearest_strike.bid.iloc[-1]
        msg['bid'] = f'{bid:.2f}'
        ask = nearest_strike.ask.iloc[-1]
        msg['ask'] = f'{ask:.2f}'
        bid_ask_spread = abs(float(bid) - float(ask))
        msg['bid-ask'] = f'{bid_ask_spread:.2f}'
        if bid_ask_spread > 0.20:
            #print(f'{exp} exp.\tWide Bid/Ask')
            msg['msg'] = 'Bid/Ask > 20'
            #output.append(msg)
            #continue
        price = float(nearest_strike.lastPrice.iloc[-1])
        dte = (datetime.strptime(exp, '%Y-%m-%d') - now).days
        print(s.__repr__(), type(s), nearest.__repr__(), type(nearest), dte.__repr__(), type(dte))
        if pick_type == 'call':
            bso_iv = mibian.BS([
                s,
                float(nearest),
                0,
                dte,
            ], callPrice=price)
        else:
            bso_iv = mibian.BS([
                s,
                float(nearest),
                0,
                dte,
            ], putPrice=price)
        iv = bso_iv.impliedVolatility
        msg['iv'] = f'{iv:.2f}'
        bso = mibian.BS([
            s,
            float(nearest),
            0,
            dte,
        ], volatility=iv)
        delta = bso.__dict__.get(f'{pick_type}Delta')
        gamma = bso.gamma
        theta = bso.__dict__.get(f'{pick_type}Theta')
        msg['delta'] = f'{delta:.2f}'
        msg['gamma'] = f'{gamma:.2f}'
        msg['theta'] = f'{theta:.2f}'
        # assumed delta of ATM
        #delta = 0.5
        contract_gain = delta * (anticipated_gain / 1)
        anticipated_total = price + contract_gain
        percent_gain = float((abs(anticipated_total - price) / price) * 100)
        # Warn of 0DTE, not exclude
        if exp == today:
            if msg['msg']:
                msg['msg'] += '\t!!! WARNING: 0DTE !!!'
            else:
                msg['msg'] = '!!! WARNING: 0DTE !!!'
        msg['strike'] = f'{nearest:.2f}'
        msg['gain_percent'] = f'{percent_gain:.02f}%'
        msg['buy_price'] = f'{price:.2f}'
        msg['sell_price'] = f'{anticipated_total:.2f}'
        output.append(msg)
    return output

if __name__ == '__main__':
    ...
