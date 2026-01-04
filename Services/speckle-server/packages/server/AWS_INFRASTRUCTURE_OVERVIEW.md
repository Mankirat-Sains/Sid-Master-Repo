# Complete AWS Infrastructure Overview for Speckle Server

## Table of Contents
1. [AWS Region & Environment](#aws-region--environment)
2. [VPC & Networking](#vpc--networking)
3. [EKS Cluster & Nodes](#eks-cluster--nodes)
4. [Database & Storage](#database--storage)
5. [Kubernetes Namespace](#kubernetes-namespace)
6. [Docker Images](#docker-images)
7. [Kubernetes Pods/Deployments](#kubernetes-podsdeployments)
8. [Kubernetes Services](#kubernetes-services)
9. [Ingress & Load Balancing](#ingress--load-balancing)
10. [Security Groups](#security-groups)
11. [IAM Roles](#iam-roles)
12. [Network Policies](#network-policies)

---

## AWS Region & Environment

- **Region**: `ca-central-1` (Canada Central)
- **Cluster Name**: `speckle-cluster`
- **Environment**: `production`
- **Namespace**: `speckle-production` (default from values.yaml: `speckle-test`)

---

## VPC & Networking

### VPC Configuration
- **CIDR Block**: `10.0.0.0/16`
- **VPC Name**: `speckle-cluster-vpc`
- **DNS Support**: Enabled
- **DNS Hostnames**: Enabled

### Subnets

#### Public Subnets (2 zones for HA)
- **Subnet 1**: `10.0.1.0/24` (Availability Zone 1)
  - Tag: `kubernetes.io/role/elb=1` (for ALB)
  - Map Public IP: Enabled
- **Subnet 2**: `10.0.2.0/24` (Availability Zone 2)
  - Tag: `kubernetes.io/role/elb=1` (for ALB)
  - Map Public IP: Enabled

#### Private Subnets (for EKS nodes)
- **Subnet 1**: `10.0.10.0/24` (Availability Zone 1)
  - Tag: `kubernetes.io/role/internal-elb=1`
- **Subnet 2**: `10.0.11.0/24` (Availability Zone 2)
  - Tag: `kubernetes.io/role/internal-elb=1`

#### Database Subnets (for RDS)
- **Subnet 1**: `10.0.20.0/24` (Availability Zone 1)
- **Subnet 2**: `10.0.21.0/24` (Availability Zone 2)
- **Subnet Group**: `speckle-cluster-db-subnet-group`

### Networking Components

#### Internet Gateway
- **Name**: `speckle-cluster-igw`
- **Purpose**: Allows public subnets to access the internet

#### NAT Gateways (2 for HA)
- **NAT Gateway 1**: In Public Subnet 1 (AZ 1)
  - Elastic IP: `speckle-cluster-nat-eip-1`
- **NAT Gateway 2**: In Public Subnet 2 (AZ 2)
  - Elastic IP: `speckle-cluster-nat-eip-2`
- **Purpose**: Allows private subnets (EKS nodes) to access internet for pulling images, etc.

#### Route Tables
- **Public Route Table**: Routes `0.0.0.0/0` → Internet Gateway
  - Associated with: Both public subnets
- **Private Route Table 1**: Routes `0.0.0.0/0` → NAT Gateway 1
  - Associated with: Private Subnet 1
- **Private Route Table 2**: Routes `0.0.0.0/0` → NAT Gateway 2
  - Associated with: Private Subnet 2

---

## EKS Cluster & Nodes

### EKS Cluster
- **Name**: `speckle-cluster`
- **Kubernetes Version**: `1.29`
- **Endpoint Access**:
  - Private Endpoint: Enabled
  - Public Endpoint: Enabled
  - Public Access CIDRs: `0.0.0.0/0` (configurable via `allowed_cidr_blocks`)
- **Subnets**: Uses both private and public subnets

### EKS Node Group
- **Node Group Name**: `speckle-cluster-nodes`
- **Instance Type**: `t3.medium` (2 vCPU, 4 GB RAM)
- **Subnets**: Private subnets only (`10.0.10.0/24`, `10.0.11.0/24`)
- **Scaling Configuration**:
  - Minimum Size: `1` node
  - Desired Size: `2` nodes
  - Maximum Size: `4` nodes
- **Auto Scaling**: Enabled (can scale 1-4 nodes based on demand)

---

## Database & Storage

### RDS PostgreSQL Database
- **Instance Identifier**: `speckle-cluster-postgres`
- **Engine**: PostgreSQL
- **Engine Version**: `16.11`
- **Instance Class**: `db.t3.medium` (2 vCPU, 4 GB RAM)
- **Storage**:
  - Allocated Storage: `100 GB`
  - Max Allocated Storage: `500 GB` (auto-scaling)
  - Storage Type: `gp3` (General Purpose SSD)
  - Encryption: Enabled at rest
- **Database**:
  - Name: `speckle`
  - Username: `speckle`
  - Password: Set via `database_password` variable
- **Network**:
  - Subnet Group: `speckle-cluster-db-subnet-group` (database subnets)
  - Security Group: `speckle-cluster-rds-sg`
  - Port: `5432`
- **Backup**:
  - Retention Period: `7 days`
  - Backup Window: `03:00-04:00 UTC`
  - Maintenance Window: `Monday 04:00-05:00 UTC`
- **Final Snapshot**: Enabled (before deletion)
- **Deletion Protection**: `false` (should be `true` for production!)
- **CloudWatch Logs**: Enabled (`postgresql`, `upgrade`)

### ElastiCache Redis
- **Replication Group ID**: `speckle-cluster-redis`
- **Engine**: Redis
- **Engine Version**: `7.1`
- **Node Type**: `cache.t3.micro` (0.5 vCPU, 0.5 GB RAM)
- **Port**: `6379`
- **Num Cache Clusters**: `1` (single node - change to 2+ for HA)
- **Network**:
  - Subnet Group: `speckle-cluster-redis-subnet-group` (private subnets)
  - Security Group: `speckle-cluster-redis-sg`
- **Encryption**:
  - At Rest: Enabled
  - In Transit: Disabled (can enable if needed)
- **Automatic Failover**: Disabled (requires 2+ nodes)

### S3 Bucket
- **Bucket Name**: `speckle-cluster-storage-production`
- **Purpose**: File storage for Speckle
- **Security**:
  - Public Access: Blocked (all settings enabled)
  - Encryption: AES256 (server-side)
  - Versioning: Enabled
- **Lifecycle Policy**:
  - After 90 days: Transition to `STANDARD_IA` (Infrequent Access)
  - After 180 days: Transition to `GLACIER` (archive storage)

---

## Kubernetes Namespace

- **Namespace**: `speckle-production` (as seen in pgadmin-deployment.yaml)
  - Default in values.yaml is `speckle-test`, but production uses `speckle-production`
- **Creation**: Managed via Helm chart (`create_namespace` parameter)

---

## Docker Images

All images default to tag specified in `docker_image_tag` (default: `2`), or can be overridden via service-specific `image` parameter.

### Application Images
1. **speckle-server**
   - Default: `speckle/speckle-server:2`
   - Used by: Server and Objects deployments

2. **speckle-frontend-2**
   - Default: `speckle/speckle-frontend-2:2`
   - Used by: Frontend deployment

3. **speckle-preview-service**
   - Default: `speckle/speckle-preview-service:2`
   - Used by: Preview Service deployment

4. **speckle-webhook-service**
   - Default: `speckle/speckle-webhook-service:2`
   - Used by: Webhook Service deployment

5. **speckle-fileimport-service**
   - Default: `speckle/speckle-fileimport-service:2`
   - Used by: File Import Service deployment (Legacy)

6. **speckle-ifc-import-service**
   - Default: `speckle/speckle-ifc-import-service:2`
   - Used by: IFC Import Service deployment

7. **speckle-monitor-deployment**
   - Default: `speckle/speckle-monitor-deployment:2`
   - Used by: Monitoring deployment

8. **speckle-test-deployment**
   - Default: `speckle/speckle-test-deployment:2`
   - Used by: Test deployment (helm test)

### Utility Images
9. **pgadmin4**
   - Image: `dpage/pgadmin4:latest`
   - Used by: pgadmin deployment (database administration tool)

---

## Kubernetes Pods/Deployments

### 1. Server Deployment (`speckle-server`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-server`
- **Port**: `3000` (HTTP)
- **Resources**:
  - Requests: Configurable (default not specified in templates)
  - Limits: Configurable (default not specified in templates)
- **Priority Class**: `high-priority`
- **Security Context**:
  - Run as non-root: `true` (user `20000`)
  - Read-only root filesystem: `true`
  - Capabilities: `ALL` dropped
- **Health Checks**:
  - Startup Probe: `/liveness` (60 attempts × 10s = 600s max)
  - Liveness Probe: `/liveness` (every 60s)
  - Readiness Probe: `/readiness` (every 4s)
- **Rolling Update**: 25% max unavailable, 25% max surge
- **Volumes**:
  - `/tmp` (emptyDir)
  - Postgres certificate (if enabled)
  - Encryption keys (if workspaces enabled)
  - Multi-region config (if enabled)

### 2. Objects Deployment (`speckle-objects`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-server` (same image as server, different config)
- **Port**: `3000` (HTTP)
- **Resources**:
  - Requests: `1000m CPU, 1Gi memory` (default)
  - Limits: `1500m CPU, 3Gi memory` (default)
- **Priority Class**: `high-priority`
- **Security Context**: Same as server
- **Health Checks**: Same as server
- **Rolling Update**: 25% max unavailable, 25% max surge

### 3. Frontend-2 Deployment (`speckle-frontend-2`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-frontend-2`
- **Port**: `8080` (HTTP, named `www`)
- **Resources**:
  - Requests: `250m CPU, 256Mi memory` (default)
  - Limits: `1000m CPU, 512Mi memory` (default)
- **Priority Class**: `high-priority`
- **Health Checks**:
  - Liveness: `/api/status` (every 5s)
  - Readiness: `/api/status` (every 5s)
- **Environment Variables**:
  - API origin, base URL, Redis URL, feature flags, analytics tokens

### 4. Preview Service Deployment (`speckle-preview-service`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-preview-service`
- **Port**: `3001` (metrics)
- **Resources**:
  - Requests: `500m CPU, 2Gi memory` (default)
  - Limits: `1000m CPU, 4Gi memory` (default)
- **Priority Class**: `low-priority`
- **Deployment Strategy**: `Recreate` (not RollingUpdate)
- **GPU Support**: Optional (Vulkan driver required)
- **HPA**: Optional (disabled by default, max 10 replicas)
- **Health Checks**:
  - Liveness: `/liveness` (every 60s)
  - Readiness: `/readiness`

### 5. Webhook Service Deployment (`speckle-webhook-service`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-webhook-service`
- **Port**: `9095` (metrics)
- **Resources**: Configurable (defaults not specified)
- **Priority Class**: `low-priority`
- **Health Check**: File-based (`/tmp/last_successful_query`)
- **Termination Grace Period**: `30s`

### 6. File Import Service Deployment (`speckle-fileimport-service`)
- **Replicas**: `1` (configurable)
- **Container**: `speckle-fileimport-service`
- **Port**: `9093` (metrics)
- **Resources**:
  - Requests: `100m CPU, 512Mi memory` (default)
  - Limits: `1000m CPU, 2Gi memory` (default)
- **Priority Class**: `low-priority`
- **Deployment Strategy**: `Recreate`
- **Health Check**: File-based (`/tmp/last_successful_query`)
- **Termination Grace Period**: `610s` (allows file imports to finish)
- **Status**: DEPRECATED (use IFC Import Service instead)

### 7. IFC Import Service Deployment (`speckle-ifc-import-service`)
- **Replicas**: `1` (configurable, disabled by default)
- **Container**: `speckle-ifc-import-service`
- **Ports**:
  - `9093` (metrics)
  - `9080` (healthz)
- **Resources**:
  - Requests: `100m CPU, 512Mi memory` (default)
  - Limits: `1000m CPU, 2Gi memory` (default)
- **Priority Class**: `low-priority`
- **Deployment Strategy**: `Recreate`
- **Health Checks**: HTTP `/healthz` endpoint
- **Termination Grace Period**: `610s`

### 8. Monitoring Deployment (`speckle-monitoring`)
- **Replicas**: `1` (configurable, enabled by default)
- **Container**: `speckle-monitor-deployment`
- **Port**: `9092` (Prometheus metrics)
- **Resources**:
  - Requests: `100m CPU, 64Mi memory` (default)
  - Limits: `200m CPU, 512Mi memory` (default)
- **Priority Class**: `low-priority`
- **Purpose**: Collects Postgres database metrics
- **Metrics Collection Period**: `120 seconds`
- **Health Checks**: HTTP `/` and `/metrics` endpoints

### 9. Test Deployment (`speckle-test`)
- **Replicas**: `1` (only when `helm_test_enabled=true`)
- **Container**: `speckle-test-deployment`
- **Resources**:
  - Requests: `100m CPU, 64Mi memory` (default)
  - Limits: `200m CPU, 512Mi memory` (default)
- **Purpose**: Helm test pod for deployment verification

### 10. pgadmin Deployment (`pgadmin`)
- **Replicas**: `1`
- **Container**: `dpage/pgadmin4:latest`
- **Port**: `80` (HTTP)
- **Namespace**: `speckle-production`
- **Resources**:
  - Requests: `250m CPU, 256Mi memory`
  - Limits: `500m CPU, 512Mi memory`
- **Environment Variables**:
  - `PGADMIN_DEFAULT_EMAIL`: `admin@speckle.com`
  - `PGADMIN_DEFAULT_PASSWORD`: `admin123`
  - `PGADMIN_CONFIG_SERVER_MODE`: `False`
  - `SCRIPT_NAME`: `/pgadmin`
- **Note**: Deployed separately (not via Helm chart)

---

## Kubernetes Services

All services are ClusterIP (internal only) unless specified otherwise.

### 1. Server Service (`speckle-server`)
- **Type**: ClusterIP
- **Port**: `3000` (targetPort: `http`/`3000`)
- **Selector**: `app: speckle-server, project: speckle-server`
- **Exposed By**: Ingress

### 2. Objects Service (`speckle-objects`)
- **Type**: ClusterIP
- **Port**: `3000` (targetPort: `http`/`3000`)
- **Selector**: `app: speckle-server, project: speckle-server`
- **Note**: Shares same pod selector as server (uses same deployment with different config)

### 3. Frontend-2 Service (`speckle-frontend-2`)
- **Type**: ClusterIP
- **Port**: `8080` (targetPort: `www`/`8080`)
- **Selector**: `app: speckle-frontend-2, project: speckle-server`
- **Exposed By**: Ingress (catch-all route)

### 4. Preview Service (`speckle-preview-service`)
- **Type**: ClusterIP
- **Port**: `3001` (metrics)
- **Selector**: `app: speckle-preview-service, project: speckle-server`
- **Note**: Internal only, not exposed via ingress

### 5. Webhook Service (`speckle-webhook-service`)
- **Type**: ClusterIP
- **Port**: `9095` (metrics)
- **Selector**: `app: speckle-webhook-service, project: speckle-server`
- **Note**: Internal only, not exposed via ingress

### 6. File Import Service (`speckle-fileimport-service`)
- **Type**: ClusterIP
- **Port**: `9093` (metrics)
- **Selector**: `app: speckle-fileimport-service, project: speckle-server`
- **Note**: Internal only, not exposed via ingress

### 7. IFC Import Service (`speckle-ifc-import-service`)
- **Type**: ClusterIP
- **Port**: `9093` (metrics), `9080` (healthz)
- **Selector**: `app: speckle-ifc-import-service, project: speckle-server`
- **Note**: Internal only, not exposed via ingress

### 8. Monitoring Service (`speckle-monitoring`)
- **Type**: ClusterIP
- **Port**: `9092` (metrics)
- **Selector**: `app: speckle-monitoring, project: speckle-server`
- **Note**: Exposed for Prometheus scraping (if ServiceMonitor enabled)

### 9. pgadmin Service (`pgadmin`)
- **Type**: ClusterIP
- **Port**: `80` (targetPort: `80`)
- **Selector**: `app: pgadmin`
- **Namespace**: `speckle-production`
- **Exposed By**: Ingress (`/pgadmin`)

---

## Ingress & Load Balancing

All ingress resources use **AWS Application Load Balancer (ALB)** with the `alb` ingress class.

### Ingress Configuration
- **Ingress Class**: `alb`
- **Scheme**: `internet-facing`
- **Target Type**: `ip` (pod IPs directly)
- **Load Balancer Name**: `speckle-alb` (shared across multiple ingress resources)
- **Listen Ports**: HTTP `80`, HTTPS `443`
- **SSL Redirect**: Enabled (if cert-manager issuer configured)
- **Backend Protocol**: HTTP/1.1
- **Cert Manager**: Uses `letsencrypt-staging` issuer (configurable)

### Ingress Resources (Order matters via `alb.ingress.kubernetes.io/order`)

#### 1. Objects Minion Ingress (`speckle-server-minion-api-objects`)
- **Order**: `1` (highest priority - evaluated first)
- **Paths**:
  - `/api/getobjects/` → `speckle-server:3000`
  - `/api/objects/` → `speckle-server:3000`
  - `/api/diff/` → `speckle-server:3000`
  - `/objects/` → `speckle-server:3000`
  - `/streams/` → `speckle-server:3000`

#### 2. File Minion Ingress (`speckle-server-minion-api-file`)
- **Order**: `2`
- **Paths**:
  - `/api/file/` → `speckle-server:3000`
  - `/api/stream/` → `speckle-server:3000`
  - `/api/thirdparty/gendo` → `speckle-server:3000`

#### 3. Main Minion Ingress (`speckle-server-minion`)
- **Order**: `99` (lowest priority - catch-all)
- **Paths**:
  - `/graphql` (Exact) → `speckle-server:3000`
  - `/explorer` (Exact) → `speckle-server:3000`
  - `/auth/` (Prefix) → `speckle-server:3000`
  - `/static/` (Prefix) → `speckle-server:3000`
  - `/api/` (Prefix) → `speckle-server:3000`
  - `/preview/` (Prefix) → `speckle-server:3000`
  - `/` (Prefix, catch-all) → `speckle-frontend-2:8080`

#### 4. Redirect Ingress (`speckle-server-redirect`)
- **Host**: `{{ domain }}` (from values.yaml)
- **Paths**:
  - `/metrics` (Exact) → `speckle-frontend-2:8080`
  - `/api/status` (Exact) → `speckle-frontend-2:8080`
  - `/liveness` (Exact) → `speckle-server:3000`
  - `/readiness` (Exact) → `speckle-server:3000`

#### 5. Master Ingress (`speckle-server`)
- **Host**: `{{ domain }}` (from values.yaml)
- **Purpose**: Base hostname routing (may be superseded by minion ingresses)

#### 6. pgadmin Ingress (`pgadmin`)
- **Path**: `/pgadmin` (Prefix)
- **Backend**: `pgadmin:80`
- **Namespace**: `speckle-production`
- **Health Check Path**: `/misc/ping`

### Routing Flow Summary
1. Objects API requests (`/api/objects/`, `/objects/`, etc.) → Objects Minion → Server
2. File API requests (`/api/file/`, etc.) → File Minion → Server
3. GraphQL, Auth, Static files → Main Minion → Server
4. Health checks (`/liveness`, `/readiness`, `/api/status`) → Redirect Ingress
5. Everything else (`/`) → Frontend-2 (catch-all)
6. pgadmin (`/pgadmin`) → pgadmin service

---

## Security Groups

### 1. EKS Cluster Security Group (`speckle-cluster-cluster-sg`)
- **Purpose**: Controls traffic to EKS control plane
- **Outbound**: All traffic allowed (`0.0.0.0/0`)

### 2. EKS Nodes Security Group (`speckle-cluster-nodes-sg`)
- **Purpose**: Controls traffic to/from worker nodes
- **Outbound**: All traffic allowed (`0.0.0.0/0`)
- **Inbound**: Managed by EKS (node-to-node, control plane)

### 3. RDS Security Group (`speckle-cluster-rds-sg`)
- **Purpose**: Controls access to PostgreSQL database
- **Inbound**:
  - Port `5432` (PostgreSQL) from: `eks_nodes` security group
- **Outbound**: All traffic allowed

### 4. Redis Security Group (`speckle-cluster-redis-sg`)
- **Purpose**: Controls access to Redis cache
- **Inbound**:
  - Port `6379` (Redis) from: `eks_nodes` security group
- **Outbound**: All traffic allowed

---

## IAM Roles

### 1. EKS Cluster Role (`speckle-cluster-cluster-role`)
- **Service**: `eks.amazonaws.com`
- **Policies Attached**:
  - `AmazonEKSClusterPolicy`
  - `AmazonEKSServicePolicy`

### 2. EKS Node Group Role (`speckle-cluster-nodes-role`)
- **Service**: `ec2.amazonaws.com`
- **Policies Attached**:
  - `AmazonEKSWorkerNodePolicy`
  - `AmazonEKS_CNI_Policy` (for pod networking)
  - `AmazonEC2ContainerRegistryReadOnly` (for pulling images from ECR)

---

## Network Policies

Network policies are **optional** and controlled per service via `networkPolicy.enabled` parameter. By default, all are **disabled**.

### Supported Network Plugin Types
- **Kubernetes NetworkPolicy** (default): Standard Kubernetes network policies
- **Cilium NetworkPolicy**: Enhanced policies for Cilium CNI

### Services with Network Policy Support
1. Server
2. Objects
3. Frontend-2
4. Preview Service
5. Webhook Service
6. File Import Service
7. IFC Import Service
8. Monitoring
9. Test

### Network Policy Requirements (when enabled)
- Must configure ingress controller pod selector
- Must configure Postgres network policy (if accessing database)
- Must configure Redis network policy (if accessing cache)
- Must configure S3 network policy (if accessing S3)

---

## Service Accounts

Each deployment can optionally create its own Kubernetes Service Account:
- Server: `speckle-server` (if enabled)
- Objects: `speckle-objects` (if enabled)
- Frontend-2: `speckle-frontend-2` (if enabled)
- Preview Service: `speckle-preview-service` (if enabled)
- Webhook Service: `speckle-webhook-service` (if enabled)
- File Import Service: `speckle-fileimport-service` (if enabled)
- IFC Import Service: `speckle-ifc-import-service` (if enabled)
- Monitoring: `speckle-monitoring` (if enabled)
- Test: `speckle-test` (if enabled)

**Default**: Service accounts are **created** for all services (`create: true`)

---

## Configuration Secrets

All sensitive configuration is stored in Kubernetes Secrets:
- **Default Secret Name**: `server-vars`
- **Components can override**: Each service can specify its own secret name

### Typical Secrets Stored
- PostgreSQL connection string
- Redis connection string
- S3 access keys
- Email server passwords
- OAuth client secrets (Google, GitHub, Azure AD)
- Session secrets
- License tokens
- Encryption keys (if workspaces enabled)

---

## Summary Statistics

### Infrastructure Components
- **VPCs**: 1
- **Subnets**: 6 (2 public, 2 private, 2 database)
- **NAT Gateways**: 2
- **Internet Gateways**: 1
- **Route Tables**: 3

### EKS Components
- **EKS Clusters**: 1
- **Node Groups**: 1
- **Nodes**: 2-4 (auto-scaling)
- **Instance Type**: t3.medium

### Database & Storage
- **RDS Instances**: 1 (PostgreSQL 16.11)
- **ElastiCache Clusters**: 1 (Redis 7.1)
- **S3 Buckets**: 1

### Kubernetes Workloads
- **Deployments**: 10 (including pgadmin)
- **Services**: 9
- **Ingress Resources**: 6
- **Docker Images**: 9 unique images

### Resource Allocation (Default Configuration)
- **Total CPU Requests**: ~3-4 cores
- **Total Memory Requests**: ~5-6 GB
- **Total CPU Limits**: ~8-10 cores
- **Total Memory Limits**: ~15-20 GB

---

## Notes & Best Practices

1. **Security**: 
   - Database password is in terraform.tfvars (should use AWS Secrets Manager)
   - Public access CIDRs set to `0.0.0.0/0` (should restrict)
   - Deletion protection disabled on RDS (should enable for production)

2. **High Availability**:
   - RDS: Single AZ (consider Multi-AZ for production)
   - Redis: Single node (consider cluster mode for HA)
   - NAT Gateways: 2 (good for HA)

3. **Cost Optimization**:
   - Consider using smaller instance types for development
   - S3 lifecycle policies configured for cost savings
   - Node auto-scaling helps control costs

4. **Monitoring**:
   - Prometheus monitoring can be enabled via ServiceMonitor
   - Database metrics collection every 120 seconds
   - CloudWatch logs enabled for RDS

5. **Scalability**:
   - Preview Service supports HPA (disabled by default)
   - Nodes can auto-scale 1-4 instances
   - Most services can scale horizontally (adjust replicas)

---

*Document Generated: Comprehensive analysis of AWS infrastructure for Speckle Server deployment*
*Last Updated: Based on current codebase state*
