# -*- mode: python -*-

block_cipher = None


a = Analysis(['von_mqtt_simulator.py'],
             pathex=['C:\\jastecm\\von_s41\\devel\\vons41fw\\script\\von_mqtt_simulator'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='von_mqtt_simulator',
          debug=False,
          strip=False,
          upx=True,
          console=True )
