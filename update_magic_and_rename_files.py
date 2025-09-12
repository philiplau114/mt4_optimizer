import os
import re
import hashlib

def generate_fixed_magic_number(ea_name: str, symbol: str, timeframe: str) -> str:
    base_string = f"{ea_name}|{symbol}|{timeframe}"
    hash_bytes = hashlib.sha256(base_string.encode('utf-8')).digest()
    mt4_magic = abs(int.from_bytes(hash_bytes[:4], byteorder='little', signed=True))
    return str(mt4_magic)

def extract_info(filename):
    # Example: PX3.71_AUDCAD_M30_1500_..._M1300603361_V1_S13.set
    match = re.match(
        r'^([A-Za-z0-9\.\-]+)_([A-Z]{6})_([A-Z0-9]+)_(.*)_M(\d+)_(V\d+_S\d+)\.set$',
        filename
    )
    if match:
        ea_name = match.group(1)
        symbol = match.group(2)
        timeframe = match.group(3)
        middle = match.group(4)
        old_magic = match.group(5)
        tail = match.group(6)
        return ea_name, symbol, timeframe, middle, old_magic, tail
    return None, None, None, None, None, None

def update_set_file_magic(set_file_path, new_magic):
    with open(set_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    found = False
    for idx, line in enumerate(lines):
        if line.strip().startswith("Magic="):
            lines[idx] = f"Magic={new_magic}\n"
            found = True
            break
    if not found:
        print(f"Warning: 'Magic=' line not found in {set_file_path}. Adding it.")
        #lines.append(f"Magic={new_magic}\n")
    with open(set_file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def rename_files(base_folder):
    for file in os.listdir(base_folder):
        if file.lower().endswith(".set"):
            ea_name, symbol, timeframe, middle, old_magic, tail = extract_info(file)
            if not all([ea_name, symbol, timeframe, middle, old_magic, tail]):
                print(f"Filename format not recognized: {file}")
                continue

            new_magic = generate_fixed_magic_number(ea_name, symbol, timeframe)
            new_base_filename = f"{ea_name}_{symbol}_{timeframe}_{middle}_M{new_magic}_{tail}.set"
            set_file_path = os.path.join(base_folder, file)
            new_set_file_path = os.path.join(base_folder, new_base_filename)

            update_set_file_magic(set_file_path, new_magic)
            os.rename(set_file_path, new_set_file_path)
            print(f"Renamed .set: {file} -> {new_base_filename}")

            for ext in [".htm", ".gif"]:
                old_ext_filename = file.replace(".set", ext)
                old_ext_file_path = os.path.join(base_folder, old_ext_filename)
                if os.path.exists(old_ext_file_path):
                    new_ext_filename = new_base_filename.replace(".set", ext)
                    new_ext_file_path = os.path.join(base_folder, new_ext_filename)
                    os.rename(old_ext_file_path, new_ext_file_path)
                    print(f"Renamed {ext}: {old_ext_filename} -> {new_ext_filename}")

if __name__ == "__main__":
    target_folder = r"C:\Users\Philip\OneDrive\Desktop\AI CAD\Philip Real Portiflio@9Sep2025\GBPAUD"
    rename_files(target_folder)