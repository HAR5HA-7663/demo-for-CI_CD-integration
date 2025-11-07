# ============================================================================
# Online Learning Portal - Complete AWS Infrastructure Deployment Script
# ============================================================================
# This script deploys the entire microservices infrastructure to AWS ECS
# ============================================================================

param(
    [string]$ProfileName = "",
    [string]$Region = "us-east-2"
)

# Color output functions
function Write-Success { param([string]$Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param([string]$Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param([string]$Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "✗ $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Magenta ; Write-Host " $Message" -ForegroundColor Magenta ; Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta }

# ============================================================================
# Step 1: AWS CLI Configuration
# ============================================================================
Write-Header "AWS CLI Configuration"

if (-not $ProfileName) {
    Write-Info "No profile specified. Let's configure AWS CLI..."
    Write-Host ""
    Write-Host "Do you want to:" -ForegroundColor Yellow
    Write-Host "  1. Use an existing AWS CLI profile" -ForegroundColor White
    Write-Host "  2. Create a new AWS CLI profile" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1 or 2)"
    
    if ($choice -eq "2") {
        Write-Info "Creating new AWS CLI profile..."
        Write-Host ""
        $ProfileName = Read-Host "Enter a name for your new profile"
        Write-Host ""
        Write-Info "Please enter your AWS credentials:"
        $accessKey = Read-Host "AWS Access Key ID"
        $secretKey = Read-Host "AWS Secret Access Key" -AsSecureString
        $secretKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretKey))
        
        # Configure AWS CLI
        aws configure set aws_access_key_id $accessKey --profile $ProfileName
        aws configure set aws_secret_access_key $secretKeyPlain --profile $ProfileName
        aws configure set region $Region --profile $ProfileName
        aws configure set output json --profile $ProfileName
        
        Write-Success "AWS CLI profile '$ProfileName' created successfully"
    }
    else {
        Write-Info "Available AWS CLI profiles:"
        aws configure list-profiles
        Write-Host ""
        $ProfileName = Read-Host "Enter the profile name to use"
    }
}

# Verify AWS CLI configuration
Write-Info "Verifying AWS credentials for profile '$ProfileName'..."
try {
    $accountId = aws sts get-caller-identity --profile $ProfileName --query Account --output text 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to authenticate with AWS. Please check your credentials."
        exit 1
    }
    Write-Success "Authenticated successfully!"
    Write-Info "AWS Account ID: $accountId"
    Write-Info "Region: $Region"
}
catch {
    Write-Error "Error verifying AWS credentials: $_"
    exit 1
}

Write-Host ""
$confirm = Read-Host "Proceed with deployment? (yes/no)"
if ($confirm -ne "yes") {
    Write-Warning "Deployment cancelled."
    exit 0
}

# ============================================================================
# Configuration Variables
# ============================================================================
$CLUSTER_NAME = "online-learning-portal"
$SERVICES = @('user-service', 'course-service', 'enrollment-service', 'payment-service', 'notification-service', 'swagger-ui')
$NAMESPACE_NAME = "learning-portal.local"
$SECURITY_GROUP_NAME = "online-learning-portal-sg"
$ECR_REPO_URI = "$accountId.dkr.ecr.$Region.amazonaws.com"

# ============================================================================
# Step 2: Create IAM Roles
# ============================================================================
Write-Header "Creating IAM Roles"

# Create ECS Task Execution Role
Write-Info "Creating ecsTaskExecutionRole..."
$executionRoleTrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$executionRoleTrustPolicy | Out-File -FilePath "execution-role-trust.json" -Encoding utf8
$executionRoleExists = aws iam get-role --role-name ecsTaskExecutionRole --profile $ProfileName 2>$null
if (-not $executionRoleExists) {
    aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://execution-role-trust.json --profile $ProfileName --no-cli-pager | Out-Null
    aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --profile $ProfileName
    Write-Success "ecsTaskExecutionRole created"
}
else {
    Write-Info "ecsTaskExecutionRole already exists"
}
Remove-Item "execution-role-trust.json" -Force

# Create ECS Task Role (for DynamoDB access)
Write-Info "Creating ecsTaskRole..."
$taskRoleTrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$taskRoleTrustPolicy | Out-File -FilePath "task-role-trust.json" -Encoding utf8
$taskRoleExists = aws iam get-role --role-name ecsTaskRole --profile $ProfileName 2>$null
if (-not $taskRoleExists) {
    aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file://task-role-trust.json --profile $ProfileName --no-cli-pager | Out-Null
    
    # Create DynamoDB policy
    $dynamoPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:${Region}:${accountId}:table/learning-portal-*"
    }
  ]
}
"@
    $dynamoPolicy | Out-File -FilePath "dynamodb-policy.json" -Encoding utf8
    aws iam put-role-policy --role-name ecsTaskRole --policy-name DynamoDBAccess --policy-document file://dynamodb-policy.json --profile $ProfileName
    Write-Success "ecsTaskRole created with DynamoDB access"
    Remove-Item "dynamodb-policy.json" -Force
}
else {
    Write-Info "ecsTaskRole already exists"
}
Remove-Item "task-role-trust.json" -Force

Start-Sleep -Seconds 5

# ============================================================================
# Step 3: Get VPC Information
# ============================================================================
Write-Header "Getting VPC Configuration"

Write-Info "Fetching default VPC..."
$vpcId = aws ec2 describe-vpcs --profile $ProfileName --region $Region --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text
Write-Info "VPC ID: $vpcId"

Write-Info "Fetching subnets..."
$subnets = aws ec2 describe-subnets --profile $ProfileName --region $Region --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[*].SubnetId" --output text
$subnetList = $subnets -split '\s+'
Write-Info "Found $($subnetList.Count) subnets"

# ============================================================================
# Step 4: Create Security Group
# ============================================================================
Write-Header "Creating Security Group"

$sgExists = aws ec2 describe-security-groups --profile $ProfileName --region $Region --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($sgExists -and $sgExists -ne "None") {
    $securityGroupId = $sgExists
    Write-Info "Security group already exists: $securityGroupId"
}
else {
    Write-Info "Creating security group..."
    $securityGroupId = aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description "Security group for Online Learning Portal" --vpc-id $vpcId --profile $ProfileName --region $Region --query "GroupId" --output text
    
    # Allow all traffic within security group
    aws ec2 authorize-security-group-ingress --group-id $securityGroupId --protocol tcp --port 8080 --source-group $securityGroupId --profile $ProfileName --region $Region 2>$null | Out-Null
    
    # Allow HTTP from anywhere for swagger-ui
    aws ec2 authorize-security-group-ingress --group-id $securityGroupId --protocol tcp --port 8080 --cidr 0.0.0.0/0 --profile $ProfileName --region $Region 2>$null | Out-Null
    
    Write-Success "Security group created: $securityGroupId"
}

# ============================================================================
# Step 5: Create DynamoDB Tables
# ============================================================================
Write-Header "Creating DynamoDB Tables"

# Users Table
Write-Info "Creating learning-portal-users table..."
$usersTableExists = aws dynamodb describe-table --table-name learning-portal-users --profile $ProfileName --region $Region 2>$null
if (-not $usersTableExists) {
    aws dynamodb create-table `
        --table-name learning-portal-users `
        --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=email,AttributeType=S `
        --key-schema AttributeName=user_id,KeyType=HASH `
        --global-secondary-indexes "IndexName=EmailIndex,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
        --billing-mode PAY_PER_REQUEST `
        --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "learning-portal-users table created"
}
else {
    Write-Info "learning-portal-users table already exists"
}

# Courses Table
Write-Info "Creating learning-portal-courses table..."
$coursesTableExists = aws dynamodb describe-table --table-name learning-portal-courses --profile $ProfileName --region $Region 2>$null
if (-not $coursesTableExists) {
    aws dynamodb create-table `
        --table-name learning-portal-courses `
        --attribute-definitions AttributeName=course_id,AttributeType=S `
        --key-schema AttributeName=course_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "learning-portal-courses table created"
}
else {
    Write-Info "learning-portal-courses table already exists"
}

# Enrollments Table
Write-Info "Creating learning-portal-enrollments table..."
$enrollmentsTableExists = aws dynamodb describe-table --table-name learning-portal-enrollments --profile $ProfileName --region $Region 2>$null
if (-not $enrollmentsTableExists) {
    aws dynamodb create-table `
        --table-name learning-portal-enrollments `
        --attribute-definitions AttributeName=enrollment_id,AttributeType=S AttributeName=user_id,AttributeType=S `
        --key-schema AttributeName=enrollment_id,KeyType=HASH `
        --global-secondary-indexes "IndexName=UserIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
        --billing-mode PAY_PER_REQUEST `
        --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "learning-portal-enrollments table created"
}
else {
    Write-Info "learning-portal-enrollments table already exists"
}

# Payments Table
Write-Info "Creating learning-portal-payments table..."
$paymentsTableExists = aws dynamodb describe-table --table-name learning-portal-payments --profile $ProfileName --region $Region 2>$null
if (-not $paymentsTableExists) {
    aws dynamodb create-table `
        --table-name learning-portal-payments `
        --attribute-definitions AttributeName=payment_id,AttributeType=S `
        --key-schema AttributeName=payment_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "learning-portal-payments table created"
}
else {
    Write-Info "learning-portal-payments table already exists"
}

# Notifications Table
Write-Info "Creating learning-portal-notifications table..."
$notificationsTableExists = aws dynamodb describe-table --table-name learning-portal-notifications --profile $ProfileName --region $Region 2>$null
if (-not $notificationsTableExists) {
    aws dynamodb create-table `
        --table-name learning-portal-notifications `
        --attribute-definitions AttributeName=notification_id,AttributeType=S `
        --key-schema AttributeName=notification_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "learning-portal-notifications table created"
}
else {
    Write-Info "learning-portal-notifications table already exists"
}

Write-Info "Waiting for DynamoDB tables to become active..."
Start-Sleep -Seconds 10

# ============================================================================
# Step 6: Create ECR Repositories
# ============================================================================
Write-Header "Creating ECR Repositories"

foreach ($service in $SERVICES) {
    Write-Info "Creating ECR repository for $service..."
    $repoExists = aws ecr describe-repositories --repository-names $service --profile $ProfileName --region $Region 2>$null
    if (-not $repoExists) {
        aws ecr create-repository --repository-name $service --profile $ProfileName --region $Region --no-cli-pager | Out-Null
        Write-Success "$service repository created"
    }
    else {
        Write-Info "$service repository already exists"
    }
}

# ============================================================================
# Step 7: Create ECS Cluster
# ============================================================================
Write-Header "Creating ECS Cluster"

$clusterExists = aws ecs describe-clusters --clusters $CLUSTER_NAME --profile $ProfileName --region $Region --query "clusters[0].status" --output text 2>$null
if ($clusterExists -eq "ACTIVE") {
    Write-Info "ECS cluster already exists: $CLUSTER_NAME"
}
else {
    Write-Info "Creating ECS cluster..."
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Write-Success "ECS cluster created: $CLUSTER_NAME"
}

# ============================================================================
# Step 8: Create CloudWatch Log Groups
# ============================================================================
Write-Header "Creating CloudWatch Log Groups"

foreach ($service in $SERVICES) {
    $logGroup = "/ecs/$service"
    Write-Info "Creating log group: $logGroup..."
    $logExists = aws logs describe-log-groups --log-group-name-prefix $logGroup --profile $ProfileName --region $Region 2>$null
    if (-not $logExists -or $logExists -eq "[]") {
        aws logs create-log-group --log-group-name $logGroup --profile $ProfileName --region $Region 2>$null | Out-Null
        Write-Success "$logGroup created"
    }
    else {
        Write-Info "$logGroup already exists"
    }
}

# ============================================================================
# Step 9: Create Cloud Map Namespace for Service Discovery
# ============================================================================
Write-Header "Creating Cloud Map Namespace"

$namespaceExists = aws servicediscovery list-namespaces --profile $ProfileName --region $Region --query "Namespaces[?Name=='$NAMESPACE_NAME'].Id" --output text 2>$null
if ($namespaceExists) {
    $namespaceId = $namespaceExists
    Write-Info "Cloud Map namespace already exists: $NAMESPACE_NAME"
}
else {
    Write-Info "Creating Cloud Map namespace..."
    $operationId = aws servicediscovery create-private-dns-namespace `
        --name $NAMESPACE_NAME `
        --vpc $vpcId `
        --profile $ProfileName --region $Region `
        --query "OperationId" --output text
    
    Write-Info "Waiting for namespace creation..."
    Start-Sleep -Seconds 15
    
    $namespaceId = aws servicediscovery list-namespaces --profile $ProfileName --region $Region --query "Namespaces[?Name=='$NAMESPACE_NAME'].Id" --output text
    Write-Success "Cloud Map namespace created: $NAMESPACE_NAME"
}

# ============================================================================
# Step 10: Register Task Definitions
# ============================================================================
Write-Header "Registering ECS Task Definitions"

foreach ($service in $SERVICES) {
    Write-Info "Registering task definition for $service..."
    
    $taskDef = @"
{
  "family": "$service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "$service",
      "image": "${ECR_REPO_URI}/${service}:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$service",
          "awslogs-region": "$Region",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
"@
    
    $taskDef | Out-File -FilePath "$service-task-def.json" -Encoding utf8
    aws ecs register-task-definition --cli-input-json file://$service-task-def.json --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    Remove-Item "$service-task-def.json" -Force
    Write-Success "$service task definition registered"
}

# ============================================================================
# Step 11: Create Service Discovery Services
# ============================================================================
Write-Header "Creating Service Discovery Services"

$serviceDiscoveryIds = @{}

foreach ($service in $SERVICES) {
    if ($service -eq "swagger-ui") {
        continue  # Skip service discovery for swagger-ui
    }
    
    Write-Info "Creating service discovery for $service..."
    $sdServiceExists = aws servicediscovery list-services --profile $ProfileName --region $Region --query "Services[?Name=='$service'].Id" --output text 2>$null
    
    if ($sdServiceExists) {
        $serviceDiscoveryIds[$service] = $sdServiceExists
        Write-Info "$service service discovery already exists"
    }
    else {
        $sdServiceId = aws servicediscovery create-service `
            --name $service `
            --dns-config "NamespaceId=$namespaceId,DnsRecords=[{Type=A,TTL=60}]" `
            --health-check-custom-config FailureThreshold=1 `
            --profile $ProfileName --region $Region `
            --query "Service.Id" --output text
        
        $serviceDiscoveryIds[$service] = $sdServiceId
        Write-Success "$service service discovery created"
    }
}

# ============================================================================
# Step 12: Create ECS Services
# ============================================================================
Write-Header "Creating ECS Services"

Write-Warning "NOTE: Services will fail to start initially because no Docker images exist yet."
Write-Warning "You need to push Docker images to ECR before services can run successfully."
Write-Host ""

$subnetString = ($subnetList -join ',')

foreach ($service in $SERVICES) {
    Write-Info "Creating ECS service for $service..."
    
    $serviceExists = aws ecs describe-services --cluster $CLUSTER_NAME --services $service --profile $ProfileName --region $Region --query "services[0].status" --output text 2>$null
    
    if ($serviceExists -eq "ACTIVE") {
        Write-Info "$service ECS service already exists"
        continue
    }
    
    if ($service -eq "swagger-ui") {
        # Swagger UI without service discovery
        aws ecs create-service `
            --cluster $CLUSTER_NAME `
            --service-name $service `
            --task-definition $service `
            --desired-count 1 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[$subnetString],securityGroups=[$securityGroupId],assignPublicIp=ENABLED}" `
            --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    }
    else {
        # Other services with service discovery
        $sdId = $serviceDiscoveryIds[$service]
        aws ecs create-service `
            --cluster $CLUSTER_NAME `
            --service-name $service `
            --task-definition $service `
            --desired-count 1 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[$subnetString],securityGroups=[$securityGroupId],assignPublicIp=ENABLED}" `
            --service-registries "registryArn=arn:aws:servicediscovery:${Region}:${accountId}:service/$sdId" `
            --profile $ProfileName --region $Region --no-cli-pager | Out-Null
    }
    
    Write-Success "$service ECS service created"
}

# ============================================================================
# Step 13: Display Summary
# ============================================================================
Write-Header "Deployment Complete!"

Write-Host ""
Write-Success "All AWS infrastructure has been created successfully!"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "AWS Account: $accountId" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Profile: $ProfileName" -ForegroundColor White
Write-Host ""
Write-Host "CREATED RESOURCES:" -ForegroundColor Yellow
Write-Host "  ✓ ECS Cluster: $CLUSTER_NAME" -ForegroundColor Green
Write-Host "  ✓ ECS Services: 6 (user, course, enrollment, payment, notification, swagger-ui)" -ForegroundColor Green
Write-Host "  ✓ DynamoDB Tables: 5 (all learning-portal-* tables)" -ForegroundColor Green
Write-Host "  ✓ ECR Repositories: 6 (all service repositories)" -ForegroundColor Green
Write-Host "  ✓ CloudWatch Log Groups: 6" -ForegroundColor Green
Write-Host "  ✓ Cloud Map Namespace: $NAMESPACE_NAME" -ForegroundColor Green
Write-Host "  ✓ Security Group: $securityGroupId" -ForegroundColor Green
Write-Host "  ✓ IAM Roles: ecsTaskExecutionRole, ecsTaskRole" -ForegroundColor Green
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Warning "IMPORTANT NEXT STEPS:"
Write-Host ""
Write-Host "1. Build and push Docker images to ECR:" -ForegroundColor Yellow
Write-Host "   - Authenticate: aws ecr get-login-password --region $Region --profile $ProfileName | docker login --username AWS --password-stdin $ECR_REPO_URI" -ForegroundColor White
Write-Host "   - Build: docker build -t <service-name> ." -ForegroundColor White
Write-Host "   - Tag: docker tag <service-name>:latest $ECR_REPO_URI/<service-name>:latest" -ForegroundColor White
Write-Host "   - Push: docker push $ECR_REPO_URI/<service-name>:latest" -ForegroundColor White
Write-Host ""
Write-Host "2. Configure Jenkins CI/CD pipeline to automate builds and deployments" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Get Swagger UI public URL:" -ForegroundColor Yellow
Write-Host "   aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks `$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name swagger-ui --query 'taskArns[0]' --output text --profile $ProfileName --region $Region) --query 'tasks[0].attachments[0].details[?name==``networkInterfaceId``].value' --output text --profile $ProfileName --region $Region" -ForegroundColor White
Write-Host ""
Write-Host "4. Monitor deployment:" -ForegroundColor Yellow
Write-Host "   aws ecs list-services --cluster $CLUSTER_NAME --profile $ProfileName --region $Region" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Success "Deployment script completed successfully!"
Write-Host ""

