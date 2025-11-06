from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib
import secrets
import boto3
from boto3.dynamodb.conditions import Key

app = FastAPI(title="User Service", version="1.0.0")

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
users_table = dynamodb.Table('learning-portal-users')
tokens = {}

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    return secrets.token_hex(32)

@app.get("/")
def home():
    return {"message": "Hello from user-service", "service": "user-service"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "user-service"}

@app.post("/users/register")
def register(user: UserRegister):
    response = users_table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('email').eq(user.email)
    )
    if response['Items']:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"u{secrets.token_hex(8)}"
    users_table.put_item(
        Item={
            "user_id": user_id,
            "name": user.name,
            "email": user.email,
            "password": hash_password(user.password),
            "role": user.role
        }
    )
    
    return {
        "user_id": user_id,
        "status": "registered",
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

@app.post("/users/login")
def login(credentials: UserLogin):
    response = users_table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('email').eq(credentials.email)
    )
    
    if not response['Items']:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = response['Items'][0]
    
    if user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = generate_token()
    tokens[token] = user["user_id"]
    
    return {
        "token": token,
        "user_id": user["user_id"],
        "role": user["role"],
        "status": "logged_in"
    }

@app.get("/users/list")
def list_users():
    response = users_table.scan()
    users_list = [
        {
            "user_id": u["user_id"],
            "name": u["name"],
            "email": u["email"],
            "role": u["role"]
        }
        for u in response['Items']
    ]
    
    return {
        "total": len(users_list),
        "users": users_list
    }

