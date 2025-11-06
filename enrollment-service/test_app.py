import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "enrollment-service"

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "enrollment-service" in response.json()["service"]

def test_enroll_missing_fields():
    response = client.post("/enrollments/enroll", json={})
    assert response.status_code == 422

