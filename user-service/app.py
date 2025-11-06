from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib
import secrets

app = FastAPI(title="User Service", version="1.0.0")

users = {}
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
    if user.email in [u["email"] for u in users.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"u{len(users) + 1}"
    users[user_id] = {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role
    }
    
    return {
        "user_id": user_id,
        "status": "registered",
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

@app.post("/users/login")
def login(credentials: UserLogin):
    user = None
    for u in users.values():
        if u["email"] == credentials.email:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
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
    return {
        "total": len(users),
        "users": [
            {
                "user_id": u["user_id"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"]
            }
            for u in users.values()
        ]
    }

