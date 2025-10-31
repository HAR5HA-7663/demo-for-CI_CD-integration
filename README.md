# Online Learning Portal - CI/CD Demo

A minimal microservices-based project demonstrating CI/CD automation using Jenkins, Docker, and Amazon EKS. Each microservice is independently buildable and deployable, focusing on pipeline automation rather than full backend implementation.

## Project Overview

This project consists of five microservices and one integration gateway service, all built with FastAPI. Each service exposes minimal endpoints and returns static JSON responses. The architecture is designed to demonstrate independent CI/CD pipelines for each service branch, culminating in a unified deployment to Kubernetes.

## Architecture

### Microservices

1. **user-service** - Manages mock user information
2. **course-service** - Lists mock course data
3. **enrollment-service** - Simulates course enrollment operations
4. **payment-service** - Provides mock payment processing endpoint
5. **notification-service** - Sends mock email and certificate notifications

### Gateway Service

- **swagger-ui** - API documentation aggregator and service gateway

## Directory Structure

```
online-learning-portal/
├── .gitignore
├── .cursorrules
├── README.md
├── Jenkinsfile                    # CD pipeline for main branch
│
├── user-service/                  # Service branch: user-service
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Jenkinsfile.ci             # CI pipeline
│
├── course-service/                # Service branch: course-service
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Jenkinsfile.ci
│
├── enrollment-service/            # Service branch: enrollment-service
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Jenkinsfile.ci
│
├── payment-service/               # Service branch: payment-service
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Jenkinsfile.ci
│
├── notification-service/          # Service branch: notification-service
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Jenkinsfile.ci
│
├── swagger-ui/                    # Main branch: Gateway service
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── k8s/                           # Main branch: Kubernetes manifests
    ├── user-deploy.yaml
    ├── course-deploy.yaml
    ├── enrollment-deploy.yaml
    ├── payment-deploy.yaml
    ├── notification-deploy.yaml
    └── frontend-lb.yaml
```

## Branch Structure

The repository uses a branch-per-service strategy:

- `user-service` - Contains user-service directory
- `course-service` - Contains course-service directory
- `enrollment-service` - Contains enrollment-service directory
- `payment-service` - Contains payment-service directory
- `notification-service` - Contains notification-service directory
- `main` - Contains swagger-ui, k8s manifests, and Jenkinsfile

## Prerequisites

- Docker installed and running
- Jenkins server with Multibranch Pipeline plugin
- Kubernetes cluster (Amazon EKS)
- kubectl configured for cluster access
- Docker Hub account
- Git repository with webhook support

## Setup Instructions

### 1. Configuration

Before deploying, update the following placeholders:

- Replace `<DOCKERHUB_USERNAME>` in all `Jenkinsfile.ci` files and Kubernetes manifests with your Docker Hub username
- Replace `<EKS_API_URL>` in the root `Jenkinsfile` with your EKS cluster API endpoint

### 2. Jenkins Configuration

1. Create a Multibranch Pipeline job in Jenkins
2. Point the job to this Git repository
3. Configure Git webhook to trigger builds on push events
4. Create Jenkins credentials:
   - `docker-cred` (Username with password) - Docker Hub credentials
   - `k8s-token` (Secret text) - Kubernetes service account token

### 3. Kubernetes Namespace

Create the target namespace in your EKS cluster:

```bash
kubectl create namespace web-apps
```

### 4. Local Testing

Test Docker builds locally:

```bash
cd user-service
docker build -t user-service:test .
docker run -p 8080:8080 user-service:test
```

Test FastAPI application:

```bash
cd user-service
pip install -r requirements.txt
uvicorn app:app --port 8080
```

Validate Kubernetes manifests:

```bash
kubectl apply --dry-run=client -f k8s/
```

## CI/CD Pipeline Flow

### Service Branch Pipelines (CI)

Each service branch triggers an independent CI pipeline when code is pushed:

1. **Build Stage** - Docker image is built using the service's Dockerfile
2. **Push Stage** - Image is tagged with commit hash and pushed to Docker Hub

Pipeline artifacts:

- Docker image: `docker.io/<DOCKERHUB_USERNAME>/<service-name>:<commit-hash>`

### Main Branch Pipeline (CD)

The main branch triggers the deployment pipeline:

1. **Deploy to EKS Stage** - Applies all Kubernetes manifests to the EKS cluster
   - Creates kubeconfig with service account token
   - Deploys all microservice deployments and services
   - Creates LoadBalancer service for Swagger UI gateway

## API Endpoints

Each microservice exposes the following endpoints:

- `GET /` - Returns service identification message
- `GET /health` - Returns health status

Swagger UI gateway:

- `GET /` - Returns list of all available services
- `GET /health` - Returns gateway health status

## Deployment Verification

After deployment, verify services are running:

```bash
kubectl get deployments -n web-apps
kubectl get services -n web-apps
kubectl get pods -n web-apps
```

Access the LoadBalancer endpoint to reach the Swagger UI gateway:

```bash
kubectl get svc swagger-ui -n web-apps
```

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Runtime**: Python 3.10
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Amazon EKS)
- **CI/CD**: Jenkins Multibranch Pipeline
- **Container Registry**: Docker Hub

## Notes

- All services return static JSON responses (no database required)
- Services are stateless and can be scaled horizontally
- Each service runs on port 8080 internally
- Kubernetes Services expose services on port 80
- Swagger UI gateway is exposed via LoadBalancer service

## License

This project is created for academic CI/CD demonstration purposes.
