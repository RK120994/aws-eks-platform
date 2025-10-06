# EKS DevOps Demo Project

This repository contains a complete end-to-end DevOps solution for deploying a FastAPI application to Amazon EKS using Terraform, Helm, and GitHub Actions.

## 🏗️ Architecture Overview

- **Infrastructure**: Amazon EKS cluster with VPC, IAM roles, and managed node groups provisioned via Terraform
- **Application**: Simple FastAPI service with health checks and Prometheus metrics
- **Deployment**: Helm charts with environment-specific configurations
- **CI/CD**: GitHub Actions workflow with automated building, testing, and deployment
- **Security**: HTTPS ingress, least-privilege IAM policies, Kubernetes secrets
- **Observability**: Prometheus metrics, CloudWatch integration, alerting rules

## 📁 Project Structure

```
├── terraform/              # Infrastructure as Code
│   ├── environments/        # Environment-specific configurations
│   ├── modules/            # Reusable Terraform modules
│   └── *.tf               # Main Terraform files
├── app/                   # FastAPI application
│   ├── src/               # Application source code
│   ├── Dockerfile         # Container definition
│   └── requirements.txt   # Python dependencies
├── helm/                  # Helm charts
│   └── sample-app/        # Application Helm chart
├── .github/              # GitHub Actions workflows
│   └── workflows/        # CI/CD pipeline definitions
├── scripts/              # Development tooling
│   └── dev-cli.py        # Python CLI for operations
├── monitoring/           # Observability configuration
│   ├── alerts/          # Prometheus alert rules
│   └── runbooks/        # Troubleshooting guides
└── docs/                # Additional documentation
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **kubectl** installed and configured
4. **Terraform** (>= 1.0)
5. **Helm** (>= 3.0)
6. **Docker** for local development
7. **Python** (>= 3.8) for dev tooling

### Setup Instructions

#### 1. Configure AWS Credentials

```bash
# Option 1: AWS CLI profiles
aws configure --profile your-profile

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

#### 2. Deploy Infrastructure

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan -var-file="environments/dev.tfvars"

# Apply infrastructure
terraform apply -var-file="environments/dev.tfvars"

# Get EKS cluster credentials
aws eks update-kubeconfig --region us-west-2 --name demo-eks-dev
```

#### 3. Deploy Application

```bash
# Build and push Docker image (or let GitHub Actions handle this)
docker build -t your-registry/sample-app:latest app/
docker push your-registry/sample-app:latest

# Deploy using Helm
helm install sample-app helm/sample-app \
  --namespace dev \
  --create-namespace \
  --values helm/sample-app/values-dev.yaml
```

#### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n dev

# Get service URL
kubectl get ingress -n dev

# Test application
curl https://your-app-url/health
```

## 🔄 CI/CD Workflow

### GitHub Actions Setup

1. **Create GitHub Repository Secrets**:
   - `AWS_ROLE_ARN`: ARN of the IAM role for OIDC
   - `ECR_REPOSITORY`: ECR repository URI
   - `EKS_CLUSTER_NAME`: Name of the EKS cluster

2. **Configure OIDC Provider** in AWS IAM for GitHub Actions

3. **Workflow Triggers**:
   - **Push to main**: Deploy to dev environment
   - **Push to stage**: Deploy to staging environment
   - **Release**: Deploy to production (with manual approval)

### Manual Deployment Commands

```bash
# Deploy to specific environment
.github/workflows/deploy.yml --environment dev

# Rollback to previous version
python scripts/dev-cli.py rollback --environment dev --revision 1
```

## 🛠️ Development Tooling

### Python CLI Script

The `scripts/dev-cli.py` provides utilities for:

- **Log Tailing**: Stream logs from application pods across environments
- **Rollback**: Trigger Helm rollbacks to previous releases

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Tail logs from dev environment
python scripts/dev-cli.py logs --environment dev --follow

# Rollback to previous release
python scripts/dev-cli.py rollback --environment prod --confirm
```

## 🔒 Security Features

- **Network Security**: Private subnets for worker nodes, security groups with minimal access
- **IAM**: Least-privilege policies for all roles (EKS service role, node group role, CI/CD role)
- **Kubernetes**: RBAC, service accounts, network policies
- **Secrets Management**: Kubernetes secrets for sensitive data, AWS Secrets Manager integration
- **Image Security**: Container image scanning in CI/CD pipeline
- **HTTPS Only**: ALB ingress controller with SSL/TLS termination

## 📊 Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Prometheus endpoint at `/metrics`
- **Infrastructure Metrics**: CloudWatch integration
- **Log Aggregation**: CloudWatch Logs for centralized logging

### Alerting
- **High Error Rate**: Alert when error rate > 5% for 5 minutes
- **High Latency**: Alert when P95 latency > 500ms for 5 minutes
- **Pod Crashes**: Alert on pod restart loops

### Dashboards
- Grafana dashboards for application and infrastructure metrics
- CloudWatch dashboards for AWS service metrics

## 🚨 Troubleshooting

See detailed runbooks in `monitoring/runbooks/`:
- [High Error Rate Investigation](monitoring/runbooks/high-error-rate.md)
- [Pod Crash Loop Debugging](monitoring/runbooks/pod-crashloop.md)
- [Network Connectivity Issues](monitoring/runbooks/network-issues.md)

## 🏷️ Environment Management

### Environments

- **dev**: Development environment (single replica, lower resources)
- **stage**: Staging environment (production-like setup)
- **prod**: Production environment (high availability, auto-scaling)

### Configuration

Environment-specific configurations are managed via:
- Terraform variable files (`environments/*.tfvars`)
- Helm values files (`helm/sample-app/values-*.yaml`)
- Kubernetes namespaces for workload isolation

## 📝 Additional Resources

- [Solution Architecture](SOLUTION.md)
- [Security Best Practices](docs/security.md)
- [Deployment Strategies](docs/deployment.md)
- [Monitoring Setup](docs/monitoring.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This is a demonstration project designed for learning and evaluation purposes. For production use, additional security hardening, monitoring, and operational procedures should be implemented.
