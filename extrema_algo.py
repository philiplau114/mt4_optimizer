import sys

import mplcyberpunk

### pandas version must be 1.5.3 ###
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

pd.set_option('display.max_rows',None)
pd.set_option('display.max_columns',None)
pd.set_option('display.width', 4096)

def local_top(df_close, curr_index, order):
    if curr_index < order * 2 + 1:
        return False

    top = True
    k = curr_index - order
    v = df_close[k]
    for i in range(1, order + 1):
        if df_close[k + i] > v or df_close[k - i] > v:
            top = False
            break
    
    return top

def local_bottom(df_close, curr_index, order):

    if curr_index < order * 2 + 1:
        return False

    bottom = True
    k = curr_index - order
    v = df_close[k]
    for i in range(1, order + 1):
        if df_close[k + i] < v or df_close[k - i] < v:
            bottom = False
            break
    
    return bottom

def local_extrema(df, order, threshold, only_extrema):
    tops = []
    bottoms = []
    up_trend = False
    confirm_i = 0

    df_close = df['close'].to_numpy()
    tmp_min = df.at[df.index[0], 'low']
    tmp_max = df.at[df.index[0], 'high']
    tmp_min_i = 0
    tmp_max_i = 0


    for i in range(len(df)):
        now_high  = df.at[df.index[i], 'high']
        now_low   = df.at[df.index[i], 'low']
        now_close = df.at[df.index[i], 'close']
        
        if up_trend:

            if now_close > tmp_max:
                tmp_max = now_close
                tmp_max_i = i

            if i - order > confirm_i and \
                    (local_top(df_close, i, order) or (not only_extrema and now_close < tmp_max - tmp_max * threshold)):
                top = [i, df_close[i] * 1.1 , i - order, df_close[i - order]]
                tops.append(top)
                up_trend = False
                confirm_i = i
                tmp_min = now_low
                tmp_min_i = i

        elif not up_trend:

            if now_close < tmp_min:
                tmp_min = now_close
                tmp_min_i = i

            if i - order > confirm_i and \
                    (local_bottom(df_close, i, order) or (not only_extrema and now_close > tmp_min + tmp_min * threshold)):
                bottom = [i, df_close[i]  * 0.9 , i - order, df_close[i - order]]
                bottoms.append(bottom)
                up_trend = True
                confirm_i = i
                tmp_max = now_high
                tmp_max_i = i

    return tops, bottoms



if __name__ == "__main__":

    start_date = '2022-01-01'
    end_date   = '2023-10-25'

    order = 15
    threshold = 0.1

    show_extrema = False
    show_confirm = True

    only_extrema = True

    ###################################################################

    df = yf.Ticker('0388.HK').history(start=start_date, end=end_date)
    df.columns = df.columns.str.lower()

    tops, bottoms = local_extrema(df, order, threshold, only_extrema)

    plt.style.use("cyberpunk")
    plt.figure(figsize=(10,6))
    df['close'].plot()

    mplcyberpunk.add_underglow()
    mplcyberpunk.add_glow_effects()
    mplcyberpunk.add_gradient_fill(alpha_gradientglow=0.5)

    for top in tops:
        if show_confirm: plt.plot(df.index[top[0]], top[1], marker='v', markersize=11, color='yellow')
        if show_extrema: plt.plot(df.index[top[2]], top[3], marker='v', markersize=11, color='gold')

    for bottom in bottoms:
        if show_confirm: plt.plot(df.index[bottom[0]], bottom[1], marker='^', markersize=11, color='white')
        if show_extrema: plt.plot(df.index[bottom[2]], bottom[3], marker='^', markersize=11, color='silver')

    if only_extrema: plt.savefig('only_extrema.png')
    if not only_extrema: plt.savefig('not_only_extrema.png')

    plt.show()

















