from fastapi import FastAPI

app = FastAPI(title="User Service")

@app.get("/")
def home():
    return {"message": "Hello from user-service", "service": "user-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "user-service"}

