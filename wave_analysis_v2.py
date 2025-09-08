import struct
import pandas as pd
import numpy as np
import sys
import argparse
from datetime import datetime

def inspect_hst_header(hst_path):
    with open(hst_path, 'rb') as f:
        header = f.read(148)
        version = struct.unpack('<I', header[12:16])[0]
        copyright_str = header[20:76].decode(errors='replace')
        symbol = header[76:88].decode(errors='replace').strip('\x00')
        period = struct.unpack('<I', header[88:92])[0]
        digits = struct.unpack('<I', header[92:96])[0]
        print("---- HST Header Info ----")
        print(f"Version   : {version}")
        print(f"Copyright : {copyright_str}")
        print(f"Symbol    : {symbol}")
        print(f"Period    : {period}")
        print(f"Digits    : {digits}")
        print(f"First 64 bytes: {header[:64]}")
        print("-------------------------")
        return version

def read_mt4_hst_auto(hst_path):
    version = inspect_hst_header(hst_path)
    bars = []
    with open(hst_path, 'rb') as f:
        header = f.read(148)
        if version >= 400:  # Build 600+ (modern MT4)
            bar_size = 60
            bar_struct = '<I4dQIIII'
            while True:
                bar = f.read(bar_size)
                if len(bar) < bar_size:
                    break
                try:
                    time, open_, high, low, close, volume, spread, reserved1, reserved2, reserved3 = struct.unpack(bar_struct, bar)
                except Exception as e:
                    print(f"Error unpacking bar: {e}")
                    continue
                dt = datetime.utcfromtimestamp(time)
                bars.append({
                    'datetime': dt,
                    'open': open_,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'spread': spread
                })
        else:  # Build < 600 (old MT4)
            bar_size = 44
            bar_struct = '<I4f2I'
            while True:
                bar = f.read(bar_size)
                if len(bar) < bar_size:
                    break
                try:
                    time, open_, low, high, close, volume, spread = struct.unpack(bar_struct, bar)
                except Exception as e:
                    print(f"Error unpacking bar: {e}")
                    continue
                dt = datetime.utcfromtimestamp(time)
                bars.append({
                    'datetime': dt,
                    'open': open_,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'spread': spread
                })
    df = pd.DataFrame(bars)
    for col in ['open', 'high', 'low', 'close']:
        df = df[df[col].map(lambda x: np.isfinite(x) and abs(x) < 1000)]
    df = df.reset_index(drop=True)
    return df

def zigzag(bars, depth, deviation, backstep):
    highs = bars['high'].values
    lows = bars['low'].values
    zz_points = []
    last_pivot = None
    for i in range(depth, len(bars) - backstep):
        window_high = highs[i - depth:i + 1]
        window_low = lows[i - depth:i + 1]
        max_high = window_high.max()
        min_low = window_low.min()
        price = bars['close'].iloc[i]
        if not np.isfinite(price) or abs(price) > 1000:
            continue
        if price >= max_high - deviation * 0.0001:
            if last_pivot != 'high':
                zz_points.append((bars['datetime'].iloc[i], price))
                last_pivot = 'high'
        elif price <= min_low + deviation * 0.0001:
            if last_pivot != 'low':
                zz_points.append((bars['datetime'].iloc[i], price))
                last_pivot = 'low'
    return zz_points

def calculate_waves(zz_points):
    waves = []
    for i in range(1, len(zz_points)):
        dt1, price1 = zz_points[i-1]
        dt2, price2 = zz_points[i]
        if not (np.isfinite(price1) and np.isfinite(price2)):
            continue
        bars = (dt2 - dt1).total_seconds() / (30*60)
        if abs(price2) < 1000 and abs(price1) < 1000:
            pips = abs(price2 - price1) * 10000
            if np.isfinite(pips) and pips < 10000:
                waves.append({'bars': bars, 'pips': pips})
    return waves

def print_wave_metrics(waves):
    pips_arr = np.array([w['pips'] for w in waves if np.isfinite(w['pips'])])
    if len(pips_arr) == 0:
        print("No valid waves detected.")
        return
    print(f"Total waves: {len(pips_arr)}")
    print(f"Min pips: {np.min(pips_arr):.2f}")
    print(f"Max pips: {np.max(pips_arr):.2f}")
    print(f"Mean pips: {np.mean(pips_arr):.2f}")
    print(f"Stddev pips: {np.std(pips_arr):.2f}")
    print("Percentiles (pips):")
    for pct in [5, 15, 25, 50, 75, 85, 95, 99]:
        print(f"  {pct}%: {np.percentile(pips_arr, pct):.2f}")
    print("First 20 wave pips (sorted):")
    print(np.sort(pips_arr)[:20])
    print("Last 20 wave pips (sorted):")
    print(np.sort(pips_arr)[-20:])

def main():
    parser = argparse.ArgumentParser(description="Auto-detect and analyze MT4 HST file format.")
    parser.add_argument('--hst_path', type=str, required=True, help='Path to MT4 HST file')
    parser.add_argument('--depth', type=int, default=12, help='ZigZag Depth')
    parser.add_argument('--deviation', type=float, default=5, help='ZigZag Deviation')
    parser.add_argument('--backstep', type=int, default=3, help='ZigZag Backstep')
    args = parser.parse_args()

    bars = read_mt4_hst_auto(args.hst_path)
    print(f"\nTotal bars loaded: {len(bars)}")
    print("First 10 bar close prices:")
    print(bars['close'].head(10).to_list())

    zz_points = zigzag(bars, args.depth, args.deviation, args.backstep)
    print(f"\nZigZag points found: {len(zz_points)}")
    print("ZigZag points (datetime, price):")
    for point in zz_points:
        print(point)

    waves = calculate_waves(zz_points)
    print(f"\nWaves calculated: {len(waves)}")
    print("Waves (bars, pips):")
    for w in waves:
        print(f"bars={w['bars']}, pips={w['pips']}")

    print_wave_metrics(waves)

if __name__ == '__main__':
    main()