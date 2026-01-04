# All-in-One Build and Package Script
# This script builds the project and creates a distribution-ready ZIP file

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Speckle AutoInstaller - Build & Package" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = Get-Location
}

Set-Location $scriptRoot

# Step 1: Build the project
Write-Host "Step 1: Building project..." -ForegroundColor Yellow
Write-Host ""

$buildResult = dotnet build AutoInstaller.csproj -c Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Check EXE size
Write-Host "Step 2: Verifying build output..." -ForegroundColor Yellow
Write-Host ""

$exePath = Join-Path $scriptRoot "bin\Release\net48\win-x64\SpeckleAutoInstaller.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: EXE not found at: $exePath" -ForegroundColor Red
    Write-Host "Build may have failed. Check build output above." -ForegroundColor Yellow
    exit 1
}

$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "EXE Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor $(if($exeSize -gt 200){"Green"}else{"Yellow"})

if ($exeSize -lt 200) {
    Write-Host ""
    Write-Host "WARNING: EXE is smaller than expected!" -ForegroundColor Yellow
    Write-Host "Expected: 200-260 MB (indicates DLLs are embedded)" -ForegroundColor Yellow
    Write-Host "Current: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This may indicate DLLs are not embedded." -ForegroundColor Yellow
    Write-Host "Continue anyway? (Y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -ne "Y" -and $response -ne "y") {
        exit 1
    }
} else {
    Write-Host "✓ EXE size looks good!" -ForegroundColor Green
}

Write-Host ""

# Step 3: Create distribution package
Write-Host "Step 3: Creating distribution package..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "CREATE_DISTRIBUTION_PACKAGE.ps1") {
    & .\CREATE_DISTRIBUTION_PACKAGE.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Distribution package creation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ERROR: CREATE_DISTRIBUTION_PACKAGE.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Verify distribution folder
Write-Host "Step 4: Verifying distribution package..." -ForegroundColor Yellow
Write-Host ""

$distFolder = Join-Path $scriptRoot "Distribution"
if (-not (Test-Path $distFolder)) {
    Write-Host "ERROR: Distribution folder not created!" -ForegroundColor Red
    exit 1
}

$exeInDist = Join-Path $distFolder "SpeckleAutoInstaller.exe"
if (-not (Test-Path $exeInDist)) {
    Write-Host "ERROR: EXE not found in distribution folder!" -ForegroundColor Red
    exit 1
}

$requiredFiles = @("SpeckleAutoInstaller.exe", "SpeckleAutoInstaller.exe.config", "START_HERE.bat", "README.txt")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $distFolder $file
    if (-not (Test-Path $filePath)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "WARNING: Missing files in distribution:" -ForegroundColor Yellow
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ All required files present!" -ForegroundColor Green
}

$dllCount = (Get-ChildItem $distFolder -Filter "*.dll").Count
Write-Host "✓ Found $dllCount DLL files" -ForegroundColor Green

$totalSize = (Get-ChildItem $distFolder -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "✓ Total package size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green

Write-Host ""

# Step 5: Create ZIP file
Write-Host "Step 5: Creating ZIP file..." -ForegroundColor Yellow
Write-Host ""

$zipName = "Speckle_Auto_Installer_v1.0.zip"
$zipPath = Join-Path $scriptRoot $zipName

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "Removed existing ZIP file" -ForegroundColor Gray
}

Compress-Archive -Path "$distFolder\*" -DestinationPath $zipPath -Force

if (-not (Test-Path $zipPath)) {
    Write-Host "ERROR: ZIP file creation failed!" -ForegroundColor Red
    exit 1
}

$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "✓ ZIP file created: $zipName" -ForegroundColor Green
Write-Host "✓ ZIP size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  READY TO SHIP!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "ZIP File: $zipName" -ForegroundColor Cyan
Write-Host "Location: $zipPath" -ForegroundColor Cyan
Write-Host "Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the package: .\Distribution\START_HERE.bat" -ForegroundColor White
Write-Host "2. Send the ZIP file to clients" -ForegroundColor White
Write-Host "3. Clients extract and run START_HERE.bat" -ForegroundColor White
Write-Host ""

