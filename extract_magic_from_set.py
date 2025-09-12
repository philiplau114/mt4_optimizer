import os

def find_set_files(folder):
    """Find all .set files in the folder (recursively)."""
    set_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.set'):
                set_files.append(os.path.join(root, file))
    return set_files

def extract_magic_from_file(filepath):
    """Extract the Magic value from a .set file. Returns None if not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('Magic='):
                    return line.strip().split('=', 1)[1]
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return None

def main(target_folder):
    set_files = find_set_files(target_folder)
    print(f"Found {len(set_files)} .set files in {target_folder}\n")
    for filepath in set_files:
        magic_value = extract_magic_from_file(filepath)
        print(f"{os.path.basename(filepath)}: Magic={magic_value if magic_value else 'Not found'}")

if __name__ == "__main__":
    # Change this to your target folder path
    target_folder = r"C:\Users\Philip\OneDrive\Desktop\AI CAD\Philip Real Portifio@29-Aug-2025\29-Aug-2025"
    main(target_folder)