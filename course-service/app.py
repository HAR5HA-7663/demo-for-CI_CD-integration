from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional

app = FastAPI(title="Course Service", version="1.0.0")

DUMMY_COURSES = [
    {
        "id": 1,
        "title": "Introduction to Python Programming",
        "description": "Learn Python basics and fundamentals",
        "instructor": "Dr. Smith",
        "duration": "8 weeks",
        "enrolled": 150
    },
    {
        "id": 2,
        "title": "Web Development with FastAPI",
        "description": "Build modern web APIs with FastAPI framework",
        "instructor": "Prof. Johnson",
        "duration": "6 weeks",
        "enrolled": 89
    },
    {
        "id": 3,
        "title": "Database Design and SQL",
        "description": "Master relational database concepts",
        "instructor": "Dr. Williams",
        "duration": "10 weeks",
        "enrolled": 210
    },
    {
        "id": 4,
        "title": "Cloud Computing with AWS",
        "description": "Deploy applications on AWS cloud infrastructure",
        "instructor": "Prof. Martinez",
        "duration": "12 weeks",
        "enrolled": 175
    }
]

@app.get("/")
def home():
    return {"message": "Hello from course-service", "service": "course-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "course-service"}

@app.get("/courses")
def get_courses():
    return {
        "total": len(DUMMY_COURSES),
        "courses": DUMMY_COURSES
    }

@app.post("/courses/upload")
async def upload_course(
    file: UploadFile = File(...),
    username: str = Form(...)
):
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    return {
        "status": "uploaded",
        "message": "Course file uploaded successfully",
        "file_metadata": {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "uploaded_by": username
        },
        "info": f"User '{username}' uploaded file '{file.filename}'"
    }

