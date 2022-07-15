# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
from pywebio import STATIC_PATH


a = Analysis(['cha.py'],
             pathex=[],
             binaries=[],
             datas=[('cha.py', '.'), (STATIC_PATH, 'pywebio/html'), (STATIC_PATH+'/../platform/tpl', 'pywebio/platform/tpl')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='cha',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='1.ico')
