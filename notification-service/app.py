from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import secrets
import boto3

app = FastAPI(title="Notification Service", version="1.0.0")

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
notifications_table = dynamodb.Table('learning-portal-notifications')

class EmailNotification(BaseModel):
    user_email: str
    subject: str
    body: str

@app.get("/")
def home():
    return {"message": "Hello from notification-service", "service": "notification-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/notify/email")
def send_email(notification: EmailNotification):
    notification_id = f"n{secrets.token_hex(8)}"
    
    notifications_table.put_item(
        Item={
            "notification_id": notification_id,
            "user_email": notification.user_email,
            "subject": notification.subject,
            "body": notification.body,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "message": f"Notification sent to {notification.user_email}",
        "notification_id": notification_id,
        "status": "sent"
    }

@app.post("/notify/success")
def send_success_notification(data: dict):
    notification_id = f"n{secrets.token_hex(8)}"
    
    notifications_table.put_item(
        Item={
            "notification_id": notification_id,
            "type": "success",
            "data": str(data),
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "message": "Success notification sent",
        "notification_id": notification_id,
        "status": "sent"
    }

@app.get("/notifications/list")
def list_notifications():
    response = notifications_table.scan()
    return {
        "total": len(response['Items']),
        "notifications": response['Items']
    }

