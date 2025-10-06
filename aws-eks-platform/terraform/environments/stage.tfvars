# Staging Environment Configuration

# Project Configuration
project_name = "demo"
environment  = "stage"
region       = "us-west-2"

# EKS Configuration
cluster_name        = "demo-eks-stage"
kubernetes_version  = "1.28"

# Node Group Configuration - Staging sizing (production-like)
node_instance_types = ["t3.large"]
node_capacity_type  = "ON_DEMAND"
node_desired_size   = 2
node_max_size       = 4
node_min_size       = 2

# GitHub Repository (update this with your repository)
github_repo = "your-username/eks-devops-demo"

# VPC Configuration
vpc_cidr               = "10.1.0.0/16"
public_subnet_cidrs    = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs   = ["10.1.10.0/24", "10.1.20.0/24"]

# Additional Tags
additional_tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Staging"
  Environment = "stage"
}
