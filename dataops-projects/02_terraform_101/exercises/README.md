# Terraform 101 - Progressive Learning Exercises

This directory contains a series of exercises that progressively teach Terraform concepts from basics to advanced topics.

## Learning Path

```
01-basics (Local)
    ↓
02-simple-aws (Single file)
    ↓
03-structured-aws (Organized files)
    ↓
04-environments (Dev/Prod separation)
    ↓
05-modules (Reusable components)
```

## Exercises Overview

### [Exercise 1: Terraform Basics](./01-basics/)
**Difficulty**: Beginner
**Duration**: 30 minutes
**Cost**: Free (local providers only)

**Topics Covered**:
- Resource creation and dependencies
- Variables (string, number, bool, map, list, object)
- Outputs
- Local values
- Count and for_each
- Conditional resources

**Prerequisites**: None

**Goal**: Understand core Terraform concepts without needing a cloud account.

---

### [Exercise 2: Simple AWS Resources](./02-simple-aws/)
**Difficulty**: Beginner
**Duration**: 45 minutes
**Cost**: ~$0.01/hour (t2.micro free tier eligible)

**Topics Covered**:
- AWS provider configuration
- EC2 instances (t2.micro)
- S3 buckets with security settings
- IAM roles and policies
- Security groups
- User data scripts
- Data sources

**Prerequisites**:
- AWS account
- AWS CLI configured
- Exercise 1 completed

**Goal**: Create real AWS infrastructure with Terraform.

**Resources Created**:
- 1× EC2 instance (t2.micro)
- 1× S3 bucket
- 1× IAM role
- 1× Security group

---

### [Exercise 3: Structured AWS Resources](./03-structured-aws/)
**Difficulty**: Intermediate
**Duration**: 1 hour
**Cost**: ~$0.01/hour

**Topics Covered**:
- Professional file organization
- Separate files per resource type
- External template files (`templatefile()`)
- Dynamic blocks
- S3 lifecycle policies
- Advanced security (IMDSv2, encryption)
- Comprehensive tagging strategy

**Prerequisites**: Exercise 2 completed

**Goal**: Learn how to organize Terraform code for real-world projects.

**File Structure**:
```
03-structured-aws/
├── providers.tf
├── variables.tf
├── data.tf
├── locals.tf
├── security-groups.tf
├── iam.tf
├── ec2.tf
├── s3.tf
├── outputs.tf
└── user-data.sh
```

---

### [Exercise 4: Environment Separation](./04-environments/)
**Difficulty**: Intermediate
**Duration**: 1 hour
**Cost**: ~$0.03/hour (dev + prod)

**Topics Covered**:
- Dev vs Prod configurations
- Directory-based environment separation
- Environment-specific variables
- Backend state management
- Cost optimization per environment
- Access control strategies

**Prerequisites**: Exercise 3 completed

**Goal**: Manage multiple environments safely with different configurations.

**Comparison**:
| Aspect | Dev | Prod |
|--------|-----|------|
| Instance | t2.micro | t3.small |
| Monitoring | Disabled | Enabled |
| Volume | 8 GB | 20 GB |
| SSH Access | Open | Restricted |

---

### [Exercise 5: Terraform Modules](./05-modules/)
**Difficulty**: Advanced
**Duration**: 2 hours
**Cost**: ~$0.03/hour

**Topics Covered**:
- Creating custom modules
- Module inputs and outputs
- Module composition
- Module versioning
- Module testing
- Publishing modules

**Prerequisites**: Exercise 4 completed

**Goal**: Create reusable Terraform modules for maximum code reuse.

**Module Structure**:
```
05-modules/
├── modules/
│   ├── ec2/      (Reusable EC2 module)
│   ├── s3/       (Reusable S3 module)
│   └── iam/      (Reusable IAM module)
└── environments/
    ├── dev/      (Uses modules)
    └── prod/     (Uses modules)
```

---

## Recommended Learning Sequence

### Week 1: Foundations
- **Day 1-2**: Complete Exercise 1 (Basics)
- **Day 3-4**: Complete Exercise 2 (Simple AWS)
- **Day 5**: Review and practice

### Week 2: Structure & Organization
- **Day 1-2**: Complete Exercise 3 (Structured AWS)
- **Day 3-4**: Complete Exercise 4 (Environments)
- **Day 5**: Review and compare approaches

### Week 3: Advanced Topics
- **Day 1-3**: Complete Exercise 5 (Modules)
- **Day 4**: Build a custom project
- **Day 5**: Review and refine

## Quick Start

### For Complete Beginners
```bash
cd exercises/01-basics
terraform init
terraform plan
terraform apply
```

### For Those With AWS Experience
```bash
cd exercises/02-simple-aws
# Update my_ip variable
terraform init
terraform plan
terraform apply
```

### For Experienced Developers
```bash
cd exercises/05-modules
# Review module structure
# Deploy to dev and prod
```

## Skills Matrix

| Skill | Ex 1 | Ex 2 | Ex 3 | Ex 4 | Ex 5 |
|-------|------|------|------|------|------|
| Basic syntax | ✅ | ✅ | ✅ | ✅ | ✅ |
| Variables | ✅ | ✅ | ✅ | ✅ | ✅ |
| Outputs | ✅ | ✅ | ✅ | ✅ | ✅ |
| AWS resources | - | ✅ | ✅ | ✅ | ✅ |
| File organization | - | - | ✅ | ✅ | ✅ |
| Environments | - | - | - | ✅ | ✅ |
| Modules | - | - | - | - | ✅ |
| Production-ready | - | - | ⚠️ | ⚠️ | ✅ |

✅ Covered | ⚠️ Partially | - Not covered

## Cost Management

### Estimated Monthly Costs

| Exercise | Resources | Est. Cost/Month |
|----------|-----------|-----------------|
| Exercise 1 | Local only | $0 |
| Exercise 2 | 1× t2.micro | $0 (free tier) or $8 |
| Exercise 3 | 1× t2.micro + S3 | $8-10 |
| Exercise 4 | 2× instances | $16-40 |
| Exercise 5 | 2× instances + modules | $16-40 |

**Important**:
- Always run `terraform destroy` after each exercise
- Set up AWS billing alerts
- Use free tier eligible resources

### Cost Optimization Tips
1. Stop instances when not in use
2. Delete resources between learning sessions
3. Use `t2.micro` or `t3.micro` instances
4. Enable AWS Free Tier notifications

## Troubleshooting

### Common Issues Across All Exercises

#### Issue: `terraform: command not found`
**Solution**: Install Terraform from [terraform.io/downloads](https://terraform.io/downloads)

#### Issue: AWS credentials not configured
**Solution**: Run `aws configure` or set environment variables

#### Issue: Bucket name already exists (S3)
**Solution**: S3 bucket names are globally unique; change `project_name` variable

#### Issue: State lock error
**Solution**: Another process is running or crashed
```bash
terraform force-unlock <LOCK_ID>
```

#### Issue: Resources stuck in state
**Solution**:
```bash
# List resources
terraform state list

# Remove from state (doesn't delete resource)
terraform state rm <resource_address>

# Or refresh state
terraform refresh
```

## Getting Help

### Resources by Topic

**Terraform Basics**:
- [Official Documentation](https://www.terraform.io/docs)
- [Terraform Registry](https://registry.terraform.io/)
- [HashiCorp Learn](https://learn.hashicorp.com/terraform)

**AWS + Terraform**:
- [AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform AWS Modules](https://github.com/terraform-aws-modules)
- [AWS Free Tier](https://aws.amazon.com/free/)

**Best Practices**:
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Gruntwork Production Framework](https://gruntwork.io/)
- [Terraform Style Guide](https://www.terraform.io/docs/language/syntax/style.html)

**Community**:
- [Terraform Community Forum](https://discuss.hashicorp.com/c/terraform-core)
- [Reddit r/Terraform](https://reddit.com/r/Terraform)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/terraform)

## What's Next?

After completing all exercises, consider:

1. **Build a Real Project**
   - Multi-tier application (web + database)
   - CI/CD pipeline
   - Complete infrastructure stack

2. **Explore Advanced Topics**
   - Terraform Cloud/Enterprise
   - Testing with Terratest
   - Policy as Code (Sentinel, OPA)
   - GitOps workflows

3. **Certification**
   - [HashiCorp Certified: Terraform Associate](https://www.hashicorp.com/certification/terraform-associate)

4. **Contribute**
   - Open source Terraform modules
   - Blog about your learnings
   - Help others in the community

## Feedback

Found an issue or have suggestions? Please contribute by:
- Opening an issue in the repository
- Submitting a pull request
- Sharing your learnings

## License

These exercises are for educational purposes. Feel free to use and modify for your learning.
