# MT4 Automation Scripts Deployment Guide

This document describes how to package and deploy the suite of MT4 automation scripts as standalone Windows executables using [PyInstaller](https://pyinstaller.org/).

## Prerequisites

- Python 3.x installed on your system
- [PyInstaller](https://pyinstaller.org/) installed (`pip install pyinstaller`)
- All required `.py` scripts and modules present in the same directory (unless noted)
- Any dependent data/config files for runtime use (e.g., database, Excel configs)

---

## Packaging Steps

### 1. Package `extract_setfilename_fields.py`

```bash
pyinstaller --onefile extract_setfilename_fields.py
```

- This will produce `dist/extract_setfilename_fields.exe`.
- No additional data files or modules required.

---

### 2. Package `run_sqlite_query.py`

```bash
pyinstaller --onefile run_sqlite_query.py
```

- This will produce `dist/run_sqlite_query.exe`.
- No additional data files or modules required.

---

### 3. Package `extract_mt4_report_v2.py` (with dependencies)

To package `extract_mt4_report_v2.py`, include all its dependent modules and hidden imports in a single line as shown below:

```bash
pyinstaller --onefile extract_mt4_report_v2.py --hidden-import=argparse --hidden-import=collections --hidden-import=datetime --hidden-import=hashlib --hidden-import=io --hidden-import=json --hidden-import=logging --hidden-import=numpy --hidden-import=openpyxl --hidden-import=os --hidden-import=pandas --hidden-import=pandas._libs --hidden-import=re --hidden-import=requests --hidden-import=set_file_updater --hidden-import=sqlite3 --hidden-import=sys --hidden-import=tiktoken --hidden-import=time --hidden-import=wave_analysis --hidden-import=ai_set_optimizer_openrouter --hidden-import=build_filename --add-data "wave_analysis.py;." --add-data "ai_set_optimizer_openrouter.py;." --add-data "build_filename.py;." --add-data "set_file_updater.py;."
```

**Tips:**
- Make sure all `.py` files listed with `--add-data` are present in the working directory.
- If your scripts use additional data files (e.g., configs, templates), add them with `--add-data "filename;."` as needed.
- Tools like [`pyi-collect-submodules`](https://pyinstaller.org/en/stable/usage.html#finding-hidden-imports) or dependency checkers can help identify hidden imports if your script fails due to missing modules.

- This will produce `dist/extract_mt4_report_v2.exe`.
- The `--add-data` flags ensure these modules are bundled with the executable:
  - `wave_analysis.py`
  - `ai_set_optimizer_openrouter.py`
  - `build_filename.py`
  - `set_file_updater.py`
- If your modules access external data files, add those with `--add-data` as well.

---

### 4. Package `extract_mt4_optimization_v2.py`

```bash
pyinstaller --onefile extract_mt4_optimization_v2.py
```

- This will produce `dist/extract_mt4_optimization_v2.exe`.
- No additional data files or modules required.

---

### 5. Package `zip_with_password.py`

```bash
pyinstaller --onefile zip_with_password.py
```

- This will produce `dist/zip_with_password.exe`.
- Ensure the `pyzipper` module is installed in your environment (`pip install pyzipper`) before packaging.

---

## Output

- All executables will be found in the `dist/` folder after packaging.
- You can copy these EXEs to your deployment or automation folder.
- Ensure any data/config files (such as `.db` or `.xlsx`) used at runtime are provided alongside the EXEs.

---

## Notes

- For modules/packages in subfolders, adjust `--add-data` accordingly (e.g., `--add-data "myfolder;myfolder"`).
- If using 3rd-party libraries (e.g., `openpyxl`, `bs4`), ensure they are installed in your Python environment **before** packaging.
- For troubleshooting, consult the `build/` and `dist/` logs, or run your EXE from a command prompt to view error output.

---

## References

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- Python Packaging Best Practices
