from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import secrets
import boto3
from datetime import datetime

app = FastAPI(title="Payment Service", version="1.0.0")

NOTIFICATION_SERVICE_URL = "http://notification-service.learning-portal.local:8080"

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
payments_table = dynamodb.Table('learning-portal-payments')

class PaymentInitiate(BaseModel):
    enrollment_id: str
    amount: float
    method: str = "card"
    user_email: str = ""

@app.get("/")
def home():
    return {"message": "Hello from payment-service", "service": "payment-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "payment-service"}

@app.post("/payments/initiate")
async def initiate_payment(payment: PaymentInitiate):
    payment_id = f"p{secrets.token_hex(8)}"
    
    payments_table.put_item(
        Item={
            "payment_id": payment_id,
            "enrollment_id": payment.enrollment_id,
            "amount": str(payment.amount),
            "method": payment.method,
            "status": "success",
            "created_at": datetime.utcnow().isoformat()
        }
    )
    
    if payment.user_email:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{NOTIFICATION_SERVICE_URL}/notify/email",
                    json={
                        "user_email": payment.user_email,
                        "subject": "Payment Successful",
                        "body": f"Your payment of ${payment.amount} was successful"
                    }
                )
        except Exception:
            pass
    
    return {
        "payment_id": payment_id,
        "enrollment_id": payment.enrollment_id,
        "status": "success",
        "amount": payment.amount
    }

@app.get("/payments/status/{payment_id}")
def get_payment_status(payment_id: str):
    response = payments_table.get_item(Key={'payment_id': payment_id})
    
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return response['Item']

@app.get("/payments/list")
def list_payments():
    response = payments_table.scan()
    return {
        "total": len(response['Items']),
        "payments": response['Items']
    }

