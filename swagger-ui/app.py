from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

app = FastAPI(
    title="Online Learning Portal - API Gateway",
    description="Unified API Gateway for all microservices",
    version="1.0.0"
)

SERVICES = {
    "user-service": "http://user-service.learning-portal.local:8080",
    "course-service": "http://course-service.learning-portal.local:8080",
    "enrollment-service": "http://enrollment-service.learning-portal.local:8080",
    "payment-service": "http://payment-service.learning-portal.local:8080",
    "notification-service": "http://notification-service.learning-portal.local:8080",
}

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class CourseCreate(BaseModel):
    title: str
    price: float
    instructor: str
    description: str = ""

class EnrollmentCreate(BaseModel):
    user_id: str
    course_id: str

class PaymentInitiate(BaseModel):
    enrollment_id: str
    amount: float
    method: str = "card"
    user_email: str = ""

class EmailNotification(BaseModel):
    user_email: str
    subject: str
    body: str

@app.get("/", tags=["Gateway"])
def index():
    return {
        "gateway": "Online Learning Portal",
        "version": "1.0.0",
        "services": list(SERVICES.keys()),
        "docs": "/docs",
        "message": "API Gateway running - visit /docs for unified API documentation"
    }

@app.get("/health", tags=["Gateway"])
def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/services/health", tags=["Gateway"])
async def check_all_services():
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json()
                }
            except Exception as e:
                results[service_name] = {"status": "unreachable", "error": str(e)}
    return results

@app.post("/users/register", tags=["User Service"])
async def register_user(user: UserRegister):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['user-service']}/users/register",
                json=user.dict()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"user-service unreachable: {str(e)}")

@app.post("/users/login", tags=["User Service"])
async def login_user(credentials: UserLogin):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['user-service']}/users/login",
                json=credentials.dict()
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"user-service unreachable: {str(e)}")

@app.get("/users/list", tags=["User Service"])
async def list_users():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['user-service']}/users/list")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"user-service unreachable: {str(e)}")

@app.post("/courses/create", tags=["Course Service"])
async def create_course(course: CourseCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['course-service']}/courses/create",
                json=course.dict()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"course-service unreachable: {str(e)}")

@app.get("/courses/list", tags=["Course Service"])
async def list_courses():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['course-service']}/courses/list")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"course-service unreachable: {str(e)}")

@app.get("/courses/{course_id}", tags=["Course Service"])
async def get_course(course_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['course-service']}/courses/{course_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Course not found")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"course-service unreachable: {str(e)}")

@app.post("/enrollments/enroll", tags=["Enrollment Service"])
async def enroll_user(enrollment: EnrollmentCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['enrollment-service']}/enrollments/enroll",
                json=enrollment.dict()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"enrollment-service unreachable: {str(e)}")

@app.get("/enrollments/{user_id}", tags=["Enrollment Service"])
async def get_enrollments(user_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['enrollment-service']}/enrollments/{user_id}")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"enrollment-service unreachable: {str(e)}")

@app.get("/enrollments/list", tags=["Enrollment Service"])
async def list_enrollments():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['enrollment-service']}/enrollments/list")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"enrollment-service unreachable: {str(e)}")

@app.post("/payments/initiate", tags=["Payment Service"])
async def initiate_payment(payment: PaymentInitiate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['payment-service']}/payments/initiate",
                json=payment.dict()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"payment-service unreachable: {str(e)}")

@app.get("/payments/status/{payment_id}", tags=["Payment Service"])
async def get_payment_status(payment_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['payment-service']}/payments/status/{payment_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Payment not found")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"payment-service unreachable: {str(e)}")

@app.get("/payments/list", tags=["Payment Service"])
async def list_payments():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['payment-service']}/payments/list")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"payment-service unreachable: {str(e)}")

@app.post("/notify/email", tags=["Notification Service"])
async def send_email_notification(notification: EmailNotification):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['notification-service']}/notify/email",
                json=notification.dict()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"notification-service unreachable: {str(e)}")

@app.post("/notify/success", tags=["Notification Service"])
async def send_success_notification(data: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['notification-service']}/notify/success",
                json=data
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"notification-service unreachable: {str(e)}")

@app.get("/notifications/list", tags=["Notification Service"])
async def list_notifications():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['notification-service']}/notifications/list")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"notification-service unreachable: {str(e)}")
