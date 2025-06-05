"""
Authentication API tests.
"""

import pytest
from fastapi.testclient import TestClient
from crow_eye_api.main import app

client = TestClient(app)


def test_login_success():
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_creator_tier():
    """Test login with creator tier assignment."""
    response = client.post(
        "/auth/login",
        json={
            "email": "creator@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["subscription"]["tier"] == "creator"


def test_login_enterprise_tier():
    """Test login with enterprise tier assignment."""
    response = client.post(
        "/auth/login",
        json={
            "email": "enterprise@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["subscription"]["tier"] == "enterprise"


def test_get_current_user_without_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_with_token():
    """Test accessing protected endpoint with valid token."""
    # First login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "subscription_tier" in data


def test_logout():
    """Test logout endpoint."""
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "message" in response.json() 