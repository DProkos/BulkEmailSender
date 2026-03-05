@echo off
REM Build script for Bulk Email Sender
REM Creates a standalone Windows executable

echo ========================================
echo Building Bulk Email Sender...
echo ========================================

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build the executable
echo Building executable...
pyinstaller bulk_email_sender.spec

if errorlevel 1 (
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo ========================================
echo BUILD SUCCESSFUL!
echo Executable: dist\BulkEmailSender.exe
echo ========================================
pause
