# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# packaging/ -> project root
PROJECT = Path(SPECPATH).resolve().parent
SRC = PROJECT / "src" / "parin_pdf_viewer.py"

pyside_datas, pyside_binaries, pyside_hidden = collect_all("PySide6")
pymupdf_datas, pymupdf_binaries, pymupdf_hidden = collect_all("pymupdf")

datas = pyside_datas + pymupdf_datas
binaries = pyside_binaries + pymupdf_binaries

hiddenimports = pyside_hidden + pymupdf_hidden + [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtPrintSupport",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
]

a = Analysis(
    [str(SRC)],
    pathex=[str(PROJECT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.scripts.deploy_lib",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Parin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Parin",
)
