import struct
from datetime import datetime

def hex_dump(data):
    return ' '.join(f'{b:02x}' for b in data)

def main(hst_path):
    with open(hst_path, 'rb') as f:
        header = f.read(148)
        print("Header hex dump:\n", hex_dump(header))
        version = struct.unpack('<I', header[:4])[0]
        symbol = header[64:76].decode(errors='replace').strip('\x00')
        print(f"Version: {version}")
        print(f"Symbol: {symbol}")

        # Try old format bar (44 bytes, unpack first 36 bytes)
        f.seek(148)
        first_bar_old = f.read(44)
        print("\nFirst bar (old format, 44 bytes):")
        print("Raw hex:", hex_dump(first_bar_old))
        try:
            unpacked_old = struct.unpack('<I4f d 2I', first_bar_old[:36])
            time, open_, low, high, close, volume, spread, reserved = unpacked_old
            print("Decoded old format:", {
                'time': time,
                'datetime': datetime.utcfromtimestamp(time),
                'open': open_,
                'low': low,
                'high': high,
                'close': close,
                'volume': volume,
                'spread': spread,
                'reserved': reserved
            })
        except Exception as e:
            print("Error decoding old format:", e)

        # Try new format bar (60 bytes)
        f.seek(148)
        first_bar_new = f.read(60)
        print("\nFirst bar (new format, 60 bytes):")
        print("Raw hex:", hex_dump(first_bar_new))
        try:
            unpacked_new = struct.unpack('<I4dQIIII', first_bar_new)
            time, open_, high, low, close, volume, spread, r1, r2, r3 = unpacked_new
            print("Decoded new format:", {
                'time': time,
                'datetime': datetime.utcfromtimestamp(time),
                'open': open_,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'spread': spread,
                'reserved1': r1,
                'reserved2': r2,
                'reserved3': r3
            })
        except Exception as e:
            print("Error decoding new format:", e)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Diagnostic tool for MT4 HST file format.")
    parser.add_argument('--hst_path', type=str, required=True, help='Path to MT4 HST file')
    args = parser.parse_args()
    main(args.hst_path)