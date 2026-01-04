# Diagnostic script to find the exact OAuth error

$serverUrl = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"

Write-Host "=== Diagnosing OAuth Issue ===" -ForegroundColor Cyan
Write-Host ""

# Test the /auth/token endpoint with proper error handling
Write-Host "Testing /auth/token endpoint..." -ForegroundColor Yellow
try {
    $testBody = @{
        appId = "sca"
        appSecret = "sca"
        accessCode = "test123"
        challenge = "testchallenge"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$serverUrl/auth/token" -Method POST -ContentType "application/json" -Body $testBody -ErrorAction Stop
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  HTTP Status: $statusCode" -ForegroundColor Red
        
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Response Body: $responseBody" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== The Issue ===" -ForegroundColor Cyan
Write-Host "The connector uses hardcoded OAuth credentials:" -ForegroundColor Yellow
Write-Host "  appId: 'sca'" -ForegroundColor White
Write-Host "  appSecret: 'sca'" -ForegroundColor White
Write-Host ""
Write-Host "Your AWS server needs to have an OAuth app configured with these values." -ForegroundColor Yellow
Write-Host "This is typically done in the server's admin settings." -ForegroundColor Yellow


