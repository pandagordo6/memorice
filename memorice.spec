# -*- mode: python ; coding: utf-8 -*-
# Uso:  pyinstaller memorice.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui', 'ui'), ('recursos', 'recursos')],   # carpetas que el juego lee en tiempo de ejecución
    hiddenimports=['PyQt5.QtMultimedia'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL'],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='MemoriceFrutas',
    console=False,            # sin ventana negra de consola
    icon='icon.ico',
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='MemoriceFrutas')
