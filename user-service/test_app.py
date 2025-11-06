import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "user-service"

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "user-service" in response.json()["service"]

def test_register_user_missing_fields():
    response = client.post("/users/register", json={})
    assert response.status_code == 422

def test_login_invalid_credentials():
    response = client.post("/users/login", json={
        "email": "nonexistent@test.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401

