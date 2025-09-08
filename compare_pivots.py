import pandas as pd
from datetime import datetime

def parse_mt4_datetime(dt):
    return datetime.strptime(str(dt).strip(), "%Y.%m.%d %H:%M")

def load_mt4_pivots(mt4_csv):
    # Always skip header, use semicolon delimiter
    pivots = pd.read_csv(mt4_csv, delimiter=';', header=None, skiprows=1, names=['DateTime', 'Price', 'Type'])
    return pivots

def load_python_pivots(python_csv):
    py = pd.read_csv(python_csv)
    py.columns = py.columns.str.strip().str.lower()
    # Try to rename columns to match MT4
    col_map = {}
    for col in py.columns:
        if col in ['datetime', 'date', 'time']:
            col_map[col] = 'DateTime'
        elif 'price' in col:
            col_map[col] = 'Price'
        elif 'type' in col:
            col_map[col] = 'Type'
    py = py.rename(columns=col_map)
    return py

def compare_pivots(mt4_csv, python_csv, tolerance_price=0.0005, tolerance_time=60):
    mt4 = load_mt4_pivots(mt4_csv)
    # Reverse MT4 order to oldest first
    mt4 = mt4.iloc[::-1].reset_index(drop=True)
    py = load_python_pivots(python_csv)

    mt4['DateTime'] = mt4['DateTime'].apply(parse_mt4_datetime)
    py['DateTime'] = pd.to_datetime(py['DateTime'], errors='coerce')

    n = min(len(mt4), len(py))
    print(f"Comparing first {n} pivots...")
    for i in range(n):
        m = mt4.iloc[i]
        p = py.iloc[i]
        msg = []
        try:
            time_diff = abs((m['DateTime'] - p['DateTime']).total_seconds())
        except Exception as e:
            msg.append(f"time error: {e}")
            time_diff = None
        if time_diff is not None and time_diff > tolerance_time:
            msg.append(f"time: MT4={m['DateTime']} Python={p['DateTime']} Δ={time_diff}s")
        if abs(float(m['Price']) - float(p['Price'])) > tolerance_price:
            msg.append(f"price: MT4={m['Price']} Python={p['Price']}")
        if str(m['Type']).strip().lower() != str(p['Type']).strip().lower():
            msg.append(f"type: MT4={m['Type']} Python={p['Type']}")
        if msg:
            print(f"Pivot {i}: {m['DateTime']} {m['Type']} {m['Price']}: " + "; ".join(msg))
    print("Done.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compare pivots from MT4 and Python pivot analysis")
    parser.add_argument('--mt4_csv', type=str, required=True, help='MT4 pivot CSV file (ZigZagExport_Pivots.csv)')
    parser.add_argument('--python_csv', type=str, required=True, help='Python pivot CSV file (EXPORT_PIVOTS.csv)')
    args = parser.parse_args()
    compare_pivots(args.mt4_csv, args.python_csv)