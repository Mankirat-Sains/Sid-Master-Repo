# Speckle Server AWS Deployment Guide

This guide walks you through deploying Speckle Server to AWS EKS using the infrastructure we've created.

## Prerequisites

✅ AWS Infrastructure created (EKS, RDS, Redis, S3)  
✅ Docker images pushed to ECR  
✅ kubectl configured to connect to EKS cluster

## Step 1: Create Kubernetes Secrets

### 1.1 Create Database and Redis Secrets

Run the setup script:

```powershell
cd C:\Users\shine\speckle1\speckle-server\infrastructure
.\setup-kubernetes-secrets.ps1
```

This creates:

- `speckle-db-secret` - Database connection string
- `speckle-redis-secret` - Redis connection string

### 1.2 Create S3 Secret

You need AWS Access Keys with S3 permissions. Create an IAM user with S3 access, then create the secret:

```powershell
kubectl create secret generic speckle-s3-secret `
  --from-literal=secret-key='YOUR_AWS_SECRET_ACCESS_KEY' `
  --namespace=speckle-production
```

**Important:** Save your AWS Access Key ID - you'll need it for the Helm values file.

## Step 2: Setup ECR Authentication

Create a Kubernetes secret to pull images from ECR:

```powershell
.\setup-ecr-auth.ps1
```

This creates `ecr-registry-secret` which allows Kubernetes to pull images from your ECR repositories.

## Step 3: Configure Helm Values

Edit `helm-values-aws.yaml` and update:

1. **Domain**: Change `your-domain.com` to your actual domain (or leave as-is for testing)
2. **S3 Access Key ID**: Replace `YOUR_AWS_ACCESS_KEY_ID` with your actual AWS Access Key ID

The file already has:

- ✅ Correct ECR image repositories
- ✅ Database and Redis secret references
- ✅ S3 configuration
- ✅ Network policy settings for external resources

## Step 4: Deploy with Helm

### 4.1 Install/Upgrade the Helm Chart

```powershell
cd C:\Users\shine\speckle1\speckle-server\utils\helm\speckle-server

helm upgrade --install speckle-server . `
  --namespace speckle-production `
  --create-namespace `
  --values C:\Users\shine\speckle1\speckle-server\infrastructure\helm-values-aws.yaml
```

### 4.2 Verify Deployment

Check if pods are running:

```powershell
kubectl get pods -n speckle-production
```

You should see pods for:

- speckle-server
- speckle-frontend-2
- speckle-preview-service
- speckle-webhook-service
- speckle-ifc-import-service (if enabled)

Check pod status:

```powershell
kubectl get pods -n speckle-production -w
```

### 4.3 Check Services

```powershell
kubectl get svc -n speckle-production
```

## Step 5: Configure Ingress (Optional)

If you want external access, you'll need to configure ingress. Options:

1. **AWS Load Balancer Controller** - Recommended for production
2. **NodePort** - For testing (not recommended for production)
3. **External Load Balancer** - Manual setup

See the Helm values file for ingress configuration options.

## Troubleshooting

### Pods Not Starting

Check pod logs:

```powershell
kubectl logs -n speckle-production <pod-name>
```

### Image Pull Errors

Verify ECR authentication:

```powershell
kubectl get secret ecr-registry-secret -n speckle-production
```

### Database Connection Issues

Verify database secret:

```powershell
kubectl get secret speckle-db-secret -n speckle-production -o yaml
```

### Redis Connection Issues

Verify Redis secret:

```powershell
kubectl get secret speckle-redis-secret -n speckle-production -o yaml
```

## Next Steps

1. Configure DNS to point to your ingress/load balancer
2. Set up SSL/TLS certificates (cert-manager recommended)
3. Configure monitoring and logging
4. Set up backups for RDS
5. Configure auto-scaling for services

## Useful Commands

```powershell
# View all resources
kubectl get all -n speckle-production

# View Helm release status
helm status speckle-server -n speckle-production

# Uninstall (if needed)
helm uninstall speckle-server -n speckle-production

# View Helm values
helm get values speckle-server -n speckle-production
```
