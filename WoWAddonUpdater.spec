# -*- mode: python -*-

block_cipher = None


a = Analysis(['WoWAddonUpdater.py'],
             pathex=['C:\\Users\\coleb\\PycharmProjects\\wow-addon-updater'],
             binaries=[],
             datas=[('config.ini', '.'), ('README.md', '.'), ('LICENSE.txt', '.'), ('world_of_warcraft.ico', '.')],
             hiddenimports=[],
             hookspath=[],
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
          [],
          exclude_binaries=True,
          name='WoWAddonUpdater',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='WoWAddonUpdater')
