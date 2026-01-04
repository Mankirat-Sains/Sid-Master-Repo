# PowerShell script to automatically click "Always Load" on Revit security dialog
# Run this BEFORE launching Revit, or while Revit is starting

Write-Host "=== Revit Security Dialog Auto-Clicker ===" -ForegroundColor Cyan
Write-Host "Monitoring for 'Security - Unsigned Add-In' dialog..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

$maxAttempts = 60  # Try for 60 seconds (30 attempts * 2 seconds)
$attempt = 0
$found = $false

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Find-SecurityDialog {
    try {
        $root = [System.Windows.Automation.AutomationElement]::RootElement
        
        # Get all top-level windows
        $condition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Window
        )
        
        $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
        
        $securityKeywords = @("Security", "Unsigned", "Add-In", "AddIn", "Publisher", "Verified")
        
        foreach ($window in $windows) {
            try {
                $name = $window.Current.Name
                if ([string]::IsNullOrEmpty($name)) { continue }
                
                # Check if window title contains security-related keywords
                $isSecurityDialog = $false
                foreach ($keyword in $securityKeywords) {
                    if ($name -like "*$keyword*") {
                        $isSecurityDialog = $true
                        break
                    }
                }
                
                if ($isSecurityDialog) {
                    Write-Host "Found security dialog: '$name'" -ForegroundColor Green
                    return $window
                }
            }
            catch { }
        }
    }
    catch {
        Write-Host "Error finding security dialog: $_" -ForegroundColor Red
    }
    
    return $null
}

function Click-AlwaysLoadButton {
    param($dialog)
    
    try {
        # Method 1: Try by button index (first button is usually "Always Load")
        $buttonCondition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button
        )
        
        $buttons = $dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)
        
        if ($buttons -and $buttons.Count -gt 0) {
            # Try first button (index 0)
            $firstButton = $buttons[0]
            $buttonName = $firstButton.Current.Name
            Write-Host "Trying first button: '$buttonName'" -ForegroundColor Yellow
            
            # Try to get InvokePattern
            $invokePattern = $null
            try {
                $invokePattern = $firstButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
            }
            catch { }
            
            if ($invokePattern) {
                $invokePattern.Invoke()
                Write-Host "SUCCESS: Clicked button '$buttonName' using InvokePattern" -ForegroundColor Green
                return $true
            }
            else {
                Write-Host "Could not get InvokePattern, trying alternative methods..." -ForegroundColor Yellow
                
                # Try finding by text
                foreach ($button in $buttons) {
                    $name = $button.Current.Name
                    if ($name -like "*Always*" -or $name -like "*Load*" -or $name -eq "Always Load") {
                        Write-Host "Found 'Always Load' button: '$name'" -ForegroundColor Yellow
                        try {
                            $invokePattern = $button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                            if ($invokePattern) {
                                $invokePattern.Invoke()
                                Write-Host "SUCCESS: Clicked 'Always Load' button" -ForegroundColor Green
                                return $true
                            }
                        }
                        catch { }
                    }
                }
                
                # Try leftmost button by position
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
                    $name = $leftmostButton.Current.Name
                    Write-Host "Trying leftmost button: '$name'" -ForegroundColor Yellow
                    try {
                        $invokePattern = $leftmostButton.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                        if ($invokePattern) {
                            $invokePattern.Invoke()
                            Write-Host "SUCCESS: Clicked leftmost button '$name'" -ForegroundColor Green
                            return $true
                        }
                    }
                    catch { }
                }
            }
        }
        
        Write-Host "Could not find or click 'Always Load' button" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "Error clicking button: $_" -ForegroundColor Red
        return $false
    }
}

# Main monitoring loop
while ($attempt -lt $maxAttempts -and -not $found) {
    $attempt++
    
    $dialog = Find-SecurityDialog
    
    if ($dialog) {
        Write-Host "`nSecurity dialog found! Attempting to click 'Always Load'..." -ForegroundColor Cyan
        
        if (Click-AlwaysLoadButton -dialog $dialog) {
            Write-Host "`n=== SUCCESS ===" -ForegroundColor Green
            Write-Host "Security dialog handled successfully!" -ForegroundColor Green
            $found = $true
            break
        }
        else {
            Write-Host "Failed to click button, will retry..." -ForegroundColor Yellow
        }
    }
    else {
        if ($attempt % 5 -eq 0) {
            Write-Host "Still monitoring... (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
        }
    }
    
    Start-Sleep -Seconds 2
}

if (-not $found) {
    Write-Host "`n=== TIMEOUT ===" -ForegroundColor Red
    Write-Host "Security dialog not found after $maxAttempts attempts" -ForegroundColor Red
    Write-Host "Either the dialog already appeared and was dismissed, or Revit hasn't started yet" -ForegroundColor Yellow
}

Write-Host "`nScript finished. Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


