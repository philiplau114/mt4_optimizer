import struct
import csv

# User: Set your file paths here
HST_FILE = r"C:\Users\Philip\AppData\Roaming\MetaQuotes\Terminal\F1BBCAACDA8825381C125EAF07296C41\history\VantageInternational-Demo\AUDCAD30.hst"
CSV_FILE = r"C:\Users\Philip\Documents\GitHub\mt4_optimizer\AUDCAD30.csv"  # Path to your exported CSV from MT4
OUT_FILE = "parsed_hst_output.csv"

HEADER_SIZE = 148
BAR_SIZE = 44

def read_csv(csv_file):
    rows = []
    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 6 or not row[2].replace('.','',1).isdigit():
                continue  # skip header or malformed rows
            rows.append(row)
    return rows

def float_matches(a, b, tol=1e-5):
    return abs(float(a) - float(b)) < tol

def scan_bar(bar_bytes, csv_row):
    targets = [float(csv_row[2]), float(csv_row[3]), float(csv_row[4]), float(csv_row[5])]
    found = {}
    for offset in range(0, BAR_SIZE - 4 + 1, 4):
        val = struct.unpack('<f', bar_bytes[offset:offset+4])[0]
        for i, target in enumerate(targets):
            if float_matches(val, target):
                found[i] = offset
    return found

def find_offsets(hst_file, csv_rows, sample_n=10):
    offsets_per_field = {i: [] for i in range(4)}  # 0:open, 1:high, 2:low, 3:close
    with open(hst_file, 'rb') as f:
        f.seek(HEADER_SIZE)
        for i in range(min(sample_n, len(csv_rows))):
            bar = f.read(BAR_SIZE)
            found = scan_bar(bar, csv_rows[i])
            for k, offset in found.items():
                offsets_per_field[k].append(offset)
    # Most common offset for each field
    offsets = tuple(max(set(lst), key=lst.count) if lst else None for lst in offsets_per_field.values())
    return offsets

def parse_hst(hst_file, offsets, n_bars):
    bars = []
    with open(hst_file, 'rb') as f:
        f.seek(HEADER_SIZE)
        for _ in range(n_bars):
            bar = f.read(BAR_SIZE)
            # Parse time (first 4 bytes, uint32)
            t = struct.unpack('<I', bar[:4])[0]
            # Parse prices
            prices = []
            for off in offsets:
                prices.append(struct.unpack('<f', bar[off:off+4])[0] if off is not None else None)
            # Volume (try offset 20/24/28)
            volume = None
            for vol_offset in [20, 24, 28]:
                v = struct.unpack('<f', bar[vol_offset:vol_offset+4])[0]
                if v > 0 and v < 1e7:
                    volume = int(v)
                    break
            bars.append([t] + prices + [volume])
    return bars

def main():
    print("Reading CSV...")
    csv_rows = read_csv(CSV_FILE)
    print("Scanning HST for price offsets...")
    offsets = find_offsets(HST_FILE, csv_rows)
    print(f"Detected price offsets (bytes): Open={offsets[0]}, High={offsets[1]}, Low={offsets[2]}, Close={offsets[3]}")
    print("Parsing full HST file...")
    n_bars = len(csv_rows)
    bars = parse_hst(HST_FILE, offsets, n_bars)
    print(f"Writing output CSV ({OUT_FILE})...")
    with open(OUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for row in bars:
            writer.writerow(row)
    print("Done!")

if __name__ == "__main__":
    main()