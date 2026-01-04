# Script to create a clean distribution package for clients
# This creates a folder with just the necessary files and a clear launcher

Write-Host "=== Creating Distribution Package ===" -ForegroundColor Cyan
Write-Host ""

# Files are in win-x64 subfolder
$sourceFolder = Join-Path $PSScriptRoot "bin\Release\net48\win-x64"
$distFolder = Join-Path $PSScriptRoot "Distribution"

# Check if source folder exists
if (-not (Test-Path $sourceFolder)) {
    Write-Host "ERROR: Source folder not found: $sourceFolder" -ForegroundColor Red
    Write-Host "Please build the project first: dotnet build AutoInstaller.csproj -c Release" -ForegroundColor Yellow
    exit 1
}

# Clean and create distribution folder
if (Test-Path $distFolder) {
    Remove-Item $distFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $distFolder -Force | Out-Null

Write-Host "Copying files from: $sourceFolder" -ForegroundColor Yellow
Write-Host ""

# Copy all necessary files (EXE, config, DLLs)
Copy-Item -Path "$sourceFolder\*.exe" -Destination $distFolder -Force
Copy-Item -Path "$sourceFolder\*.config" -Destination $distFolder -Force
Copy-Item -Path "$sourceFolder\*.dll" -Destination $distFolder -Force

# Copy runtimes folder if it exists (needed for SQLite)
if (Test-Path "$sourceFolder\runtimes") {
    Copy-Item -Path "$sourceFolder\runtimes" -Destination $distFolder -Recurse -Force
    Write-Host "Copied runtimes folder" -ForegroundColor Green
}

# Create START_HERE.bat if it doesn't exist
$startBatPath = Join-Path $distFolder "START_HERE.bat"
if (-not (Test-Path $startBatPath)) {
    $startBat = @"
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
"@
    Set-Content -Path $startBatPath -Value $startBat
    Write-Host "Created START_HERE.bat" -ForegroundColor Green
}

# Create README.txt if it doesn't exist
$readmePath = Join-Path $distFolder "README.txt"
if (-not (Test-Path $readmePath)) {
    $readme = @"
========================================
  Speckle Auto Installer
========================================

QUICK START:
------------
👉 DOUBLE-CLICK "START_HERE.bat" to begin installation

That's it! The installer will guide you through everything.

WHAT IT DOES:
-------------
✓ Sets up your Speckle account connection
✓ Installs the Revit connector for your Revit versions  
✓ Configures automatic file monitoring and sending

INSTALLATION STEPS:
-------------------
1. Double-click "START_HERE.bat"
2. Follow the on-screen wizard:
   - Enter your Speckle credentials (browser will open)
   - Select which Revit versions to install
   - Choose when to run (now, midnight, weekends, etc.)
   - Select folder to monitor for Revit files
3. Done! The installer runs automatically in the background

REQUIREMENTS:
-------------
✓ Windows 10 or later
✓ .NET Framework 4.8 (usually pre-installed)
✓ Revit 2020, 2021, 2022, 2023, 2024, or 2025

TROUBLESHOOTING:
----------------
- If "START_HERE.bat" doesn't work, try double-clicking 
  "SpeckleAutoInstaller.exe" directly
- Make sure all files are in the same folder
- Contact your Speckle administrator if you have issues

SUPPORT:
--------
If you have any questions or issues, contact your 
Speckle administrator.

========================================
"@
    Set-Content -Path $readmePath -Value $readme
    Write-Host "Created README.txt" -ForegroundColor Green
}

Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow

# Create a Windows shortcut (requires COM object)
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$distFolder\Speckle Installer.lnk")
$Shortcut.TargetPath = "$distFolder\START_HERE.bat"
$Shortcut.WorkingDirectory = $distFolder
$Shortcut.Description = "Speckle Auto Installer - Double-click to start"
$Shortcut.Save()

Write-Host ""
Write-Host "=== Package Created Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "Distribution folder: $distFolder" -ForegroundColor Cyan
Write-Host ""

# Check EXE size
$exePath = Join-Path $distFolder "SpeckleAutoInstaller.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "EXE Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor $(if($exeSize -gt 200){"Green"}else{"Yellow"})
    if ($exeSize -lt 200) {
        Write-Host "WARNING: EXE is smaller than expected. DLLs may not be embedded!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Files included:" -ForegroundColor Yellow
Get-ChildItem $distFolder | Select-Object Name, @{Name="Size";Expression={if($_.PSIsContainer){"<DIR>"}else{"$([math]::Round($_.Length/1MB,2)) MB"}}} | Format-Table -AutoSize

$totalSize = (Get-ChildItem $distFolder -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Total package size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the package: .\Distribution\START_HERE.bat"
Write-Host "2. Zip the 'Distribution' folder"
Write-Host "3. Send the ZIP file to clients"
Write-Host "4. Clients extract and double-click START_HERE.bat"
Write-Host ""


