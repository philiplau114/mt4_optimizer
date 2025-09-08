import pandas as pd
import numpy as np
import sys
import argparse
from datetime import datetime, timedelta

def read_mt4_csv(csv_path):
    """
    Reads MT4 CSV file with columns: Date, Time, Open, High, Low, Close, Tick volume.
    Returns DataFrame of price bars with 'datetime' column.
    """
    # Try auto delimiter detection (tab or comma)
    with open(csv_path, 'r', encoding='utf-8') as f:
        sample = f.read(2048)
        delimiter = '\t' if '\t' in sample else ','
    df = pd.read_csv(csv_path, delimiter=delimiter)
    # Rename columns if needed (handle variations in headers)
    df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]
    # Parse datetime column
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S')
    else:
        raise ValueError("CSV must have 'Date' and 'Time' columns")
    # Standardize field names
    rename_map = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'tick_volume': 'volume',   # for compatibility with previous code
        'tickvolume': 'volume',
        'volume': 'volume'
    }
    # Only keep needed columns
    keep = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    for k, v in rename_map.items():
        if k in df.columns:
            df[v] = df[k]
    df = df[keep]
    # Make sure all are numeric except datetime
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Filter out invalid rows
    df = df[
        (df['close'] != 0.0) &
        (df['open'] != 0.0) &
        (df['high'] != 0.0) &
        (df['low'] != 0.0) &
        df['close'].map(np.isfinite) &
        df['open'].map(np.isfinite) &
        df['high'].map(np.isfinite) &
        df['low'].map(np.isfinite)
    ].reset_index(drop=True)
    print(f"Bars after basic filtering: {len(df)}")
    return df

def filter_bars_by_years(bars, years):
    now = datetime.utcnow()
    cutoff = now - timedelta(days=365 * years)
    filtered = bars[
        (bars['datetime'] >= cutoff) &
        (bars['datetime'] <= now)
    ].reset_index(drop=True)
    print(f"Bars after years filter ({years}): {len(filtered)}")
    return filtered

def print_analysed_period(bars):
    if len(bars) == 0:
        print("No bars to analyse.")
        return
    start = bars['datetime'].iloc[0]
    end = bars['datetime'].iloc[-1]
    print(f"Analysed from {start.strftime('%Y.%m.%d %H:%M')} to {end.strftime('%Y.%m.%d %H:%M')}")

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
        dt = bars['datetime'].iloc[i]
        # Filter out invalid points again
        if not np.isfinite(price) or price == 0.0:
            continue
        if price >= max_high - deviation * 0.0001:
            if last_pivot != 'high':
                zz_points.append((dt, price))
                last_pivot = 'high'
        elif price <= min_low + deviation * 0.0001:
            if last_pivot != 'low':
                zz_points.append((dt, price))
                last_pivot = 'low'
    return zz_points

def calculate_waves(zz_points):
    waves = []
    for i in range(1, len(zz_points)):
        dt1, price1 = zz_points[i-1]
        dt2, price2 = zz_points[i]
        # Only use valid price points
        if not (np.isfinite(price1) and np.isfinite(price2)):
            continue
        if price1 == 0.0 or price2 == 0.0:
            continue
        bars = (dt2 - dt1).total_seconds() / (30*60)
        if abs(price2) < 10000 and abs(price1) < 10000:
            pips = abs(price2 - price1) * 10000
            if np.isfinite(pips) and pips < 10000 and pips > 0.0:
                waves.append({'bars': bars, 'pips': pips})
    return waves

def wave_stats(waves, normal_pct, medium_pct, rare_pct):
    waves = [w for w in waves if np.isfinite(w['pips']) and w['pips'] > 0]
    pips_arr = np.array([w['pips'] for w in waves])
    if len(pips_arr) == 0:
        print("No valid waves detected.")
        return {}

    # Calculate percentile thresholds
    normal_upper = np.percentile(pips_arr, normal_pct)
    medium_upper = np.percentile(pips_arr, normal_pct + medium_pct)
    rare_upper = np.percentile(pips_arr, 100)

    print("\nWave Frequency Bands Calculated:")
    print(f"  Normal Wave: <= {normal_upper:.2f} pips (up to {normal_pct}%)")
    print(f"  Medium Wave: > {normal_upper:.2f} and <= {medium_upper:.2f} pips (next {medium_pct}%)")
    print(f"  Rare Wave: > {medium_upper:.2f} and <= {rare_upper:.2f} pips (top {rare_pct}%)\n")

    normal_mask = (pips_arr <= normal_upper)
    medium_mask = (pips_arr > normal_upper) & (pips_arr <= medium_upper)
    rare_mask = (pips_arr > medium_upper) & (pips_arr <= rare_upper)

    results = {}
    for name, mask in zip(['Normal', 'Medium', 'Rare'], [normal_mask, medium_mask, rare_mask]):
        ws = [w for w, m in zip(waves, mask) if m]
        if ws:
            results[name] = {
                'Count': len(ws),
                'TotalPips': sum(w['pips'] for w in ws),
                'AverageBars': np.mean([w['bars'] for w in ws]),
                'AveragePips': np.mean([w['pips'] for w in ws]),
                'LongestBars': max(w['bars'] for w in ws),
                'LongestPips': max(w['pips'] for w in ws),
                'ShortestBars': min(w['bars'] for w in ws),
                'ShortestPips': min(w['pips'] for w in ws),
            }
    return results

def main():
    parser = argparse.ArgumentParser(description="Analyze MT4 CSV file for wave frequencies using ZigZag settings.")
    parser.add_argument('--csv_path', type=str, required=True, help='Path to MT4 CSV file')
    parser.add_argument('--depth', type=int, default=12, help='ZigZag Depth')
    parser.add_argument('--deviation', type=float, default=5, help='ZigZag Deviation')
    parser.add_argument('--backstep', type=int, default=3, help='ZigZag Backstep')
    parser.add_argument('--percentage', type=float, default=50.0, help='ZigZag Percentage (unused)')
    parser.add_argument('--force_factor', type=float, default=3, help='Force Factor (unused)')
    parser.add_argument('--normal_wave', type=float, default=80, help='Normal Wave percentile')
    parser.add_argument('--medium_wave', type=float, default=15, help='Medium Wave percentile')
    parser.add_argument('--rare_wave', type=float, default=5, help='Rare Wave percentile')
    parser.add_argument('--years', type=int, default=5, help='How many years of recent data to analyze')

    args = parser.parse_args()

    bars = read_mt4_csv(args.csv_path)
    bars = filter_bars_by_years(bars, args.years)
    print_analysed_period(bars)
    print(f"First 10 bar close prices (filtered):")
    print(bars['close'].head(10).to_list())
    zz_points = zigzag(bars, args.depth, args.deviation, args.backstep)
    print(f"ZigZag points found: {len(zz_points)}")
    print("ZigZag points (datetime, price):")
    for point in zz_points[:20]:
        print(point)
    waves = calculate_waves(zz_points)
    print(f"Waves calculated: {len(waves)}")
    print("Waves (bars, pips):")
    for w in waves[:20]:
        print(f"bars={w['bars']}, pips={w['pips']}")

    stats = wave_stats(
        waves,
        normal_pct=args.normal_wave,
        medium_pct=args.medium_wave,
        rare_pct=args.rare_wave,
    )
    for wave_type, data in stats.items():
        print(f"{wave_type} Wave Frequency:")
        for k, v in data.items():
            print(f"  {k}: {v}")
        print()

if __name__ == '__main__':
    main()