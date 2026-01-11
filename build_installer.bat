@echo off
REM Build installer script
REM Requires Inno Setup to be installed

echo ========================================
echo Image Stitcher - Installer Build Tool
echo ========================================
echo.

echo [1/3] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer_output rmdir /s /q installer_output

echo [2/3] Building with PyInstaller...
pyinstaller --clean image_stitcher_dir.spec
if %errorlevel% neq 0 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

echo [3/3] Creating installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_script.iss
if %errorlevel% neq 0 (
    echo Inno Setup build failed!
    echo Please install Inno Setup: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build successful!
echo Installer location: installer_output\ImageStitcher-Setup.exe
echo ========================================
pause
