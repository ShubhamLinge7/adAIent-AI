# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for adAIent Troubleshooting Assistant
Creates a standalone .exe with all dependencies bundled
"""

a = Analysis(
    ['app\\main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('admin.html', '.'),
        ('index_adaient.html', '.'),
        ('login.html', '.'),
        ('config.py', '.'),
        ('data', 'data'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'sqlite3',
        'pathlib',
        'logging',
        'json',
        'secrets',
        'hashlib',
        'datetime',
        'typing',
        'starlette',
        'pydantic',
        'sentence_transformers',
        'torch',
        'faiss',
        'PyPDF2',
        'requests',
        'httpx',
        'aiofiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='adAIent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for server output
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add company logo here later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='adAIent'
)
