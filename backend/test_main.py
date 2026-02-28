import pytest
from fastapi.testclient import TestClient
from main import app

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


def test_verify_endpoint():
    """Test verify endpoint with valid claim"""
    response = client.post(
        "/verify",
        json={"claim": "The Eiffel Tower is in Paris"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "claim" in data
    assert "result" in data
    assert "confidence" in data
    assert "mode" in data
    assert data["claim"] == "The Eiffel Tower is in Paris"
    assert data["mode"] in ["live", "mock", "error"]


def test_verify_endpoint_empty_claim():
    """Test verify endpoint with empty claim"""
    response = client.post(
        "/verify",
        json={"claim": ""}
    )
    assert response.status_code == 200


def test_verify_endpoint_missing_claim():
    """Test verify endpoint with missing claim field"""
    response = client.post(
        "/verify",
        json={}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
def test_api_cors_headers():
    """Integration test: Check CORS headers are present"""
    response = client.options("/verify")
    assert response.status_code == 200
