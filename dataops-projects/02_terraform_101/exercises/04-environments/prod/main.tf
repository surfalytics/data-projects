# Production Environment Configuration
# This demonstrates a production-ready setup with enhanced monitoring and security

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state
  # backend "s3" {
  #   bucket = "mycompany-terraform-state-prod"
  #   key    = "app/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment  = "prod"
      Project      = var.project_name
      ManagedBy    = "Terraform"
      CostCenter   = "Production"
      Backup       = "required"
      Compliance   = "required"
    }
  }
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "terraform101"
}

# Production EC2 instance with enhanced features
resource "aws_instance" "prod_web" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.small"  # Larger instance for production workloads

  monitoring = true  # Enable detailed monitoring

  root_block_device {
    volume_size = 20  # Larger volume for production
    encrypted   = true
  }

  tags = {
    Name       = "${var.project_name}-prod-web"
    Note       = "Production server - do not stop without approval"
    Backup     = "daily"
    Monitoring = "enabled"
  }
}

# Data source for AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Outputs
output "instance_id" {
  value = aws_instance.prod_web.id
}

output "public_ip" {
  value = aws_instance.prod_web.public_ip
}

output "environment" {
  value = "production"
}

output "monitoring_enabled" {
  value = aws_instance.prod_web.monitoring
}
