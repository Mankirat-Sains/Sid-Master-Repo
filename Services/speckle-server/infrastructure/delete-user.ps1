# Script to delete user from Speckle database
# This will delete the user with email: shinesains@gmail.com

$connectionString = "postgresql://speckle:Sidian2025!@speckle-cluster-postgres.cbqs804kett3.ca-central-1.rds.amazonaws.com:5432/speckle?sslmode=require"
$email = "shinesains@gmail.com"

Write-Host "`n⚠️  WARNING: This will permanently delete the user: $email" -ForegroundColor Red
Write-Host "Press Ctrl+C to cancel, or any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "`nConnecting to database..." -ForegroundColor Cyan

# Check if psql is available
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "`n❌ psql (PostgreSQL client) not found!" -ForegroundColor Red
    Write-Host "`nPlease install PostgreSQL client tools, or use one of these options:" -ForegroundColor Yellow
    Write-Host "  1. Install PostgreSQL from: https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host "  2. Use pgAdmin to connect and run the SQL manually" -ForegroundColor White
    Write-Host "  3. Use the password reset feature on the login page" -ForegroundColor White
    Write-Host "`nSQL to run manually:" -ForegroundColor Cyan
    Write-Host "  DELETE FROM users WHERE email = '$email';" -ForegroundColor White
    exit 1
}

Write-Host "Executing SQL to delete user..." -ForegroundColor Cyan

# Extract connection details
$connParts = $connectionString -replace 'postgresql://', '' -split '@'
$userPass = $connParts[0] -split ':'
$hostDb = $connParts[1] -split '/'
$hostPort = $hostDb[0] -split ':'
$dbName = ($hostDb[1] -split '\?')[0]

$env:PGPASSWORD = $userPass[1]
$host = $hostPort[0]
$port = if ($hostPort.Length -gt 1) { $hostPort[1] } else { "5432" }
$user = $userPass[0]

$sql = "DELETE FROM users WHERE email = '$email';"

try {
    $result = & psql -h $host -p $port -U $user -d $dbName -c $sql 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ User deleted successfully!" -ForegroundColor Green
        Write-Host "You can now register again with the same email." -ForegroundColor White
    } else {
        Write-Host "`n❌ Error deleting user:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}




