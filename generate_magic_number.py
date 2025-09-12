import hashlib

def generate_magic_number(ea_name: str, symbol: str, timeframe: str) -> str:
    """
    Generate a deterministic 'magic number' from EA name, symbol, and timeframe.
    Uses SHA256, takes first 4 bytes, returns absolute value as an integer string.
    """
    base_string = f"{ea_name}|{symbol}|{timeframe}"
    hash_bytes = hashlib.sha256(base_string.encode('utf-8')).digest()
    mt4_magic = abs(int.from_bytes(hash_bytes[:4], byteorder='little', signed=True))
    return str(mt4_magic)

# Example usage:
if __name__ == "__main__":
    ea_name = "PX3.71"
    symbol = "AUDCAD"
    timeframe = "M30"
    magic = generate_magic_number(ea_name, symbol, timeframe)
    print(f"Magic number for {ea_name}, {symbol}, {timeframe}: {magic}")