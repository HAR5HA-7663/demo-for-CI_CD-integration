# Online Learning Portal - AWS Deployment Guide

Complete automation scripts for deploying and cleaning up the Online Learning Portal microservices infrastructure on AWS ECS Fargate.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Script](#deployment-script)
- [Cleanup Script](#cleanup-script)
- [Architecture](#architecture)
- [Cost Estimates](#cost-estimates)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project includes two PowerShell scripts for complete infrastructure automation:

1. **`deploy-aws-infrastructure.ps1`** - Creates all AWS resources needed for the project
2. **`cleanup-aws-infrastructure.ps1`** - Removes all AWS resources to prevent charges

### What Gets Deployed

The deployment script creates:
- **ECS Cluster** (Fargate) - Container orchestration
- **6 Microservices** - user, course, enrollment, payment, notification, swagger-ui
- **5 DynamoDB Tables** - Persistent data storage
- **6 ECR Repositories** - Docker image storage
- **Cloud Map Namespace** - Service discovery
- **Security Groups** - Network access control
- **IAM Roles** - Permission management
- **CloudWatch Log Groups** - Application logging

---

## ✅ Prerequisites

### Required Software

1. **PowerShell 7+** (for Windows/Linux/Mac)
   ```powershell
   $PSVersionTable.PSVersion
   ```

2. **AWS CLI v2**
   ```bash
   aws --version
   ```
   Install from: https://aws.amazon.com/cli/

3. **Docker** (for building and pushing images)
   ```bash
   docker --version
   ```
   Install from: https://www.docker.com/

### AWS Requirements

- AWS Account with administrative access
- AWS IAM user with programmatic access (Access Key ID and Secret Access Key)
- Recommended: IAM user with `AdministratorAccess` policy for full permissions

---

## 🚀 Quick Start

### 1. Deploy Infrastructure

Run the deployment script:

```powershell
.\deploy-aws-infrastructure.ps1
```

The script will:
- Prompt you to configure AWS CLI (if not already done)
- Ask for confirmation before deploying
- Create all AWS resources
- Display a complete summary

**Example output:**
```
═══════════════════════════════════════════════════════
 AWS CLI Configuration
═══════════════════════════════════════════════════════

Do you want to:
  1. Use an existing AWS CLI profile
  2. Create a new AWS CLI profile

Enter your choice (1 or 2): 2
Enter a name for your new profile: my-project
AWS Access Key ID: AKIA...
AWS Secret Access Key: ****
✓ AWS CLI profile 'my-project' created successfully
```

### 2. Build and Push Docker Images

After infrastructure is created, build and push your Docker images:

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-2 --profile <your-profile> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-2.amazonaws.com

# For each service (user-service, course-service, etc.)
cd <service-directory>
docker build -t <service-name> .
docker tag <service-name>:latest <account-id>.dkr.ecr.us-east-2.amazonaws.com/<service-name>:latest
docker push <account-id>.dkr.ecr.us-east-2.amazonaws.com/<service-name>:latest
```

### 3. Configure Jenkins CI/CD (Optional)

Set up Jenkins to automate the build and deployment process:
- Configure multibranch pipeline
- Point to GitHub repository
- Jenkins will automatically build and deploy on commits

### 4. Access Your Application

Get the Swagger UI public URL:

```bash
# Get the task network interface
aws ecs describe-tasks \
  --cluster online-learning-portal \
  --tasks $(aws ecs list-tasks --cluster online-learning-portal --service-name swagger-ui --query 'taskArns[0]' --output text --profile <your-profile> --region us-east-2) \
  --profile <your-profile> --region us-east-2 \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text

# Get the public IP from the network interface ID
aws ec2 describe-network-interfaces \
  --network-interface-ids <network-interface-id> \
  --profile <your-profile> --region us-east-2 \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

Access Swagger UI at: `http://<public-ip>:8080/docs`

### 5. Cleanup (When Done)

Remove all AWS resources to prevent charges:

```powershell
.\cleanup-aws-infrastructure.ps1
```

The script will:
- Ask for confirmation (you must type "DELETE")
- Remove all created resources
- Display a summary of deleted resources

---

## 📖 Deployment Script Details

### Command Line Options

```powershell
.\deploy-aws-infrastructure.ps1 [-ProfileName <profile>] [-Region <region>]
```

**Parameters:**
- `-ProfileName` (optional) - AWS CLI profile to use (default: prompts user)
- `-Region` (optional) - AWS region (default: us-east-2)

**Example with parameters:**
```powershell
.\deploy-aws-infrastructure.ps1 -ProfileName my-project -Region us-east-2
```

### Interactive Setup

If you don't specify a profile, the script will guide you through:

1. **Profile Selection**
   - Option 1: Use existing profile
   - Option 2: Create new profile

2. **AWS Configuration** (for new profiles)
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region
   - Output format

3. **Verification**
   - Tests credentials
   - Shows account ID
   - Asks for deployment confirmation

### Deployment Steps

The script performs these operations in order:

1. **IAM Roles**
   - `ecsTaskExecutionRole` - For ECS infrastructure
   - `ecsTaskRole` - For DynamoDB access

2. **VPC Configuration**
   - Discovers default VPC
   - Gets available subnets

3. **Security Group**
   - Creates security group
   - Allows port 8080 traffic
   - Allows inter-service communication

4. **DynamoDB Tables**
   - `learning-portal-users` (with EmailIndex)
   - `learning-portal-courses`
   - `learning-portal-enrollments` (with UserIndex)
   - `learning-portal-payments`
   - `learning-portal-notifications`

5. **ECR Repositories**
   - Creates repository for each service

6. **ECS Cluster**
   - Creates Fargate cluster

7. **CloudWatch Logs**
   - Creates log group for each service

8. **Service Discovery**
   - Creates Cloud Map namespace
   - Registers DNS records for internal communication

9. **Task Definitions**
   - Registers task definition for each service
   - Configures CPU, memory, logging

10. **ECS Services**
    - Creates service for each microservice
    - Configures networking and service discovery

### Idempotency

The script is **idempotent** - you can run it multiple times safely. It checks if resources already exist before creating them.

---

## 🧹 Cleanup Script Details

### Command Line Options

```powershell
.\cleanup-aws-infrastructure.ps1 [-ProfileName <profile>] [-Region <region>]
```

### Safety Features

- Requires explicit confirmation (must type "DELETE")
- Shows what will be deleted
- Cannot be accidentally executed

### Deletion Order

Resources are deleted in this order to avoid dependency issues:

1. Scale ECS services to 0 tasks
2. Delete ECS services
3. Delete ECS cluster
4. Deregister task definitions
5. Delete DynamoDB tables
6. Delete ECR repositories
7. Delete CloudWatch log groups
8. Delete Cloud Map namespace
9. Delete security groups
10. Check for other resources (NAT, ALB, EC2, EIP)

### What Remains After Cleanup

These resources are **not deleted** automatically:

- **IAM Roles** (`ecsTaskRole`, `ecsTaskExecutionRole`)
  - Reason: May be used by other projects
  - Safe to delete manually if not needed

- **Default VPC and Subnets**
  - Reason: AWS default resources, safe to keep
  - Should not be deleted

### Verification Commands

Check if cleanup was successful:

```bash
# Check ECS clusters
aws ecs list-clusters --profile <your-profile> --region us-east-2

# Check DynamoDB tables
aws dynamodb list-tables --profile <your-profile> --region us-east-2

# Check ECR repositories
aws ecr describe-repositories --profile <your-profile> --region us-east-2
```

---

## 🏗️ Architecture

### Microservices Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Swagger UI (ALB)    │ ◄── Public Access
              │   Port 8080           │
              └──────────┬────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  User   │    │ Course  │    │Enrollment│
    │ Service │    │ Service │    │ Service │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Payment  │    │Notification│  │         │
    │Service  │    │ Service    │  │         │
    └────┬────┘    └────┬────────┘  │         │
         │              │              │
         └──────────────┴──────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   DynamoDB Tables     │
              │  - users              │
              │  - courses            │
              │  - enrollments        │
              │  - payments           │
              │  - notifications      │
              └───────────────────────┘
```

### Service Discovery

Services communicate internally via Cloud Map DNS:
- `user-service.learning-portal.local`
- `course-service.learning-portal.local`
- `enrollment-service.learning-portal.local`
- `payment-service.learning-portal.local`
- `notification-service.learning-portal.local`

### Security

- **Security Group**: Controls network access
- **IAM Roles**: Separate execution and task roles
- **Private Communication**: Services use internal DNS
- **Public Access**: Only Swagger UI is publicly accessible

---

## 💰 Cost Estimates

### Running Costs (Approximate)

| Service | Estimated Cost | Notes |
|---------|---------------|-------|
| ECS Fargate (6 tasks) | ~$15-20/month | 0.25 vCPU, 0.5 GB RAM each |
| DynamoDB (5 tables) | ~$1-5/month | On-demand pricing, depends on usage |
| ECR (6 repositories) | ~$1-2/month | First 500 MB free, then $0.10/GB |
| CloudWatch Logs | ~$0.50-1/month | First 5 GB free |
| Data Transfer | ~$1-2/month | First 100 GB free |
| **Total** | **~$18-30/month** | For development/testing |

### Cost Optimization Tips

1. **Stop services when not in use**
   ```bash
   aws ecs update-service --cluster online-learning-portal \
     --service <service-name> --desired-count 0
   ```

2. **Use spot instances** (for non-critical environments)

3. **Delete unused ECR images**
   ```bash
   aws ecr batch-delete-image --repository-name <service-name> \
     --image-ids imageTag=<tag>
   ```

4. **Always run cleanup script when done**
   ```powershell
   .\cleanup-aws-infrastructure.ps1
   ```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Unable to locate credentials"

**Problem:** AWS CLI is not configured

**Solution:**
```bash
aws configure --profile <your-profile>
# Enter your Access Key ID and Secret Access Key
```

#### 2. Services fail to start (tasks stopping immediately)

**Problem:** Docker images not pushed to ECR

**Solution:**
- Build and push images to ECR
- Check CloudWatch logs for errors

#### 3. "Security token is invalid"

**Problem:** AWS credentials expired or incorrect profile

**Solution:**
- Verify profile: `aws sts get-caller-identity --profile <your-profile>`
- Reconfigure: `aws configure --profile <your-profile>`

#### 4. Services can't communicate

**Problem:** Service discovery not working

**Solution:**
- Verify Cloud Map namespace exists
- Check security group allows internal traffic
- Ensure services have service discovery configuration

#### 5. Cleanup script fails to delete security group

**Problem:** Network interfaces still attached

**Solution:**
- Wait 2-3 minutes for ENIs to detach
- Run cleanup script again
- Manually delete from AWS Console if needed

### Checking Logs

View service logs in CloudWatch:

```bash
aws logs tail /ecs/<service-name> --follow \
  --profile <your-profile> --region us-east-2
```

### Manual Resource Check

Verify resources:

```bash
# List all ECS services
aws ecs list-services --cluster online-learning-portal \
  --profile <your-profile> --region us-east-2

# List DynamoDB tables
aws dynamodb list-tables --profile <your-profile> --region us-east-2

# List ECR repositories
aws ecr describe-repositories --profile <your-profile> --region us-east-2
```

---

## 📚 Additional Resources

### AWS Documentation
- [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [ECR](https://docs.aws.amazon.com/ecr/)
- [Cloud Map](https://docs.aws.amazon.com/cloud-map/)

### Project Structure
```
Online Learning Portal/
├── deploy-aws-infrastructure.ps1    # Deployment automation
├── cleanup-aws-infrastructure.ps1   # Cleanup automation
├── Jenkinsfile                      # CI/CD orchestrator
├── user-service/
│   ├── app.py                       # User management API
│   ├── Dockerfile
│   ├── Jenkinsfile                  # Service-specific CI/CD
│   └── requirements.txt
├── course-service/                  # Course management
├── enrollment-service/              # Enrollment handling
├── payment-service/                 # Payment processing
├── notification-service/            # Notifications
└── swagger-ui/                      # API Gateway
```

---

## 🎓 For Academic Use

This project is designed for academic CI/CD demonstrations. Key learning objectives:

1. **Infrastructure as Code** - Automated deployment scripts
2. **Microservices Architecture** - Loosely coupled services
3. **Container Orchestration** - ECS Fargate management
4. **Service Discovery** - Cloud Map DNS
5. **CI/CD Pipeline** - Jenkins automation
6. **Cloud-Native Development** - AWS-native services

---

## 📝 License

This project is for academic/educational purposes.

---

## ✅ Checklist

Before presenting:
- [ ] Run deployment script
- [ ] Build and push all Docker images
- [ ] Verify services are running
- [ ] Test API endpoints via Swagger UI
- [ ] Demonstrate CI/CD pipeline
- [ ] Run cleanup script
- [ ] Verify $0.00 AWS bill

---

**Need Help?** Check the troubleshooting section or AWS CloudWatch logs for detailed error messages.

