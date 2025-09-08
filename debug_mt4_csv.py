import pandas as pd

def debug_mt4_csv(mt4_csv):
    mt4_raw = pd.read_csv(mt4_csv, header=None, names=['raw'], dtype=str)
    mt4_raw = mt4_raw.dropna()
    mt4_raw['raw'] = mt4_raw['raw'].astype(str)
    print("Raw lines:")
    for idx, line in enumerate(mt4_raw['raw'].values[:10]):  # show first 10 for debug
        split_line = line.split(';')
        print(f"Row {idx}: {split_line} (len={len(split_line)})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mt4_csv', type=str, required=True)
    args = parser.parse_args()
    debug_mt4_csv(args.mt4_csv)