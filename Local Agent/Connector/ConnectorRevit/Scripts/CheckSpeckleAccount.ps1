# Quick script to check if Speckle account exists

Write-Host "=== Checking Speckle Account ===" -ForegroundColor Cyan
Write-Host ""

$appData = [Environment]::GetFolderPath("ApplicationData")
$specklePath = Join-Path $appData "Speckle"

Write-Host "Speckle folder: $specklePath" -ForegroundColor Yellow

if (Test-Path $specklePath) {
    Write-Host "Speckle folder exists" -ForegroundColor Green
    
    $dbFiles = Get-ChildItem $specklePath -Recurse -Filter "*.db" -ErrorAction SilentlyContinue
    if ($dbFiles) {
        Write-Host "Found account database files:" -ForegroundColor Green
        $dbFiles | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Gray }
    }
    
    $configFile = Join-Path $specklePath "RevitAutomatedSend.json"
    if (Test-Path $configFile) {
        Write-Host "Config file exists" -ForegroundColor Green
        $config = Get-Content $configFile | ConvertFrom-Json
        Write-Host "  ServerUrl: $($config.ServerUrl)" -ForegroundColor Cyan
    }
} else {
    Write-Host "Speckle folder not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== IMPORTANT ===" -ForegroundColor Cyan
Write-Host "The account must be added in Speckle Manager (not just the web interface)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Steps:" -ForegroundColor White
Write-Host "1. Open Speckle Manager application" -ForegroundColor White
Write-Host "2. Click Add Account button" -ForegroundColor White
Write-Host "3. Enter these EXACT values:" -ForegroundColor White
Write-Host "   Server: http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com" -ForegroundColor Cyan
Write-Host "   Email: shinesains@gmail.com" -ForegroundColor Cyan
Write-Host "   Password: Sidian2025!" -ForegroundColor Cyan
Write-Host ""
Write-Host "The web login and Speckle Manager are separate!" -ForegroundColor Yellow
