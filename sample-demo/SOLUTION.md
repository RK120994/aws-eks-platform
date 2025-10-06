# EKS DevOps Demo - Solution Architecture

This document describes the architecture, security considerations, design decisions, and implementation details of the EKS DevOps demonstration project.

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                        VPC                                  ││
│  │                                                             ││
│  │  ┌─────────────────┐    ┌─────────────────┐                ││
│  │  │  Public Subnet  │    │  Public Subnet  │                ││
│  │  │       AZ-1      │    │       AZ-2      │                ││
│  │  │                 │    │                 │                ││
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │                ││
│  │  │  │ NAT GW    │  │    │  │ NAT GW    │  │                ││
│  │  │  └───────────┘  │    │  └───────────┘  │                ││
│  │  └─────────────────┘    └─────────────────┘                ││
│  │            │                      │                        ││
│  │  ┌─────────────────┐    ┌─────────────────┐                ││
│  │  │ Private Subnet  │    │ Private Subnet  │                ││
│  │  │      AZ-1       │    │      AZ-2       │                ││
│  │  │                 │    │                 │                ││
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │                ││
│  │  │  │EKS Worker │  │    │  │EKS Worker │  │                ││
│  │  │  │   Nodes   │  │    │  │   Nodes   │  │                ││
│  │  │  └───────────┘  │    │  └───────────┘  │                ││
│  │  └─────────────────┘    └─────────────────┘                ││
│  │                                                             ││
│  │              ┌─────────────────┐                           ││
│  │              │  EKS Control    │                           ││
│  │              │     Plane       │                           ││
│  │              └─────────────────┘                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │      ECR        │  │  Application    │  │   CloudWatch    │ │
│  │   Repository    │  │ Load Balancer   │  │     Logs        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       GitHub Actions                            │
│                         CI/CD                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

#### Infrastructure Layer
- **Amazon EKS**: Managed Kubernetes control plane
- **VPC**: Custom VPC with public/private subnet architecture
- **NAT Gateways**: High-availability internet access for private subnets
- **Security Groups**: Network-level security controls
- **IAM Roles**: Least-privilege access control

#### Application Layer
- **FastAPI Microservice**: Python-based REST API with health checks
- **Container Runtime**: Docker with multi-stage builds for security
- **Helm Charts**: Kubernetes package management with environment-specific configurations

#### CI/CD Pipeline
- **GitHub Actions**: Automated build, test, and deployment
- **ECR**: Secure container image registry with vulnerability scanning
- **OIDC Integration**: Secure, passwordless authentication to AWS

## 🔐 Security Implementation

### Infrastructure Security

#### Network Security
- **Private Subnets**: Worker nodes deployed in private subnets only
- **Security Groups**: Minimal ingress/egress rules based on least privilege
- **Network Policies**: Kubernetes-native network segmentation (enabled in staging/prod)
- **VPC Flow Logs**: Network traffic monitoring and analysis

#### Identity and Access Management
```yaml
# GitHub Actions OIDC Role
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:your-org/your-repo:*"
        }
      }
    }
  ]
}
```

#### Container Security
- **Non-root User**: Application runs as non-privileged user (UID 1000)
- **Read-only Root Filesystem**: Prevents runtime modifications
- **Dropped Capabilities**: All Linux capabilities dropped
- **Security Contexts**: Pod and container security constraints
- **Image Scanning**: Automated vulnerability scanning in ECR

### Application Security

#### Runtime Security
```yaml
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```

#### Secret Management
- **Kubernetes Secrets**: Base64-encoded sensitive data
- **AWS Secrets Manager**: External secret management (recommended for production)
- **Secret Rotation**: Automated credential rotation capabilities

## 📊 Observability Strategy

### Monitoring Stack

#### Application Metrics
- **Prometheus Endpoints**: `/metrics` endpoint exposing application metrics
- **Custom Metrics**: HTTP request counts, durations, error rates
- **Health Checks**: Liveness and readiness probes

#### Infrastructure Monitoring
- **CloudWatch Integration**: EKS cluster and node metrics
- **Container Insights**: Pod and container performance metrics
- **Log Aggregation**: Centralized logging to CloudWatch Logs

#### Alerting Rules
```yaml
groups:
- name: sample-app-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    annotations:
      summary: "High latency detected"
```

## 🚀 CI/CD Pipeline Design

### Pipeline Stages

#### 1. Code Quality Gate
- **Linting**: Flake8 for Python code style
- **Security Scanning**: Bandit for security vulnerabilities
- **Testing**: pytest for unit and integration tests
- **Type Checking**: mypy for static type analysis

#### 2. Container Build
- **Multi-stage Build**: Optimized Docker images with minimal attack surface
- **Build Arguments**: Version and build metadata injection
- **Registry Push**: Secure push to Amazon ECR
- **Vulnerability Scanning**: Automated image security scanning

#### 3. Deployment Strategy
```yaml
# Environment-specific deployment strategy
Dev:      Automatic on push to develop/main
Stage:    Automatic on push to stage branch
Prod:     Manual approval required for releases (tags)
```

#### 4. Rollback Capabilities
- **Automated**: Failed health checks trigger rollback
- **Manual**: CLI tool for operators to rollback releases
- **Canary**: Support for canary deployments (future enhancement)

## 🏢 Environment Management

### Environment Isolation

#### Development Environment
- **Purpose**: Active development and testing
- **Resources**: Minimal (1 replica, low CPU/memory)
- **Security**: Relaxed for development velocity
- **Monitoring**: Debug-level logging and frequent health checks

#### Staging Environment
- **Purpose**: Production-like testing and validation
- **Resources**: Production-like sizing (2-6 replicas)
- **Security**: Production-equivalent security controls
- **Monitoring**: Production-like monitoring configuration

#### Production Environment
- **Purpose**: Live customer-facing workloads
- **Resources**: High-availability (3-10 replicas, auto-scaling)
- **Security**: Maximum security controls and compliance
- **Monitoring**: Minimal logging, comprehensive metrics and alerting

### Configuration Management
```yaml
# Environment-specific configurations
├── terraform/environments/
│   ├── dev.tfvars      # Development infrastructure
│   ├── stage.tfvars    # Staging infrastructure  
│   └── prod.tfvars     # Production infrastructure
└── helm/sample-app/
    ├── values-dev.yaml   # Development application config
    ├── values-stage.yaml # Staging application config
    └── values-prod.yaml  # Production application config
```

## 🛠️ Developer Experience

### Local Development
```bash
# Quick development setup
cd app/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### DevOps Tooling
The `scripts/dev-cli.py` provides essential operational capabilities:

#### Log Tailing
```bash
# Follow logs from development environment
python scripts/dev-cli.py logs --environment dev --follow

# View recent logs from production
python scripts/dev-cli.py logs --environment prod --lines 100
```

#### Rollback Operations
```bash
# Rollback to previous release
python scripts/dev-cli.py rollback --environment stage

# Rollback to specific revision
python scripts/dev-cli.py rollback --environment prod --revision 3 --confirm
```

## 📋 Deployment Procedures

### Initial Infrastructure Deployment
```bash
cd terraform/

# Initialize Terraform
terraform init

# Plan infrastructure for development
terraform plan -var-file="environments/dev.tfvars"

# Apply infrastructure
terraform apply -var-file="environments/dev.tfvars"

# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name demo-eks-dev
```

### Application Deployment
```bash
# Deploy using Helm
helm install sample-app helm/sample-app \
  --namespace dev \
  --create-namespace \
  --values helm/sample-app/values-dev.yaml
```

### Production Deployment Process
1. **Code Review**: Pull request review and approval
2. **Automated Testing**: CI pipeline validation
3. **Staging Deployment**: Automatic deployment to staging
4. **Integration Testing**: Automated and manual testing in staging
5. **Release Creation**: Git tag creation for production release
6. **Production Approval**: Manual approval gate
7. **Production Deployment**: Automated deployment with monitoring
8. **Smoke Testing**: Post-deployment validation
9. **Rollback Plan**: Documented rollback procedures

## ⚡ Performance Considerations

### Scaling Strategy
- **Horizontal Pod Autoscaler**: CPU and memory-based scaling
- **Cluster Autoscaler**: Node-level scaling based on resource demands
- **Vertical Pod Autoscaler**: Right-sizing recommendations (future enhancement)

### Resource Optimization
```yaml
# Production resource configuration
resources:
  limits:
    cpu: 1000m      # Maximum CPU allocation
    memory: 1Gi     # Maximum memory allocation
  requests:
    cpu: 250m       # Guaranteed CPU allocation
    memory: 256Mi   # Guaranteed memory allocation
```

### Caching Strategy
- **Application-level Caching**: In-memory caching for frequently accessed data
- **CDN Integration**: CloudFront for static asset delivery (future enhancement)
- **Database Connection Pooling**: Efficient database connectivity

## 🎯 Design Decisions & Tradeoffs

### Technology Choices

#### FastAPI vs. Flask/Django
**Chosen**: FastAPI
**Rationale**: 
- High performance with async support
- Automatic API documentation generation
- Built-in Pydantic validation
- Modern Python typing support

#### Helm vs. Kustomize
**Chosen**: Helm
**Rationale**:
- Mature ecosystem and community
- Templating capabilities for environment variations
- Release management and rollback features
- Industry standard for Kubernetes packaging

#### GitHub Actions vs. Jenkins/GitLab CI
**Chosen**: GitHub Actions
**Rationale**:
- Native GitHub integration
- No infrastructure overhead
- Rich ecosystem of actions
- OIDC integration with AWS

### Architecture Decisions

#### Single EKS Cluster vs. Multiple Clusters
**Chosen**: Single cluster with namespace isolation
**Rationale**:
- Cost optimization for demonstration purposes
- Simplified management overhead
- Adequate isolation through namespaces and RBAC
- **Production Recommendation**: Separate clusters for production isolation

#### Application Load Balancer vs. Network Load Balancer
**Chosen**: Application Load Balancer (ALB)
**Rationale**:
- HTTP/HTTPS protocol support
- SSL termination capabilities
- Path-based routing for microservices
- Integration with AWS Certificate Manager

## 🚨 Known Limitations & Future Enhancements

### Current Limitations
1. **Single Cluster**: All environments in one EKS cluster (cost optimization)
2. **Basic Monitoring**: Limited to Prometheus metrics (no Grafana dashboards)
3. **Secret Management**: Kubernetes secrets instead of AWS Secrets Manager
4. **Database**: No persistent database layer (application-only demonstration)
5. **Service Mesh**: No Istio or Linkerd implementation

### Future Enhancements
1. **Multi-cluster Architecture**: Separate EKS clusters per environment
2. **Service Mesh**: Istio implementation for advanced traffic management
3. **GitOps**: ArgoCD or Flux for declarative deployment management
4. **Advanced Monitoring**: Grafana dashboards and advanced alerting
5. **Chaos Engineering**: Chaos Monkey for resilience testing
6. **Policy as Code**: OPA/Gatekeeper for Kubernetes policy enforcement
7. **External Secrets**: External Secrets Operator for secret management
8. **Database Layer**: RDS/Aurora integration with proper data persistence

### Security Enhancements for Production
1. **Pod Security Standards**: Implement Pod Security Standards/OPA Gatekeeper
2. **Image Vulnerability Management**: Continuous image scanning and patching
3. **Network Segmentation**: Service mesh with mTLS
4. **Audit Logging**: Comprehensive audit trail for compliance
5. **Backup & Disaster Recovery**: Cross-region backup strategy
6. **Compliance Framework**: SOC2/ISO27001 compliance implementation

## 📊 Cost Optimization

### Infrastructure Costs
- **EKS Control Plane**: $0.10/hour per cluster
- **EC2 Worker Nodes**: t3.medium instances with spot pricing
- **NAT Gateways**: $0.045/hour + data processing charges
- **Application Load Balancer**: $0.0225/hour + LCU charges

### Optimization Strategies
1. **Spot Instances**: Use spot instances for development environments
2. **Right-sizing**: Regular review of resource requests and limits
3. **Cluster Autoscaler**: Automatic node scaling based on demand
4. **Reserved Instances**: Long-term commitments for stable workloads

## 🔧 Operational Runbooks

### Common Operations
- [High Error Rate Investigation](monitoring/runbooks/high-error-rate.md)
- [Pod Crash Loop Debugging](monitoring/runbooks/pod-crashloop.md)
- [Network Connectivity Issues](monitoring/runbooks/network-issues.md)

### Emergency Procedures
- **Incident Response**: Escalation procedures and communication plans
- **Rollback Procedures**: Automated and manual rollback strategies
- **Disaster Recovery**: RTO/RPO objectives and recovery procedures

## 📝 Compliance & Governance

### Security Compliance
- **Access Control**: RBAC implementation with least privilege
- **Data Encryption**: Encryption in transit and at rest
- **Audit Trails**: Comprehensive logging and monitoring
- **Vulnerability Management**: Regular scanning and patching

### Operational Excellence
- **Infrastructure as Code**: All infrastructure defined in Terraform
- **Configuration Management**: Helm charts for application configuration
- **Automated Testing**: CI/CD pipeline with quality gates
- **Documentation**: Comprehensive documentation and runbooks

---

This solution demonstrates a production-ready approach to EKS deployment with security, observability, and operational best practices. The modular design allows for easy scaling and enhancement based on specific organizational requirements.
