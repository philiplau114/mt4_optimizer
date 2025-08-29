import os
import re
import csv

def find_set_files(folder):
    set_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.set'):
                set_files.append(os.path.join(root, file))
    return set_files

def extract_sections_from_set(set_path):
    # Matches lines like: ___bs========== General Setting =========
    # or ___ma=****** Entry System Main Setting ******
    section_pattern = re.compile(
        r'^[\s_]*(?P<marker>[a-zA-Z0-9]+)[=*_]+[ ]*(?P<name>[a-zA-Z0-9 \-\(\)\.@!]+)[ =*_]+$'
    )
    sections = []
    try:
        with open(set_path, encoding='latin1', errors='ignore') as f:
            for line in f:
                line = line.strip()
                match = section_pattern.match(line)
                if match:
                    marker = match.group("marker").strip()
                    name = match.group("name").strip()
                    sections.append((os.path.basename(set_path), marker, name))
    except Exception as e:
        print(f"Error reading {set_path}: {e}")
    return sections

def write_sections_to_csv(sections, csv_path):
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'section_marker', 'section_name'])
        for row in sections:
            writer.writerow(row)

def main(folder, output_csv):
    all_sections = []
    set_files = find_set_files(folder)
    for set_file in set_files:
        all_sections.extend(extract_sections_from_set(set_file))
    write_sections_to_csv(all_sections, output_csv)
    print(f"Extracted section names from {len(set_files)} .set files to {output_csv}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract section names from .set files to CSV.")
    parser.add_argument("folder", help="Folder to search for .set files")
    parser.add_argument("output_csv", help="Output CSV file path")
    args = parser.parse_args()
    main(args.folder, args.output_csv)