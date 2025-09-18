@echo off
REM MT4 Automation Scripts Bulk Packaging Script
REM Each PyInstaller command is on a single line as required

REM 1. Package extract_setfilename_fields.py
pyinstaller --onefile extract_setfilename_fields.py

REM 2. Package run_sqlite_query.py
pyinstaller --onefile run_sqlite_query.py

REM 3. Package extract_mt4_report_v2.py (with dependencies)
pyinstaller --onefile extract_mt4_report_v2.py --hidden-import=argparse --hidden-import=collections --hidden-import=datetime --hidden-import=hashlib --hidden-import=io --hidden-import=json --hidden-import=logging --hidden-import=numpy --hidden-import=openpyxl --hidden-import=os --hidden-import=pandas --hidden-import=pandas._libs --hidden-import=re --hidden-import=requests --hidden-import=set_file_updater --hidden-import=sqlite3 --hidden-import=sys --hidden-import=tiktoken --hidden-import=time --hidden-import=wave_analysis --hidden-import=ai_set_optimizer_openrouter --hidden-import=build_filename --add-data "wave_analysis.py;." --add-data "ai_set_optimizer_openrouter.py;." --add-data "build_filename.py;." --add-data "set_file_updater.py;."

REM 4. Package extract_mt4_optimization_v2.py
pyinstaller --onefile extract_mt4_optimization_v2.py

REM 5. Package zip_with_password.py
pyinstaller --onefile zip_with_password.py

echo.
echo Packaging complete! All executables are in the dist\ folder.
pause