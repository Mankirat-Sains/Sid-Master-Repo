# Script to copy built connector DLLs to Resources folders for embedding
# This copies DLLs from the build output folders to Resources/Revit{Year}/ folders

Write-Host "=== Copying Connector DLLs to Resources Folders ===" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
if ($PSScriptRoot) {
    $scriptDir = $PSScriptRoot
} else {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$basePath = Split-Path -Parent $scriptDir
$resourcesPath = Join-Path $scriptDir "Resources"

# Ensure Resources folder exists
if (-not (Test-Path $resourcesPath)) {
    New-Item -ItemType Directory -Path $resourcesPath -Force | Out-Null
    Write-Host "Created Resources folder: $resourcesPath" -ForegroundColor Green
}

# Process each Revit version
$years = @(2020, 2021, 2022, 2023, 2024, 2025)

foreach ($year in $years) {
    Write-Host "Processing Revit $year..." -ForegroundColor Yellow
    
    # Find the connector DLL in build output
    $connectorProjectPath = Join-Path $basePath "ConnectorRevit$year"
    $binPath = Join-Path $connectorProjectPath "bin"
    
    # Try Debug first, then Release
    $dllPath = $null
    if (Test-Path (Join-Path $binPath "Debug")) {
        $debugPath = Join-Path $binPath "Debug"
        # Check for win-x64 subfolder (newer builds)
        $winX64Path = Join-Path $debugPath "win-x64"
        if (Test-Path (Join-Path $winX64Path "SpeckleConnectorRevit.dll")) {
            $dllPath = $winX64Path
        } elseif (Test-Path (Join-Path $debugPath "SpeckleConnectorRevit.dll")) {
            $dllPath = $debugPath
        }
    }
    
    if ($null -eq $dllPath -and (Test-Path (Join-Path $binPath "Release"))) {
        $releasePath = Join-Path $binPath "Release"
        $winX64ReleasePath = Join-Path $releasePath "win-x64"
        if (Test-Path (Join-Path $winX64ReleasePath "SpeckleConnectorRevit.dll")) {
            $dllPath = $winX64ReleasePath
        } elseif (Test-Path (Join-Path $releasePath "SpeckleConnectorRevit.dll")) {
            $dllPath = $releasePath
        }
    }
    
    if ($null -eq $dllPath) {
        Write-Host "  Warning: No build output found for Revit $year - skipping" -ForegroundColor Yellow
        continue
    }
    
    # Create Resources/Revit{Year} folder
    $targetFolder = Join-Path $resourcesPath "Revit$year"
    if (-not (Test-Path $targetFolder)) {
        New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
    }
    
    # Copy all DLLs
    $dllFiles = Get-ChildItem -Path $dllPath -Filter "*.dll" -File -ErrorAction SilentlyContinue
    
    if ($null -eq $dllFiles -or $dllFiles.Count -eq 0) {
        Write-Host "  Warning: No DLLs found in $dllPath - skipping" -ForegroundColor Yellow
        continue
    }
    
    $copiedCount = 0
    foreach ($dll in $dllFiles) {
        $targetFile = Join-Path $targetFolder $dll.Name
        Copy-Item -Path $dll.FullName -Destination $targetFile -Force
        $copiedCount++
    }
    
    Write-Host "  Success: Copied $copiedCount DLLs to Resources\Revit$year\" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "DLLs copied to: $resourcesPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify DLLs are in Resources\Revit{Year}\ folders"
Write-Host "2. Build AutoInstaller project: dotnet build AutoInstaller.csproj"
Write-Host "3. DLLs will be embedded in the EXE automatically"
Write-Host ""
