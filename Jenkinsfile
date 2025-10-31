pipeline {
    agent any

    stages {
        stage('Deploy to EKS') {
            steps {
                withCredentials([string(credentialsId: 'k8s-token', variable: 'TOKEN')]) {
                    sh '''
                    echo "apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://<EKS_API_URL>
    insecure-skip-tls-verify: true
  name: eks
contexts:
- context:
    cluster: eks
    user: jenkins
    namespace: web-apps
  name: eks
current-context: eks
users:
- name: jenkins
  user:
    token: $TOKEN" > kubeconfig

                    export KUBECONFIG=$PWD/kubeconfig
                    kubectl apply -f k8s/
                    kubectl get svc -n web-apps
                    '''
                }
            }
        }
    }
}

