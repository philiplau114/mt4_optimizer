import pandas as pd
import numpy as np
import argparse
import logging

logging.getLogger().handlers = []  # Remove all handlers
logging.disable(logging.CRITICAL)  # Disable all logging
logger = logging.getLogger(__name__)

from datetime import datetime

def read_mt4_csv(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        sample = f.read(2048)
        delimiter = '\t' if '\t' in sample else ','
    df = pd.read_csv(csv_path, delimiter=delimiter)
    df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S')
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        raise ValueError("CSV must have 'Date' and 'Time' columns or a 'datetime' column")
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
        logger.info("No bars to analyse.")
        return
    start = bars['datetime'].iloc[0]
    end = bars['datetime'].iloc[-1]
    logger.info(f"\nAnalysed from {start.strftime('%Y.%m.%d %H:%M')} to {end.strftime('%Y.%m.%d %H:%M')}\n")

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

def mt4_percentiles(pips_arr, percentiles):
    arr_sorted = np.sort(pips_arr)
    edges = []
    for percent in percentiles:
        idx = int(len(arr_sorted) * percent / 100.0)
        if idx >= len(arr_sorted): idx = len(arr_sorted) - 1
        edges.append(arr_sorted[idx])
    edges.append(arr_sorted[-1])
    return edges

def wave_band_stats_mt4(waves, percentiles):
    pips_arr = np.array([w['pips'] for w in waves])
    edges = mt4_percentiles(pips_arr, percentiles)
    min_pips = int(pips_arr.min())
    bands = [
        (min_pips, int(edges[0])),
        (int(edges[0]), int(edges[1])),
        (int(edges[1]), int(edges[2]))
    ]
    results = []
    for idx, (low, high) in enumerate(bands):
        if idx < 2:
            mask = (pips_arr >= low) & (pips_arr < high)
        else:
            mask = (pips_arr >= low) & (pips_arr <= high)
        ws = [w for w, m in zip(waves, mask) if m]
        if not ws:
            stats = {
                'count': 0, 'total_bars': 0, 'total_pips': 0, 'avg_bars': 0, 'avg_pips': 0,
                'longest_bars': 0, 'longest_pips': 0, 'shortest_bars': 0, 'shortest_pips': 0,
                'min_pips': low, 'max_pips': high
            }
        else:
            total_bars = sum(w['bars'] for w in ws)
            total_pips = sum(w['pips'] for w in ws)
            avg_bars = np.mean([w['bars'] for w in ws])
            avg_pips = np.mean([w['pips'] for w in ws])
            longest = max(ws, key=lambda w: w['bars'])
            shortest = min(ws, key=lambda w: w['bars'])
            stats = {
                'count': len(ws),
                'total_bars': total_bars,
                'total_pips': total_pips,
                'avg_bars': avg_bars,
                'avg_pips': avg_pips,
                'longest_bars': longest['bars'],
                'longest_pips': longest['pips'],
                'shortest_bars': shortest['bars'],
                'shortest_pips': shortest['pips'],
                'min_pips': low,
                'max_pips': high
            }
        results.append(stats)
    return results

def print_band(name, stats, percent):
    if not stats: return
    logger.info(f"{name} Wave Frequency ({percent}%): {int(stats['min_pips'])} Pips - {int(stats['max_pips'])} Pips")
    logger.info(f"Total: {int(stats['total_bars'])} bars with {stats['total_pips']:.1f} pips")
    logger.info(f"Average: {stats['avg_bars']:.1f} bars with {stats['avg_pips']:.1f} pips")
    logger.info(f"Longest: {int(stats['longest_bars'])} bars with {stats['longest_pips']:.1f} pips")
    logger.info(f"Shortest: {int(stats['shortest_bars'])} bars with {stats['shortest_pips']:.1f} pips\n")

def print_wave_samples(waves, count=10):
    logger.info(f"\nWaves: First {count} entries")
    for w in waves[:count]:
        logger.info(f"bars={w['bars']:.1f}, pips={w['pips']:.1f}, start={w['start']}, end={w['end']}")

def export_pivots_to_csv(pivots, filename):
    df = pd.DataFrame({
        'datetime': [str(p[0]) for p in pivots],
        'price': [p[1] for p in pivots],
        'type': [p[2] for p in pivots]
    })
    df.to_csv(filename, index=False)

def export_waves_to_csv(waves, filename):
    df = pd.DataFrame({
        'start': [str(w['start']) for w in waves],
        'end': [str(w['end']) for w in waves],
        'bars': [w['bars'] for w in waves],
        'pips': [w['pips'] for w in waves],
        'type': [w['type'] for w in waves]
    })
    df.to_csv(filename, index=False)

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
    parser.add_argument('--export_pivots', type=str, default="", help='Export pivots to CSV filename')
    parser.add_argument('--export_waves', type=str, default="", help='Export waves to CSV filename')

    args = parser.parse_args()

    bars = read_mt4_csv(args.csv_path)

    if args.start_date and args.end_date:
        try:
            start_dt = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(args.end_date, "%Y-%m-%d %H:%M")
            bars = filter_bars_by_date_range(bars, start_dt, end_dt)
        except Exception as e:
            logger.info("Error parsing start/end date. Please use the format YYYY-MM-DD HH:MM")
            return

    print_analysed_period(bars)
    pivots = zigzag_mt4_pivots(bars, args.depth, args.deviation, args.backstep)
    logger.info("First 20 pivots from Python:")
    for p in pivots[:20]:
        logger.info(f"{p[0]}, {p[1]:.5f}, {p[2]}")
    waves = calculate_waves_from_pivots(pivots)
    waves_filtered = filter_waves(waves, args.percentage, args.force_factor, args.deviation)
    print_wave_samples(waves_filtered, count=10)
    percentiles = [args.normal_wave, args.normal_wave + args.medium_wave]
    band_stats_list = wave_band_stats_mt4(waves_filtered, percentiles)
    band_names = ["Normal", "Medium", "Rare"]
    for name, stats, percent in zip(band_names, band_stats_list, [args.normal_wave, args.medium_wave, args.rare_wave]):
        print_band(name, stats, percent)

    if args.export_pivots:
        export_pivots_to_csv(pivots, args.export_pivots)
        logger.info(f"Exported pivots to {args.export_pivots}")
    if args.export_waves:
        export_waves_to_csv(waves_filtered, args.export_waves)
        logger.info(f"Exported waves to {args.export_waves}")

def get_wave_analysis_result_block(
    csv_path,
    depth=12,
    deviation=5,
    backstep=3,
    percentage=50.0,
    force_factor=3,
    normal_wave=80,
    medium_wave=15,
    start_date=None,
    end_date=None
):
    """
    Returns a formatted wave analysis result block (as string) suitable for AI prompt injection.
    """
    import io
    from datetime import datetime
    bars = read_mt4_csv(csv_path)

    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
            bars = filter_bars_by_date_range(bars, start_dt, end_dt)
        except Exception as e:
            return f"Wave Analysis: Error parsing start/end date: {e}"

    output = io.StringIO()
    # Analysed period
    if len(bars) == 0:
        output.write("No bars to analyse.\n")
        return output.getvalue()
    start = bars['datetime'].iloc[0]
    end = bars['datetime'].iloc[-1]
    output.write(f"Analysed from {start.strftime('%Y.%m.%d %H:%M')} to {end.strftime('%Y.%m.%d %H:%M')}\n\n")

    pivots = zigzag_mt4_pivots(bars, depth, deviation, backstep)
    waves = calculate_waves_from_pivots(pivots)
    waves_filtered = filter_waves(waves, percentage, force_factor, deviation)
    percentiles = [normal_wave, normal_wave + medium_wave]
    band_stats_list = wave_band_stats_mt4(waves_filtered, percentiles)
    band_names = ["Normal", "Medium", "Rare"]

    for name, stats, percent in zip(
        band_names, band_stats_list, [normal_wave, medium_wave, 100 - (normal_wave + medium_wave)]
    ):
        if not stats: continue
        output.write(f"{name} Wave Frequency ({percent:.1f}%): {int(stats['min_pips'])} Pips - {int(stats['max_pips'])} Pips\n")
        output.write(f"Total: {int(stats['total_bars'])} bars with {stats['total_pips']:.1f} pips\n")
        output.write(f"Average: {stats['avg_bars']:.1f} bars with {stats['avg_pips']:.1f} pips\n")
        output.write(f"Longest: {int(stats['longest_bars'])} bars with {stats['longest_pips']:.1f} pips\n")
        output.write(f"Shortest: {int(stats['shortest_bars'])} bars with {stats['shortest_pips']:.1f} pips\n\n")

    return output.getvalue()

if __name__ == '__main__':
    main()