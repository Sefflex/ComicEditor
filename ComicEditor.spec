# -*- mode: python ; coding: utf-8 -*-
"""
ComicEditor — PyInstaller Spec (Windows, tek klasör build)
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# easyocr model ve veri dosyaları
easyocr_datas   = collect_data_files("easyocr")
# deep_translator
translator_datas = collect_data_files("deep_translator")

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Uygulama varlıkları
        ("cizgi.png",       "."),
        ("icon.jpg",        "."),
        ("fonts",           "fonts"),
        ("unrar_windows",   "unrar_windows"),
        # easyocr ve deep_translator verileri
        *easyocr_datas,
        *translator_datas,
    ],
    hiddenimports=[
        # easyocr içindeki dinamik yüklemeler
        *collect_submodules("easyocr"),
        # cv2 / numpy
        "cv2",
        "numpy",
        # PIL
        "PIL",
        "PIL._tkinter_finder",
        # PyQt6
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        # fitz (PyMuPDF)
        "fitz",
        # deep_translator
        "deep_translator",
        # google-generativeai (opsiyonel)
        "google.generativeai",
        # rarfile
        "rarfile",
        # pickle, zipfile, ssl, ctypes
        "pickle",
        "zipfile",
        "ssl",
        "ctypes",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "IPython",
        "notebook",
        "jupyter",
        "PyQt5",
        "PySide2",
        "PySide6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ComicEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # GUI uygulaması — konsol penceresi yok
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="cizgi.ico",        # görev çubuğu / .exe ikonu
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ComicEditor",
)
