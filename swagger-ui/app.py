from fastapi import FastAPI

app = FastAPI(title="Online Learning Portal Gateway")

@app.get("/")
def index():
    return {
        "services": [
            "user-service",
            "course-service",
            "enrollment-service",
            "payment-service",
            "notification-service"
        ],
        "message": "Swagger UI Gateway running"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "swagger-ui"}

