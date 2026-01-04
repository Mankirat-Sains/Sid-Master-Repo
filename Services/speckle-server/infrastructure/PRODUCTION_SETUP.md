# Production Setup Guide - Exposing Speckle Externally

## Current Status
- ✅ All core pods are running
- ✅ Services are configured as `ClusterIP` (internal only)
- ⚠️ Currently using `kubectl port-forward` for local access (ports 8080 and 3000)

## Option 1: AWS Load Balancer Controller (Recommended for Production)

This is the **best option** for production. It creates an AWS Application Load Balancer (ALB) that automatically handles SSL/TLS termination and provides a public URL.

### Prerequisites
1. AWS Load Balancer Controller installed in your EKS cluster
2. A domain name (e.g., `speckle.yourdomain.com`)
3. SSL certificate in AWS Certificate Manager (ACM)

### Step 1: Install AWS Load Balancer Controller (if not already installed)

```powershell
# Check if it's already installed
kubectl get deployment -n kube-system aws-load-balancer-controller

# If not installed, install it:
# (You'll need to follow AWS documentation for your specific setup)
```

### Step 2: Create an Ingress Resource

Create a file `ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: speckle-ingress
  namespace: speckle-production
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ca-central-1:995419655044:certificate/YOUR-CERT-ID
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  ingressClassName: alb
  rules:
    - host: speckle.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: speckle-frontend-2
                port:
                  number: 8080
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: speckle-server
                port:
                  number: 3000
```

### Step 3: Apply the Ingress

```powershell
kubectl apply -f ingress.yaml
```

### Step 4: Get the Load Balancer URL

```powershell
kubectl get ingress -n speckle-production
# Wait for ADDRESS to be assigned (may take 2-3 minutes)
```

### Step 5: Update DNS

Point your domain to the ALB DNS name:
- Create a CNAME record: `speckle.yourdomain.com` → `<alb-dns-name>`

### Step 6: Update Frontend Environment Variable

```powershell
# Update NUXT_PUBLIC_API_ORIGIN to use your domain
kubectl set env deployment/speckle-frontend-2 NUXT_PUBLIC_API_ORIGIN=https://speckle.yourdomain.com/api -n speckle-production

# Restart the frontend pod
kubectl rollout restart deployment/speckle-frontend-2 -n speckle-production
```

---

## Option 2: LoadBalancer Service Type (Simpler, but less flexible)

This creates a Network Load Balancer (NLB) for each service. **Note:** This will create separate load balancers for frontend and API, which costs more.

### Step 1: Change Service Types to LoadBalancer

```powershell
# Change frontend service
kubectl patch svc speckle-frontend-2 -n speckle-production -p '{"spec":{"type":"LoadBalancer"}}'

# Change server service  
kubectl patch svc speckle-server -n speckle-production -p '{"spec":{"type":"LoadBalancer"}}'
```

### Step 2: Wait for External IPs

```powershell
kubectl get svc -n speckle-production -w
# Wait for EXTERNAL-IP to be assigned (may take 2-3 minutes)
```

### Step 3: Get the URLs

```powershell
# Get frontend URL
$frontendIP = (kubectl get svc speckle-frontend-2 -n speckle-production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
Write-Host "Frontend URL: http://$frontendIP:8080"

# Get API URL
$apiIP = (kubectl get svc speckle-server -n speckle-production -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
Write-Host "API URL: http://$apiIP:3000"
```

### Step 4: Update Frontend Environment Variable

```powershell
# Update to use the API load balancer URL
kubectl set env deployment/speckle-frontend-2 NUXT_PUBLIC_API_ORIGIN=http://$apiIP:3000 -n speckle-production
```

**Note:** LoadBalancer services don't automatically provide HTTPS. You'll need to:
- Use a reverse proxy (nginx, Traefik)
- Or use AWS Certificate Manager with an ALB (Option 1 is better)

---

## Option 3: NodePort (Testing Only - NOT for Production)

This exposes services on high-numbered ports on each node. **Not recommended for production** but useful for quick testing.

```powershell
# Change to NodePort
kubectl patch svc speckle-frontend-2 -n speckle-production -p '{"spec":{"type":"NodePort"}}'
kubectl patch svc speckle-server -n speckle-production -p '{"spec":{"type":"NodePort"}}'

# Get the node port numbers
kubectl get svc -n speckle-production
```

Then access via: `http://<node-ip>:<node-port>`

---

## Recommended: Option 1 (Ingress with ALB)

**Why?**
- ✅ Single entry point (one load balancer)
- ✅ Automatic SSL/TLS termination
- ✅ Path-based routing (frontend and API on same domain)
- ✅ Cost-effective (one load balancer vs. multiple)
- ✅ Production-ready

**Steps Summary:**
1. Install AWS Load Balancer Controller
2. Get SSL certificate from ACM
3. Create Ingress resource
4. Point DNS to ALB
5. Update `NUXT_PUBLIC_API_ORIGIN` environment variable

---

## Quick Check Commands

```powershell
# Check all pods
kubectl get pods -n speckle-production

# Check services
kubectl get svc -n speckle-production

# Check ingress (if using Option 1)
kubectl get ingress -n speckle-production

# Check frontend environment variable
kubectl get deployment speckle-frontend-2 -n speckle-production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="NUXT_PUBLIC_API_ORIGIN")]}'
```

---

## Security Considerations

1. **HTTPS Required**: Always use HTTPS in production
2. **CORS Configuration**: Ensure CORS is configured correctly for your domain
3. **Security Groups**: Ensure your ALB/NLB security groups allow traffic on ports 80/443
4. **Database Access**: Keep database as internal-only (don't expose it)
5. **Redis Access**: Keep Redis as internal-only (don't expose it)

---

## Cost Estimate

- **Option 1 (ALB)**: ~$16/month + data transfer
- **Option 2 (NLB)**: ~$16/month per load balancer (2x cost)
- **Option 3 (NodePort)**: Free, but not secure for production

---

## Need Help?

If you need help with any step, let me know which option you want to use!



