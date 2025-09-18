import sys
import re
import os
import csv
import json

EA_PATTERNS = [
    r'PX[ _]?\d+\.\d+', r'PX\d+', r'PX',
    r'FC[ _]?\d+\.\d+', r'FC\d+', r'FC',
    r'FN[ _]?\d+\.\d+', r'FN\d+', r'FN',
    r'FX[ _]?\d+\.\d+', r'FX\d+', r'FX',
    r'Falcon[\w.]*',
    r'Phoenix[\w.]*',
    r'Cobra(?: Prem)?', r'(?<!\w)CB(?!\w)',
    r'Bubo', r'(?<!\w)BB(?!\w)',
    r'(?<!\w)Lotto(?!\w)', r'(?<!\w)LO(?!\w)', r'(?<!\w)LT(?!\w)',
    r'PE[ _]?\d+\.\d+',
    r'PP\d+',
    r'PP'
]

def load_symbol_list(symbol_csv_path):
    symbols = []
    with open(symbol_csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                symbol = row[0].strip()
                if symbol: symbols.append(symbol)
    symbols = sorted(list(set(symbols)), key=lambda s: -len(s))
    return symbols

def extract_fields(filename, symbol_list):
    base = os.path.basename(filename)
    base = os.path.splitext(base)[0]
    tokens = re.split(r'[ _\-]+', base)  # Split by space, underscore, dash

    result = {
        "EA": "",
        "Symbol": "",
        "Timeframe": "",
        "InitialDeposit": "",
        "ProfitAmount": "",
        "DrawDown": "",
        "StartDate": "",
        "EndDate": "",
        "Stoploss": "",
        "WinRate": "",
        "ProfitFactor": "",
        "NumTrade": "",
        "SetVersion": "",
        "Step": ""
    }

    # EA detection (support in any position, support new EAs)
    ea_pattern = re.compile('|'.join(EA_PATTERNS), re.IGNORECASE)
    m = ea_pattern.search(base)
    if m:
        ea = m.group(0)
        # Make sure EA is not a substring in the middle of another word (for Lotto/LO/LT/BB/CB)
        if ea.lower() in {"lo","lt","bb","cb"}:
            if re.search(r'\b' + re.escape(ea) + r'\b', base, re.IGNORECASE):
                result["EA"] = ea
        else:
            result["EA"] = ea

    # Symbol detection (longest match priority)
    for symbol in symbol_list:
        if re.search(r'(?<![A-Z0-9])' + re.escape(symbol) + r'(?![A-Z0-9])', base, re.IGNORECASE):
            result["Symbol"] = symbol
            break

    # Timeframe detection
    m = re.search(r'\b(M1|M5|M15|M30|H1|H4|D1|W1|MN1)\b', base, re.IGNORECASE)
    if m:
        result["Timeframe"] = m.group(1).upper()
    else:
        for token in tokens:
            if token.upper() in {"M1","M5","M15","M30","H1","H4","D1","W1","MN1"}:
                result["Timeframe"] = token.upper()
                break

    # StartDate & EndDate: Look for 6-8 digit number patterns separated by dash, underscore, tilde, or space
    date_pattern = re.compile(r'(\d{6,8})\s*[-_~ ]\s*(\d{6,8})')
    m = date_pattern.search(base)
    if m:
        result["StartDate"] = m.group(1)[:8]  # Truncate to 8 digits if longer
        enddate = m.group(2)
        result["EndDate"] = enddate[:8]  # Truncate to 8 digits if longer
    else:
        # fallback: find all 6-8 digit numbers, use first two as Start/End date
        all_dates = re.findall(r'\b\d{6,8}\b', base)
        if all_dates:
            result["StartDate"] = all_dates[0][:8]
            if len(all_dates) > 1:
                result["EndDate"] = all_dates[1][:8]

    # InitialDeposit: look for number after symbol and timeframe (not a date, not a year/month)
    initial_deposit = ""
    if result["Symbol"] and result["Timeframe"]:
        # Only consider the pattern: Symbol Timeframe [number]
        pattern = re.escape(result["Symbol"]) + r'[ _\-]+' + re.escape(result["Timeframe"]) + r'[ _\-]+(\d{3,6})\b'
        m = re.search(pattern, base)
        if m:
            candidate = m.group(1)
            # Only assign if not a date (i.e., not equal to StartDate or EndDate)
            if candidate != result["StartDate"] and candidate != result["EndDate"]:
                initial_deposit = candidate
    # If not found, try to find a token that is a 3-6 digit number, not a date
    if not initial_deposit:
        for token in tokens:
            if re.match(r'^\d{3,6}$', token):
                if token != result["StartDate"] and token != result["EndDate"]:
                    initial_deposit = token
                    break
    result["InitialDeposit"] = initial_deposit

    # ProfitAmount: Pxxxx, PPxxxx, NPxxxx, or TPxxxx (must not be followed by a dot)
    m = re.search(r'\b(P|PP|NP|TP)(\d+)(?!\.)\b', base)
    if m:
        result["ProfitAmount"] = m.group(2)
    else:
        # fallback: scan tokens for Pxxx, PPxxx, NPxxx
        for token in tokens:
            mt = re.match(r'^(P|PP|NP|TP)(\d+)$', token)
            if mt:
                result["ProfitAmount"] = mt.group(2)
                break

    # DrawDown: DDxxx, Dxxx, Dxxxx
    m = re.search(r'DD(\d+)', base)
    if m:
        result["DrawDown"] = m.group(1)
    else:
        # Only Dxxx if not ProfitAmount or NumTrade
        matches = re.findall(r'\bD(\d{2,6})\b', base)
        for candidate in matches:
            if candidate != result["ProfitAmount"] and candidate != result["NumTrade"]:
                result["DrawDown"] = candidate
                break

    # Stoploss: SLxxx, SL xxx, (SL xxx), SLNil
    m = re.search(r'SL[\s_]?(\d+|Nil)', base, re.IGNORECASE)
    if not m:
        m = re.search(r'\(SL[\s_]?(\d+|Nil)\)', base, re.IGNORECASE)
    if m:
        result["Stoploss"] = m.group(1)

    # WinRate: WRxx or WRxx.x or WinRatexx
    m = re.search(r'WR[\s_]?(\d+(?:\.\d+)?)', base, re.IGNORECASE)
    if m:
        result["WinRate"] = str(int(float(m.group(1))))

    # ProfitFactor: PFx.xx (first), then TPx.xx or PEx.xx (but only if decimal)
    m = re.search(r'PF(\d+\.\d+)', base)
    if not m:
        m = re.search(r'PF(\d+)', base)
    if not m:
        m = re.search(r'TP(\d+\.\d+)', base)
    if not m:
        m = re.search(r'PE(\d+\.\d+)', base)
    if not m:
        m = re.search(r'PE(\d+)', base)
    if m:
        result["ProfitFactor"] = m.group(1)
    else:
        # Enhanced fallback: Find last decimal number not in parentheses/brackets or after x or x.
        no_paren = re.sub(r'\([^)]*\)', ' ', base)
        no_paren = re.sub(r'\[[^]]*\]', ' ', no_paren)
        no_noise = re.sub(r'(Custom|Dynamic|XLOT|Lot)[^\s]*', ' ', no_paren, flags=re.IGNORECASE)
        decs = re.findall(r'(?<![\dA-Za-z])(\d+\.\d+)(?![\dA-Za-z])', no_noise)
        if decs:
            result["ProfitFactor"] = decs[-1]

    # NumTrade: Txxxx, TTxxxx, Txxx, Txx, T598 (not part of PF or TP)
    m = re.search(r'\bT{1,2}(\d+)\b', base)
    if m:
        result["NumTrade"] = m.group(1)
    else:
        # fallback: scan tokens for Txxx, TTxxx
        for token in tokens:
            mt = re.match(r'^T{1,2}(\d+)$', token)
            if mt:
                result["NumTrade"] = mt.group(1)
                break

    # SetVersion: priority to _V1_, _V1-, _V1., _V1$ (not as part of EA)
    m = re.search(r'(?:_|-)V(\d+(?:\.\d+)?)(?=_|-|\.|$)', base, re.IGNORECASE)
    if m:
        result["SetVersion"] = m.group(1)
    else:
        # If EA has version in it, extract to SetVersion as well (for legacy compatibility)
        m = re.search(r'([0-9]{1,2}\.[0-9]{1,2})', result["EA"])
        if m:
            result["SetVersion"] = m.group(1)

    # Step: priority to _S1_, _S1-, _S1., _S1$ etc.
    m = re.search(r'(?:_|-)S(\d+)(?=_|-|\.|$)', base, re.IGNORECASE)
    if m:
        result["Step"] = m.group(1)

    return result

def extract_fields_from_csv(filename, symbol_csv_path):
    symbol_list = load_symbol_list(symbol_csv_path)
    result = extract_fields(filename, symbol_list)
    return json.dumps(result)

# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python extract_setfilename_fields.py SymbolList.csv filename.set")
#         sys.exit(1)
#     symbol_csv = sys.argv[1]
#     filename = sys.argv[2]
#     symbol_list = load_symbol_list(symbol_csv)
#     fields = extract_fields(filename, symbol_list)
#     print(f"Filename: {filename}")
#     for k, v in fields.items():
#         print(f"{k}: {v}")

# New Main to output JSON with success/error/data and prepare for pyinstall packaging for integration with uipath
# {
#   "success": true,
#   "error": "",
#   "EA": "Phoenix",
#   "Symbol": "AUDCAD",
#   "Timeframe": "M30",
#   "InitialDeposit": "10000",
#   "ProfitAmount": "493",
#   "DrawDown": "142",
#   "StartDate": "20240101",
#   "EndDate": "20240901",
#   "Stoploss": "Nil",
#   "WinRate": "85",
#   "ProfitFactor": "2.35",
#   "NumTrade": "598",
#   "SetVersion": "1",
#   "Step": "3"
# }
if __name__ == "__main__":
    import json
    output = {}
    try:
        if len(sys.argv) < 3:
            output["success"] = False
            output["error"] = "Usage: python extract_setfilename_fields.py SymbolList.csv filename.set"
        else:
            symbol_csv = sys.argv[1]
            filename = sys.argv[2]
            symbol_list = load_symbol_list(symbol_csv)
            fields = extract_fields(filename, symbol_list)
            output["success"] = True
            output["error"] = ""
            output.update(fields)  # Flatten fields into top-level output
    except Exception as e:
        output["success"] = False
        output["error"] = str(e)
    print(json.dumps(output))