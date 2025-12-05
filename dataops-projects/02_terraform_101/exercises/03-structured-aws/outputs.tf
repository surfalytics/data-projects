# ============================================================================
# Outputs
# ============================================================================

# EC2 Outputs
output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.web.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.web.public_dns
}

output "ec2_availability_zone" {
  description = "Availability zone of the EC2 instance"
  value       = aws_instance.web.availability_zone
}

# S3 Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.data.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.data.arn
}

output "s3_bucket_region" {
  description = "Region of the S3 bucket"
  value       = aws_s3_bucket.data.region
}

# IAM Outputs
output "iam_role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.ec2.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.ec2.arn
}

# Security Group Outputs
output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.ec2.id
}

# Connection Information
output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i your-key.pem ec2-user@${aws_instance.web.public_dns}"
}

output "web_url" {
  description = "URL to access the web server"
  value       = "http://${aws_instance.web.public_dns}"
}

# AWS Account Information
output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

# Resource Summary
output "resource_summary" {
  description = "Summary of created resources"
  value = {
    ec2_instance    = aws_instance.web.id
    s3_bucket       = aws_s3_bucket.data.id
    iam_role        = aws_iam_role.ec2.name
    security_group  = aws_security_group.ec2.id
    environment     = var.environment
    project         = var.project_name
  }
}
