# Build and Push Speckle Server to ECR
# This script builds the server Docker image and pushes it to ECR

param(
    [string]$Region = "ca-central-1",
    [string]$AccountId = "995419655044",
    [string]$ImageTag = "latest",
    [string]$RepositoryName = "speckle-server"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Building and Pushing Speckle Server" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Set variables
$ecrRegistry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$imageName = "$ecrRegistry/$RepositoryName"
$fullImageTag = "$imageName:$ImageTag"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $Region" -ForegroundColor Gray
Write-Host "  Account ID: $AccountId" -ForegroundColor Gray
Write-Host "  Repository: $RepositoryName" -ForegroundColor Gray
Write-Host "  Tag: $ImageTag" -ForegroundColor Gray
Write-Host "  Full Image: $fullImageTag" -ForegroundColor Gray
Write-Host ""

# Step 1: Authenticate with ECR
Write-Host "Step 1: Authenticating with ECR..." -ForegroundColor Green
try {
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ecrRegistry
    Write-Host "✅ ECR authentication successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to authenticate with ECR" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Check if ECR repository exists, create if not
Write-Host "Step 2: Checking ECR repository..." -ForegroundColor Green
try {
    aws ecr describe-repositories --repository-names $RepositoryName --region $Region | Out-Null
    Write-Host "✅ Repository '$RepositoryName' exists" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Repository '$RepositoryName' does not exist. Creating..." -ForegroundColor Yellow
    try {
        aws ecr create-repository `
            --repository-name $RepositoryName `
            --region $Region `
            --image-scanning-configuration scanOnPush=true `
            --encryption-configuration encryptionType=AES256
        Write-Host "✅ Repository '$RepositoryName' created" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to create repository" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 3: Build Docker image
Write-Host "Step 3: Building Docker image..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Gray
Write-Host ""

$rootDir = Split-Path -Parent $PSScriptRoot
Set-Location $rootDir

try {
    docker build `
        -f packages/server/Dockerfile `
        -t $fullImageTag `
        -t "$imageName:latest" `
        --build-arg NODE_ENV=production `
        --build-arg SPECKLE_SERVER_VERSION=$ImageTag `
        .
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed with exit code $LASTEXITCODE"
    }
    
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Push to ECR
Write-Host "Step 4: Pushing image to ECR..." -ForegroundColor Green
try {
    docker push $fullImageTag
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed with exit code $LASTEXITCODE"
    }
    
    # Also push latest tag if different
    if ($ImageTag -ne "latest") {
        docker push "$imageName:latest"
    }
    
    Write-Host "✅ Image pushed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to push image to ECR" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 5: Summary
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✅ Build and Push Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Image pushed to: $fullImageTag" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update Helm deployment (if needed):" -ForegroundColor Gray
Write-Host "   helm upgrade --install speckle-server utils\helm\speckle-server `" -ForegroundColor Gray
Write-Host "     --namespace speckle-production `" -ForegroundColor Gray
Write-Host "     --values infrastructure\helm-values-aws.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or restart the deployment:" -ForegroundColor Gray
Write-Host "   kubectl rollout restart deployment/speckle-server -n speckle-production" -ForegroundColor Gray
Write-Host ""




