# Build and Distribution Guide

## Quick Start - Build and Package for Distribution

Follow these steps in order to build and prepare the AutoInstaller for client distribution.

---

## Step 1: Build the Project

Open PowerShell and navigate to the AutoInstaller folder:

```powershell
cd speckle-sharp\ConnectorRevit\AutoInstaller
```

Build the project in Release mode:

```powershell
dotnet build AutoInstaller.csproj -c Release
```

**Expected output:**
- Build should complete successfully
- Files will be in: `bin\Release\net48\win-x64\`

---

## Step 2: Verify the Build

Check that the EXE was created and has the correct size (~250 MB if DLLs are embedded):

```powershell
Get-Item bin\Release\net48\win-x64\SpeckleAutoInstaller.exe | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
```

**What to look for:**
- ✅ EXE size should be **200-260 MB** (indicates DLLs are embedded)
- ⚠️ If size is **< 10 MB**, DLLs are NOT embedded - you need to rebuild with embedded resources

---

## Step 3: Create Distribution Package

Run the distribution script:

```powershell
.\CREATE_DISTRIBUTION_PACKAGE.ps1
```

**What it does:**
- Creates a `Distribution` folder
- Copies all necessary files (EXE, DLLs, config)
- Creates `START_HERE.bat` launcher
- Creates `README.txt` instructions
- Creates desktop shortcut

**Expected output:**
- Distribution folder created
- EXE size displayed (should be ~250 MB)
- Total package size displayed (~250-260 MB)

---

## Step 4: Test the Distribution Package

**IMPORTANT:** Test before shipping!

```powershell
cd Distribution
.\START_HERE.bat
```

**Verify:**
- ✅ Setup wizard opens
- ✅ Can enter credentials
- ✅ Can select Revit versions
- ✅ Installation completes without errors

If it works, close the wizard and proceed to Step 5.

---

## Step 5: Create ZIP File

Create a ZIP file of the Distribution folder:

```powershell
cd ..
$zipName = "Speckle_Auto_Installer_v1.0.zip"
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}
Compress-Archive -Path "Distribution\*" -DestinationPath $zipName -Force

Write-Host "ZIP created: $zipName" -ForegroundColor Green
Write-Host "Size: $([math]::Round((Get-Item $zipName).Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host "Location: $((Get-Item $zipName).FullName)" -ForegroundColor Yellow
```

**Expected result:**
- ZIP file created: `Speckle_Auto_Installer_v1.0.zip`
- Size: ~250-260 MB (compressed may be smaller)
- Location: Same folder as AutoInstaller project

---

## Step 6: Final Checklist

Before sending to clients, verify:

- [ ] EXE size is 200-260 MB (DLLs embedded)
- [ ] Distribution folder contains:
  - [ ] `SpeckleAutoInstaller.exe`
  - [ ] `SpeckleAutoInstaller.exe.config`
  - [ ] All `.dll` files (~30+ files)
  - [ ] `START_HERE.bat`
  - [ ] `README.txt`
  - [ ] `runtimes\` folder (if present)
- [ ] Tested the package (Step 4)
- [ ] ZIP file created successfully
- [ ] ZIP file size is reasonable

---

## Step 7: Send to Clients

**Send the ZIP file** via:
- Email (if under size limit)
- File sharing service (OneDrive, Dropbox, Google Drive)
- USB drive
- Network share

**Client instructions:**
1. Extract the ZIP file
2. Double-click `START_HERE.bat`
3. Follow the setup wizard

---

## Troubleshooting

### Build Fails
- Make sure you're in the correct directory
- Check that all dependencies are restored: `dotnet restore`
- Verify .NET Framework 4.8 SDK is installed

### EXE Size Too Small
- DLLs are not embedded in the EXE
- Check that `Resources\Revit{Year}\` folders contain DLLs
- Rebuild the project

### Distribution Script Fails
- Make sure you built the project first (Step 1)
- Check that `bin\Release\net48\win-x64\` folder exists
- Verify `SpeckleAutoInstaller.exe` is in that folder

### Package Doesn't Work on Client Machine
- Verify client has .NET Framework 4.8 installed
- Check that all files are in the same folder
- Review logs in `%APPDATA%\Speckle\AutoInstaller\Logs\`

---

## All-in-One Script

If you want to do everything at once, run this:

```powershell
cd speckle-sharp\ConnectorRevit\AutoInstaller

# Build
Write-Host "Building project..." -ForegroundColor Yellow
dotnet build AutoInstaller.csproj -c Release

# Check EXE size
$exePath = "bin\Release\net48\win-x64\SpeckleAutoInstaller.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "EXE Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor $(if($exeSize -gt 200){"Green"}else{"Red"})
    if ($exeSize -lt 200) {
        Write-Host "WARNING: EXE is too small - DLLs may not be embedded!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ERROR: Build failed - EXE not found" -ForegroundColor Red
    exit 1
}

# Create distribution
Write-Host "`nCreating distribution package..." -ForegroundColor Yellow
.\CREATE_DISTRIBUTION_PACKAGE.ps1

# Create ZIP
Write-Host "`nCreating ZIP file..." -ForegroundColor Yellow
$zipName = "Speckle_Auto_Installer_v1.0.zip"
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}
Compress-Archive -Path "Distribution\*" -DestinationPath $zipName -Force

Write-Host "`n=== READY TO SHIP ===" -ForegroundColor Green
Write-Host "ZIP File: $zipName" -ForegroundColor Cyan
Write-Host "Size: $([math]::Round((Get-Item $zipName).Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host "Location: $((Get-Item $zipName).FullName)" -ForegroundColor Yellow
```

---

## File Locations

**Build output:**
- `bin\Release\net48\win-x64\` - All build files

**Distribution package:**
- `Distribution\` - Ready-to-ship folder

**Final ZIP:**
- `Speckle_Auto_Installer_v1.0.zip` - File to send to clients

---

## Notes

- The EXE contains embedded connector DLLs for Revit 2020-2025
- Total package size is ~250-260 MB
- All files must stay together (don't separate DLLs from EXE)
- Clients need .NET Framework 4.8 (usually pre-installed on Windows 10/11)

