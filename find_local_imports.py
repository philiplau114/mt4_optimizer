import os
import re

PROJECT_ROOT = r"C:\Users\Philip\Documents\GitHub\mt4_optimizer"
START_FILES = [
    "extract_setfilename_fields.py",
    "run_sqlite_query.py",
    "extract_mt4_report_v2.py",
    "extract_mt4_optimization_v2.py"
]

def is_local_module(name):
    # Checks for .py file or package folder
    return (
        os.path.isfile(os.path.join(PROJECT_ROOT, name + ".py")) or
        os.path.isdir(os.path.join(PROJECT_ROOT, name))
    )

def find_local_imports(file_path, visited=None):
    if visited is None:
        visited = set()
    full_path = os.path.join(PROJECT_ROOT, file_path)
    if not os.path.isfile(full_path):
        return []
    local_imports = []
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*(?:from|import)\s+([a-zA-Z_][\w\.]*)", line)
            if match:
                mod = match.group(1).split('.')[0]
                if is_local_module(mod) and mod not in visited:
                    local_imports.append(mod)
                    visited.add(mod)
                    # Recursively look for imports in this module
                    # Try .py file first
                    mod_file_py = mod + ".py"
                    if os.path.isfile(os.path.join(PROJECT_ROOT, mod_file_py)):
                        local_imports += find_local_imports(mod_file_py, visited)
                    # Or __init__.py if it's a package
                    elif os.path.isdir(os.path.join(PROJECT_ROOT, mod)):
                        init_file = os.path.join(mod, "__init__.py")
                        if os.path.isfile(os.path.join(PROJECT_ROOT, init_file)):
                            local_imports += find_local_imports(init_file, visited)
    return local_imports

if __name__ == "__main__":
    all_local_imports = set()
    for start_file in START_FILES:
        found = find_local_imports(start_file)
        print(f"{start_file}: {set(found)}")
        all_local_imports.update(found)
    print("All local modules imported recursively in project:", all_local_imports)