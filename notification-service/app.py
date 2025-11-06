from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Notification Service", version="1.0.0")

notifications = {}

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
    notification_id = f"n{len(notifications) + 1}"
    
    notifications[notification_id] = {
        "notification_id": notification_id,
        "user_email": notification.user_email,
        "subject": notification.subject,
        "body": notification.body,
        "status": "sent",
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "message": f"Notification sent to {notification.user_email}",
        "notification_id": notification_id,
        "status": "sent"
    }

@app.post("/notify/success")
def send_success_notification(data: dict):
    notification_id = f"n{len(notifications) + 1}"
    
    notifications[notification_id] = {
        "notification_id": notification_id,
        "type": "success",
        "data": data,
        "status": "sent",
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "message": "Success notification sent",
        "notification_id": notification_id,
        "status": "sent"
    }

@app.get("/notifications/list")
def list_notifications():
    return {
        "total": len(notifications),
        "notifications": list(notifications.values())
    }

