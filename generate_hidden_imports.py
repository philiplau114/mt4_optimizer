import os
import re

# List your Python files here
files = [
    "wave_analysis.py",
    "ai_set_optimizer_openrouter.py",
    "build_filename.py",
    "set_file_updater.py"
]

# Set to collect all unique imports
all_imports = set()

# Regex patterns for import statements
re_import = re.compile(r"^\s*import\s+([a-zA-Z0-9_\.]+)")
re_from_import = re.compile(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import")

for file in files:
    if not os.path.exists(file):
        print(f"File not found: {file}")
        continue
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            m_import = re_import.match(line)
            m_from_import = re_from_import.match(line)
            if m_import:
                # Split on commas, just in case: import a, b, c
                mods = [mod.strip() for mod in m_import.group(1).split(",")]
                all_imports.update(mods)
            elif m_from_import:
                all_imports.add(m_from_import.group(1))

# Filter out built-in modules if you want (optional)
# For now, generate all
hidden_imports = [f"--hidden-import={mod}" for mod in sorted(all_imports)]

# Output for PyInstaller
print(" ".join(hidden_imports))