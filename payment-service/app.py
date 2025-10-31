from fastapi import FastAPI

app = FastAPI(title="Payment Service")

@app.get("/")
def home():
    return {"message": "Hello from payment-service", "service": "payment-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "payment-service"}

