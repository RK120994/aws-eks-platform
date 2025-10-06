# Development Environment Configuration

# Project Configuration
project_name = "demo"
environment  = "dev"
region       = "us-west-2"

# EKS Configuration
cluster_name        = "demo-eks-dev"
kubernetes_version  = "1.28"

# Node Group Configuration - Development sizing
node_instance_types = ["t3.medium"]
node_capacity_type  = "ON_DEMAND"
node_desired_size   = 1
node_max_size       = 2
node_min_size       = 1

# GitHub Repository (update this with your repository)
github_repo = "your-username/eks-devops-demo"

# VPC Configuration
vpc_cidr               = "10.0.0.0/16"
public_subnet_cidrs    = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs   = ["10.0.10.0/24", "10.0.20.0/24"]

# Additional Tags
additional_tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Development"
  Environment = "dev"
}
