# Script to help fix the account connection to AWS
# The issue is that the account exists but is pointing to localhost instead of AWS

Write-Host "=== Fixing Account Connection to AWS ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "The problem:" -ForegroundColor Yellow
Write-Host "  Your account (shinesains@gmail.com) exists but is connected to localhost:3000" -ForegroundColor White
Write-Host "  instead of your AWS server." -ForegroundColor White
Write-Host ""

Write-Host "Solution:" -ForegroundColor Yellow
Write-Host "  You need to use Speckle Manager DESKTOP APPLICATION (not web) to:" -ForegroundColor White
Write-Host "  1. Remove the localhost account" -ForegroundColor Cyan
Write-Host "  2. Add a NEW account with AWS server URL" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== How to Open Speckle Manager Desktop App ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Method 1: From Revit" -ForegroundColor Yellow
Write-Host "  1. In Revit, go to Sidian tab" -ForegroundColor White
Write-Host "  2. Click the dropdown (where you see accounts)" -ForegroundColor White
Write-Host "  3. Click 'Manage accounts in Manager'" -ForegroundColor White
Write-Host "  4. This opens Speckle Manager desktop app" -ForegroundColor White
Write-Host ""

Write-Host "Method 2: Windows Start Menu" -ForegroundColor Yellow
Write-Host "  1. Press Windows key" -ForegroundColor White
Write-Host "  2. Type 'Speckle Manager'" -ForegroundColor White
Write-Host "  3. Click the desktop application (NOT the web version)" -ForegroundColor White
Write-Host ""

Write-Host "Method 3: From File Explorer" -ForegroundColor Yellow
$appData = [Environment]::GetFolderPath("ApplicationData")
$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
Write-Host "  Check these locations:" -ForegroundColor White
Write-Host "    $localAppData\Programs\Speckle" -ForegroundColor Cyan
Write-Host "    $appData\Speckle" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== Once Speckle Manager Opens ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. You'll see your accounts listed" -ForegroundColor White
Write-Host "2. Find the one for 'shinesains@gmail.com' on 'localhost:3000'" -ForegroundColor White
Write-Host "3. DELETE or REMOVE that account" -ForegroundColor Yellow
Write-Host "4. Click 'Add Account' button" -ForegroundColor White
Write-Host "5. Enter:" -ForegroundColor White
Write-Host "   Server: http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com" -ForegroundColor Cyan
Write-Host "   Email: shinesains@gmail.com" -ForegroundColor Cyan
Write-Host "   Password: Sidian2025!" -ForegroundColor Cyan
Write-Host "6. Click Login/Add" -ForegroundColor White
Write-Host "7. Close Speckle Manager" -ForegroundColor White
Write-Host "8. Restart Revit" -ForegroundColor White
Write-Host ""

Write-Host "=== Alternative: Check Account Storage ===" -ForegroundColor Cyan
Write-Host "Checking account database..." -ForegroundColor Yellow

$accountsDb = Join-Path $appData "Speckle\Accounts.db"
if (Test-Path $accountsDb) {
    Write-Host "Found accounts database: $accountsDb" -ForegroundColor Green
    Write-Host "Note: You can't edit this directly - use Speckle Manager app" -ForegroundColor Yellow
} else {
    Write-Host "Accounts database not found at expected location" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "The key is: Speckle Manager is a DESKTOP APP, not a website!" -ForegroundColor Yellow
Write-Host "It's separate from the web interface you've been using." -ForegroundColor Yellow


