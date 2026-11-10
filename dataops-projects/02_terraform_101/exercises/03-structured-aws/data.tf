# ============================================================================
# Data Sources
# ============================================================================
# This file contains all data source queries for existing AWS resources

# Get the latest Amazon Linux 2023 AMI (Amazon Linux 2 support ended 2026-06-30)
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Get availability zones in the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}
