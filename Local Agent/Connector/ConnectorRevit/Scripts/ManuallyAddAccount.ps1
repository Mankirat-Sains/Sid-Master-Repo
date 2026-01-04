# Script to manually add an account to Speckle Manager
# This bypasses the OAuth flow by directly creating the account object

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [string]$RefreshToken = ""
)

Write-Host "=== Manual Account Addition ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will help you manually add an account." -ForegroundColor Yellow
Write-Host "You need to get a token from your browser's developer tools." -ForegroundColor Yellow
Write-Host ""
Write-Host "To get your token:" -ForegroundColor White
Write-Host "1. Open your AWS server in browser: $ServerUrl" -ForegroundColor Gray
Write-Host "2. Log in" -ForegroundColor Gray
Write-Host "3. Press F12 to open Developer Tools" -ForegroundColor Gray
Write-Host "4. Go to Application > Local Storage > (your server URL)" -ForegroundColor Gray
Write-Host "5. Look for 'authToken' or 'token' key" -ForegroundColor Gray
Write-Host "6. Copy the token value" -ForegroundColor Gray
Write-Host ""
Write-Host "Alternatively, check Network tab for any GraphQL requests" -ForegroundColor Gray
Write-Host "and look for 'Authorization: Bearer <token>' in request headers" -ForegroundColor Gray
Write-Host ""

if (-not $Token -or $Token -eq "") {
    Write-Host "ERROR: Token is required!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\ManuallyAddAccount.ps1 -ServerUrl `"$ServerUrl`" -Email `"$Email`" -Token `"YOUR_TOKEN_HERE`"" -ForegroundColor White
    exit 1
}

Write-Host "Attempting to create account..." -ForegroundColor Yellow
Write-Host "  Server: $ServerUrl" -ForegroundColor Gray
Write-Host "  Email: $Email" -ForegroundColor Gray
Write-Host "  Token: $($Token.Substring(0, [Math]::Min(20, $Token.Length)))..." -ForegroundColor Gray
Write-Host ""

# The account will need to be created programmatically
# This is a guide - actual implementation would require C# code
Write-Host "NOTE: This requires C# code to properly create the account." -ForegroundColor Yellow
Write-Host "The account needs:" -ForegroundColor White
Write-Host "  1. Token (you have this)" -ForegroundColor Gray
Write-Host "  2. UserInfo (fetched from GraphQL with token)" -ForegroundColor Gray
Write-Host "  3. ServerInfo (fetched from GraphQL)" -ForegroundColor Gray
Write-Host ""
Write-Host "See: CreateAccountManually.cs for implementation" -ForegroundColor Cyan


