# Test if AWS server auth endpoint is working
# This helps diagnose the OAuth issue

$serverUrl = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"

Write-Host "=== Testing AWS Server Auth Endpoint ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if server is reachable
Write-Host "Test 1: Checking if server is reachable..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$serverUrl/graphql" -Method POST -ContentType "application/json" -Body '{"query":"{ __typename }"}' -ErrorAction Stop
    Write-Host "  Server is reachable" -ForegroundColor Green
} catch {
    Write-Host "  Server not reachable: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check auth/token endpoint exists
Write-Host ""
Write-Host "Test 2: Checking /auth/token endpoint..." -ForegroundColor Yellow
try {
    $testBody = @{
        appId = "sca"
        appSecret = "sca"
        accessCode = "test"
        challenge = "test"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$serverUrl/auth/token" -Method POST -ContentType "application/json" -Body $testBody -ErrorAction Stop
    Write-Host "  /auth/token endpoint exists" -ForegroundColor Green
    Write-Host "  Response: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "  /auth/token endpoint issue: $($_.Exception.Message)" -ForegroundColor Yellow
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Response body: $responseBody" -ForegroundColor Gray
    }
}

# Test 3: Check server info
Write-Host ""
Write-Host "Test 3: Getting server info..." -ForegroundColor Yellow
try {
    $query = @{
        query = "{ serverInfo { name version } }"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$serverUrl/graphql" -Method POST -ContentType "application/json" -Body $query -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "  Server info retrieved" -ForegroundColor Green
    Write-Host "  Server: $($data.data.serverInfo.name)" -ForegroundColor Cyan
    Write-Host "  Version: $($data.data.serverInfo.version)" -ForegroundColor Cyan
} catch {
    Write-Host "  Failed to get server info: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "If /auth/token returns an error, the server might not be configured" -ForegroundColor Yellow
Write-Host "for OAuth with appId=sca and appSecret=sca" -ForegroundColor Yellow
Write-Host ""
Write-Host "The connector uses these hardcoded values for OAuth." -ForegroundColor Yellow
Write-Host "Your AWS server might need these configured in its settings." -ForegroundColor Yellow
