# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['extract_mt4_report_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('wave_analysis.py', '.'), ('ai_set_optimizer_openrouter.py', '.'), ('build_filename.py', '.'), ('set_file_updater.py', '.')],
    hiddenimports=['argparse', 'collections', 'datetime', 'hashlib', 'io', 'json', 'logging', 'numpy', 'openpyxl', 'os', 'pandas', 'pandas._libs', 're', 'requests', 'set_file_updater', 'sqlite3', 'sys', 'tiktoken', 'time', 'wave_analysis', 'ai_set_optimizer_openrouter', 'build_filename'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='extract_mt4_report_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
