# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Bulk Email Sender

Build command:
    pyinstaller bulk_email_sender.spec

This creates a single executable with all dependencies bundled.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = [
    ('icons', 'icons'),
    ('templates', 'templates'),
    ('docs', 'docs'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'pandas',
    'pandas._libs',
    'openpyxl',
    'jinja2',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'cryptography',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',
    'smtplib',
    'ssl',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='BulkEmailSender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/icon.ico',  # Application icon
)
