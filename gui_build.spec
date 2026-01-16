# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AutoTranslate GUI application.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

block_cipher = None

# Collect all data files
datas = []

# GUI related files
datas += [
    ('gui/styles/app.qss', 'gui/styles'),
    ('gui/i18n/translations/en.json', 'gui/i18n/translations'),
    ('gui/i18n/translations/ko.json', 'gui/i18n/translations'),
]

# Source data files
if os.path.exists('src/assets/vanilla_minecraft_assets'):
    datas += [('src/assets/vanilla_minecraft_assets', 'src/assets/vanilla_minecraft_assets')]

if os.path.exists('src/glossary/vanilla_glossaries'):
    datas += [('src/glossary/vanilla_glossaries', 'src/glossary/vanilla_glossaries')]

# Collect all submodules
hiddenimports = []
hiddenimports += collect_submodules('PySide6')
hiddenimports += collect_submodules('qfluentwidgets')
hiddenimports += collect_submodules('langchain')
hiddenimports += collect_submodules('langchain_openai')
hiddenimports += collect_submodules('langchain_anthropic')
hiddenimports += collect_submodules('langchain_google_genai')
hiddenimports += collect_submodules('langchain_ollama')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('aiofiles')
hiddenimports += collect_submodules('aiohttp')
hiddenimports += collect_submodules('ftb_snbt_lib')

# Additional hidden imports
hiddenimports += [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'queue',
    'json',
    're',
    'pathlib',
    'typing',
]

a = Analysis(
    ['gui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'IPython',
        'notebook',
        'pytest',
        'setuptools',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoTranslate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # GUI 애플리케이션이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="./assets/mct-icon.ico",  # 아이콘 파일이 있다면 경로 지정 (예: 'icon.ico')
)
