# Setup ECR Authentication for Kubernetes
# This script creates a Kubernetes secret to pull images from ECR

param(
    [string]$Namespace = "speckle-production",
    [string]$Region = "ca-central-1",
    [string]$AccountId = "995419655044"
)

Write-Host "Setting up ECR authentication..." -ForegroundColor Green

# Get ECR login token
Write-Host "Getting ECR login token..." -ForegroundColor Yellow
$ecrToken = aws ecr get-login-password --region $Region

# Create Kubernetes secret for ECR
Write-Host "Creating Kubernetes secret for ECR..." -ForegroundColor Yellow

# Create docker config JSON
$ecrRegistry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$authString = "AWS:$ecrToken"
$authBytes = [System.Text.Encoding]::ASCII.GetBytes($authString)
$authBase64 = [Convert]::ToBase64String($authBytes)

$dockerConfig = @{
    auths = @{
        $ecrRegistry = @{
            username = "AWS"
            password = $ecrToken
            auth = $authBase64
        }
    }
}

$dockerConfigJson = $dockerConfig | ConvertTo-Json -Compress

# Create the secret
kubectl create secret docker-registry ecr-registry-secret `
    --docker-server=$ecrRegistry `
    --docker-username=AWS `
    --docker-password=$ecrToken `
    --namespace=$Namespace `
    --dry-run=client -o yaml | kubectl apply -f -

Write-Host "`n✅ ECR authentication secret created: ecr-registry-secret" -ForegroundColor Green
Write-Host "This secret will be used by Helm to pull images from ECR." -ForegroundColor Green

