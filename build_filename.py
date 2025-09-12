import hashlib
import re

def generate_magic_number(base_filename: str) -> str:
    """
    Generate a deterministic 'magic number' from the base file name.
    The logic uses SHA256, takes the first 4 bytes, and returns the absolute value as an integer string.
    """
    if base_filename:
        hash_bytes = hashlib.sha256(base_filename.encode('utf-8')).digest()
        mt4_magic = abs(int.from_bytes(hash_bytes[:4], byteorder='little', signed=True))
        return str(mt4_magic)
    else:
        return ""

def generate_fixed_magic_number(ea_name: str, symbol: str, timeframe: str) -> str:
    """
    Generate a deterministic 'magic number' from EA name, symbol, and timeframe.
    Uses SHA256, takes first 4 bytes, returns absolute value as an integer string.
    """
    base_string = f"{ea_name}|{symbol}|{timeframe}"
    hash_bytes = hashlib.sha256(base_string.encode('utf-8')).digest()
    mt4_magic = abs(int.from_bytes(hash_bytes[:4], byteorder='little', signed=True))
    return str(mt4_magic)

def clean_symbol(symbol):
    """
    Extract only the main symbol, e.g., "AUDCAD" from "AUDCAD (Australian Dollar vs Canadian Dollar)"
    """
    match = re.match(r"([A-Z]{6,7})", symbol.replace(" ", ""))
    return match.group(1) if match else symbol

def safe_int(val):
    """
    Convert a value to its integer part as string, or "" if not possible.
    """
    try:
        return str(int(float(val)))
    except Exception:
        return ""

def build_filename(
    EA, Symbol, Timeframe, InitialDeposit="", ProfitAmount="", DrawDown="",
    StartDate="", EndDate="", Stoploss="", WinRate="", ProfitFactor="",
    NumTrade="", SetVersion="", Step="", ext=".set"
):
    # Clean/format values as requested
    SymbolShort = clean_symbol(Symbol)
    InitialDeposit = safe_int(InitialDeposit)
    ProfitAmount = f"P{safe_int(ProfitAmount)}" if ProfitAmount else ""
    DrawDown = f"DD{safe_int(DrawDown)}" if DrawDown else ""
    date_str = f"{StartDate}-{EndDate}" if StartDate and EndDate else ""
    Stoploss = f"SL{safe_int(Stoploss)}" if Stoploss else ""
    WinRate = f"WR{WinRate}" if WinRate else ""
    ProfitFactor = f"PF{ProfitFactor}" if ProfitFactor else ""
    NumTrade = f"T{NumTrade}" if NumTrade else ""
    SetVersion = f"V{SetVersion}" if SetVersion else ""
    Step = f"S{Step}" if str(Step) else ""

    # Construct base filename up to NumTrade for magic number generation (as before)
    base_parts = [
        EA, SymbolShort, Timeframe, InitialDeposit, ProfitAmount, DrawDown, date_str,
        Stoploss, WinRate, ProfitFactor, NumTrade
    ]
    base_filename = "_".join([str(x) for x in base_parts if x])

    # Generate magic number using the function
    #magic_number = generate_magic_number(base_filename)
    magic_number = generate_fixed_magic_number(EA, SymbolShort, Timeframe)

    # Now insert magic_number into the full file name
    parts = base_parts + [f"M{magic_number}", SetVersion, Step]
    file_name = "_".join([str(x) for x in parts if x]) + ext

    return file_name, magic_number

if __name__ == "__main__":
    # Example usage with sample values (you can replace with your actual data)
    file_name, magic_number = build_filename(
        EA="PX3.7",
        Symbol="GBPAUD (British Pound vs Australian Dollar)",
        Timeframe="M30",
        InitialDeposit="1500.00",
        ProfitAmount="1858",
        DrawDown="27",
        StartDate="20220808",
        EndDate="20250808",
        Stoploss="",
        WinRate="84.42",
        ProfitFactor="2.83",
        NumTrade="443",
        SetVersion="1",
        Step=2
    )

    print("File Name:", file_name)
    print("Magic Number:", magic_number)