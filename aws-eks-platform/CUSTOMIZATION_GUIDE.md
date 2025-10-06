# Customization Guide - Required Changes for Your Environment

This guide outlines all the files you need to modify to deploy this EKS DevOps demo in your AWS environment.

## 🔴 CRITICAL - Must Update Before Deployment

### 1. AWS Account Configuration

**File**: `terraform/environments/dev.tfvars`
```hcl
# CHANGE THESE VALUES
project_name = "demo"                    # Keep or change to your project name
environment  = "dev"                     # Keep as "dev"
region       = "us-west-2"               # Change to your preferred AWS region

# CRITICAL: Update with your GitHub repository
github_repo = "YOUR-GITHUB-USERNAME/YOUR-REPO-NAME"  # ← MUST CHANGE

# Update if using different region
cluster_name = "demo-eks-dev"            # Keep or customize
```

**Repeat for**:
- `terraform/environments/stage.tfvars`
- `terraform/environments/prod.tfvars`

### 2. Container Registry Configuration

**Files to Update**:
- `helm/sample-app/values.yaml`
- `helm/sample-app/values-dev.yaml`
- `helm/sample-app/values-stage.yaml`
- `helm/sample-app/values-prod.yaml`

**Change**:
```yaml
image:
  repository: YOUR-AWS-ACCOUNT-ID.dkr.ecr.us-west-2.amazonaws.com/demo-app
  #           ^^^^^^^^^^^^^^^^^^^^ REPLACE WITH YOUR ACCOUNT ID
```

**How to find your AWS Account ID**:
```bash
aws sts get-caller-identity --query Account --output text
```

### 3. GitHub Actions Configuration

**File**: `.github/workflows/ci-cd.yml`

**Environment Variables Section** (lines 8-11):
```yaml
env:
  AWS_REGION: us-west-2        # Change if using different region
  ECR_REPOSITORY: demo-app     # Keep as-is
  EKS_CLUSTER_NAME: demo-eks   # Keep as-is
```

### 4. GitHub Repository Secrets

After deploying Terraform, add these secrets in GitHub:
- Go to your repository → Settings → Secrets and Variables → Actions
- Add New Repository Secret:

```
AWS_ROLE_ARN: arn:aws:iam::YOUR-ACCOUNT:role/demo-dev-github-actions-role
ECR_REGISTRY: YOUR-ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
EKS_CLUSTER_NAME: demo-eks
```

## 🟡 RECOMMENDED - Update for Production Use

### 5. Domain Configuration

**Files**:
- `helm/sample-app/values-dev.yaml`
- `helm/sample-app/values-stage.yaml`
- `helm/sample-app/values-prod.yaml`

**Change**:
```yaml
ingress:
  hosts:
    - host: sample-app-dev.YOUR-DOMAIN.com  # ← Change to your domain
      paths:
        - path: /
          pathType: Prefix
```

### 6. SSL Certificates (Production)

**Files**:
- `helm/sample-app/values-stage.yaml`
- `helm/sample-app/values-prod.yaml`

**Add your certificate ARN**:
```yaml
ingress:
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:REGION:ACCOUNT:certificate/CERT-ID"
```

**To create SSL certificate**:
```bash
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS \
  --region us-west-2
```

## 🟢 OPTIONAL - Customizations

### 7. Resource Limits

**Files**: All `helm/sample-app/values-*.yaml`

**Adjust based on your needs**:
```yaml
resources:
  limits:
    cpu: 500m      # Adjust based on expected load
    memory: 512Mi  # Adjust based on application needs
```

### 8. Scaling Configuration

```yaml
autoscaling:
  minReplicas: 1          # Minimum pods
  maxReplicas: 10         # Maximum pods
  targetCPUUtilizationPercentage: 70  # Scale trigger
```

### 9. Monitoring Configuration

**File**: `monitoring/alerts/prometheus-rules.yaml`

**Update runbook URLs**:
```yaml
annotations:
  runbook_url: "https://github.com/YOUR-ORG/YOUR-REPO/blob/main/monitoring/runbooks/high-error-rate.md"
```

## 📋 Deployment Checklist

### Pre-deployment:
- [ ] Updated all AWS Account IDs in Helm values
- [ ] Updated GitHub repository name in Terraform files
- [ ] Configured AWS CLI with appropriate credentials
- [ ] Updated region settings if not using us-west-2

### Phase 1: Infrastructure
```bash
cd terraform
terraform init
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"

# Note the outputs - you'll need them for GitHub secrets
terraform output
```

### Phase 2: GitHub Setup
- [ ] Added GitHub repository secrets (AWS_ROLE_ARN, ECR_REGISTRY, EKS_CLUSTER_NAME)
- [ ] Enabled GitHub Actions workflows

### Phase 3: Application Deployment
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name demo-eks-dev

# Deploy application
helm install sample-app helm/sample-app \
  --namespace dev \
  --create-namespace \
  --values helm/sample-app/values-dev.yaml
```

## 🚨 Security Recommendations

### For Production Environments:

1. **Remove hardcoded secrets** from values files
2. **Use AWS Secrets Manager** or External Secrets Operator
3. **Set up proper IAM policies** with least privilege
4. **Enable VPC Flow Logs** for network monitoring
5. **Configure backup strategies** for persistent data

### Example: External Secrets Setup
```yaml
# Replace secrets section in values files with:
secretStore:
  provider: aws
  secretsManager:
    region: us-west-2
    secretName: "sample-app-secrets"
```

## 🔧 Quick Setup Commands

### 1. Find Your AWS Account ID:
```bash
aws sts get-caller-identity --query Account --output text
```

### 2. Create ECR Repository:
```bash
aws ecr create-repository --repository-name demo-app --region us-west-2
```

### 3. Get ECR Login:
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-west-2.amazonaws.com
```

### 4. Build and Push Initial Image:
```bash
docker build -t demo-app app/
docker tag demo-app:latest ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/demo-app:latest
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/demo-app:latest
```

## 📞 Need Help?

If you encounter issues:

1. **Check AWS credentials**: `aws sts get-caller-identity`
2. **Verify region settings**: Ensure consistency across all files
3. **Check GitHub secrets**: Ensure all required secrets are set
4. **Review logs**: Use `kubectl logs` and `terraform plan` output

## 🔄 File Summary

**MUST UPDATE**:
- `terraform/environments/*.tfvars` (3 files)
- `helm/sample-app/values*.yaml` (4 files)
- GitHub repository secrets

**SHOULD UPDATE**:
- Domain configurations in Helm values
- SSL certificate ARNs
- Resource limits and scaling parameters

**OPTIONAL**:
- Monitoring configurations
- Alert thresholds
- Application-specific settings

---

**Next Steps**: Start with updating the AWS Account ID in all Helm values files, then proceed with the deployment checklist above.
