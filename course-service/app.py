from fastapi import FastAPI

app = FastAPI(title="Course Service")

@app.get("/")
def home():
    return {"message": "Hello from course-service", "service": "course-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "course-service"}

