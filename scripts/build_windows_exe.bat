@echo off
echo Building Medical-Spytool for Windows...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Starting build process...
echo.

REM Build with PyInstaller
pyinstaller --clean Medical-Spytool-Windows.spec

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ================================
    echo Build completed successfully!
    echo ================================
    echo.
    echo Executable location: dist\Medical-Spytool.exe
    echo Installer directory: dist\Medical-Spytool-Installer\
    echo.
)

pause
