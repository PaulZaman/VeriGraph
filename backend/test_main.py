import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test mode and use SQLite in-memory database for tests
os.environ["TEST_MODE"] = "true"
os.environ["NEON_DB_URL"] = "sqlite:///:memory:"

from main import app, Base

# Create test database
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to VeriGraph API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_verify_endpoint_creates_task():
    """Test verify endpoint creates a task and returns task_id"""
    response = client.post(
        "/verify",
        json={"claim": "The Eiffel Tower is in Paris"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "task_id" in data
    assert "message" in data
    assert data["status"] == "success"
    
    # Save task_id for next test
    return data["task_id"]


def test_get_verification_task():
    """Test getting verification task status"""
    # First create a task
    create_response = client.post(
        "/verify",
        json={"claim": "The Earth orbits the Sun"}
    )
    task_id = create_response.json()["task_id"]
    
    # Then retrieve it
    get_response = client.get(f"/verify/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert "task_id" in data
    assert "claim" in data
    assert "status" in data
    assert data["task_id"] == task_id
    assert data["claim"] == "The Earth orbits the Sun"
    assert data["status"] in ["pending", "processing", "completed", "failed"]


def test_get_verification_task_not_found():
    """Test getting non-existent verification task"""
    response = client.get("/verify/nonexistent-task-id")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_verify_endpoint_empty_claim():
    """Test verify endpoint with empty claim"""
    response = client.post(
        "/verify",
        json={"claim": ""}
    )
    # Should still create a task even with empty claim
    assert response.status_code == 200
    assert "task_id" in response.json()


def test_verify_endpoint_missing_claim():
    """Test verify endpoint with missing claim field"""
    response = client.post(
        "/verify",
        json={}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
def test_api_cors_headers():
    """Integration test: Check CORS headers are present on POST requests"""
    response = client.post(
        "/verify",
        json={"claim": "Test claim"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    # Check that CORS headers are present
    assert "access-control-allow-origin" in response.headers or \
           "Access-Control-Allow-Origin" in response.headers
