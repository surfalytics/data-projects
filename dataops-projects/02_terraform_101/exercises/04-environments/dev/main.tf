# Dev Environment Configuration
# This demonstrates a cost-optimized development setup

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
  #   bucket = "mycompany-terraform-state-dev"
  #   key    = "app/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment  = "dev"
      Project      = var.project_name
      ManagedBy    = "Terraform"
      CostCenter   = "Development"
      AutoShutdown = "true"
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

# Simple EC2 instance for development
resource "aws_instance" "dev_web" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t2.micro"  # Smallest instance for cost savings

  tags = {
    Name = "${var.project_name}-dev-web"
    Note = "Development server - can be stopped after hours"
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
  value = aws_instance.dev_web.id
}

output "public_ip" {
  value = aws_instance.dev_web.public_ip
}

output "environment" {
  value = "development"
}
