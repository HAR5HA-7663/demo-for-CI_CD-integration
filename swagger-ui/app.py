from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI(
    title="Online Learning Portal - API Gateway",
    description="Unified API Gateway for all microservices",
    version="1.0.0"
)

SERVICES = {
    "user-service": "http://user-service.learning-portal.local:8080",
    "course-service": "http://course-service.learning-portal.local:8080",
    "enrollment-service": "http://enrollment-service.learning-portal.local:8080",
    "payment-service": "http://payment-service.learning-portal.local:8080",
    "notification-service": "http://notification-service.learning-portal.local:8080",
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

@app.get("/courses/list")
async def list_courses():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['course-service']}/courses")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"course-service unreachable: {str(e)}")

@app.post("/courses/upload")
async def upload_course_file(
    file: UploadFile = File(...),
    username: str = Form(...)
):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            file_content = await file.read()
            files = {"file": (file.filename, file_content, file.content_type)}
            data = {"username": username}
            response = await client.post(
                f"{SERVICES['course-service']}/courses/upload",
                files=files,
                data=data
            )
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

