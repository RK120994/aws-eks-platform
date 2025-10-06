# Production Environment Configuration

# Project Configuration
project_name = "demo"
environment  = "prod"
region       = "us-west-2"

# EKS Configuration
cluster_name        = "demo-eks-prod"
kubernetes_version  = "1.28"

# Node Group Configuration - Production sizing (high availability)
node_instance_types = ["t3.large"]
node_capacity_type  = "ON_DEMAND"
node_desired_size   = 3
node_max_size       = 6
node_min_size       = 3

# GitHub Repository (update this with your repository)
github_repo = "your-username/eks-devops-demo"

# VPC Configuration
vpc_cidr               = "10.2.0.0/16"
public_subnet_cidrs    = ["10.2.1.0/24", "10.2.2.0/24"]
private_subnet_cidrs   = ["10.2.10.0/24", "10.2.20.0/24"]

# Additional Tags
additional_tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Production"
  Environment = "prod"
  Backup      = "daily"
  Monitoring  = "enhanced"
}
