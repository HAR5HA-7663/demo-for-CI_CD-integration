pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-2'
        ECR_REPO = '037931886697.dkr.ecr.us-east-2.amazonaws.com'
        CLUSTER_NAME = 'online-learning-portal'
    }

    stages {
        stage('Build and Push Swagger UI') {
            steps {
                sh '''
                echo "=========================================="
                echo "Building Swagger UI Docker Image"
                echo "=========================================="
                
                cd swagger-ui
                # Pull correct platform base image first
                docker pull --platform linux/amd64 python:3.10-slim
                docker build --platform linux/amd64 --pull -t swagger-ui:latest .
                docker tag swagger-ui:latest $ECR_REPO/swagger-ui:latest
                
                echo "Authenticating to ECR..."
                aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
                
                echo "Pushing swagger-ui image to ECR..."
                docker push $ECR_REPO/swagger-ui:latest
                
                echo "SUCCESS: Swagger UI image pushed to ECR"
                '''
            }
        }
        
        stage('Force Redeploy All ECS Services') {
            steps {
                sh '''
                echo "=========================================="
                echo "Global ECS Redeploy Orchestrator"
                echo "Forces all services to pull latest images from ECR"
                echo "=========================================="
                echo ""
                
                for service in user-service course-service enrollment-service payment-service notification-service swagger-ui
                do
                    echo "Redeploying $service..."
                    
                    if ! aws ecs describe-services --cluster $CLUSTER_NAME --services $service --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
                        echo "  WARNING: $service not found or inactive"
                        continue
                    fi
                    
                    aws ecs update-service --cluster $CLUSTER_NAME --service $service --force-new-deployment --region $AWS_REGION > /dev/null
                    echo "  SUCCESS: Deployment triggered for $service"
                done
                
                echo ""
                echo "=========================================="
                echo "Active Services:"
                aws ecs list-services --cluster $CLUSTER_NAME --region $AWS_REGION --query 'serviceArns[*]' --output text | sed 's/.*\\///g'
                echo "=========================================="
                '''
            }
        }
    }
}
