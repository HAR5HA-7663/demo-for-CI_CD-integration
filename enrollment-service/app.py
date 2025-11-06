from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Enrollment Service", version="1.0.0")

PAYMENT_SERVICE_URL = "http://payment-service.learning-portal.local:8080"

enrollments = {}

class EnrollmentCreate(BaseModel):
    user_id: str
    course_id: str

@app.get("/")
def home():
    return {"message": "Hello from enrollment-service", "service": "enrollment-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "enrollment-service"}

@app.post("/enrollments/enroll")
async def enroll(enrollment: EnrollmentCreate):
    enrollment_id = f"e{len(enrollments) + 1}"
    
    enrollments[enrollment_id] = {
        "enrollment_id": enrollment_id,
        "user_id": enrollment.user_id,
        "course_id": enrollment.course_id,
        "status": "pending_payment"
    }
    
    return {
        "enrollment_id": enrollment_id,
        "user_id": enrollment.user_id,
        "course_id": enrollment.course_id,
        "status": "pending_payment",
        "message": "Enrollment created, proceed to payment"
    }

@app.get("/enrollments/{user_id}")
def get_enrollments(user_id: str):
    user_enrollments = [
        e for e in enrollments.values() if e["user_id"] == user_id
    ]
    
    return {
        "user_id": user_id,
        "total": len(user_enrollments),
        "enrollments": user_enrollments
    }

@app.get("/enrollments/list")
def list_enrollments():
    return {
        "total": len(enrollments),
        "enrollments": list(enrollments.values())
    }

