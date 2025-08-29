import sys
import csv
from extract_setfilename_fields import load_symbol_list, extract_fields

def main(symbol_csv, filename_txt, output_txt):
    symbol_list = load_symbol_list(symbol_csv)
    with open(filename_txt, encoding="utf-8") as fin, open(output_txt, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line or not line.lower().endswith(".set"):  # skip empty or non-set
                continue
            fields = extract_fields(line, symbol_list)
            # Write in tab-separated format, one line per file
            fout.write(f"Filename: {line}\n")
            for k in ["EA","Symbol","Timeframe","InitialDeposit","ProfitAmount","DrawDown","StartDate","EndDate","Stoploss","WinRate","ProfitFactor","NumTrade","SetVersion","Step"]:
                fout.write(f"{k}: {fields.get(k,'')}\n")
            fout.write("\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python batch_extract_setfilename_fields.py SymbolList.csv setfilename.txt result.txt")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])