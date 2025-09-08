import pandas as pd
import numpy as np
import argparse
from datetime import datetime

def read_mt4_csv(csv_path):
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

def zigzag_mt4_pivots(bars, depth, deviation, backstep):
    lows = bars['low'].values
    highs = bars['high'].values
    times = bars['datetime'].values
    N = len(lows)
    Point = 0.0001

    ExtZigzagBuffer = np.zeros(N)
    ExtHighBuffer = np.zeros(N)
    ExtLowBuffer = np.zeros(N)

    def InitializeAll():
        ExtZigzagBuffer.fill(0.0)
        ExtHighBuffer.fill(0.0)
        ExtLowBuffer.fill(0.0)
        return N - depth

    limit = InitializeAll()
    lastlow = 0.0
    lasthigh = 0.0

    for i in range(limit-1, -1, -1):
        idx_min = i + np.argmin(lows[i:i+depth])
        extremum = lows[idx_min]
        if extremum == lastlow:
            extremum = 0.0
        else:
            lastlow = extremum
            if lows[i]-extremum > deviation*Point:
                extremum = 0.0
            else:
                for back in range(1, backstep+1):
                    pos = i + back
                    if pos < N and ExtLowBuffer[pos]!=0 and ExtLowBuffer[pos]>extremum:
                        ExtLowBuffer[pos] = 0.0
        if lows[i]==extremum:
            ExtLowBuffer[i]=extremum
        else:
            ExtLowBuffer[i]=0.0

        idx_max = i + np.argmax(highs[i:i+depth])
        extremum = highs[idx_max]
        if extremum == lasthigh:
            extremum = 0.0
        else:
            lasthigh = extremum
            if extremum-highs[i] > deviation*Point:
                extremum = 0.0
            else:
                for back in range(1, backstep+1):
                    pos = i + back
                    if pos < N and ExtHighBuffer[pos]!=0 and ExtHighBuffer[pos]<extremum:
                        ExtHighBuffer[pos]=0.0
        if highs[i]==extremum:
            ExtHighBuffer[i]=extremum
        else:
            ExtHighBuffer[i]=0.0

    pivots = []
    whatlookfor = 0
    lastlow = 0.0
    lasthigh = 0.0
    lasthighpos = None
    lastlowpos = None

    for i in range(limit-1, -1, -1):
        if whatlookfor == 0:
            if lastlow == 0.0 and lasthigh == 0.0:
                if ExtHighBuffer[i] != 0.0:
                    lasthigh = highs[i]
                    lasthighpos = i
                    whatlookfor = -1
                    ExtZigzagBuffer[i]=lasthigh
                    pivots.append((times[i], lasthigh, 'High'))
                if ExtLowBuffer[i] != 0.0:
                    lastlow = lows[i]
                    lastlowpos = i
                    whatlookfor = 1
                    ExtZigzagBuffer[i]=lastlow
                    pivots.append((times[i], lastlow, 'Low'))
        elif whatlookfor == 1:  # look for peak
            if ExtLowBuffer[i]!=0.0 and ExtLowBuffer[i]<lastlow and ExtHighBuffer[i]==0.0:
                ExtZigzagBuffer[lastlowpos]=0.0
                lastlowpos = i
                lastlow = ExtLowBuffer[i]
                ExtZigzagBuffer[i]=lastlow
                pivots[-1] = (times[i], lastlow, 'Low')
            if ExtHighBuffer[i]!=0.0 and ExtLowBuffer[i]==0.0:
                lasthigh = ExtHighBuffer[i]
                lasthighpos = i
                ExtZigzagBuffer[i]=lasthigh
                whatlookfor = -1
                pivots.append((times[i], lasthigh, 'High'))
        elif whatlookfor == -1:  # look for lawn
            if ExtHighBuffer[i]!=0.0 and ExtHighBuffer[i]>lasthigh and ExtLowBuffer[i]==0.0:
                ExtZigzagBuffer[lasthighpos]=0.0
                lasthighpos = i
                lasthigh = ExtHighBuffer[i]
                ExtZigzagBuffer[i]=lasthigh
                pivots[-1] = (times[i], lasthigh, 'High')
            if ExtLowBuffer[i]!=0.0 and ExtHighBuffer[i]==0.0:
                lastlow = ExtLowBuffer[i]
                lastlowpos = i
                ExtZigzagBuffer[i]=lastlow
                whatlookfor = 1
                pivots.append((times[i], lastlow, 'Low'))

    pivots = pivots[::-1]
    return pivots

def calculate_waves_from_pivots(filtered_pivots):
    waves = []
    for i in range(1, len(filtered_pivots)):
        dt1, price1, type1 = filtered_pivots[i - 1]
        dt2, price2, type2 = filtered_pivots[i]
        bars = (pd.to_datetime(dt2) - pd.to_datetime(dt1)).total_seconds() / (30 * 60)
        pips = abs(price2 - price1) * 10000
        wave_type = type2
        if pips > 0 and bars > 0:
            waves.append({'bars': bars, 'pips': pips, 'type': wave_type, 'start': pd.to_datetime(dt1), 'end': pd.to_datetime(dt2)})
    return waves

def filter_waves(waves, percentage=50.0, force_factor=3, deviation=5):
    if percentage == 0.0 and force_factor == 0:
        return waves
    filtered = []
    prev_type = None
    prev_pips = None
    for wave in waves:
        this_type = wave['type']
        pips = wave['pips']
        if prev_type == this_type:
            percentage_ok = (prev_pips is None or pips >= prev_pips * (percentage / 100.0))
            force_ok = pips >= (force_factor * deviation)
            if percentage_ok and force_ok:
                filtered.append(wave)
                prev_type = this_type
                prev_pips = pips
            else:
                if filtered:
                    filtered[-1] = wave
        else:
            filtered.append(wave)
            prev_type = this_type
            prev_pips = pips
    return filtered

def wave_band_bar_stats(bars, pivots, percentiles):
    # For each interval between pivots, assign all bars in interval to a wave band
    if len(pivots) < 2:
        return []
    pips_list = [abs(pivots[i][1] - pivots[i-1][1]) * 10000 for i in range(1, len(pivots))]
    edges = np.percentile(pips_list, percentiles)
    band_edges = [
        (min(pips_list), edges[0]),
        (edges[0], edges[1]),
        (edges[1], edges[2])
    ]
    band_counts = [0, 0, 0]
    band_pips = [0.0, 0.0, 0.0]
    band_bars = [[], [], []]
    band_pips_list = [[], [], []]
    for i in range(1, len(pivots)):
        start = pd.to_datetime(pivots[i-1][0])
        end = pd.to_datetime(pivots[i][0])
        wave_pips = abs(pivots[i][1] - pivots[i-1][1]) * 10000
        wave_bars = bars[(bars['datetime'] > start) & (bars['datetime'] <= end)]
        for j, (low, high) in enumerate(band_edges):
            # Last band is inclusive of high edge
            if (j < 2 and low <= wave_pips < high) or (j == 2 and low <= wave_pips <= high):
                band_counts[j] += len(wave_bars)
                band_pips[j] += wave_pips * len(wave_bars)
                band_bars[j].append(len(wave_bars))
                band_pips_list[j].append(wave_pips)
                break
    stats = []
    for j in range(3):
        avg_bars = np.mean(band_bars[j]) if band_bars[j] else 0
        longest_bars = max(band_bars[j]) if band_bars[j] else 0
        shortest_bars = min(band_bars[j]) if band_bars[j] else 0
        avg_pips = band_pips[j] / band_counts[j] if band_counts[j] else 0
        # longest/shortest pips is taken from the pips value of the longest/shortest bar
        if band_bars[j]:
            idx_longest = np.argmax(band_bars[j])
            idx_shortest = np.argmin(band_bars[j])
            longest_pips = band_pips_list[j][idx_longest]
            shortest_pips = band_pips_list[j][idx_shortest]
        else:
            longest_pips = 0
            shortest_pips = 0
        stats.append({
            'count': band_counts[j],
            'total_pips': band_pips[j],
            'avg_bars': avg_bars,
            'avg_pips': avg_pips,
            'longest_bars': longest_bars,
            'longest_pips': longest_pips,
            'shortest_bars': shortest_bars,
            'shortest_pips': shortest_pips,
            'min_pips': band_edges[j][0],
            'max_pips': band_edges[j][1]
        })
    return stats

def print_band(name, stats, percent):
    if not stats: return
    print(f"{name} Wave Frequency ({percent}%): {int(stats['min_pips'])} Pips - {int(stats['max_pips'])} Pips")
    print(f"Total: {int(stats['count'])} bars with {stats['total_pips']:.1f} pips")
    print(f"Average: {stats['avg_bars']:.1f} bars with {stats['avg_pips']:.1f} pips")
    print(f"Longest: {int(stats['longest_bars'])} bars with {stats['longest_pips']:.1f} pips")
    print(f"Shortest: {int(stats['shortest_bars'])} bars with {stats['shortest_pips']:.1f} pips\n")

def print_wave_samples(waves, count=10):
    print(f"\nWaves: First {count} entries")
    for w in waves[:count]:
        print(f"bars={w['bars']:.1f}, pips={w['pips']:.1f}, start={w['start']}, end={w['end']}")

def main():
    parser = argparse.ArgumentParser(description="Analyze MT4 CSV file for wave frequencies using ZigZag settings.")
    parser.add_argument('--csv_path', type=str, required=True, help='Path to MT4 CSV file')
    parser.add_argument('--depth', type=int, default=12, help='ZigZag Depth')
    parser.add_argument('--deviation', type=float, default=5, help='ZigZag Deviation')
    parser.add_argument('--backstep', type=int, default=3, help='ZigZag Backstep')
    parser.add_argument('--percentage', type=float, default=50.0, help='Minimum % of previous wave for filtering')
    parser.add_argument('--force_factor', type=float, default=3, help='Minimum multiple of deviation for wave filtering')
    parser.add_argument('--normal_wave', type=float, default=80, help='Normal Wave percentile')
    parser.add_argument('--medium_wave', type=float, default=15, help='Medium Wave percentile')
    parser.add_argument('--rare_wave', type=float, default=5, help='Rare Wave percentile')
    parser.add_argument('--start_date', type=str, default=None, help='Analysis start date (YYYY-MM-DD HH:MM)')
    parser.add_argument('--end_date', type=str, default=None, help='Analysis end date (YYYY-MM-DD HH:MM)')

    args = parser.parse_args()

    bars = read_mt4_csv(args.csv_path)

    if args.start_date and args.end_date:
        try:
            start_dt = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(args.end_date, "%Y-%m-%d %H:%M")
            bars = filter_bars_by_date_range(bars, start_dt, end_dt)
        except Exception as e:
            print("Error parsing start/end date. Please use the format YYYY-MM-DD HH:MM")
            return

    print_analysed_period(bars)
    pivots = zigzag_mt4_pivots(bars, args.depth, args.deviation, args.backstep)
    print("First 20 pivots from Python:")
    for p in pivots[:20]:
        print(f"{p[0]}, {p[1]:.5f}, {p[2]}")
    waves = calculate_waves_from_pivots(pivots)
    waves_filtered = filter_waves(waves, args.percentage, args.force_factor, args.deviation)
    print_wave_samples(waves_filtered, count=10)
    percentiles = [args.normal_wave, args.normal_wave + args.medium_wave, 100]
    band_stats_list = wave_band_bar_stats(bars, pivots, percentiles)
    band_names = ["Normal", "Medium", "Rare"]
    for name, stats, percent in zip(band_names, band_stats_list, [args.normal_wave, args.medium_wave, args.rare_wave]):
        print_band(name, stats, percent)

if __name__ == '__main__':
    main()