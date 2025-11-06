import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "notification-service"

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "notification-service" in response.json()["service"]

def test_email_notification_missing_fields():
    response = client.post("/notify/email", json={})
    assert response.status_code == 422

