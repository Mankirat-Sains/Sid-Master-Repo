# Setup Kubernetes Secrets for Speckle Deployment
# This script creates the necessary Kubernetes secrets for database, Redis, and S3

param(
    [string]$Namespace = "speckle-production"
)

# Create namespace if it doesn't exist
Write-Host "Creating namespace: $Namespace" -ForegroundColor Green
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# Database connection string
$DB_HOST = "speckle-cluster-postgres.cbqs804kett3.ca-central-1.rds.amazonaws.com"
$DB_PORT = "5432"
$DB_USER = "speckle"
$DB_PASS = "Sidian2025!"
$DB_NAME = "speckle"
$DB_CONNECTION_STRING = "postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"

# Redis connection string (ElastiCache doesn't use auth by default)
$REDIS_HOST = "speckle-cluster-redis.gwxdfz.ng.0001.cac1.cache.amazonaws.com"
$REDIS_PORT = "6379"
$REDIS_CONNECTION_STRING = "redis://${REDIS_HOST}:${REDIS_PORT}"

Write-Host "`nCreating database secret..." -ForegroundColor Yellow
kubectl create secret generic speckle-db-secret `
    --from-literal=connection-string="$DB_CONNECTION_STRING" `
    --namespace=$Namespace `
    --dry-run=client -o yaml | kubectl apply -f -

Write-Host "Creating Redis secret..." -ForegroundColor Yellow
kubectl create secret generic speckle-redis-secret `
    --from-literal=connection-string="$REDIS_CONNECTION_STRING" `
    --namespace=$Namespace `
    --dry-run=client -o yaml | kubectl apply -f -

Write-Host "`n⚠️  IMPORTANT: You need to create S3 secrets manually!" -ForegroundColor Red
Write-Host "You need AWS Access Key ID and Secret Access Key with S3 permissions." -ForegroundColor Yellow
Write-Host "`nTo create S3 secret, run:" -ForegroundColor Cyan
Write-Host "kubectl create secret generic speckle-s3-secret \`" -ForegroundColor White
Write-Host "  --from-literal=secret-key='I9V71sLQOcyGDUWxuNNzZqZzY+AK3et4WZu9mUjo' \`" -ForegroundColor White
Write-Host "  --namespace=$Namespace" -ForegroundColor White
Write-Host "`nNote: Your AWS Access Key ID will be set in the Helm values file." -ForegroundColor Yellow

Write-Host "`n✅ Secrets created successfully!" -ForegroundColor Green
Write-Host "Database secret: speckle-db-secret" -ForegroundColor Green
Write-Host "Redis secret: speckle-redis-secret" -ForegroundColor Green

