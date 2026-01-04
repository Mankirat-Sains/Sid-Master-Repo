#Requires -Version 5.1
<#
.SYNOPSIS
    Finds and sends Revit files from the Waddell Samples folder structure.

.DESCRIPTION
    This script scans the Waddell Samples folder structure and finds the most recent
    Revit files in specific locations:
    - {Project}/Drawings/ - base level .rvt files
    - {Project}/Drawings/rvt/ - .rvt files in the rvt subfolder
    
    For each location, it selects the most recent file. If there's a tie (same date),
    it prefers files ending with ").rvt" (for Drawings) or ".rvt" without numbers (for rvt folder).

.PARAMETER BasePath
    Path to the Waddell Samples folder. Defaults to the standard location.

.PARAMETER RevitYear
    Revit version year (e.g., 2024, 2025). Default is 2025.

.PARAMETER WhatIf
    If specified, only shows what files would be processed without actually sending.

.PARAMETER TimeoutMinutes
    Timeout in minutes for each file. Default is 30.

.PARAMETER WorkingDirectory
    Directory to copy files to before processing. Files will be renamed as "{Project} - {FileName}".
    Defaults to a "Sidian" folder in the same parent directory as BasePath.

.PARAMETER CleanupWorkingFiles
    If specified, removes the working directory after processing completes.

.EXAMPLE
    .\FindAndSendWaddellSamples.ps1 -WhatIf
    Shows what files would be found and processed.

.EXAMPLE
    .\FindAndSendWaddellSamples.ps1 -RevitYear 2025
    Finds and sends all applicable Revit files.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$BasePath = "C:\Users\shine\OneDrive\Documents\Mankirat Singh Sains\Sidian\Resources\Revit\Waddell Samples",

    [Parameter(Mandatory = $false)]
    [ValidateRange(2019, 2030)]
    [int]$RevitYear = 2025,

    [Parameter(Mandatory = $false)]
    [switch]$WhatIf,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 240)]
    [int]$TimeoutMinutes = 30,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath,

    [Parameter(Mandatory = $false)]
    [string]$WorkingDirectory,

    [Parameter(Mandatory = $false)]
    [switch]$CleanupWorkingFiles
)

$ErrorActionPreference = "Stop"
$script:StartTime = Get-Date
$script:SecurityDialogHandler = $null  # Track security dialog handler (Job + LogFile)
$script:ManageLinksDialogHandler = $null  # Track Manage Links dialog handler (Job + LogFile)

# Load UI Automation assemblies for security dialog handling
Add-Type -AssemblyName UIAutomationClient -ErrorAction SilentlyContinue
Add-Type -AssemblyName UIAutomationTypes -ErrorAction SilentlyContinue

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

function Start-SecurityDialogHandler {
    <#
    .SYNOPSIS
        Monitors and automatically clicks "Always Load" on Revit security dialogs.
        Runs in background thread with file logging for visibility.
    #>
    
    $logFile = Join-Path $env:TEMP "SpeckleSecurityDialogHandler.log"
    "=== Security Dialog Handler Started at $(Get-Date) ===" | Out-File -FilePath $logFile
    
    # Start as background job but with logging
    $jobScript = {
        param($logFilePath)
        
        function Write-Log {
            param($message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
            "$timestamp - $message" | Out-File -FilePath $logFilePath -Append
        }
        
        Add-Type -AssemblyName UIAutomationClient -ErrorAction SilentlyContinue
        Add-Type -AssemblyName UIAutomationTypes -ErrorAction SilentlyContinue
        
        Write-Log "Handler started, beginning monitoring..."
        
        function Find-RevitWindow {
            try {
                # Strategy 1: Find by process (most reliable)
                Write-Log "Trying to find Revit by process name..."
                $revitProcesses = Get-Process -Name "Revit" -ErrorAction SilentlyContinue
                foreach ($process in $revitProcesses) {
                    try {
                        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
                            $window = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
                            if ($window -and $window.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window) {
                                $name = $window.Current.Name
                                Write-Log "Found Revit window by process handle: '$name' (PID: $($process.Id))"
                                return $window
                            }
                        }
                    }
                    catch { }
                }
                
                # Strategy 2: Find by window name (but exclude File Explorer)
                Write-Log "Trying to find Revit by window name..."
                $root = [System.Windows.Automation.AutomationElement]::RootElement
                $condition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Window
                )
                $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
                
                Write-Log "Looking for Revit window among $($windows.Count) top-level windows..."
                
                $revitKeywords = @("Autodesk Revit", "Revit")
                $excludeKeywords = @("File Explorer", "Explorer", "and 4 more tabs", "and 3 more tabs", "and 2 more tabs")
                
                foreach ($window in $windows) {
                    try {
                        $name = $window.Current.Name
                        if ([string]::IsNullOrEmpty($name)) { continue }
                        
                        # Skip File Explorer windows
                        $isExcluded = $false
                        foreach ($exclude in $excludeKeywords) {
                            if ($name -like "*$exclude*") {
                                $isExcluded = $true
                                break
                            }
                        }
                        if ($isExcluded) { continue }
                        
                        # Check if it matches Revit keywords
                        foreach ($keyword in $revitKeywords) {
                            if ($name -like "*$keyword*") {
                                Write-Log "Found Revit window by name: '$name'"
                                return $window
                            }
                        }
                    }
                    catch { }
                }
            }
            catch {
                Write-Log "Error finding Revit window: $_"
            }
            return $null
        }
        
        function Is-SecurityDialog {
            <#
            .SYNOPSIS
                Identifies if a dialog is the security dialog by checking its button characteristics.
                This is more reliable and language-agnostic than checking window titles.
            #>
            param($dialog)
            
            try {
                # Look for buttons in the dialog
                $buttonCondition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Button
                )
                $buttons = $dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)
                
                if ($null -eq $buttons -or $buttons.Count -lt 2) {
                    return $false  # Security dialog should have at least 2-3 buttons
                }
                
                Write-Log "Dialog has $($buttons.Count) button(s), checking characteristics..."
                
                # Characteristic button text patterns for security dialog (various languages)
                # Security dialog typically has: "Always Load", "Load Once", "Do Not Load"
                $characteristicPatterns = @(
                    "Always", "Load", "Once", "Do Not", "Not Load",
                    "Toujours", "charger",  # French
                    "Siempre", "cargar",   # Spanish
                    "Immer", "laden",       # German
                    "Carica", "sempre"     # Italian
                )
                
                $matchingButtons = 0
                $buttonTexts = @()
                
                foreach ($button in $buttons) {
                    try {
                        $buttonName = $button.Current.Name
                        if ([string]::IsNullOrEmpty($buttonName)) { continue }
                        
                        $buttonTexts += $buttonName
                        
                        # Check if button text matches characteristic patterns
                        foreach ($pattern in $characteristicPatterns) {
                            if ($buttonName -like "*$pattern*") {
                                $matchingButtons++
                                Write-Log "  Found characteristic button: '$buttonName'"
                                break
                            }
                        }
                    }
                    catch { }
                }
                
                Write-Log "  Button texts: $($buttonTexts -join ', ')"
                Write-Log "  Matching buttons: $matchingButtons"
                
                # Security dialog characteristics:
                # 1. Has 2-3 buttons
                # 2. At least 2 buttons match characteristic patterns
                # 3. First button (leftmost) typically contains "Always" or "Load"
                
                if ($matchingButtons -ge 2) {
                    Write-Log "  Identified as security dialog (found $matchingButtons matching buttons)"
                    return $true
                }
                
                # Also check: Security dialog typically has exactly 3 buttons
                # And the first button is usually "Always Load" (leftmost)
                if ($buttons.Count -eq 3) {
                    # Find leftmost button
                    $leftmostButton = $null
                    $minX = [double]::MaxValue
                    foreach ($button in $buttons) {
                        try {
                            $bounds = $button.Current.BoundingRectangle
                            if ($bounds.Left -lt $minX) {
                                $minX = $bounds.Left
                                $leftmostButton = $button
                            }
                        }
                        catch { }
                    }
                    
                    if ($leftmostButton) {
                        $firstButtonName = $leftmostButton.Current.Name
                        Write-Log "  Dialog has 3 buttons. Leftmost button: '$firstButtonName'"
                        
                        # If first button contains characteristic patterns, it's likely the security dialog
                        foreach ($pattern in @("Always", "Load", "Toujours", "Siempre", "Immer", "Carica")) {
                            if ($firstButtonName -like "*$pattern*") {
                                Write-Log "  Identified as security dialog (3 buttons with characteristic first button)"
                                return $true
                            }
                        }
                    }
                }
            }
            catch {
                Write-Log "Error in Is-SecurityDialog: $_"
            }
            
            return $false
        }
        
        function Find-SecurityDialog {
            try {
                # Strategy 1: Search ALL top-level windows for the security dialog
                # Modal dialogs can appear as separate top-level windows
                Write-Log "Searching all top-level windows for security dialog..."
                $root = [System.Windows.Automation.AutomationElement]::RootElement
                $condition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Window
                )
                $allWindows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
                Write-Log "Checking $($allWindows.Count) top-level windows..."
                
                foreach ($window in $allWindows) {
                    try {
                        $name = $window.Current.Name
                        Write-Log "Checking top-level window: '$name'"
                        
                        # Identify by button characteristics
                        if (Is-SecurityDialog -dialog $window) {
                            Write-Log "FOUND SECURITY DIALOG (top-level window): '$name' (identified by button characteristics)"
                            return $window
                        }
                    }
                    catch {
                        Write-Log "Error checking top-level window: $_"
                    }
                }
                
                # Strategy 2: Search within Revit window
                $revitWindow = Find-RevitWindow
                if ($null -ne $revitWindow) {
                    Write-Log "Searching for security dialog within Revit window (by button characteristics)..."
                    
                    # Search for dialogs within Revit window (descendants)
                    # Security dialogs can be Window, Dialog, or Pane control types
                    $dialogTypes = @(
                        [System.Windows.Automation.ControlType]::Window,
                        [System.Windows.Automation.ControlType]::Dialog,
                        [System.Windows.Automation.ControlType]::Pane
                    )
                    
                    foreach ($dialogType in $dialogTypes) {
                        $condition = New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                            $dialogType
                        )
                        
                        $dialogs = $revitWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
                        Write-Log "Found $($dialogs.Count) $($dialogType.ProgrammaticName) elements in Revit window"
                        
                        foreach ($dialog in $dialogs) {
                            try {
                                $name = $dialog.Current.Name
                                Write-Log "Checking dialog: '$name' (Type: $($dialogType.ProgrammaticName))"
                                
                                # Identify by button characteristics, not window title
                                if (Is-SecurityDialog -dialog $dialog) {
                                    Write-Log "FOUND SECURITY DIALOG: '$name' (identified by button characteristics)"
                                    return $dialog
                                }
                            }
                            catch {
                                Write-Log "Error checking dialog: $_"
                            }
                        }
                    }
                    
                    # Also check if the security dialog is a direct child window of Revit
                    $childWindows = $revitWindow.FindAll([System.Windows.Automation.TreeScope]::Children, 
                        (New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                            [System.Windows.Automation.ControlType]::Window
                        )))
                    
                    Write-Log "Found $($childWindows.Count) child windows of Revit"
                    foreach ($childWindow in $childWindows) {
                        try {
                            $name = $childWindow.Current.Name
                            Write-Log "Checking child window: '$name'"
                            
                            if (Is-SecurityDialog -dialog $childWindow) {
                                Write-Log "FOUND SECURITY DIALOG (child window): '$name' (identified by button characteristics)"
                                return $childWindow
                            }
                        }
                        catch { }
                    }
                }
                else {
                    Write-Log "Revit window not found, but already checked all top-level windows"
                }
            }
            catch {
                Write-Log "Error in Find-SecurityDialog: $_"
            }
            return $null
        }
        
        function Click-AlwaysLoadButton {
            param($dialog)
            
            try {
                $buttonCondition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Button
                )
                $buttons = $dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)
                
                Write-Log "Found $($buttons.Count) button(s) in dialog"
                
                if ($buttons -and $buttons.Count -gt 0) {
                    # Log all button names for debugging
                    $allButtonNames = @()
                    foreach ($btn in $buttons) {
                        try {
                            $allButtonNames += $btn.Current.Name
                        }
                        catch { }
                    }
                    Write-Log "Button names: $($allButtonNames -join ', ')"
                    
                    # Strategy 1: Find button by text pattern (most reliable)
                    # "Always Load" button typically contains "Always" or "Load" (or equivalents in other languages)
                    $alwaysLoadPatterns = @("Always", "Load", "Toujours", "Siempre", "Immer", "Carica")
                    $targetButton = $null
                    
                    foreach ($button in $buttons) {
                        try {
                            $buttonName = $button.Current.Name
                            if ([string]::IsNullOrEmpty($buttonName)) { continue }
                            
                            foreach ($pattern in $alwaysLoadPatterns) {
                                if ($buttonName -like "*$pattern*") {
                                    Write-Log "Found 'Always Load' button by pattern: '$buttonName'"
                                    $targetButton = $button
                                    break
                                }
                            }
                            if ($targetButton) { break }
                        }
                        catch { }
                    }
                    
                    # Strategy 2: If not found by pattern, use leftmost button (typically "Always Load" is first)
                    if ($null -eq $targetButton) {
                        Write-Log "Could not find button by pattern, trying leftmost button..."
                        $leftmostButton = $null
                        $minX = [double]::MaxValue
                        foreach ($button in $buttons) {
                            try {
                                $bounds = $button.Current.BoundingRectangle
                                if ($bounds.Left -lt $minX) {
                                    $minX = $bounds.Left
                                    $leftmostButton = $button
                                }
                            }
                            catch { }
                        }
                        $targetButton = $leftmostButton
                        if ($targetButton) {
                            $name = $targetButton.Current.Name
                            Write-Log "Using leftmost button: '$name'"
                        }
                    }
                    
                    # Strategy 3: Fallback to first button (index 0)
                    if ($null -eq $targetButton) {
                        Write-Log "Using first button (index 0) as fallback..."
                        $targetButton = $buttons[0]
                        $name = $targetButton.Current.Name
                        Write-Log "First button: '$name'"
                    }
                    
                    # Click the button
                    if ($targetButton) {
                        try {
                            $invokePattern = $targetButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                            if ($invokePattern) {
                                Start-Sleep -Milliseconds 500  # Small delay to ensure dialog is ready
                                $buttonName = $targetButton.Current.Name
                                Write-Log "Attempting to click button: '$buttonName'"
                                $invokePattern.Invoke()
                                Write-Log "SUCCESS: Clicked button '$buttonName'"
                                return $true
                            }
                            else {
                                Write-Log "Could not get InvokePattern for button"
                            }
                        }
                        catch {
                            Write-Log "Error invoking button: $_"
                        }
                    }
                }
                else {
                    Write-Log "No buttons found in dialog!"
                }
            }
            catch {
                Write-Log "Error in Click-AlwaysLoadButton: $_"
            }
            return $false
        }
        
        function Close-ManageLinksDialog {
            <#
            .SYNOPSIS
                Closes "Manage Links" and similar dialogs that can block automation.
            #>
            try {
                $dialogsToClose = @("Manage Links", "ManageLinks", "Link Manager", "External References")
                
                # Strategy 1: Search all top-level windows
                $root = [System.Windows.Automation.AutomationElement]::RootElement
                $condition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Window
                )
                $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
                
                Write-Log "Checking $($windows.Count) top-level windows for dialogs to close..."
                
                foreach ($window in $windows) {
                    try {
                        $name = $window.Current.Name
                        if ([string]::IsNullOrEmpty($name)) { continue }
                        
                        foreach ($dialogName in $dialogsToClose) {
                            if ($name -like "*$dialogName*") {
                                Write-Log "Found dialog to close (top-level): '$name', attempting to close..."
                                if (Close-DialogWindow -window $window -name $name) {
                                    return $true
                                }
                            }
                        }
                    }
                    catch { }
                }
                
                # Strategy 2: Search within Revit window for child windows
                $revitWindow = Find-RevitWindow
                if ($revitWindow) {
                    Write-Log "Searching within Revit window for dialogs to close..."
                    $childWindows = $revitWindow.FindAll([System.Windows.Automation.TreeScope]::Children, 
                        (New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                            [System.Windows.Automation.ControlType]::Window
                        )))
                    
                    Write-Log "Found $($childWindows.Count) child windows of Revit"
                    foreach ($childWindow in $childWindows) {
                        try {
                            $name = $childWindow.Current.Name
                            if ([string]::IsNullOrEmpty($name)) { continue }
                            
                            Write-Log "Checking child window: '$name'"
                            
                            foreach ($dialogName in $dialogsToClose) {
                                if ($name -like "*$dialogName*") {
                                    Write-Log "Found dialog to close (child window): '$name', attempting to close..."
                                    if (Close-DialogWindow -window $childWindow -name $name) {
                                        return $true
                                    }
                                }
                            }
                        }
                        catch { }
                    }
                }
            }
            catch {
                Write-Log "Error in Close-ManageLinksDialog: $_"
            }
            return $false
        }
        
        function Close-DialogWindow {
            param($window, $name)
            
            try {
                # Method 1: Try to find and click the close button (X button)
                # Close button might have different names: "Close", "×", etc.
                $closeButtonNames = @("Close", "×", "✕")
                
                foreach ($closeButtonName in $closeButtonNames) {
                    try {
                        $closeButton = $window.FindFirst(
                            [System.Windows.Automation.TreeScope]::Descendants,
                            (New-Object System.Windows.Automation.PropertyCondition(
                                [System.Windows.Automation.AutomationElement]::NameProperty,
                                $closeButtonName
                            ))
                        )
                        
                        if ($closeButton) {
                            $invokePattern = $closeButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                            if ($invokePattern) {
                                Write-Log "  Found close button '$closeButtonName', clicking..."
                                $invokePattern.Invoke()
                                Start-Sleep -Milliseconds 300
                                Write-Log "  SUCCESS: Closed dialog '$name' via close button"
                                return $true
                            }
                        }
                    }
                    catch {
                        Write-Log "  Could not use close button '$closeButtonName': $_"
                    }
                }
                
                # Method 2: Try to find close button by AutomationId or ControlType
                try {
                    $buttonCondition = New-Object System.Windows.Automation.AndCondition(
                        (New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                            [System.Windows.Automation.ControlType]::Button
                        )),
                        (New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
                            "Close"
                        ))
                    )
                    $closeButton = $window.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)
                    if ($closeButton) {
                        $invokePattern = $closeButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                        if ($invokePattern) {
                            Write-Log "  Found close button by AutomationId, clicking..."
                            $invokePattern.Invoke()
                            Start-Sleep -Milliseconds 300
                            Write-Log "  SUCCESS: Closed dialog '$name' via AutomationId"
                            return $true
                        }
                    }
                }
                catch {
                    Write-Log "  Could not find close button by AutomationId: $_"
                }
                
                # Method 3: Send Escape key (focus the window first)
                try {
                    # Try to set focus to the window
                    try {
                        $window.SetFocus()
                        Start-Sleep -Milliseconds 100
                    }
                    catch { }
                    
                    Add-Type -AssemblyName System.Windows.Forms
                    [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
                    Start-Sleep -Milliseconds 300
                    Write-Log "  Sent Escape key to close dialog '$name'"
                    return $true
                }
                catch {
                    Write-Log "  Could not send Escape key: $_"
                }
                
                Write-Log "  Could not close dialog '$name' - all methods failed"
            }
            catch {
                Write-Log "  Error in Close-DialogWindow: $_"
            }
            return $false
        }
        
        # Monitor for security dialog AND close unwanted dialogs
        $maxAttempts = 30
        $attempt = 0
        $found = $false
        
        while ($attempt -lt $maxAttempts -and -not $found) {
            $attempt++
            Write-Log "Attempt $attempt/$maxAttempts - Looking for security dialog..."
            
            # Also try to close "Manage Links" and similar dialogs
            Close-ManageLinksDialog | Out-Null
            
            $dialog = Find-SecurityDialog
            
            if ($dialog) {
                Write-Log "Dialog found! Attempting to click button..."
                if (Click-AlwaysLoadButton -dialog $dialog) {
                    Write-Log "SUCCESS: Security dialog handled!"
                    $found = $true
                    break
                }
                else {
                    Write-Log "Failed to click button, will retry..."
                }
            }
            
            Start-Sleep -Seconds 2
        }
        
        # Final attempt to close unwanted dialogs
        Close-ManageLinksDialog | Out-Null
        
        if (-not $found) {
            Write-Log "TIMEOUT: Security dialog not found after $maxAttempts attempts"
        }
        
        Write-Log "Handler completed"
        return $found
    }
    
    # Start as background job with log file path
    $job = Start-Job -ScriptBlock $jobScript -ArgumentList $logFile
    
    return @{
        Job = $job
        LogFile = $logFile
    }
}

function Stop-SecurityDialogHandler {
    param($HandlerResult)
    
    if ($HandlerResult -and $HandlerResult.Job) {
        $job = $HandlerResult.Job
        if ($job.State -eq "Running") {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -ErrorAction SilentlyContinue
        
        # Show final log status
        if ($HandlerResult.LogFile -and (Test-Path $HandlerResult.LogFile)) {
            Write-Log "  Security handler log (last 5 lines):" -Level Info
            Get-Content $HandlerResult.LogFile -Tail 5 | ForEach-Object {
                Write-Log "    $_" -Level Info
            }
        }
    }
}

function Get-SecurityDialogHandlerStatus {
    <#
    .SYNOPSIS
        Checks and displays the current status of the security dialog handler.
    #>
    if ($null -ne $script:SecurityDialogHandler -and $script:SecurityDialogHandler.LogFile) {
        $logFile = $script:SecurityDialogHandler.LogFile
        if (Test-Path $logFile) {
            Write-Log "  Security handler status (last 10 lines):" -Level Info
            Get-Content $logFile -Tail 10 | ForEach-Object {
                Write-Log "    $_" -Level Info
            }
        }
    }
}

function Start-ManageLinksDialogHandler {
    <#
    .SYNOPSIS
        Monitors and automatically closes "Manage Links" and similar dialogs.
        Runs in background with fast polling (every 1 second) for quick response.
    #>
    
    $logFile = Join-Path $env:TEMP "SpeckleManageLinksHandler.log"
    "=== Manage Links Dialog Handler Started at $(Get-Date) ===" | Out-File -FilePath $logFile
    
    $jobScript = {
        param($logFilePath)
        
        function Write-Log {
            param($message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
            "$timestamp - $message" | Out-File -FilePath $logFilePath -Append
        }
        
        Add-Type -AssemblyName UIAutomationClient -ErrorAction SilentlyContinue
        Add-Type -AssemblyName UIAutomationTypes -ErrorAction SilentlyContinue
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
        
        Write-Log "Handler started, beginning fast monitoring (every 1 second)..."
        
        function Close-ManageLinksDialogFast {
            try {
                $dialogsToClose = @("Manage Links", "ManageLinks", "Link Manager", "External References")
                
                # Strategy 1: Check all top-level windows
                $root = [System.Windows.Automation.AutomationElement]::RootElement
                $condition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Window
                )
                $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
                
                foreach ($window in $windows) {
                    try {
                        $name = $window.Current.Name
                        if ([string]::IsNullOrEmpty($name)) { continue }
                        
                        foreach ($dialogName in $dialogsToClose) {
                            if ($name -like "*$dialogName*") {
                                Write-Log "Found '$name' dialog (top-level), closing immediately..."
                                
                                # Try close button
                                $closeButton = $window.FindFirst(
                                    [System.Windows.Automation.TreeScope]::Descendants,
                                    (New-Object System.Windows.Automation.PropertyCondition(
                                        [System.Windows.Automation.AutomationElement]::NameProperty,
                                        "Close"
                                    ))
                                )
                                
                                if ($closeButton) {
                                    try {
                                        $invokePattern = $closeButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                                        if ($invokePattern) {
                                            $window.SetFocus()
                                            Start-Sleep -Milliseconds 50
                                            $invokePattern.Invoke()
                                            Write-Log "SUCCESS: Closed '$name' via close button"
                                            return $true
                                        }
                                    }
                                    catch { }
                                }
                                
                                # Fallback: Send Escape
                                try {
                                    $window.SetFocus()
                                    Start-Sleep -Milliseconds 50
                                    [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
                                    Write-Log "SUCCESS: Closed '$name' via Escape key"
                                    return $true
                                }
                                catch { }
                            }
                        }
                    }
                    catch { }
                }
                
                # Strategy 2: Check child windows of Revit
                try {
                    $revitProcesses = Get-Process -Name "Revit" -ErrorAction SilentlyContinue
                    foreach ($process in $revitProcesses) {
                        try {
                            if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
                                $revitWindow = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
                                if ($revitWindow) {
                                    $childWindows = $revitWindow.FindAll([System.Windows.Automation.TreeScope]::Children, 
                                        (New-Object System.Windows.Automation.PropertyCondition(
                                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                                            [System.Windows.Automation.ControlType]::Window
                                        )))
                                    
                                    foreach ($childWindow in $childWindows) {
                                        try {
                                            $name = $childWindow.Current.Name
                                            if ([string]::IsNullOrEmpty($name)) { continue }
                                            
                                            foreach ($dialogName in $dialogsToClose) {
                                                if ($name -like "*$dialogName*") {
                                                    Write-Log "Found '$name' dialog (child window), closing immediately..."
                                                    
                                                    # Try close button
                                                    $closeButton = $childWindow.FindFirst(
                                                        [System.Windows.Automation.TreeScope]::Descendants,
                                                        (New-Object System.Windows.Automation.PropertyCondition(
                                                            [System.Windows.Automation.AutomationElement]::NameProperty,
                                                            "Close"
                                                        ))
                                                    )
                                                    
                                                    if ($closeButton) {
                                                        try {
                                                            $invokePattern = $closeButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                                                            if ($invokePattern) {
                                                                $childWindow.SetFocus()
                                                                Start-Sleep -Milliseconds 50
                                                                $invokePattern.Invoke()
                                                                Write-Log "SUCCESS: Closed '$name' via close button"
                                                                return $true
                                                            }
                                                        }
                                                        catch { }
                                                    }
                                                    
                                                    # Fallback: Send Escape
                                                    try {
                                                        $childWindow.SetFocus()
                                                        Start-Sleep -Milliseconds 50
                                                        [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
                                                        Write-Log "SUCCESS: Closed '$name' via Escape key"
                                                        return $true
                                                    }
                                                    catch { }
                                                }
                                            }
                                        }
                                        catch { }
                                    }
                                }
                            }
                        }
                        catch { }
                    }
                }
                catch { }
            }
            catch {
                Write-Log "Error in Close-ManageLinksDialogFast: $_"
            }
            return $false
        }
        
        # Fast polling loop - check every 1 second
        $maxAttempts = 300  # Run for up to 5 minutes (300 seconds)
        $attempt = 0
        
        while ($attempt -lt $maxAttempts) {
            $attempt++
            
            if (Close-ManageLinksDialogFast) {
                Write-Log "Dialog closed successfully, continuing to monitor..."
            }
            
            Start-Sleep -Seconds 1  # Check every 1 second for fast response
        }
        
        Write-Log "Handler completed (reached max attempts)"
        return $true
    }
    
    $job = Start-Job -ScriptBlock $jobScript -ArgumentList $logFile
    
    return @{
        Job = $job
        LogFile = $logFile
    }
}

function Stop-ManageLinksDialogHandler {
    param($HandlerResult)
    
    if ($HandlerResult -and $HandlerResult.Job) {
        $job = $HandlerResult.Job
        if ($job.State -eq "Running") {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -ErrorAction SilentlyContinue
        
        # Show final log status
        if ($HandlerResult.LogFile -and (Test-Path $HandlerResult.LogFile)) {
            Write-Log "  Manage Links handler log (last 5 lines):" -Level Info
            Get-Content $HandlerResult.LogFile -Tail 5 | ForEach-Object {
                Write-Log "    $_" -Level Info
            }
        }
    }
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
        # NOTE: Journal files are disabled as they prevent files from opening properly
        # Dialogs will appear but files will open and auto-send will work
        # TODO: Implement dialog handling via Revit API in the C# connector if needed
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $RevitExe
        $processInfo.Arguments = "`"$FilePath`""
        Write-Log "  Launching Revit with file (journal files disabled to ensure file opens)" -Level Info
        Write-Log "  Note: Dialogs may appear - they will need to be dismissed manually for now" -Level Warning
        
        $processInfo.UseShellExecute = $true
        
        $process = [System.Diagnostics.Process]::Start($processInfo)
        
        if ($null -eq $process) {
            throw "Failed to start Revit process"
        }
        
        Write-Log "  Revit started (PID: $($process.Id)), waiting for completion..."
        
        # Start security dialog handler in background
        Write-Log "  Starting security dialog auto-handler..." -Level Info
        $handlerResult = Start-SecurityDialogHandler
        $script:SecurityDialogHandler = $handlerResult  # Store for cleanup
        Write-Log "  Handler log file: $($handlerResult.LogFile)" -Level Info
        Write-Log "  Handler job ID: $($handlerResult.Job.Id)" -Level Info
        
        # Start Manage Links dialog handler in background (fast polling - every 1 second)
        Write-Log "  Starting Manage Links dialog auto-handler (fast polling)..." -Level Info
        $manageLinksHandler = Start-ManageLinksDialogHandler
        $script:ManageLinksDialogHandler = $manageLinksHandler  # Store for cleanup
        Write-Log "  Manage Links handler log file: $($manageLinksHandler.LogFile)" -Level Info
        Write-Log "  Manage Links handler job ID: $($manageLinksHandler.Job.Id)" -Level Info
        
        # Wait for result file or timeout
        $estimatedSendTime = 300 # 5 minutes
        $startTime = Get-Date
        $checkInterval = 10
        $resultFile = $null
        $sendCompleted = $false
        $revitExited = $false
        
        Write-Log "  Waiting for send to complete..." -Level Info
        Write-Log "  Result file location: $ResultsDir" -Level Info
        Write-Log "  Expected pattern: $([System.IO.Path]::GetFileNameWithoutExtension($fileName))_*.json" -Level Info
        Write-Log "  Strategy: Check for result file every 10s, wait up to 5 minutes, then close Revit" -Level Info
        
        while ((Get-Date) - $startTime -lt [TimeSpan]::FromSeconds($estimatedSendTime)) {
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            
            # Check security handler status periodically (every 30 seconds)
            if ($elapsed -gt 0 -and [math]::Floor($elapsed) % 30 -lt $checkInterval -and $null -ne $script:SecurityDialogHandler) {
                Get-SecurityDialogHandlerStatus
            }
            
            # Continuously monitor and close "Manage Links" and similar dialogs
            # Run this check every loop iteration to catch dialogs as soon as they appear
            try {
                Add-Type -AssemblyName UIAutomationClient -ErrorAction SilentlyContinue
                Add-Type -AssemblyName UIAutomationTypes -ErrorAction SilentlyContinue
                
                $dialogsToClose = @("Manage Links", "ManageLinks", "Link Manager", "External References")
                
                # Strategy 1: Check all top-level windows
                $root = [System.Windows.Automation.AutomationElement]::RootElement
                $condition = New-Object System.Windows.Automation.PropertyCondition(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Window
                )
                $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
                
                foreach ($window in $windows) {
                    try {
                        $name = $window.Current.Name
                        if ([string]::IsNullOrEmpty($name)) { continue }
                        
                        foreach ($dialogName in $dialogsToClose) {
                            if ($name -like "*$dialogName*") {
                                Write-Log "  [AUTO-CLOSE] Found '$name' dialog (top-level), closing..." -Level Warning
                                if (Close-DialogWindowInline -window $window -name $name) {
                                    break
                                }
                            }
                        }
                    }
                    catch { }
                }
                
                # Strategy 2: Check child windows of Revit (where "Manage Links" often appears)
                try {
                    $revitProcesses = Get-Process -Name "Revit" -ErrorAction SilentlyContinue
                    foreach ($process in $revitProcesses) {
                        try {
                            if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
                                $revitWindow = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
                                if ($revitWindow) {
                                    $childWindows = $revitWindow.FindAll([System.Windows.Automation.TreeScope]::Children, 
                                        (New-Object System.Windows.Automation.PropertyCondition(
                                            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                                            [System.Windows.Automation.ControlType]::Window
                                        )))
                                    
                                    foreach ($childWindow in $childWindows) {
                                        try {
                                            $name = $childWindow.Current.Name
                                            if ([string]::IsNullOrEmpty($name)) { continue }
                                            
                                            foreach ($dialogName in $dialogsToClose) {
                                                if ($name -like "*$dialogName*") {
                                                    Write-Log "  [AUTO-CLOSE] Found '$name' dialog (child window), closing..." -Level Warning
                                                    if (Close-DialogWindowInline -window $childWindow -name $name) {
                                                        break
                                                    }
                                                }
                                            }
                                        }
                                        catch { }
                                    }
                                }
                            }
                        }
                        catch { }
                    }
                }
                catch { }
            }
            catch {
                # Silently fail - don't spam logs with UI Automation errors
            }
            
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
                    break
                }
            }
            
            if ($elapsed -gt 0 -and [math]::Floor($elapsed) % 60 -lt $checkInterval) {
                Write-Log "  Send in progress... (${elapsed}s elapsed)" -Level Info
            }
            
            Start-Sleep -Seconds $checkInterval
        }
        
        # Final check for result file
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
        
        # Close Revit if still running
        if (-not $process.HasExited) {
            if ($null -ne $resultFile) {
                Write-Log "  Result file found, waiting 10 seconds for Revit to close gracefully..."
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
        
        # Stop security dialog handler and show status
        if ($null -ne $script:SecurityDialogHandler) {
            Write-Log "  Checking security dialog handler status..." -Level Info
            Get-SecurityDialogHandlerStatus
            Stop-SecurityDialogHandler -HandlerResult $script:SecurityDialogHandler
            $script:SecurityDialogHandler = $null
        }
        
        # Stop Manage Links dialog handler
        if ($null -ne $script:ManageLinksDialogHandler) {
            Write-Log "  Stopping Manage Links dialog handler..." -Level Info
            Stop-ManageLinksDialogHandler -HandlerResult $script:ManageLinksDialogHandler
            $script:ManageLinksDialogHandler = $null
        }
        
        Start-Sleep -Seconds 2
        
        # Journal file cleanup removed (journal files are disabled)
        
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

function Get-MostRecentRevitFile {
    <#
    .SYNOPSIS
        Gets the most recent Revit file from a folder.
        If there's a tie on modification date, prefers files ending with ").rvt" or ".rvt" (no numbers).
    #>
    param(
        [string]$FolderPath,
        [switch]$PreferCleanExtension  # If true, prefer ".rvt" over ".0001.rvt" on tie
    )
    
    if (-not (Test-Path $FolderPath)) {
        return $null
    }
    
    # Get all .rvt files
    $rvtFiles = Get-ChildItem -Path $FolderPath -Filter "*.rvt" -File -ErrorAction SilentlyContinue |
                Where-Object { 
                    $name = $_.Name.ToLower()
                    # Exclude backups and temp files
                    $name -notlike "*_backup*" -and 
                    $name -notlike "*~*"
                }
    
    if ($rvtFiles.Count -eq 0) {
        return $null
    }
    
    if ($rvtFiles.Count -eq 1) {
        return $rvtFiles[0]
    }
    
    # Sort by LastWriteTime descending to get the most recent
    $sortedFiles = $rvtFiles | Sort-Object LastWriteTime -Descending
    
    # Get the most recent date
    $mostRecentDate = $sortedFiles[0].LastWriteTime
    
    # Get all files with the most recent date (potential ties)
    $tiedFiles = $sortedFiles | Where-Object { $_.LastWriteTime -eq $mostRecentDate }
    
    if ($tiedFiles.Count -eq 1) {
        return $tiedFiles[0]
    }
    
    # There's a tie - apply preference rules
    if ($PreferCleanExtension) {
        # Prefer files ending with just ".rvt" (no numbers like .0001.rvt)
        # This means the filename doesn't have a number before .rvt
        $cleanFiles = $tiedFiles | Where-Object { 
            $_.Name -match '\)\s*\.rvt$' -or  # Ends with ).rvt
            ($_.Name -notmatch '\.\d+\.rvt$' -and $_.Name -notmatch '\.\d+\)\.rvt$')  # No number before .rvt
        }
        
        if ($cleanFiles.Count -gt 0) {
            # Among clean files, prefer ones ending with ).rvt
            $parenFiles = $cleanFiles | Where-Object { $_.Name -match '\)\.rvt$' }
            if ($parenFiles.Count -gt 0) {
                return $parenFiles[0]
            }
            return $cleanFiles[0]
        }
    }
    else {
        # Prefer files ending with ").rvt"
        $parenFiles = $tiedFiles | Where-Object { $_.Name -match '\)\.rvt$' }
        if ($parenFiles.Count -gt 0) {
            return $parenFiles[0]
        }
    }
    
    # No preference match, return the first (most recent by name if dates are equal)
    return ($tiedFiles | Sort-Object Name -Descending)[0]
}

function New-RevitJournalFile {
    <#
    .SYNOPSIS
        Creates a Revit journal file that automatically handles common dialogs.
    #>
    param(
        [string]$FilePath,
        [string]$OutputPath
    )
    
    # Journal file content that handles common dialogs
    # Revit journal files are VBScript files that must initialize the Jrn object first
    # Format based on actual Revit journal files
    $journalContent = @"
' Revit Journal File - Auto-dismiss dialogs
' Generated for automated processing
' File: $([System.IO.Path]::GetFileName($FilePath))
' Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

' Initialize the Jrn object (REQUIRED for journal files to work)
Dim Jrn
Set Jrn = CrsJournalScript

' Handle dialogs that may appear when opening the file
' Unresolved References
Jrn.Directive "Modal" , "Unresolved References" , "Ignore and continue opening the project" , IDOK

' Upgrade dialogs
Jrn.Directive "Modal" , "Upgrade" , "Yes" , IDYES
Jrn.Directive "Modal" , "Model Upgrade Required" , "Yes" , IDYES

' File Version
Jrn.Directive "Modal" , "File Version" , "Yes" , IDYES
Jrn.Directive "Modal" , "File Version" , "OK" , IDOK

' Worksharing
Jrn.Directive "Modal" , "Worksharing" , "Open Local" , 2
Jrn.Directive "Modal" , "Detach from Central" , "Detach and preserve worksets" , 1
Jrn.Directive "Modal" , "Workset" , "OK" , IDOK
Jrn.Directive "Modal" , "Central File" , "Open Local" , 2

' Audit
Jrn.Directive "Modal" , "Audit" , "No" , IDNO

' File Not Saved
Jrn.Directive "Modal" , "File Not Saved" , "OK" , IDOK
"@
    
    try {
        # Ensure output directory exists
        $outputDir = Split-Path $OutputPath -Parent
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        # Write journal file
        Set-Content -Path $OutputPath -Value $journalContent -Encoding ASCII
        return $OutputPath
    }
    catch {
        Write-Log "Failed to create journal file: $_" -Level Error
        throw
    }
}

function Copy-FileToWorkingDirectory {
    <#
    .SYNOPSIS
        Copies a Revit file to the working directory with renamed format: "{Project} - {FileName}"
    #>
    param(
        [string]$SourceFilePath,
        [string]$ProjectName,
        [string]$WorkingDir
    )
    
    # Create working directory if it doesn't exist
    if (-not (Test-Path $WorkingDir)) {
        New-Item -ItemType Directory -Path $WorkingDir -Force | Out-Null
        Write-Log "Created working directory: $WorkingDir" -Level Info
    }
    
    # Get original file name without extension
    $originalFileName = [System.IO.Path]::GetFileNameWithoutExtension($SourceFilePath)
    $extension = [System.IO.Path]::GetExtension($SourceFilePath)
    
    # Create new name: "{Project} - {FileName}.rvt"
    $newFileName = "$ProjectName - $originalFileName$extension"
    $destinationPath = Join-Path $WorkingDir $newFileName
    
    # Check if file already exists
    if (Test-Path $destinationPath) {
        Write-Log "  Working copy already exists: $newFileName" -Level Info
        # Remove and recopy to ensure we have the latest version
        Remove-Item $destinationPath -Force -ErrorAction SilentlyContinue
    }
    
    try {
        Write-Log "  Copying to working directory..." -Level Info
        Write-Log "    Source: $([System.IO.Path]::GetFileName($SourceFilePath))" -Level Info
        Write-Log "    Destination: $newFileName" -Level Info
        
        Copy-Item -Path $SourceFilePath -Destination $destinationPath -Force
        
        Write-Log "  Successfully copied: $newFileName" -Level Success
        return $destinationPath
    }
    catch {
        Write-Log "  Failed to copy file: $_" -Level Error
        throw
    }
}

function Find-WaddellSamplesRevitFiles {
    <#
    .SYNOPSIS
        Scans the Waddell Samples folder structure and finds applicable Revit files.
    #>
    param(
        [string]$BasePath
    )
    
    $foundFiles = @()
    
    if (-not (Test-Path $BasePath)) {
        Write-Log "Base path does not exist: $BasePath" -Level Error
        return $foundFiles
    }
    
    Write-Log "Scanning: $BasePath" -Level Info
    
    # Get all project subfolders (like 25-01-133, 25-02-145, etc.)
    $projectFolders = Get-ChildItem -Path $BasePath -Directory -ErrorAction SilentlyContinue
    
    Write-Log "Found $($projectFolders.Count) project folder(s)" -Level Info
    
    foreach ($projectFolder in $projectFolders) {
        Write-Log ""
        Write-Log "Checking project: $($projectFolder.Name)" -Level Info
        
        $drawingsPath = Join-Path $projectFolder.FullName "Drawings"
        
        if (-not (Test-Path $drawingsPath)) {
            Write-Log "  No Drawings folder found, skipping" -Level Warning
            continue
        }
        
        # Check 1: Drawings folder base level
        Write-Log "  Checking: Drawings/" -Level Info
        $drawingsFile = Get-MostRecentRevitFile -FolderPath $drawingsPath
        if ($null -ne $drawingsFile) {
            Write-Log "    Selected: $($drawingsFile.Name) (Modified: $($drawingsFile.LastWriteTime))" -Level Success
            $foundFiles += [PSCustomObject]@{
                Project = $projectFolder.Name
                Location = "Drawings"
                File = $drawingsFile
                FullPath = $drawingsFile.FullName
            }
        }
        else {
            Write-Log "    No .rvt files found in Drawings base" -Level Info
        }
        
        # Check 2: Drawings/rvt folder
        $rvtPath = Join-Path $drawingsPath "rvt"
        if (Test-Path $rvtPath) {
            Write-Log "  Checking: Drawings/rvt/" -Level Info
            $rvtFile = Get-MostRecentRevitFile -FolderPath $rvtPath -PreferCleanExtension
            if ($null -ne $rvtFile) {
                Write-Log "    Selected: $($rvtFile.Name) (Modified: $($rvtFile.LastWriteTime))" -Level Success
                $foundFiles += [PSCustomObject]@{
                    Project = $projectFolder.Name
                    Location = "Drawings/rvt"
                    File = $rvtFile
                    FullPath = $rvtFile.FullName
                }
            }
            else {
                Write-Log "    No .rvt files found in Drawings/rvt" -Level Info
            }
        }
        else {
            Write-Log "  No rvt subfolder found in Drawings" -Level Info
        }
    }
    
    return $foundFiles
}

#endregion

#region Main Script

Write-Log "========== Waddell Samples Revit File Finder =========="
Write-Log "Base Path: $BasePath"
Write-Log "Revit Year: $RevitYear"
Write-Log "Mode: $(if ($WhatIf) { 'Preview (WhatIf)' } else { 'Process' })"

# Set default working directory if not specified
if ([string]::IsNullOrEmpty($WorkingDirectory)) {
    $parentDir = Split-Path $BasePath -Parent
    $WorkingDirectory = Join-Path $parentDir "Sidian"
}
Write-Log "Working Directory: $WorkingDirectory"
Write-Log ""

# Find all applicable Revit files
$filesToProcess = Find-WaddellSamplesRevitFiles -BasePath $BasePath

Write-Log ""
Write-Log "========== Summary ==========" -Level Info
Write-Log "Total files found: $($filesToProcess.Count)" -Level $(if ($filesToProcess.Count -gt 0) { "Success" } else { "Warning" })

if ($filesToProcess.Count -eq 0) {
    Write-Log "No Revit files found to process" -Level Warning
    exit 0
}

# Display found files
Write-Log ""
Write-Log "Files to process:" -Level Info
$fileIndex = 0
foreach ($item in $filesToProcess) {
    $fileIndex++
    $newFileName = "$($item.Project) - $([System.IO.Path]::GetFileNameWithoutExtension($item.File.Name)).rvt"
    Write-Log "  $fileIndex. [$($item.Project)] $($item.Location)/$($item.File.Name)" -Level Info
    Write-Log "      â†’ Will copy to: $newFileName" -Level Info
}

if ($WhatIf) {
    Write-Log ""
    Write-Log "WhatIf mode - not processing files. Remove -WhatIf to actually send." -Level Warning
    Write-Log "Working directory would be: $WorkingDirectory" -Level Info
    exit 0
}

Write-Log ""
Write-Log "========== Processing Files ==========" -Level Info

# Find Revit executable
$RevitPath = Find-RevitExecutable -Year $RevitYear
if ([string]::IsNullOrEmpty($RevitPath) -or -not (Test-Path $RevitPath)) {
    Write-Log "Revit executable not found for year $RevitYear" -Level Error
    exit 1
}
Write-Log "Revit: $RevitPath"

# Get config and results directory
$ConfigPath = Get-SpeckleConfigPath
if (-not (Test-SpeckleConfig -Path $ConfigPath)) {
    Write-Log "Invalid or missing Speckle config at: $ConfigPath" -Level Error
    exit 1
}
Write-Log "Config: $ConfigPath"

# Update config for auto-send
Update-ConfigForAutoSend -Path $ConfigPath

# Get results directory
$resultsDir = Get-ResultsDirectory -ConfigPath $ConfigPath
if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
}
Write-Log "Results directory: $resultsDir"

# Process each file
$script:Results = @()
$fileIndex = 0

foreach ($item in $filesToProcess) {
    $fileIndex++
    Write-Log ""
    Write-Log "========== Processing file $fileIndex of $($filesToProcess.Count) ==========" -Level Info
    Write-Log "Project: $($item.Project)" -Level Info
    Write-Log "Location: $($item.Location)" -Level Info
    Write-Log "Original File: $($item.File.Name)" -Level Info
    
    # Copy file to working directory with renamed format
    $workingFilePath = $null
    try {
        $workingFilePath = Copy-FileToWorkingDirectory -SourceFilePath $item.FullPath -ProjectName $item.Project -WorkingDir $WorkingDirectory
        Write-Log "Working File: $([System.IO.Path]::GetFileName($workingFilePath))" -Level Info
    }
    catch {
        Write-Log "  [ERROR] Failed to copy file: $_" -Level Error
        $errorResult = @{
            FilePath = $item.FullPath
            FileName = $item.File.Name
            Project = $item.Project
            Location = $item.Location
            Success = $false
            CommitId = $null
            ErrorMessage = "Failed to copy to working directory: $_"
            StartTime = Get-Date
            EndTime = Get-Date
            DurationSeconds = 0
        }
        $script:Results += $errorResult
        continue
    }
    
    # Check if Revit is already running
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
        # Process the WORKING COPY, not the original
        $result = Send-RevitFile -FilePath $workingFilePath -RevitExe $RevitPath -TimeoutMinutes $TimeoutMinutes -ResultsDir $resultsDir
        
        # Add project info to result
        $result.Project = $item.Project
        $result.Location = $item.Location
        $result.OriginalPath = $item.FullPath  # Track original path for reference
        
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
            FilePath = $item.FullPath
            FileName = $item.File.Name
            Project = $item.Project
            Location = $item.Location
            Success = $false
            CommitId = $null
            ErrorMessage = $_.Exception.Message
            StartTime = Get-Date
            EndTime = Get-Date
            DurationSeconds = 0
        }
        $script:Results += $errorResult
    }
    
    # Small delay between files
    if ($fileIndex -lt $filesToProcess.Count) {
        Write-Log "  Waiting 5 seconds before processing next file" -Level Info
        Start-Sleep -Seconds 5
    }
}

# Write summary
Write-Log ""
Write-Log "========== BATCH SUMMARY ==========" -Level Info

$successCount = ($script:Results | Where-Object { $_.Success }).Count
$failedCount = ($script:Results | Where-Object { -not $_.Success }).Count

Write-Log "Total files: $($script:Results.Count)"
Write-Log "Successful: $successCount" -Level Success
Write-Log "Failed: $failedCount" -Level $(if ($failedCount -gt 0) { "Error" } else { "Info" })

# Calculate total duration
$totalDuration = ((Get-Date) - $script:StartTime).TotalMinutes
Write-Log "Total duration: $([math]::Round($totalDuration, 2)) minutes"

# Save summary to file
if ([string]::IsNullOrEmpty($OutputPath)) {
    $OutputPath = $BasePath
}

$summaryPath = Join-Path $OutputPath "WaddellSamplesSummary_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$summary = @{
    TotalFiles = $script:Results.Count
    Successful = $successCount
    Failed = $failedCount
    TotalDurationMinutes = [math]::Round($totalDuration, 2)
    StartTime = $script:StartTime
    EndTime = Get-Date
    Results = $script:Results
}
$summary | ConvertTo-Json -Depth 10 | Set-Content $summaryPath -Encoding UTF8
Write-Log "Summary saved to: $summaryPath"
Write-Log "===================================" -Level Info

# Cleanup working directory if requested
if ($CleanupWorkingFiles -and (Test-Path $WorkingDirectory)) {
    Write-Log ""
    Write-Log "Cleaning up working directory..." -Level Info
    try {
        Remove-Item $WorkingDirectory -Recurse -Force -ErrorAction Stop
        Write-Log "Working directory removed: $WorkingDirectory" -Level Success
    }
    catch {
        Write-Log "Failed to remove working directory: $_" -Level Warning
        Write-Log "You may need to manually delete: $WorkingDirectory" -Level Warning
    }
}

# Exit with appropriate code
if ($failedCount -gt 0) {
    exit 1
}
exit 0

#endregion

