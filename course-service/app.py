from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import secrets
import boto3
from datetime import datetime

app = FastAPI(title="Course Service", version="1.0.0")

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
courses_table = dynamodb.Table('learning-portal-courses')

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
    course_id = f"c{secrets.token_hex(8)}"
    courses_table.put_item(
        Item={
            "course_id": course_id,
            "title": course.title,
            "price": str(course.price),
            "instructor": course.instructor,
            "description": course.description,
            "status": "created",
            "created_at": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "course_id": course_id,
        "status": "created",
        "title": course.title,
        "price": course.price
    }

@app.get("/courses/list")
def list_courses():
    response = courses_table.scan()
    return {
        "total": len(response['Items']),
        "courses": response['Items']
    }

@app.get("/courses/{course_id}")
def get_course(course_id: str):
    response = courses_table.get_item(Key={'course_id': course_id})
    
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return response['Item']

@app.post("/courses/upload")
async def upload_course_material(
    course_id: str,
    file: UploadFile = File(...)
):
    response = courses_table.get_item(Key={'course_id': course_id})
    
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="Course not found")
    
    file_content = await file.read()
    file_metadata = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(file_content),
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    courses_table.update_item(
        Key={'course_id': course_id},
        UpdateExpression="SET file_metadata = :metadata",
        ExpressionAttributeValues={':metadata': file_metadata}
    )
    
    return {
        "status": "uploaded",
        "course_id": course_id,
        "file": file_metadata,
        "message": "File metadata stored successfully"
    }

