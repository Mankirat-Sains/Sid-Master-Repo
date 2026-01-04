@echo off
title Speckle Auto Installer
cd /d "%~dp0"
if not exist "SpeckleAutoInstaller.exe" (
    echo.
    echo ERROR: SpeckleAutoInstaller.exe not found!
    echo Please make sure all files are in the same folder.
    echo.
    pause
    exit /b 1
)
echo.
echo ========================================
echo   Starting Speckle Auto Installer...
echo ========================================
echo.
start "" "SpeckleAutoInstaller.exe"
exit
