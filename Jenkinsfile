pipeline {
    agent any

    stages {
        stage('Deploy to EKS') {
            steps {
                withCredentials([string(credentialsId: 'k8s-token', variable: 'TOKEN')]) {
                    sh '''
                    cat <<'EOF' > kubeconfig.yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://185D5289E0331C94BA526E07B255872C.sk1.us-east-2.eks.amazonaws.com
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
    token: ${TOKEN}
EOF

                    export KUBECONFIG=$(pwd)/kubeconfig.yaml
                    kubectl create ns web-apps --dry-run=client -o yaml | kubectl apply -f -
                    kubectl apply -f k8s/
                    kubectl get svc -n web-apps
                    '''
                }
            }
        }
    }
}
