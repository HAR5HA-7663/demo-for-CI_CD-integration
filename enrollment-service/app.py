from fastapi import FastAPI

app = FastAPI(title="Enrollment Service")

@app.get("/")
def home():
    return {"message": "Hello from enrollment-service", "service": "enrollment-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "enrollment-service"}

