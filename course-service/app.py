from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Course Service", version="1.0.0")

courses = {}

class CourseCreate(BaseModel):
    title: str
    price: float
    instructor: str
    description: str = ""

@app.get("/")
def home():
    return {"message": "Hello from course-service", "service": "course-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "course-service"}

@app.post("/courses/create")
def create_course(course: CourseCreate):
    course_id = f"c{len(courses) + 1}"
    courses[course_id] = {
        "course_id": course_id,
        "title": course.title,
        "price": course.price,
        "instructor": course.instructor,
        "description": course.description,
        "status": "created"
    }
    
    return {
        "course_id": course_id,
        "status": "created",
        "title": course.title,
        "price": course.price
    }

@app.get("/courses/list")
def list_courses():
    return {
        "total": len(courses),
        "courses": list(courses.values())
    }

@app.get("/courses/{course_id}")
def get_course(course_id: str):
    if course_id not in courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return courses[course_id]

