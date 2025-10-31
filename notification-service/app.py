from fastapi import FastAPI

app = FastAPI(title="Notification Service")

@app.get("/")
def home():
    return {"message": "Hello from notification-service", "service": "notification-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "notification-service"}

