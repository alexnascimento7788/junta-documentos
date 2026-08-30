# -*- mode: python ; coding: utf-8 -*-
# Spec compartilhado do PyInstaller — usado para gerar o executável nas 3 plataformas.
# Rode com: pyinstaller build_scripts/junta_documentos.spec
# (na plataforma correspondente ao executável desejado — PyInstaller não faz cross-compile)

import sys
from pathlib import Path

block_cipher = None
# SPECPATH é injetado pelo PyInstaller no namespace de execução do .spec (não há __file__ aqui).
root = Path(SPECPATH).resolve().parent

icon_file = None
if sys.platform.startswith("win"):
    candidate = root / "assets" / "icon.ico"
    icon_file = str(candidate) if candidate.exists() else None
elif sys.platform == "darwin":
    candidate = root / "assets" / "icon.icns"
    icon_file = str(candidate) if candidate.exists() else None

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DocJoin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == "darwin"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="DocJoin.app",
        icon=icon_file,
        bundle_identifier="br.com.ceasaminas.docjoin",
        info_plist={
            "NSHighResolutionCapable": "True",
            "CFBundleShortVersionString": "2.0.0",
        },
    )
