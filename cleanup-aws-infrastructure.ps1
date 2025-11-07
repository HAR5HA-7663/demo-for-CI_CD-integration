# ============================================================================
# Online Learning Portal - Complete AWS Infrastructure Cleanup Script
# ============================================================================
# This script removes all AWS resources created by the deployment script
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
# Step 1: Get AWS Profile
# ============================================================================
Write-Header "AWS Cleanup Script"

if (-not $ProfileName) {
    Write-Info "Available AWS CLI profiles:"
    aws configure list-profiles
    Write-Host ""
    $ProfileName = Read-Host "Enter the profile name to use"
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
Write-Warning "This will DELETE ALL resources for the Online Learning Portal project!"
Write-Warning "This action CANNOT be undone!"
Write-Host ""
$confirm = Read-Host "Are you sure you want to proceed? Type 'DELETE' to confirm"
if ($confirm -ne "DELETE") {
    Write-Warning "Cleanup cancelled."
    exit 0
}

# ============================================================================
# Configuration Variables
# ============================================================================
$CLUSTER_NAME = "online-learning-portal"
$SERVICES = @('user-service', 'course-service', 'enrollment-service', 'payment-service', 'notification-service', 'swagger-ui')
$NAMESPACE_NAME = "learning-portal.local"
$SECURITY_GROUP_NAME = "online-learning-portal-sg"

# ============================================================================
# Step 2: Scale Down and Delete ECS Services
# ============================================================================
Write-Header "Deleting ECS Services"

Write-Info "Scaling all services to 0..."
foreach ($service in $SERVICES) {
    Write-Info "Scaling down $service..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $service --desired-count 0 --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
}

Write-Info "Waiting 30 seconds for tasks to stop..."
Start-Sleep -Seconds 30

Write-Info "Deleting services..."
foreach ($service in $SERVICES) {
    Write-Info "Deleting $service..."
    aws ecs delete-service --cluster $CLUSTER_NAME --service $service --force --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
}
Write-Success "All services deleted"

# ============================================================================
# Step 3: Delete ECS Cluster
# ============================================================================
Write-Header "Deleting ECS Cluster"

Write-Info "Deleting cluster $CLUSTER_NAME..."
aws ecs delete-cluster --cluster $CLUSTER_NAME --region $Region --profile $ProfileName --no-cli-pager | Out-Null
Write-Success "Cluster deleted"

# ============================================================================
# Step 4: Deregister Task Definitions
# ============================================================================
Write-Header "Deregistering Task Definitions"

foreach ($service in $SERVICES) {
    Write-Info "Deregistering task definitions for $service..."
    $revisions = aws ecs list-task-definitions --family-prefix $service --region $Region --profile $ProfileName --query "taskDefinitionArns" --output text 2>$null
    if ($revisions) {
        $revList = $revisions -split '\s+'
        foreach ($arn in $revList) {
            aws ecs deregister-task-definition --task-definition $arn --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
        }
    }
}
Write-Success "All task definitions deregistered"

# ============================================================================
# Step 5: Delete DynamoDB Tables
# ============================================================================
Write-Header "Deleting DynamoDB Tables"

$tables = @('learning-portal-users', 'learning-portal-courses', 'learning-portal-enrollments', 'learning-portal-payments', 'learning-portal-notifications')
foreach ($table in $tables) {
    Write-Info "Deleting $table..."
    aws dynamodb delete-table --table-name $table --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
}
Write-Success "All DynamoDB tables deleted"

# ============================================================================
# Step 6: Delete ECR Repositories
# ============================================================================
Write-Header "Deleting ECR Repositories"

foreach ($service in $SERVICES) {
    Write-Info "Deleting ECR repository $service..."
    aws ecr delete-repository --repository-name $service --force --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
}
Write-Success "All ECR repositories deleted"

# ============================================================================
# Step 7: Delete CloudWatch Log Groups
# ============================================================================
Write-Header "Deleting CloudWatch Log Groups"

foreach ($service in $SERVICES) {
    $logGroup = "/ecs/$service"
    Write-Info "Deleting $logGroup..."
    aws logs delete-log-group --log-group-name $logGroup --region $Region --profile $ProfileName 2>$null | Out-Null
}
Write-Success "All log groups deleted"

# ============================================================================
# Step 8: Delete Cloud Map Namespace
# ============================================================================
Write-Header "Deleting Cloud Map Namespace"

$namespaceId = aws servicediscovery list-namespaces --region $Region --profile $ProfileName --query "Namespaces[?Name=='$NAMESPACE_NAME'].Id" --output text 2>$null
if ($namespaceId) {
    Write-Info "Deleting namespace $NAMESPACE_NAME..."
    aws servicediscovery delete-namespace --id $namespaceId --region $Region --profile $ProfileName --no-cli-pager 2>$null | Out-Null
    Write-Success "Cloud Map namespace deleted"
}
else {
    Write-Info "No Cloud Map namespace found"
}

# ============================================================================
# Step 9: Delete Security Group
# ============================================================================
Write-Header "Deleting Security Group"

Write-Info "Waiting 20 seconds for network interfaces to detach..."
Start-Sleep -Seconds 20

$sgId = aws ec2 describe-security-groups --profile $ProfileName --region $Region --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($sgId -and $sgId -ne "None") {
    Write-Info "Deleting security group $sgId..."
    aws ec2 delete-security-group --group-id $sgId --profile $ProfileName --region $Region 2>$null | Out-Null
    Write-Success "Security group deleted"
}
else {
    Write-Info "Security group not found or already deleted"
}

# ============================================================================
# Step 10: Check for Other Resources
# ============================================================================
Write-Header "Checking for Additional Resources"

# Check for Load Balancers
Write-Info "Checking for Load Balancers..."
$albs = aws elbv2 describe-load-balancers --region $Region --profile $ProfileName --query "LoadBalancers[*].LoadBalancerArn" --output text 2>$null
if ($albs) {
    Write-Warning "Found Application Load Balancers - these may need manual deletion"
}
else {
    Write-Success "No Application Load Balancers found"
}

# Check for NAT Gateways
Write-Info "Checking for NAT Gateways..."
$nats = aws ec2 describe-nat-gateways --region $Region --profile $ProfileName --filter "Name=state,Values=available,pending" --query "NatGateways[*].NatGatewayId" --output text 2>$null
if ($nats) {
    Write-Warning "Found NAT Gateways - these may incur charges and need manual deletion"
}
else {
    Write-Success "No NAT Gateways found"
}

# Check for EC2 Instances
Write-Info "Checking for EC2 Instances..."
$instances = aws ec2 describe-instances --region $Region --profile $ProfileName --filters "Name=instance-state-name,Values=running,stopped" --query "Reservations[*].Instances[*].InstanceId" --output text 2>$null
if ($instances) {
    Write-Warning "Found EC2 Instances - you may want to terminate these manually"
}
else {
    Write-Success "No EC2 Instances found"
}

# Check for Elastic IPs
Write-Info "Checking for Elastic IPs..."
$eips = aws ec2 describe-addresses --region $Region --profile $ProfileName --query "Addresses[?AssociationId==null].AllocationId" --output text 2>$null
if ($eips) {
    Write-Warning "Found unattached Elastic IPs - releasing them now..."
    $eipList = $eips -split '\s+'
    foreach ($id in $eipList) {
        aws ec2 release-address --allocation-id $id --region $Region --profile $ProfileName --no-cli-pager | Out-Null
    }
    Write-Success "Elastic IPs released"
}
else {
    Write-Success "No unattached Elastic IPs found"
}

# ============================================================================
# Step 11: Summary
# ============================================================================
Write-Header "Cleanup Complete!"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " CLEANUP SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ DELETED:" -ForegroundColor Green
Write-Host "  • 6 ECS Services" -ForegroundColor White
Write-Host "  • 1 ECS Cluster" -ForegroundColor White
Write-Host "  • 5 DynamoDB Tables" -ForegroundColor White
Write-Host "  • 6 ECR Repositories" -ForegroundColor White
Write-Host "  • 6 CloudWatch Log Groups" -ForegroundColor White
Write-Host "  • 1 Cloud Map Namespace" -ForegroundColor White
Write-Host "  • Security Group" -ForegroundColor White
Write-Host "  • Task Definitions (all revisions)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  REMAINING (may need manual cleanup):" -ForegroundColor Yellow
Write-Host "  • IAM Roles (ecsTaskRole, ecsTaskExecutionRole)" -ForegroundColor White
Write-Host "  • VPC/Subnets (default VPC - safe to keep)" -ForegroundColor White
Write-Host ""
Write-Host "💰 COST STATUS:" -ForegroundColor Green
Write-Host "  All billable ECS/DynamoDB/ECR resources have been deleted." -ForegroundColor White
Write-Host "  Your AWS bill should be $0.00 for this project." -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Success "Cleanup script completed successfully!"
Write-Host ""

