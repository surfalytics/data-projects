# Exercise 3: Structured AWS Resources

## Goal
Learn professional Terraform project organization by separating resources into logical files.

## What You'll Learn
- Proper file organization for Terraform projects
- Using `templatefile()` for user data scripts
- Dynamic blocks for flexible resource configuration
- Lifecycle policies for S3
- Advanced security configurations (IMDSv2, encrypted volumes)
- Using `for_each` to create multiple similar resources

## File Structure

```
03-structured-aws/
├── providers.tf        # Provider and Terraform configuration
├── variables.tf        # Input variable definitions
├── data.tf            # Data sources (AMI, VPC, etc.)
├── locals.tf          # Local computed values
├── security-groups.tf # Security group definitions
├── iam.tf             # IAM roles and policies
├── ec2.tf             # EC2 instance configuration
├── s3.tf              # S3 bucket and configuration
├── outputs.tf         # Output values
├── user-data.sh       # EC2 user data script
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Why Structure This Way?

### Benefits of Organized Files:
1. **Easy Navigation**: Find resources quickly
2. **Team Collaboration**: Multiple people can work on different files
3. **Code Review**: Easier to review specific changes
4. **Modularity**: Clear separation of concerns
5. **Maintenance**: Simpler to update specific components

### File Naming Conventions:
- `providers.tf` - Always first alphabetically, contains setup
- `variables.tf` - Input parameters
- `data.tf` - Read-only queries to AWS
- `locals.tf` - Computed values
- `{resource-type}.tf` - One file per major resource type
- `outputs.tf` - Always last alphabetically

## Prerequisites
- Completed Exercise 2
- AWS credentials configured
- Understanding of EC2, S3, and IAM basics

## Instructions

### Step 1: Review the File Structure
Before applying, read through each file to understand:
- **data.tf**: What existing AWS resources are we querying?
- **locals.tf**: What values are being computed?
- **security-groups.tf**: What traffic is allowed?
- **iam.tf**: What permissions does the EC2 instance have?

### Step 2: Customize Variables
Create a `terraform.tfvars` file:
```hcl
aws_region     = "us-east-1"
environment    = "dev"
project_name   = "myproject"
my_ip          = "YOUR_IP_HERE/32"
enable_http    = true
instance_type  = "t2.micro"
```

### Step 3: Initialize and Apply
```bash
cd exercises/03-structured-aws
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

### Step 4: Test the Deployment

**1. Access the Web Server**
```bash
# Get the URL
terraform output web_url

# Or use curl
curl $(terraform output -raw web_url)
```

**2. Check S3 Bucket**
```bash
# List bucket contents
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/

# Check startup logs uploaded by the instance
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/logs/
```

**3. Verify IAM Permissions**
```bash
# View the IAM role
aws iam get-role --role-name $(terraform output -raw iam_role_name)

# List attached policies
aws iam list-role-policies --role-name $(terraform output -raw iam_role_name)
```

### Step 5: Experiment with Changes

**Experiment 1: Disable HTTP Access**
```hcl
# In terraform.tfvars
enable_http = false
```
Apply and note how the security group changes.

**Experiment 2: Change Instance Type**
```hcl
instance_type = "t3.micro"
```
Does Terraform replace or update the instance?

**Experiment 3: Add Custom Tags**
```hcl
additional_tags = {
  Owner = "YourName"
  CostCenter = "Engineering"
}
```

### Step 6: Explore Advanced Features

**Dynamic Blocks**
Check `security-groups.tf` - notice the `dynamic` block:
```hcl
dynamic "ingress" {
  for_each = local.ingress_rules
  # ...
}
```
This creates ingress rules based on a list of maps.

**Templatefile Function**
Check `locals.tf` - the `user_data` uses `templatefile()`:
```hcl
user_data = templatefile("${path.module}/user-data.sh", {
  environment = var.environment
  # ...
})
```
Variables are injected into the shell script.

**S3 Lifecycle Policies**
Check `s3.tf` - lifecycle rules automatically:
- Transition old versions to cheaper storage
- Delete old logs after 30 days

### Step 7: View State Organization
```bash
# List all resources
terraform state list

# Resources are organized by type
# aws_instance.web
# aws_s3_bucket.data
# aws_iam_role.ec2
```

### Step 8: Generate Documentation
```bash
# Create a resource graph
terraform graph | dot -Tpng > graph.png

# View dependency relationships
terraform graph
```

### Step 9: Clean Up
```bash
terraform destroy
```

## Key Concepts

### 1. File Organization
```
Small Project (< 10 resources):    main.tf, variables.tf, outputs.tf
Medium Project (< 50 resources):   Separate by resource type (this exercise)
Large Project (> 50 resources):    Use modules (Exercise 5)
```

### 2. Dynamic Blocks
Create multiple nested blocks from a list:
```hcl
dynamic "ingress" {
  for_each = local.ingress_rules
  content {
    from_port = ingress.value.from_port
    # ...
  }
}
```

### 3. Templatefile Function
```hcl
templatefile(path, vars)
```
- Injects variables into a file
- Useful for user data, config files, scripts

### 4. Locals Block
```hcl
locals {
  name_prefix = "${var.project}-${var.env}"
}
```
- Computed once, reused everywhere
- Keeps code DRY (Don't Repeat Yourself)

### 5. Data Sources
```hcl
data "aws_ami" "latest" { ... }
data "aws_vpc" "default" { ... }
```
- Query existing resources
- Reference values you didn't create

## Comparison with Exercise 2

| Aspect | Exercise 2 | Exercise 3 |
|--------|-----------|-----------|
| **Files** | Single `main.tf` | 9 separate files |
| **User Data** | Inline script | External template file |
| **Security Rules** | Hardcoded | Dynamic blocks |
| **Maintainability** | Harder | Easier |
| **Team Work** | Conflicts | Parallel work |
| **Navigation** | Scroll to find | Open specific file |

## Best Practices Demonstrated

1. ✅ **Separation of Concerns**: Each file has a clear purpose
2. ✅ **DRY Principle**: Locals avoid repetition
3. ✅ **Template Files**: Keep code and scripts separate
4. ✅ **Dynamic Configuration**: Flexible security rules
5. ✅ **Comprehensive Tagging**: Use locals for consistent tags
6. ✅ **Security First**: IMDSv2, encryption, private S3
7. ✅ **Lifecycle Management**: S3 cost optimization

## Common Patterns

### Pattern 1: Resource Per File
```
ec2.tf      → aws_instance
s3.tf       → aws_s3_bucket, aws_s3_bucket_*
iam.tf      → aws_iam_role, aws_iam_policy
```

### Pattern 2: Logical Grouping
```
network.tf    → VPC, subnets, route tables
compute.tf    → EC2, ASG, launch templates
database.tf   → RDS, DynamoDB
```

### Pattern 3: Environment Files
```
main.tf
dev.tfvars
prod.tfvars
```

## Troubleshooting

### Issue: User data not applied
**Check**: Did you set `user_data_replace_on_change = true`?

### Issue: S3 bucket name taken
**Solution**: The random suffix should prevent this, but change `project_name` if needed

### Issue: Can't see web page
**Solutions**:
1. Check `enable_http = true`
2. Wait 2-3 minutes for user data to complete
3. Check instance logs: `aws logs tail /aws/ec2/...`

## Next Steps
Move to **Exercise 4** to learn environment separation (dev/prod).

## Additional Resources
- [Terraform Style Guide](https://www.terraform-best-practices.com/code-structure)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
