from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Payment Service", version="1.0.0")

NOTIFICATION_SERVICE_URL = "http://notification-service.learning-portal.local:8080"

payments = {}

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
    payment_id = f"p{len(payments) + 1}"
    
    payments[payment_id] = {
        "payment_id": payment_id,
        "enrollment_id": payment.enrollment_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": "success"
    }
    
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
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payments[payment_id]

@app.get("/payments/list")
def list_payments():
    return {
        "total": len(payments),
        "payments": list(payments.values())
    }

