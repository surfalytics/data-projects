variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for naming resources"
  type        = string
  default     = "metabase"
}

variable "vpc_cidr" {
  description = "CIDR block for the Metabase VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.0.0/20", "10.0.16.0/20"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (one per AZ), used by RDS"
  type        = list(string)
  default     = ["10.0.128.0/20", "10.0.144.0/20"]
}

variable "availability_zones" {
  description = "Availability zones to spread subnets across"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_name" {
  description = "Name of the application database Metabase connects to"
  type        = string
  default     = "metabase"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "metabase_admin"
}

variable "db_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "metabase_image" {
  description = "Container image for the Metabase task"
  type        = string
  default     = "metabase/metabase:latest"
}

variable "task_cpu" {
  description = "Fargate task vCPU units"
  type        = string
  default     = "1024"
}

variable "task_memory" {
  description = "Fargate task memory in MB"
  type        = string
  default     = "3072"
}
