pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-2'
        CLUSTER_NAME = 'online-learning-portal'
    }

    stages {
        stage('Deploy to ECS') {
            steps {
                sh '''
                echo "Deploying all services to ECS Fargate..."
                
                for service in user-service course-service enrollment-service payment-service notification-service swagger-ui
                do
                    echo "Deploying $service..."
                    
                    # Check if service exists
                    SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $service --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")
                    
                    if [ "$SERVICE_EXISTS" = "MISSING" ] || [ "$SERVICE_EXISTS" = "None" ]; then
                        echo "Service $service does not exist. Please create it manually first."
                    else
                        # Force new deployment
                        aws ecs update-service --cluster $CLUSTER_NAME --service $service --force-new-deployment --region $AWS_REGION
                        echo "Triggered deployment for $service"
                    fi
                done
                
                echo "Listing running services..."
                aws ecs list-services --cluster $CLUSTER_NAME --region $AWS_REGION
                '''
            }
        }
    }
}
