# -*- mode: python ; coding: utf-8 -*-
# EvoTail 실행 파일 (PyInstaller 6.22.3, requirements-build.txt). 빌드: build_exe.bat
#   python -m PyInstaller EvoTail.spec --noconfirm
# 결과: dist/EvoTail/EvoTail.exe + dist/EvoTail/_internal/  (onedir: onefile은 시작이 느리고 백신 오탐이 잦아서 안 씀)
# 제출: dist/EvoTail 폴더를 zip으로 (build_exe.bat가 dist/EvoTail.zip도 만든다)
#
# 묶는 것: 코드(run_gui.py에서 import되는 gui/, roc/), assets/(그림·글꼴, fonts/Galmuri_LICENSE.txt 포함), data/
# 안 묶는 것: tests/, tools/, docs/, saves/, demo_*.py, examples_bridge.py (import되지 않고 datas에도 없음)
# 그림·데이터 위치: gui/theme.py ROOT, roc/service.py __file__ 기준 → exe에서는 _internal/ 안
# 세이브: EvoTail.exe 옆 saves/game.db (쓸 수 없으면 %LOCALAPPDATA%\EvoTail\saves), gui/paths.py

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('data', 'data'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 게임에서 안 쓰는 큰 모듈 (pygame이 있으면 가져다 쓰려는 것 포함)
    excludes=['tkinter', 'unittest', 'test', 'numpy', 'PIL', 'tests', 'tools', 'docs'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EvoTail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,              # 창만 (콘솔 없음). 오류는 saves/error.log
    disable_windowed_traceback=False,
    icon='assets/icon/evotail.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='EvoTail',
)
