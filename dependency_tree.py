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
    """Checks if 'name' is a local .py file or package directory in the project root."""
    return (
        os.path.isfile(os.path.join(PROJECT_ROOT, name + ".py")) or
        os.path.isdir(os.path.join(PROJECT_ROOT, name))
    )

def get_local_imports(file_path):
    """Parse a Python file and return a set of local module names imported."""
    full_path = os.path.join(PROJECT_ROOT, file_path)
    local_imports = set()
    if not os.path.isfile(full_path):
        return local_imports
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*(?:from|import)\s+([a-zA-Z_][\w\.]*)", line)
            if match:
                mod = match.group(1).split('.')[0]
                if is_local_module(mod):
                    local_imports.add(mod)
    return local_imports

def build_dependency_tree(file_path, visited=None, prefix="", last=True):
    """Recursively print the dependency tree for the given file."""
    if visited is None:
        visited = set()
    node = os.path.splitext(os.path.basename(file_path))[0]
    connector = "└── " if last else "├── "
    print(prefix + connector + node)

    local_imports = get_local_imports(file_path)
    imports_list = list(local_imports)
    for i, mod in enumerate(imports_list):
        sub_last = (i == len(imports_list) - 1)
        if mod in visited:
            # Avoid infinite recursion on circular imports
            sub_connector = "└── " if sub_last else "├── "
            print(prefix + ("    " if last else "│   ") + sub_connector + mod + " (already visited)")
            continue
        visited.add(mod)
        mod_file = mod + ".py"
        mod_pkg_init = os.path.join(mod, "__init__.py")
        if os.path.isfile(os.path.join(PROJECT_ROOT, mod_file)):
            # .py file
            build_dependency_tree(mod_file, visited, prefix + ("    " if last else "│   "), sub_last)
        elif os.path.isfile(os.path.join(PROJECT_ROOT, mod_pkg_init)):
            # package
            build_dependency_tree(mod_pkg_init, visited, prefix + ("    " if last else "│   "), sub_last)
        else:
            # Should not occur if is_local_module is correct
            sub_connector = "└── " if sub_last else "├── "
            print(prefix + ("    " if last else "│   ") + sub_connector + mod + " (not found)")

if __name__ == "__main__":
    for i, start_file in enumerate(START_FILES):
        print(f"\nDependency tree for {start_file}:")
        build_dependency_tree(start_file)