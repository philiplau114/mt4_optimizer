import struct
from datetime import datetime

def hex_dump(data):
    return ' '.join(f'{b:02x}' for b in data)

def try_structs(bar_bytes):
    results = []
    structs = [
        # Name, struct format, expected length
        ("MT4 old (I4f d 2I)", "<I4f d 2I", 36),
        ("MT4 old padded (I4f d 2I +8)", "<I4f d 2I", 44),  # Only decode first 36 bytes
        ("MT4 new (I4dQIIII)", "<I4dQIIII", 60),
        ("All float (IffffQII)", "<IffffQII", 36),
        ("All float padded (IffffQII +8)", "<IffffQII", 44),  # Only decode first 36 bytes
        ("All double (IddddQIIII)", "<IddddQIIII", 60),
        # Add more as needed
    ]
    for name, fmt, length in structs:
        try:
            if len(bar_bytes) < length:
                results.append((name, "Not enough bytes"))
                continue
            if length == 44:
                data = struct.unpack(fmt, bar_bytes[:36])
            else:
                data = struct.unpack(fmt, bar_bytes[:length])
            results.append((name, data))
        except Exception as e:
            results.append((name, f"Error: {e}"))
    return results

def main(hst_path):
    with open(hst_path, 'rb') as f:
        header = f.read(148)
        print("Header hex dump:\n", hex_dump(header))
        version = struct.unpack('<I', header[:4])[0]
        symbol = header[64:76].decode(errors='replace').strip('\x00')
        print(f"Version: {version}")
        print(f"Symbol: {symbol}")

        f.seek(148)
        first_60 = f.read(60)
        print("\nFirst bar (60 bytes):")
        print("Raw hex:", hex_dump(first_60))
        print("\nTrying multiple struct formats:")
        results = try_structs(first_60)
        for name, data in results:
            print(f"\n{name}:")
            print(data)
            # If time field is plausible, show as datetime
            if isinstance(data, tuple) and len(data) > 0 and isinstance(data[0], int):
                try:
                    print("  time (unix):", data[0])
                    print("  datetime:", datetime.utcfromtimestamp(data[0]))
                except Exception:
                    pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Try multiple struct formats for MT4 HST file.")
    parser.add_argument('--hst_path', type=str, required=True, help='Path to MT4 HST file')
    args = parser.parse_args()
    main(args.hst_path)