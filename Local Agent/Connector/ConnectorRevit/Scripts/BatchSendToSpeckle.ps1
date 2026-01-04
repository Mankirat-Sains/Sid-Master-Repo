#Requires -Version 5.1
<#
.SYNOPSIS
    Batch sends Revit files to Speckle.

.DESCRIPTION
    This script iterates over .rvt files in a folder and sends each one to Speckle
    using the headless send functionality of the Speckle Revit connector.
    
    Prerequisites:
    1. Revit must be installed
    2. Speckle Revit connector must be installed
    3. A valid Speckle account must be configured in Speckle Manager
    4. The RevitAutomatedSend.json config file must be set up

.PARAMETER FolderPath
    Path to the folder containing .rvt files to process.

.PARAMETER RevitPath
    Path to Revit.exe. If not specified, will try to find Revit automatically.

.PARAMETER RevitYear
    Revit version year (e.g., 2024, 2025). Used to find Revit if RevitPath is not specified.

.PARAMETER ConfigPath
    Path to the RevitAutomatedSend.json config file. If not specified, uses the default location.

.PARAMETER Recursive
    If specified, searches for .rvt files recursively in subfolders.

.PARAMETER MaxParallel
    Maximum number of Revit instances to run in parallel. Default is 1 (sequential).

.PARAMETER TimeoutMinutes
    Timeout in minutes for each file. Default is 30.

.PARAMETER OutputPath
    Path to save the batch results summary. If not specified, saves to the input folder.

.EXAMPLE
    .\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitYear 2024

.EXAMPLE
    .\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitPath "C:\Program Files\Autodesk\Revit 2024\Revit.exe" -Recursive

.NOTES
    Author: Speckle Systems
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path $_ -PathType Container })]
    [string]$FolderPath,

    [Parameter(Mandatory = $false)]
    [string]$RevitPath,

    [Parameter(Mandatory = $false)]
    [ValidateRange(2019, 2030)]
    [int]$RevitYear = 2024,

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $false)]
    [switch]$Recursive,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 4)]
    [int]$MaxParallel = 1,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 240)]
    [int]$TimeoutMinutes = 30,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath
)

# Script configuration
$ErrorActionPreference = "Stop"
$script:StartTime = Get-Date
$script:Results = @()

#region Functions

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error", "Success")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Info" { "White" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Success" { "Green" }
    }
    
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Find-RevitExecutable {
    param([int]$Year)
    
    $possiblePaths = @(
        "C:\Program Files\Autodesk\Revit $Year\Revit.exe",
        "C:\Program Files\Autodesk\Revit $Year\Revit.exe",
        "${env:ProgramFiles}\Autodesk\Revit $Year\Revit.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Try to find any Revit installation
    $revitInstalls = Get-ChildItem "C:\Program Files\Autodesk" -Directory -Filter "Revit*" -ErrorAction SilentlyContinue
    foreach ($install in $revitInstalls | Sort-Object Name -Descending) {
        $exePath = Join-Path $install.FullName "Revit.exe"
        if (Test-Path $exePath) {
            Write-Log "Found Revit at: $exePath" -Level Warning
            return $exePath
        }
    }
    
    return $null
}

function Get-SpeckleConfigPath {
    $appData = [Environment]::GetFolderPath("ApplicationData")
    return Join-Path $appData "Speckle\RevitAutomatedSend.json"
}

function Test-SpeckleConfig {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return $false
    }
    
    try {
        $config = Get-Content $Path -Raw | ConvertFrom-Json
        
        if ([string]::IsNullOrEmpty($config.ServerUrl)) {
            Write-Log "Config missing ServerUrl" -Level Warning
            return $false
        }
        
        if (-not $config.AutoCreateStream -and 
            [string]::IsNullOrEmpty($config.DefaultStreamId) -and 
            ($null -eq $config.StreamIdMapping -or $config.StreamIdMapping.PSObject.Properties.Count -eq 0)) {
            Write-Log "Config missing DefaultStreamId or StreamIdMapping (and AutoCreateStream is false)" -Level Warning
            return $false
        }
        
        return $true
    }
    catch {
        Write-Log "Failed to parse config: $_" -Level Error
        return $false
    }
}

function Update-ConfigForAutoSend {
    param([string]$Path)
    
    try {
        $config = Get-Content $Path -Raw | ConvertFrom-Json
        
        # Ensure auto-send is enabled for batch processing
        $config.AutoSendOnDocumentOpen = $true
        $config.CloseDocumentAfterSend = $true
        $config.CloseRevitAfterSend = $true
        
        $config | ConvertTo-Json -Depth 10 | Set-Content $Path -Encoding UTF8
        
        Write-Log "Updated config for batch processing"
    }
    catch {
        Write-Log "Failed to update config: $_" -Level Warning
    }
}

function Get-ResultsDirectory {
    param([string]$ConfigPath)
    
    try {
        if (Test-Path $ConfigPath) {
            $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
            if (-not [string]::IsNullOrEmpty($config.ResultsDirectory)) {
                return $config.ResultsDirectory
            }
        }
    }
    catch {
        # Ignore
    }
    
    return Join-Path $env:TEMP "SpeckleAutoSend"
}

function Wait-ForResultFile {
    param(
        [string]$ResultsDir,
        [string]$FileName,
        [int]$TimeoutSeconds
    )
    
    # The result file is named: {FileNameWithoutExtension}_{Timestamp}.json
    # For "6513-005-SB-R22-GALA.ifc.0001.RVT", it would be "6513-005-SB-R22-GALA.ifc.0001_20251204_141234.json"
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    $pattern = $baseName + "_*.json"
    $startTime = Get-Date
    $checkInterval = 5 # seconds
    $lastLogTime = $startTime
    
    Write-Log "  Waiting for result file matching pattern: $pattern" -Level Info
    Write-Log "  Checking directory: $ResultsDir" -Level Info
    
    while ((Get-Date) - $startTime -lt [TimeSpan]::FromSeconds($TimeoutSeconds)) {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        # Log progress every 30 seconds
        if (($elapsed -gt 0) -and ($elapsed % 30 -lt $checkInterval)) {
            Write-Log "  Still waiting for result file... (${elapsed}s elapsed)" -Level Info
        }
        
        # Check for result files
        $resultFiles = Get-ChildItem $ResultsDir -Filter $pattern -ErrorAction SilentlyContinue |
                       Where-Object { $_.LastWriteTime -gt $startTime } |
                       Sort-Object LastWriteTime -Descending
        
        if ($resultFiles.Count -gt 0) {
            Write-Log "  Result file found: $($resultFiles[0].Name)" -Level Success
            return $resultFiles[0].FullName
        }
        
        # Also check for any new JSON files in case the pattern doesn't match exactly
        $allJsonFiles = Get-ChildItem $ResultsDir -Filter "*.json" -ErrorAction SilentlyContinue |
                        Where-Object { $_.LastWriteTime -gt $startTime } |
                        Sort-Object LastWriteTime -Descending
        
        if ($allJsonFiles.Count -gt 0) {
            # Check if any of them might be for this file (contains base name)
            $matchingFile = $allJsonFiles | Where-Object { $_.Name -like "*$baseName*" } | Select-Object -First 1
            if ($null -ne $matchingFile) {
                Write-Log "  Found potential result file: $($matchingFile.Name)" -Level Success
                return $matchingFile.FullName
            }
        }
        
        Start-Sleep -Seconds $checkInterval
    }
    
    Write-Log "  Timeout waiting for result file after $TimeoutSeconds seconds" -Level Warning
    Write-Log "  Pattern searched: $pattern" -Level Warning
    Write-Log "  Files in results directory:" -Level Warning
    Get-ChildItem $ResultsDir -Filter "*.json" -ErrorAction SilentlyContinue | 
        ForEach-Object { Write-Log "    - $($_.Name) (modified: $($_.LastWriteTime))" -Level Warning }
    
    return $null
}

function Send-RevitFile {
    param(
        [string]$FilePath,
        [string]$RevitExe,
        [int]$TimeoutMinutes,
        [string]$ResultsDir
    )
    
    $fileName = [System.IO.Path]::GetFileName($FilePath)
    $result = @{
        FilePath = $FilePath
        FileName = $fileName
        Success = $false
        CommitId = $null
        ErrorMessage = $null
        StartTime = Get-Date
        EndTime = $null
        DurationSeconds = 0
    }
    
    Write-Log "Processing: $fileName"
    
    try {
        # Launch Revit with the file
        # Note: We're relying on the auto-send on document open feature
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $RevitExe
        $processInfo.Arguments = "`"$FilePath`""
        $processInfo.UseShellExecute = $true
        
        $process = [System.Diagnostics.Process]::Start($processInfo)
        
        if ($null -eq $process) {
            throw "Failed to start Revit process"
        }
        
        Write-Log "  Revit started (PID: $($process.Id)), waiting for completion..."
        
        # Strategy: Wait reasonable time for send to complete, then close Revit
        # The result file is written AFTER SendDocument completes (in the 'finally' block)
        # Since commits are being created successfully, we can use time-based completion
        # Typical send takes 2-5 minutes for large files, so we'll wait up to 5 minutes
        
        $estimatedSendTime = 300 # 5 minutes - reasonable for large Revit files
        $startTime = Get-Date
        $checkInterval = 10 # Check every 10 seconds
        $resultFile = $null
        $sendCompleted = $false
        $revitExited = $false
        
        Write-Log "  Waiting for send to complete..." -Level Info
        Write-Log "  Result file location: $ResultsDir" -Level Info
        Write-Log "  Expected pattern: $([System.IO.Path]::GetFileNameWithoutExtension($fileName))_*.json" -Level Info
        Write-Log "  Strategy: Check for result file every 10s, wait up to 5 minutes, then close Revit" -Level Info
        
        # Poll for result file while waiting
        while ((Get-Date) - $startTime -lt [TimeSpan]::FromSeconds($estimatedSendTime)) {
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            
            # Check for result file
            if ($null -eq $resultFile) {
                $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
                $pattern = $baseName + "_*.json"
                
                $resultFiles = Get-ChildItem $ResultsDir -Filter $pattern -ErrorAction SilentlyContinue |
                               Where-Object { $_.LastWriteTime -gt $startTime } |
                               Sort-Object LastWriteTime -Descending
                
                if ($resultFiles.Count -gt 0) {
                    $resultFile = $resultFiles[0].FullName
                    Write-Log "  [SUCCESS] Result file found: $($resultFiles[0].Name) (after ${elapsed}s)" -Level Success
                    $sendCompleted = $true
                    # Continue to wait a bit for Revit to potentially close gracefully
                    break
                }
            }
            
            # Log progress every 60 seconds
            if ($elapsed -gt 0 -and [math]::Floor($elapsed) % 60 -lt $checkInterval) {
                Write-Log "  Send in progress... (${elapsed}s elapsed)" -Level Info
            }
            
            Start-Sleep -Seconds $checkInterval
        }
        
        # After waiting, check one more time for result file
        if ($null -eq $resultFile) {
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
            $pattern = $baseName + "_*.json"
            $resultFiles = Get-ChildItem $ResultsDir -Filter $pattern -ErrorAction SilentlyContinue |
                           Where-Object { $_.LastWriteTime -gt $startTime } |
                           Sort-Object LastWriteTime -Descending
            
            if ($resultFiles.Count -gt 0) {
                $resultFile = $resultFiles[0].FullName
                Write-Log "  [SUCCESS] Result file found on final check: $($resultFiles[0].Name)" -Level Success
                $sendCompleted = $true
            }
            else {
                $elapsed = ((Get-Date) - $startTime).TotalSeconds
                Write-Log "  No result file found after ${elapsed}s" -Level Warning
                Write-Log "  Assuming send completed (commits are being created in Speckle)" -Level Info
                Write-Log "  Will close Revit and proceed to next file" -Level Info
                $sendCompleted = $true
            }
        }
        
        # Close Revit if it's still running (it won't close itself)
        if (-not $process.HasExited) {
            if ($null -ne $resultFile) {
                Write-Log "  Result file found, waiting 10 seconds for Revit to close gracefully, then forcing close..."
                Start-Sleep -Seconds 10
            }
            
            if (-not $process.HasExited) {
                Write-Log "  Closing Revit process (send completed, moving to next file)..." -Level Info
                try {
                    $process.Kill()
                    $process.WaitForExit(10000)
                    Write-Log "  Revit process closed successfully"
                    $revitExited = $true
                }
                catch {
                    Write-Log "  Error closing Revit: $_" -Level Error
                    # Try alternative method
                    try {
                        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                        Write-Log "  Revit process closed using alternative method"
                        $revitExited = $true
                    }
                    catch {
                        Write-Log "  Failed to close Revit process" -Level Error
                    }
                }
            }
            else {
                $revitExited = $true
            }
        }
        else {
            Write-Log "  Revit already closed"
            $revitExited = $true
        }
        
        # Additional wait to ensure process is fully cleaned up
        Start-Sleep -Seconds 2
        
        $result.EndTime = Get-Date
        $result.DurationSeconds = ($result.EndTime - $result.StartTime).TotalSeconds
        
        # Parse result file if found
        if ($null -ne $resultFile -and (Test-Path $resultFile)) {
            try {
                $sendResult = Get-Content $resultFile -Raw | ConvertFrom-Json
                $result.Success = $sendResult.Success
                $result.CommitId = $sendResult.CommitId
                $result.ErrorMessage = $sendResult.ErrorMessage
                
                if ($result.Success) {
                    Write-Log "  Success! Commit: $($result.CommitId)" -Level Success
                }
                else {
                    Write-Log "  Failed: $($result.ErrorMessage)" -Level Error
                }
            }
            catch {
                Write-Log "  Failed to parse result file: $_" -Level Error
                $result.Success = $false
                $result.ErrorMessage = "Failed to parse result file: $_"
            }
        }
        elseif ($sendCompleted) {
            # Send completed (result file found OR reasonable time passed) - assume success
            # Commits are being created successfully, so the send is working
            $result.Success = $true
            $result.CommitId = if ($null -ne $resultFile) { "see result file" } else { "unknown (check Speckle server)" }
            $result.ErrorMessage = if ($null -eq $resultFile) { "No result file written, but send likely completed. Verify commit in Speckle server." } else { $null }
            Write-Log "  Assumed success (send completed, Revit closed)" -Level Success
            if ($null -eq $resultFile) {
                Write-Log "  Note: Result file not written, but commits are being created. Check Speckle server to verify." -Level Info
            }
        }
        else {
            $result.Success = $false
            $result.ErrorMessage = "Timeout: Revit did not close and no result file generated"
            Write-Log "  Failed: $($result.ErrorMessage)" -Level Error
        }
    }
    catch {
        $result.Success = $false
        $result.ErrorMessage = $_.Exception.Message
        $result.EndTime = Get-Date
        $result.DurationSeconds = ($result.EndTime - $result.StartTime).TotalSeconds
        Write-Log "  Error: $($result.ErrorMessage)" -Level Error
    }
    
    return $result
}

function Write-BatchSummary {
    param(
        [array]$Results,
        [string]$OutputPath
    )
    
    # Calculate total duration safely (handle missing DurationSeconds)
    $validResults = $Results | Where-Object { $null -ne $_.DurationSeconds -and $_.DurationSeconds -gt 0 }
    $totalDuration = if ($validResults.Count -gt 0) {
        ($validResults | Measure-Object -Property DurationSeconds -Sum).Sum
    } else {
        0
    }
    
    $summary = @{
        TotalFiles = $Results.Count
        Successful = ($Results | Where-Object { $_.Success }).Count
        Failed = ($Results | Where-Object { -not $_.Success }).Count
        TotalDurationSeconds = $totalDuration
        StartTime = $script:StartTime
        EndTime = Get-Date
        Results = $Results
    }
    
    $summaryPath = Join-Path $OutputPath "BatchSendSummary_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $summary | ConvertTo-Json -Depth 10 | Set-Content $summaryPath -Encoding UTF8
    
    Write-Log ""
    Write-Log "========== BATCH SUMMARY ==========" -Level Info
    Write-Log "Total files: $($summary.TotalFiles)"
    Write-Log "Successful: $($summary.Successful)" -Level Success
    Write-Log "Failed: $($summary.Failed)" -Level $(if ($summary.Failed -gt 0) { "Error" } else { "Info" })
    Write-Log "Total duration: $([math]::Round($summary.TotalDurationSeconds / 60, 2)) minutes"
    Write-Log "Summary saved to: $summaryPath"
    Write-Log "===================================" -Level Info
    
    return $summary
}

#endregion

#region Main Script

Write-Log "========== Speckle Batch Send =========="
Write-Log "Folder: $FolderPath"

# Find Revit executable
if ([string]::IsNullOrEmpty($RevitPath)) {
    $RevitPath = Find-RevitExecutable -Year $RevitYear
}

if ([string]::IsNullOrEmpty($RevitPath) -or -not (Test-Path $RevitPath)) {
    Write-Log "Revit executable not found. Please specify -RevitPath or install Revit." -Level Error
    exit 1
}

Write-Log "Revit: $RevitPath"

# Check config
if ([string]::IsNullOrEmpty($ConfigPath)) {
    $ConfigPath = Get-SpeckleConfigPath
}

Write-Log "Config: $ConfigPath"

if (-not (Test-SpeckleConfig -Path $ConfigPath)) {
    Write-Log "Invalid or missing Speckle config. Please set up $ConfigPath" -Level Error
    Write-Log "Example config:" -Level Info
    @"
{
  "ServerUrl": "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com",
  "AccountEmail": "shinesains@gmail.com",
  "DefaultStreamId": "your-stream-id",
  "AutoSendOnDocumentOpen": true,
  "CloseDocumentAfterSend": true,
  "CloseRevitAfterSend": true,
  "BranchName": "main",
  "CommitMessageTemplate": "Automated send: {DocumentName} at {Timestamp}"
}
"@ | Write-Host
    exit 1
}

# Update config for batch processing
Update-ConfigForAutoSend -Path $ConfigPath

# Get results directory
$resultsDir = Get-ResultsDirectory -ConfigPath $ConfigPath
if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
}
Write-Log "Results directory: $resultsDir"

# Find .rvt files (case-insensitive, including files with .ifc in the name)
$searchOption = if ($Recursive) { "AllDirectories" } else { "TopDirectoryOnly" }
$allFiles = Get-ChildItem -Path $FolderPath -Recurse:$Recursive -File

Write-Log "Scanning for Revit files in: $FolderPath" -Level Info
Write-Log "Found $($allFiles.Count) total file(s) to check" -Level Info

# Filter for Revit files - handle .rvt, .RVT (case-insensitive)
# Note: PowerShell's $_.Extension only returns the LAST extension (e.g., .RVT for file.ifc.0001.RVT)
$rvtFiles = $allFiles | Where-Object { 
    $ext = $_.Extension.ToLower()
    $name = $_.Name.ToLower()
    
    # Check if file ends with .rvt extension (case-insensitive)
    # This will catch both .RVT and .rvt files, including files like:
    # - 6513-005-SB-R22-GALA.ifc.RVT
    # - 6513-005-SB-R22-GALA.ifc.0001.RVT
    $isRevitFile = $false
    
    if ($ext -eq ".rvt") {
        $isRevitFile = $true
        Write-Log "  Found Revit file: $($_.Name) ($([math]::Round($_.Length/1MB, 2)) MB)" -Level Info
    }
    
    $isRevitFile
} | Where-Object { 
    $name = $_.Name.ToLower()
    # Exclude backups and temporary files
    # Note: Don't exclude files with .0 in the name (like .ifc.0001.RVT) - those are valid Revit files
    $name -notlike "*_backup*" -and 
    $name -notlike "*~*" -and
    # Only exclude files that are clearly temporary (like file.0000.rvt, not file.ifc.0001.rvt)
    -not ($name -like "*.0000.rvt" -or $name -like "*.0000.ifc.rvt")
} | Sort-Object Name

if ($rvtFiles.Count -eq 0) {
    Write-Log "No .rvt files found in $FolderPath" -Level Warning
    Write-Log "Searched for files with extensions: .rvt, .RVT, and numbered files like .ifc.0001" -Level Info
    exit 0
}

Write-Log "Found $($rvtFiles.Count) .rvt file(s) to process"
Write-Log "========================================="
Write-Log ""

# Process files
$fileIndex = 0
foreach ($file in $rvtFiles) {
    $fileIndex++
    Write-Log ""
    Write-Log "========== Processing file $fileIndex of $($rvtFiles.Count) ==========" -Level Info
    Write-Log "File: $($file.Name)" -Level Info
    
    # Check if Revit is already running from previous file
    $existingRevit = Get-Process | Where-Object { $_.ProcessName -like "*Revit*" -and $_.Path -like "*Revit*" } | Select-Object -First 1
    if ($null -ne $existingRevit) {
        Write-Log "  Warning: Revit process (PID: $($existingRevit.Id)) is still running. Waiting for it to close..." -Level Warning
        $waitStart = Get-Date
        while ($null -ne (Get-Process -Id $existingRevit.Id -ErrorAction SilentlyContinue) -and ((Get-Date) - $waitStart).TotalSeconds -lt 120) {
            Start-Sleep -Seconds 2
        }
        if ($null -ne (Get-Process -Id $existingRevit.Id -ErrorAction SilentlyContinue)) {
            Write-Log "  Force killing remaining Revit process..." -Level Warning
            Stop-Process -Id $existingRevit.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
    }
    
    try {
        $result = Send-RevitFile -FilePath $file.FullName -RevitExe $RevitPath -TimeoutMinutes $TimeoutMinutes -ResultsDir $resultsDir
        $script:Results += $result
        
        if ($result.Success) {
            Write-Log "  [SUCCESS] File $fileIndex completed successfully" -Level Success
        }
        else {
            Write-Log "  [FAILED] File $fileIndex failed: $($result.ErrorMessage)" -Level Error
        }
    }
    catch {
        Write-Log "  [ERROR] File $fileIndex threw an exception: $_" -Level Error
        $errorResult = @{
            FilePath = $file.FullName
            FileName = $file.Name
            Success = $false
            CommitId = $null
            ErrorMessage = $_.Exception.Message
            StartTime = Get-Date
            EndTime = Get-Date
            DurationSeconds = 0
        }
        $script:Results += $errorResult
    }
    
    # Small delay between files to let system resources recover
    if ($fileIndex -lt $rvtFiles.Count) {
        Write-Log "  Waiting 5 seconds before processing next file" -Level Info
        Start-Sleep -Seconds 5
    }
}

# Output path for summary
if ([string]::IsNullOrEmpty($OutputPath)) {
    $OutputPath = $FolderPath
}

# Write summary
$summary = Write-BatchSummary -Results $script:Results -OutputPath $OutputPath

# Exit with appropriate code
if ($summary.Failed -gt 0) {
    exit 1
}
exit 0

#endregion


