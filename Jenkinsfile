pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-2'
        ECR_REPO = '037931886697.dkr.ecr.us-east-2.amazonaws.com'
        SERVICE_NAME = "${env.BRANCH_NAME}"
        CLUSTER_NAME = 'online-learning-portal'
    }

    stages {
        stage('Run Tests') {
            steps {
                sh '''
                echo "Running unit tests for $SERVICE_NAME"
                cd user-service
                python3 -m pip install --no-cache-dir -r requirements.txt --user
                python3 -m pytest test_app.py -v --tb=short
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                echo "Building Docker image for $SERVICE_NAME"
                cd user-service
                # Setup buildx for cross-platform builds with AMD64 support
                docker buildx use multiarch 2>/dev/null || docker buildx create --name multiarch --use --driver docker-container --platform linux/amd64,linux/arm64
                docker buildx inspect --bootstrap
                # Build for linux/amd64 and load locally
                docker buildx build --platform linux/amd64 --load -t $SERVICE_NAME .
                docker tag $SERVICE_NAME:latest $ECR_REPO/$SERVICE_NAME:latest
                '''
            }
        }

        stage('Push to ECR') {
            steps {
                sh '''
                echo "Authenticating to AWS ECR..."
                aws ecr get-login-password --region $AWS_REGION | \
                docker login --username AWS --password-stdin $ECR_REPO

                echo "Pushing image to ECR..."
                docker push $ECR_REPO/$SERVICE_NAME:latest
                '''
            }
        }

        stage('Deploy to ECS') {
            steps {
                sh '''
                echo "Deploying $SERVICE_NAME to ECS Fargate..."
                
                # Create task definition with correct roles and latest image
                cat > task-def.json << EOF
{
  "family": "$SERVICE_NAME",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::037931886697:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::037931886697:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "$SERVICE_NAME",
      "image": "$ECR_REPO/$SERVICE_NAME:latest",
      "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$SERVICE_NAME",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF
                
                aws ecs register-task-definition --cli-input-json file://task-def.json --region $AWS_REGION
                
                # Update service if exists
                SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")
                
                if [ "$SERVICE_EXISTS" != "MISSING" ] && [ "$SERVICE_EXISTS" != "None" ]; then
                    echo "Updating ECS service with new task definition..."
                    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION
                    echo "Deployment triggered successfully!"
                else
                    echo "WARNING: Service $SERVICE_NAME does not exist in cluster $CLUSTER_NAME"
                    echo "Please create the service manually in AWS ECS console first"
                fi
                '''
            }
        }
    }
}
