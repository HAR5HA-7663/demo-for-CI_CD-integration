import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "course-service"

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "course-service" in response.json()["service"]

def test_create_course_missing_fields():
    response = client.post("/courses/create", json={})
    assert response.status_code == 422

def test_get_nonexistent_course():
    response = client.get("/courses/nonexistent-id")
    assert response.status_code == 404

