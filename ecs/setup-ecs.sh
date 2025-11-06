#!/bin/bash

# ECS Setup Script for Online Learning Portal
# Run this once to create ECS cluster and services

set -e

AWS_REGION="us-east-2"
CLUSTER_NAME="online-learning-portal"
ACCOUNT_ID="037931886697"

echo "Creating ECS Cluster: $CLUSTER_NAME"
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION

echo "Creating CloudWatch Log Groups..."
for service in user-service course-service enrollment-service payment-service notification-service swagger-ui
do
    aws logs create-log-group --log-group-name /ecs/$service --region $AWS_REGION || true
done

echo "ECS Cluster setup complete!"
echo "Next steps:"
echo "1. Create VPC and subnets (or use default)"
echo "2. Create security groups allowing port 8080"
echo "3. Run Jenkins pipelines to deploy services"

