import pandas as pd
from datetime import datetime

def parse_mt4_datetime(dt):
    return datetime.strptime(str(dt).strip(), "%Y.%m.%d %H:%M")

def load_mt4_waves(mt4_csv):
    waves = pd.read_csv(mt4_csv, delimiter=';', header=None, skiprows=1, names=['start', 'end', 'bars', 'pips', 'type'])
    return waves

def load_python_waves(python_csv):
    py = pd.read_csv(python_csv)
    py.columns = py.columns.str.strip().str.lower()
    # Map possible column names to standard names
    col_map = {}
    for col in py.columns:
        if col in ['start', 'starttime', 'start_date', 'datetime']:
            col_map[col] = 'start'
        elif col in ['end', 'endtime', 'end_date']:
            col_map[col] = 'end'
        elif 'bar' in col:
            col_map[col] = 'bars'
        elif 'pip' in col:
            col_map[col] = 'pips'
        elif 'type' in col:
            col_map[col] = 'type'
    py = py.rename(columns=col_map)
    return py

def parse_python_datetime(dt):
    # Try ISO and other common formats
    try:
        return pd.to_datetime(dt)
    except Exception:
        return pd.NaT

def compare_waves(mt4_csv, python_csv, tolerance_pips=1.0, tolerance_time=60):
    mt4 = load_mt4_waves(mt4_csv)
    # Reverse MT4 order to oldest first
    mt4 = mt4.iloc[::-1].reset_index(drop=True)
    py = load_python_waves(python_csv)

    mt4['start'] = mt4['start'].apply(parse_mt4_datetime)
    mt4['end'] = mt4['end'].apply(parse_mt4_datetime)
    py['start'] = py['start'].apply(parse_python_datetime)
    py['end'] = py['end'].apply(parse_python_datetime)

    n = min(len(mt4), len(py))
    print(f"Comparing first {n} waves...")
    for i in range(n):
        m = mt4.iloc[i]
        p = py.iloc[i]
        msg = []
        # Compare start time
        try:
            start_diff = abs((m['start'] - p['start']).total_seconds())
        except Exception as e:
            msg.append(f"start error: {e}")
            start_diff = None
        # Compare end time
        try:
            end_diff = abs((m['end'] - p['end']).total_seconds())
        except Exception as e:
            msg.append(f"end error: {e}")
            end_diff = None
        # Compare bars
        try:
            bars_diff = abs(float(m['bars']) - float(p['bars']))
            if bars_diff > 0.01:
                msg.append(f"bars: MT4={m['bars']} Python={p['bars']}")
        except Exception as e:
            msg.append(f"bars error: {e}")
        # Compare pips
        try:
            pips_diff = abs(float(m['pips']) - float(p['pips']))
            if pips_diff > tolerance_pips:
                msg.append(f"pips: MT4={m['pips']} Python={p['pips']}")
        except Exception as e:
            msg.append(f"pips error: {e}")
        # Compare type
        if str(m['type']).strip().lower() != str(p['type']).strip().lower():
            msg.append(f"type: MT4={m['type']} Python={p['type']}")
        # Time difference
        if start_diff is not None and start_diff > tolerance_time:
            msg.append(f"start: MT4={m['start']} Python={p['start']} Δ={start_diff}s")
        if end_diff is not None and end_diff > tolerance_time:
            msg.append(f"end: MT4={m['end']} Python={p['end']} Δ={end_diff}s")
        if msg:
            print(f"Wave {i}: {m['start']} -> {m['end']}: " + "; ".join(msg))
    print("Done.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compare ZigZag waves from MT4 and Python analysis")
    parser.add_argument('--mt4_csv', type=str, required=True, help='MT4 wave CSV file (ZigZagExport_Waves.csv)')
    parser.add_argument('--python_csv', type=str, required=True, help='Python wave CSV file (EXPORT_WAVES.csv)')
    args = parser.parse_args()
    compare_waves(args.mt4_csv, args.python_csv)