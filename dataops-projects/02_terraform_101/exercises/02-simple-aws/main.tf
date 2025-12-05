# ============================================================================
# Exercise 2: Simple AWS Resources in a Single File
# ============================================================================
# This exercise demonstrates creating basic AWS resources:
# - EC2 instance (t2.micro)
# - S3 bucket
# - IAM role with policy
#
# IMPORTANT: This will create real AWS resources that may incur costs!
# Remember to run 'terraform destroy' when done.

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================
provider "aws" {
  region = var.aws_region

  # Optional: Add default tags to all resources
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "Terraform-101"
      ManagedBy   = "Terraform"
      Exercise    = "02-simple-aws"
    }
  }
}

# ============================================================================
# Variables
# ============================================================================
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "terraform101"
}

variable "my_ip" {
  description = "Your public IP for SSH access (format: x.x.x.x/32)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Open to all! Replace with your IP
}

# ============================================================================
# Data Sources
# ============================================================================
# WHY: Data sources query existing AWS resources rather than creating them
# WHAT: Here we're finding the latest Amazon Linux 2 AMI

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# ============================================================================
# Security Group for EC2
# ============================================================================
# WHY: Security groups control inbound/outbound traffic to EC2 instances
# WHAT: Allows SSH access from your IP

resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-${var.environment}-ec2-sg"
  description = "Security group for EC2 instance - allows SSH"
  vpc_id      = data.aws_vpc.default.id

  # Inbound rule: Allow SSH from your IP
  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # Outbound rule: Allow all outbound traffic
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-sg"
  }
}

# ============================================================================
# Example 1: EC2 Instance (t2.micro - Free Tier Eligible)
# ============================================================================
# WHY: EC2 is the fundamental compute service in AWS
# WHAT: Creates a small Linux instance
# COST: Free tier eligible (750 hours/month for first 12 months)

resource "aws_instance" "web_server" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t2.micro"

  # Attach security group
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  # Attach IAM role (created below)
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  # User data script runs on first boot
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
              echo "<p>Instance ID: $(ec2-metadata --instance-id | cut -d ' ' -f 2)</p>" >> /var/www/html/index.html
              EOF

  # Enable detailed monitoring (optional, may incur small costs)
  monitoring = false

  # Root volume configuration
  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "${var.project_name}-${var.environment}-root-volume"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-web-server"
    Role = "web-server"
  }
}

# ============================================================================
# Example 2: S3 Bucket
# ============================================================================
# WHY: S3 is AWS's object storage service, essential for data storage
# WHAT: Creates a private S3 bucket with encryption and versioning
# COST: Pay for storage used and requests (very low cost for small usage)

resource "aws_s3_bucket" "data_bucket" {
  # Bucket names must be globally unique
  bucket = "${var.project_name}-${var.environment}-data-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-data-bucket"
    Environment = var.environment
  }
}

# Random suffix for unique bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block (Best Practice: Keep buckets private)
resource "aws_s3_bucket_public_access_block" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Example 3: IAM Role for EC2
# ============================================================================
# WHY: IAM roles grant AWS service permissions to other AWS services
# WHAT: Creates a role that allows EC2 to access S3
# COST: Free (IAM is not charged)

# IAM Role
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  # Trust policy: Who can assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-role"
  }
}

# IAM Policy for S3 Access
resource "aws_iam_role_policy" "s3_access" {
  name = "s3-access-policy"
  role = aws_iam_role.ec2_role.id

  # Permission policy: What this role can do
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*"
        ]
      }
    ]
  })
}

# IAM Instance Profile (required to attach role to EC2)
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-profile"
  }
}

# ============================================================================
# Outputs
# ============================================================================
output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web_server.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.web_server.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.web_server.public_dns
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.data_bucket.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.data_bucket.arn
}

output "iam_role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.ec2_role.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i your-key.pem ec2-user@${aws_instance.web_server.public_dns}"
}

output "web_url" {
  description = "URL to access the web server (Note: Security group must allow HTTP)"
  value       = "http://${aws_instance.web_server.public_dns}"
}
