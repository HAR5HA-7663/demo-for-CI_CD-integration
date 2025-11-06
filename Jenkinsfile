pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-2'
        CLUSTER_NAME = 'online-learning-portal'
    }

    stages {
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
                aws ecs list-services --cluster $CLUSTER_NAME --region $AWS_REGION --query 'serviceArns[*]' --output text | sed 's/.*\///g'
                echo "=========================================="
                '''
            }
        }
    }
}
