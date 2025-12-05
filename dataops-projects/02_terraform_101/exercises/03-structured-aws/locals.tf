# ============================================================================
# Local Values
# ============================================================================
# This file contains computed local values used across resources

locals {
  # Resource naming
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags
  common_tags = merge(
    var.additional_tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  )

  # S3 bucket name (must be globally unique)
  s3_bucket_name = "${local.name_prefix}-data-${random_id.bucket_suffix.hex}"

  # Security group rules
  ingress_rules = concat(
    [
      {
        description = "SSH from my IP"
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = [var.my_ip]
      }
    ],
    var.enable_http ? [
      {
        description = "HTTP from anywhere"
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
    ] : []
  )

  # User data script
  user_data = templatefile("${path.module}/user-data.sh", {
    environment   = var.environment
    project_name  = var.project_name
    bucket_name   = local.s3_bucket_name
    aws_region    = var.aws_region
  })
}

# Random ID for unique bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}
