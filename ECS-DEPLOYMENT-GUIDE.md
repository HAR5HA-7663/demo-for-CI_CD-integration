# ECS Fargate Deployment Guide

## Migration from EKS to ECS Complete

All service branches have been migrated from Amazon EKS (Kubernetes) to Amazon ECS (Fargate) for simplified deployment.

---

## What Changed

### Main Branch
- Removed `/k8s/` directory (Kubernetes manifests)
- Added `/ecs/` directory with ECS task definitions
- Updated `Jenkinsfile` for ECS deployments
- Added `ecs/setup-ecs.sh` setup script

### All Service Branches (5 branches)
- **user-service**
- **course-service**
- **enrollment-service**
- **payment-service**
- **notification-service**

Each branch's `Jenkinsfile.ci` now deploys to ECS Fargate instead of EKS.

---

## Required AWS Account Information

Before deployment, provide these details to replace placeholders:

1. **AWS Account ID** (12 digits)
   - Current placeholder: `ACCOUNT_ID`
   - Find it: AWS Console → Account Settings or run:
     ```bash
     aws sts get-caller-identity --profile ltu --query Account --output text
     ```

2. **AWS Region**
   - Current placeholder: `REGION`
   - Recommended: `us-east-2` or `us-east-1`

3. **ECS Cluster Name** (optional, default: `online-learning-portal`)

---

## Pre-Deployment Setup

### 1. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name online-learning-portal --region <REGION> --profile ltu
```

### 2. Create CloudWatch Log Groups

```bash
for service in user-service course-service enrollment-service payment-service notification-service swagger-ui
do
    aws logs create-log-group --log-group-name /ecs/$service --region <REGION> --profile ltu
done
```

### 3. Create VPC and Subnets (if needed)

Use default VPC or create new:
```bash
# Get default VPC
aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --region <REGION> --profile ltu

# Get default subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<VPC_ID>" --region <REGION> --profile ltu
```

### 4. Create Security Group

```bash
# Create security group allowing port 8080
aws ec2 create-security-group --group-name ecs-services-sg --description "Security group for ECS services" --vpc-id <VPC_ID> --region <REGION> --profile ltu

# Allow inbound traffic on port 8080
aws ec2 authorize-security-group-ingress --group-id <SG_ID> --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region <REGION> --profile ltu
```

### 5. Create ECS Services (One-Time Setup)

For each service, create an ECS service in AWS Console or CLI:

```bash
aws ecs create-service \
    --cluster online-learning-portal \
    --service-name user-service \
    --task-definition user-service:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_ID>],securityGroups=[<SG_ID>],assignPublicIp=ENABLED}" \
    --region <REGION> \
    --profile ltu
```

Repeat for: `course-service`, `enrollment-service`, `payment-service`, `notification-service`, `swagger-ui`

---

## Jenkins Configuration

### Environment Variables Required

Add to Jenkins:
```bash
AWS_PROFILE=ltu  # If using named profile
AWS_REGION=<your-region>
```

### Credentials

Store AWS credentials in Jenkins:
1. Go to Jenkins → Manage Jenkins → Credentials
2. Add AWS Access Key ID and Secret Access Key

---

## Deployment Flow

### Automatic (via Jenkins)

1. Push code to service branch (e.g., `user-service`)
2. Jenkins detects change via webhook
3. Pipeline runs:
   - Build Docker image
   - Push to ECR (auto-creates repository)
   - Register ECS task definition
   - Update ECS service (triggers deployment)

### Manual Deployment

```bash
# Build and push image
cd user-service
docker build -t user-service .
aws ecr get-login-password --region <REGION> --profile ltu | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
docker tag user-service:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/user-service:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/user-service:latest

# Update ECS service
aws ecs update-service --cluster online-learning-portal --service user-service --force-new-deployment --region <REGION> --profile ltu
```

---

## Cost Comparison

### EKS (Previous)
- Control Plane: $0.10/hour (~$73/month)
- Worker Nodes: EC2 instances
- **Total**: ~$100-150/month minimum

### ECS Fargate (Current)
- No control plane cost
- Pay only for running tasks
- 256 CPU + 512 MB memory per task
- **Cost per task**: ~$0.01/hour
- **6 services × $0.01/hour**: ~$4.30/month (running 24/7)
- **Estimated**: $5-10/month for college project

---

## Accessing Services

Services run on private IPs. For public access:

### Option 1: Application Load Balancer (Recommended)
Create ALB and target groups for each service

### Option 2: Assign Public IPs
Services already configured with `assignPublicIp=ENABLED`

Check service IPs:
```bash
aws ecs describe-tasks --cluster online-learning-portal --tasks $(aws ecs list-tasks --cluster online-learning-portal --service-name user-service --region <REGION> --profile ltu --query 'taskArns[0]' --output text) --region <REGION> --profile ltu
```

---

## Monitoring

### CloudWatch Logs
View logs in AWS Console:
- CloudWatch → Log Groups → `/ecs/<service-name>`

Or via CLI:
```bash
aws logs tail /ecs/user-service --follow --region <REGION> --profile ltu
```

### ECS Service Status
```bash
aws ecs describe-services --cluster online-learning-portal --services user-service --region <REGION> --profile ltu
```

---

## Troubleshooting

### Service Won't Start
Check task definition and logs:
```bash
aws ecs describe-task-definition --task-definition user-service --region <REGION> --profile ltu
aws logs tail /ecs/user-service --region <REGION> --profile ltu
```

### Cannot Pull Image from ECR
Ensure task execution role has ECR permissions

### Jenkins Pipeline Fails
- Verify AWS credentials in Jenkins
- Check AWS CLI is installed on Jenkins agent
- Verify `jq` is installed (required for JSON processing)

---

## Next Steps

1. **Provide AWS Account Details** (Account ID + Region)
2. I'll update all placeholders in:
   - All Jenkinsfile.ci files (5 service branches)
   - Jenkinsfile (main branch)
   - ECS task definitions (6 files)
   - Setup script
3. **Create Pull Requests** from service branches to main
4. **Pull main** to local
5. **Run setup script** to create ECS cluster
6. **Create ECS services** (one-time)
7. **Deploy via Jenkins**

Ready to proceed! Share your AWS Account ID and Region when ready.

