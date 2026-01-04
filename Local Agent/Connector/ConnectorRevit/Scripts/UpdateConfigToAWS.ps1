# Update RevitAutomatedSend.json to use AWS server

$configPath = "$env:APPDATA\Speckle\RevitAutomatedSend.json"

if (-not (Test-Path $configPath)) {
    Write-Host "Config file not found at: $configPath" -ForegroundColor Red
    exit 1
}

Write-Host "Reading config file..." -ForegroundColor Yellow
$config = Get-Content $configPath | ConvertFrom-Json

Write-Host "Current ServerUrl: $($config.ServerUrl)" -ForegroundColor Cyan
Write-Host "Updating to AWS server..." -ForegroundColor Yellow

$config.ServerUrl = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"
$config.AccountEmail = "shinesains@gmail.com"

$config | ConvertTo-Json -Depth 10 | Set-Content $configPath

Write-Host ""
Write-Host "Config updated successfully!" -ForegroundColor Green
Write-Host "New ServerUrl: $($config.ServerUrl)" -ForegroundColor Green
Write-Host "AccountEmail: $($config.AccountEmail)" -ForegroundColor Green
Write-Host ""
Write-Host "Note: You may need to restart Revit for the changes to take effect." -ForegroundColor Yellow


