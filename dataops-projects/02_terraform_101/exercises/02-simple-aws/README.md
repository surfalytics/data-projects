# Exercise 2: Simple AWS Resources

## Goal
Learn to create real AWS infrastructure including EC2, S3, and IAM resources using Terraform.

## What You'll Learn
- Creating EC2 instances
- S3 bucket configuration with security best practices
- IAM roles and policies
- AWS provider configuration
- Data sources for querying AWS
- Security groups
- User data scripts

## Prerequisites
- AWS account ([AWS Free Tier](https://aws.amazon.com/free/))
- AWS CLI configured with credentials
- Terraform installed (>= 1.0)
- Basic understanding of AWS services

## Cost Warning
This exercise creates real AWS resources:
- **EC2 t2.micro**: Free tier eligible (750 hours/month for 12 months)
- **S3 bucket**: Very low cost for small usage
- **IAM role**: Free

**Remember to run `terraform destroy` when done to avoid charges!**

## Setup

### Step 1: Configure AWS Credentials
Choose one method:

**Option A: AWS CLI**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option C: AWS SSO**
```bash
aws sso login
```

### Step 2: Get Your Public IP
For security, restrict SSH access to your IP:
```bash
curl -s ifconfig.me
# Copy the IP address
```

### Step 3: Update Variables (Optional)
Edit `main.tf` and update the `my_ip` variable:
```hcl
variable "my_ip" {
  default = "YOUR_IP_HERE/32"  # Replace with your IP
}
```

Or use a `terraform.tfvars` file:
```hcl
aws_region   = "us-east-1"
environment  = "dev"
project_name = "myproject"
my_ip        = "1.2.3.4/32"  # Your IP
```

## Instructions

### Step 1: Initialize
```bash
cd exercises/02-simple-aws
terraform init
```

### Step 2: Validate
```bash
terraform validate
terraform fmt
```

### Step 3: Plan
```bash
terraform plan
```

Review the plan:
- How many resources will be created?
- What EC2 instance type?
- Is the S3 bucket encrypted?
- What permissions does the IAM role have?

### Step 4: Apply
```bash
terraform apply
```

Type `yes` to confirm. This will take 1-2 minutes.

### Step 5: Verify Resources

**Check EC2 Instance**
```bash
# Get instance details
aws ec2 describe-instances --filters "Name=tag:Name,Values=*terraform101*" --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]'

# Or use Terraform output
terraform output ec2_public_ip
```

**Check S3 Bucket**
```bash
# List buckets
aws s3 ls | grep terraform101

# Test upload
echo "Hello from Terraform" > test.txt
aws s3 cp test.txt s3://$(terraform output -raw s3_bucket_name)/
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/
```

**Check IAM Role**
```bash
aws iam get-role --role-name $(terraform output -raw iam_role_name)
```

### Step 6: Test EC2 Instance

**Option A: If you have an EC2 key pair**
```bash
# SSH to instance (if you have the key configured)
terraform output ssh_command
```

**Option B: Test the web server**
```bash
# The instance runs a simple web server
curl $(terraform output -raw ec2_public_dns)
```

Note: You may need to add HTTP (port 80) to the security group to access the web server.

### Step 7: Make Changes

**Experiment 1: Add HTTP Access**
1. Add ingress rule for port 80 in the security group
2. Run `terraform plan` and `terraform apply`
3. Access the web server via browser

**Experiment 2: Change Instance Type**
1. Change `instance_type` from `t2.micro` to `t3.micro`
2. Plan and apply
3. Notice what Terraform does (replacement vs update)

**Experiment 3: Add S3 Object**
Create a new file called `s3_objects.tf`:
```hcl
resource "aws_s3_object" "readme" {
  bucket  = aws_s3_bucket.data_bucket.id
  key     = "README.txt"
  content = "This bucket was created with Terraform!"
}
```
Apply and verify.

### Step 8: Inspect State
```bash
# List all resources
terraform state list

# Show EC2 details
terraform state show aws_instance.web_server

# Show S3 bucket details
terraform state show aws_s3_bucket.data_bucket
```

### Step 9: Clean Up
```bash
terraform destroy
```

Type `yes` to confirm. This will delete all created resources.

Verify deletion:
```bash
# Check EC2
aws ec2 describe-instances --filters "Name=tag:Name,Values=*terraform101*"

# Check S3
aws s3 ls | grep terraform101
```

## What's Happening Behind the Scenes?

### Resource Creation Order
Terraform automatically determines the correct order:
1. Random ID (for bucket name)
2. Security Group
3. IAM Role → IAM Policy → IAM Instance Profile
4. S3 Bucket → Versioning, Encryption, Public Access Block
5. EC2 Instance (depends on Security Group and IAM Profile)

### State File
After applying, examine `terraform.tfstate`:
```bash
cat terraform.tfstate | jq '.resources[] | {type, name}'
```

This file contains the current state of your infrastructure.

## Key Concepts

### 1. Data Sources
```hcl
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  # ...
}
```
Data sources **read** existing resources, they don't create them.

### 2. Resource Dependencies
```hcl
iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
```
Terraform knows the EC2 instance depends on the IAM profile being created first.

### 3. Implicit vs Explicit Dependencies
- **Implicit**: Automatic (via resource references)
- **Explicit**: Using `depends_on` (rarely needed)

### 4. AWS Provider Default Tags
```hcl
provider "aws" {
  default_tags {
    tags = { Environment = "dev" }
  }
}
```
These tags are automatically added to all resources.

## Common Issues

### Issue: AWS credentials not found
**Solution**: Run `aws configure` or set environment variables

### Issue: Bucket name already exists
**Solution**: Bucket names are globally unique. The random suffix should prevent this, but you can change the `project_name` variable.

### Issue: Can't SSH to instance
**Solutions**:
1. Check security group allows your IP
2. Ensure you have the correct key pair attached
3. Verify instance is running: `aws ec2 describe-instances`

### Issue: Insufficient permissions
**Solution**: Ensure your AWS user/role has permissions to create EC2, S3, and IAM resources

## Security Best Practices Demonstrated

1. ✅ S3 bucket encryption enabled
2. ✅ S3 bucket versioning enabled
3. ✅ S3 public access blocked
4. ✅ Security group restricts SSH to specific IP
5. ✅ IAM role follows least privilege (only S3 access)
6. ✅ EBS volume encrypted
7. ✅ Default tags for resource tracking

## Cost Optimization Tips

1. **Use t2.micro** (free tier eligible)
2. **Stop instances when not in use**: `aws ec2 stop-instances --instance-ids i-xxx`
3. **Delete S3 objects before destroying bucket**
4. **Enable AWS Cost Explorer** to monitor spending
5. **Set up billing alerts** in AWS Console

## Next Steps
Once comfortable with this exercise, move to:
- **Exercise 3**: Structured AWS resources (proper file organization)
- Learn how to organize code for real projects

## Additional Resources
- [AWS Free Tier](https://aws.amazon.com/free/)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
