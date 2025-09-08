import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta

def read_mt4_csv(csv_path):
    """Reads MT4 CSV file with columns: Date, Time, Open, High, Low, Close, Tick volume.
    Returns DataFrame of price bars with 'datetime' column."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        sample = f.read(2048)
        delimiter = '\t' if '\t' in sample else ','
    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S')
    else:
        raise ValueError("CSV must have 'Date' and 'Time' columns")
    rename_map = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'tick_volume': 'volume',
        'tickvolume': 'volume',
        'volume': 'volume'
    }
    keep = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    for k, v in rename_map.items():
        if k in df.columns:
            df[v] = df[k]
    df = df[keep]
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
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
    return df

def filter_bars_by_date_range(bars, start_date, end_date):
    filtered = bars[(bars['datetime'] >= start_date) & (bars['datetime'] <= end_date)].reset_index(drop=True)
    return filtered

def print_analysed_period(bars):
    if len(bars) == 0:
        print("No bars to analyse.")
        return
    start = bars['datetime'].iloc[0]
    end = bars['datetime'].iloc[-1]
    print(f"\nAnalysed from {start.strftime('%Y.%m.%d %H:%M')} to {end.strftime('%Y.%m.%d %H:%M')}\n")

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

def calculate_waves(zz_points, percentage=50.0, force_factor=3, deviation=5):
    # Only keep waves that are at least X% of previous swing, and above force factor threshold
    waves = []
    prev_pips = None
    for i in range(1, len(zz_points)):
        dt1, price1 = zz_points[i-1]
        dt2, price2 = zz_points[i]
        if not (np.isfinite(price1) and np.isfinite(price2)):
            continue
        if price1 == 0.0 or price2 == 0.0:
            continue
        bars = (dt2 - dt1).total_seconds() / (30*60)
        if abs(price2) < 10000 and abs(price1) < 10000:
            pips = abs(price2 - price1) * 10000
            # Percentage filter: must be at least X% of previous swing
            if prev_pips is not None:
                if pips < prev_pips * (percentage / 100.0):
                    prev_pips = pips
                    continue
            # Force factor filter: must be at least force_factor * deviation pips
            if pips < force_factor * deviation:
                prev_pips = pips
                continue
            waves.append({'bars': bars, 'pips': pips})
            prev_pips = pips
        else:
            prev_pips = None
    return waves

def band_stats(waves, pips_arr, lower, upper):
    mask = (pips_arr > lower) & (pips_arr <= upper)
    ws = [w for w, m in zip(waves, mask) if m]
    if not ws:
        return None
    total_bars = sum(w['bars'] for w in ws)
    total_pips = sum(w['pips'] for w in ws)
    avg_bars = np.mean([w['bars'] for w in ws])
    avg_pips = np.mean([w['pips'] for w in ws])
    longest = max(ws, key=lambda w: w['bars'])
    shortest = min(ws, key=lambda w: w['bars'])
    return dict(
        count=len(ws),
        total_bars=total_bars,
        total_pips=total_pips,
        avg_bars=avg_bars,
        avg_pips=avg_pips,
        longest_bars=longest['bars'],
        longest_pips=longest['pips'],
        shortest_bars=shortest['bars'],
        shortest_pips=shortest['pips'],
        min_pips=lower,
        max_pips=upper
    )

def print_band(name, stats, percent):
    if not stats: return
    print(f"{name} Wave Frequency ({percent}%): {int(stats['min_pips'])} Pips - {int(stats['max_pips'])} Pips")
    print(f"Total: {int(stats['count'])} bars with {stats['total_pips']:.1f} pips")
    print(f"Average: {stats['avg_bars']:.1f} bars with {stats['avg_pips']:.1f} pips")
    print(f"Longest: {int(stats['longest_bars'])} bars with {stats['longest_pips']:.1f} pips")
    print(f"Shortest: {int(stats['shortest_bars'])} bars with {stats['shortest_pips']:.1f} pips\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze MT4 CSV file for wave frequencies using ZigZag settings.")
    parser.add_argument('--csv_path', type=str, required=True, help='Path to MT4 CSV file')
    parser.add_argument('--depth', type=int, default=12, help='ZigZag Depth')
    parser.add_argument('--deviation', type=float, default=5, help='ZigZag Deviation')
    parser.add_argument('--backstep', type=int, default=3, help='ZigZag Backstep')
    parser.add_argument('--percentage', type=float, default=50.0, help='Only consider moves at least X%% of previous swing')
    parser.add_argument('--force_factor', type=float, default=3, help='Force Factor for wave selection')
    parser.add_argument('--normal_wave', type=float, default=80, help='Normal Wave percentile')
    parser.add_argument('--medium_wave', type=float, default=15, help='Medium Wave percentile')
    parser.add_argument('--rare_wave', type=float, default=5, help='Rare Wave percentile')
    parser.add_argument('--start_date', type=str, default=None, help='Analysis start date (YYYY-MM-DD HH:MM)')
    parser.add_argument('--end_date', type=str, default=None, help='Analysis end date (YYYY-MM-DD HH:MM)')

    args = parser.parse_args()

    bars = read_mt4_csv(args.csv_path)

    # Date filtering by explicit range if provided
    if args.start_date and args.end_date:
        try:
            start_dt = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(args.end_date, "%Y-%m-%d %H:%M")
            bars = filter_bars_by_date_range(bars, start_dt, end_dt)
        except Exception as e:
            print("Error parsing start/end date. Please use the format YYYY-MM-DD HH:MM")
            return

    print_analysed_period(bars)
    zz_points = zigzag(bars, args.depth, args.deviation, args.backstep)
    waves = calculate_waves(zz_points, percentage=args.percentage, force_factor=args.force_factor, deviation=args.deviation)
    waves = [w for w in waves if np.isfinite(w['pips']) and w['pips'] > 0]
    pips_arr = np.array([w['pips'] for w in waves])
    if len(pips_arr) == 0:
        print("No valid waves detected.")
        return

    # Calculate percentile edges
    normal_upper = np.percentile(pips_arr, args.normal_wave)
    medium_upper = np.percentile(pips_arr, args.normal_wave + args.medium_wave)
    rare_upper = np.percentile(pips_arr, 100)

    bands = [
        ("Normal", 0, normal_upper, args.normal_wave),
        ("Medium", normal_upper, medium_upper, args.medium_wave),
        ("Rare", medium_upper, rare_upper, args.rare_wave)
    ]
    for name, lower, upper, percent in bands:
        stats = band_stats(waves, pips_arr, lower, upper)
        print_band(f"{name}", stats, percent)

if __name__ == '__main__':
    main()