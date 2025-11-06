from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI(
    title="Online Learning Portal - API Gateway",
    description="Unified API Gateway for all microservices",
    version="1.0.0"
)

SERVICES = {
    "user-service": os.getenv("USER_SERVICE_URL", "http://user-service:8080"),
    "course-service": os.getenv("COURSE_SERVICE_URL", "http://course-service:8080"),
    "enrollment-service": os.getenv("ENROLLMENT_SERVICE_URL", "http://enrollment-service:8080"),
    "payment-service": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8080"),
    "notification-service": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8080"),
}

@app.get("/")
def index():
    return {
        "gateway": "Online Learning Portal",
        "version": "1.0.0",
        "services": list(SERVICES.keys()),
        "docs": "/docs",
        "message": "API Gateway running - visit /docs for unified API documentation"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/services/health")
async def check_all_services():
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json()
                }
            except Exception as e:
                results[service_name] = {"status": "unreachable", "error": str(e)}
    return results

@app.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['user-service']}/")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"user-service unreachable: {str(e)}")

@app.get("/courses")
async def get_courses():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['course-service']}/")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"course-service unreachable: {str(e)}")

@app.get("/enrollments")
async def get_enrollments():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['enrollment-service']}/")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"enrollment-service unreachable: {str(e)}")

@app.get("/payments")
async def get_payments():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['payment-service']}/")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"payment-service unreachable: {str(e)}")

@app.get("/notifications")
async def get_notifications():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['notification-service']}/")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"notification-service unreachable: {str(e)}")

