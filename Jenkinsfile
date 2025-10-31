pipeline {
    agent any

    stages {
        stage('Deploy to EKS') {
            steps {
                sh '''
                aws eks update-kubeconfig --region us-east-2 --name assignment5-cluster
                kubectl create ns web-apps --dry-run=client -o yaml | kubectl apply -f -
                kubectl apply -f k8s/
                kubectl get svc -n web-apps
                '''
            }
        }

    }
}
