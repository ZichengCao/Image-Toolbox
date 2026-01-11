@echo off
REM Build portable version script

echo ========================================
echo Image Stitcher - Portable Build Tool
echo ========================================
echo.

echo [1/2] Cleaning old build files...
if exist build rmdir /s /q build
if exist portable rmdir /s /q portable

echo [2/2] Building portable EXE with PyInstaller...
pyinstaller --clean image_stitcher.spec
if %errorlevel% neq 0 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

REM Create portable directory and copy files
if not exist portable mkdir portable
copy dist\ImageStitcher.exe portable\
if exist portable\ImageStitcher.exe (
    echo.
    echo ========================================
    echo Build successful!
    echo Portable version location: portable\ImageStitcher.exe
    echo ========================================
) else (
    echo Build failed: Generated EXE file not found
)
pause
