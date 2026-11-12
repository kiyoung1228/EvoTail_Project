@echo off
rem EvoTail 실행 파일 만들기: 더블클릭 또는 build_exe.bat
rem 결과: dist\EvoTail\EvoTail.exe (+ _internal\), 제출용 dist\EvoTail.zip
chcp 65001 >nul
cd /d "%~dp0"

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [EvoTail] PyInstaller 설치: requirements-build.txt
    python -m pip install -r requirements-build.txt || goto :fail
)

python -m PyInstaller EvoTail.spec --noconfirm || goto :fail

if exist dist\EvoTail.zip del /q dist\EvoTail.zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\EvoTail' -DestinationPath 'dist\EvoTail.zip'" || goto :fail

echo.
echo [EvoTail] 완료: dist\EvoTail\EvoTail.exe  /  제출용 dist\EvoTail.zip
exit /b 0

:fail
echo.
echo [EvoTail] 빌드 실패
exit /b 1
