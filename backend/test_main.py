import pytest
import os
from fastapi.testclient import TestClient

# Set test mode before importing the app
os.environ["TEST_MODE"] = "true"

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
    assert "verdict" in data  # Changed from 'result' to 'verdict'
    assert "confidence" in data
    assert "probabilities" in data  # Added probabilities check
    assert "mode" in data
    assert data["status"] == "success"
    assert data["claim"] == "The Eiffel Tower is in Paris"
    assert data["mode"] in ["live", "mock", "error"]
    assert isinstance(data["probabilities"], dict)


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
