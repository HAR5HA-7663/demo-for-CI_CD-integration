from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import secrets
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

app = FastAPI(title="Enrollment Service", version="1.0.0")

PAYMENT_SERVICE_URL = "http://payment-service.learning-portal.local:8080"

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
enrollments_table = dynamodb.Table('learning-portal-enrollments')

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
    enrollment_id = f"e{secrets.token_hex(8)}"
    
    enrollments_table.put_item(
        Item={
            "enrollment_id": enrollment_id,
            "user_id": enrollment.user_id,
            "course_id": enrollment.course_id,
            "status": "pending_payment",
            "created_at": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "enrollment_id": enrollment_id,
        "user_id": enrollment.user_id,
        "course_id": enrollment.course_id,
        "status": "pending_payment",
        "message": "Enrollment created, proceed to payment"
    }

@app.get("/enrollments/{user_id}")
def get_enrollments(user_id: str):
    response = enrollments_table.query(
        IndexName='UserIndex',
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    
    return {
        "user_id": user_id,
        "total": len(response['Items']),
        "enrollments": response['Items']
    }

@app.get("/enrollments/list")
def list_enrollments():
    response = enrollments_table.scan()
    return {
        "total": len(response['Items']),
        "enrollments": response['Items']
    }

