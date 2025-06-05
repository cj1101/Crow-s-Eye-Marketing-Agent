"""
Tier-based access control tests.
"""

import pytest
from fastapi.testclient import TestClient
from crow_eye_api.main import app

client = TestClient(app)


def get_auth_headers(email: str = "test@example.com") -> dict:
    """Helper function to get authentication headers."""
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_free_tier_media_access():
    """Test that free tier can access media endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should be able to list media
    response = client.get("/media/", headers=headers)
    assert response.status_code == 200


def test_free_tier_gallery_access():
    """Test that free tier can access gallery endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should be able to create galleries
    response = client.post(
        "/gallery/",
        json={
            "prompt": "Best 5 photos for social media",
            "max_items": 5
        },
        headers=headers
    )
    assert response.status_code == 200


def test_free_tier_highlights_denied():
    """Test that free tier cannot access highlight reel endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should NOT be able to create highlight reels
    response = client.post(
        "/highlights/",
        json={
            "media_ids": ["media_1", "media_2", "media_3"],
            "duration": 30
        },
        headers=headers
    )
    assert response.status_code == 403
    assert "not available in your current subscription tier" in response.json()["detail"]


def test_creator_tier_highlights_access():
    """Test that creator tier can access highlight reel endpoints."""
    headers = get_auth_headers("creator@example.com")
    
    # Creator tier should be able to create highlight reels
    response = client.post(
        "/highlights/",
        json={
            "media_ids": ["media_1", "media_2", "media_3"],
            "duration": 30
        },
        headers=headers
    )
    assert response.status_code == 200


def test_creator_tier_audio_access():
    """Test that creator tier can access audio import endpoints."""
    headers = get_auth_headers("creator@example.com")
    
    # Creator tier should be able to list audio files
    response = client.get("/audio/", headers=headers)
    assert response.status_code == 200


def test_free_tier_audio_denied():
    """Test that free tier cannot access audio import endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should NOT be able to list audio files
    response = client.get("/audio/", headers=headers)
    assert response.status_code == 403


def test_free_tier_analytics_denied():
    """Test that free tier cannot access analytics endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should NOT be able to access analytics
    response = client.get("/analytics/", headers=headers)
    assert response.status_code == 403


def test_pro_tier_analytics_access():
    """Test that pro tier can access analytics endpoints."""
    headers = get_auth_headers("pro@example.com")
    
    # Pro tier should be able to access analytics
    response = client.get("/analytics/", headers=headers)
    assert response.status_code == 200


def test_free_tier_admin_denied():
    """Test that free tier cannot access admin endpoints."""
    headers = get_auth_headers("spark@example.com")
    
    # Free tier should NOT be able to access admin endpoints
    response = client.get("/admin/accounts", headers=headers)
    assert response.status_code == 403


def test_enterprise_tier_admin_access():
    """Test that enterprise tier can access admin endpoints."""
    headers = get_auth_headers("enterprise@example.com")
    
    # Enterprise tier should be able to access admin endpoints
    response = client.get("/admin/accounts", headers=headers)
    assert response.status_code == 200


def test_byo_api_key_enterprise_access():
    """Test that BYO API key grants enterprise access."""
    # Test with X-USER-API-KEY header (no JWT token needed)
    headers = {"X-USER-API-KEY": "custom-api-key-123"}
    
    # Should be able to access enterprise features
    response = client.get("/admin/accounts", headers=headers)
    assert response.status_code == 200 