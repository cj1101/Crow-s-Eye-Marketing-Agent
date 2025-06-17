import pytest
import uuid
from httpx import AsyncClient

from crow_eye_api.main import app


@pytest.mark.asyncio
async def test_register_login_get_user():
    """Full happy-path flow for /auth/* endpoints."""

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        # -------- Register --------
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "P@ssw0rd123!"

        register_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": "Test User"},
        )
        assert register_resp.status_code == 200
        reg_json = register_resp.json()
        assert reg_json["success"] is True
        data = reg_json["data"]
        assert {"access_token", "refresh_token", "user"}.issubset(data)
        assert data["user"]["email"] == email

        # -------- Login --------
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        login_json = login_resp.json()
        assert login_json["success"] is True
        access_token = login_json["data"]["access_token"]

        # -------- Current User --------
        me_resp = await client.get(
            "/api/v1/auth/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_resp.status_code == 200
        me_json = me_resp.json()
        assert me_json["success"] is True
        assert me_json["data"]["email"] == email

        # -------- Logout --------
        logout_resp = await client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json()["success"] is True 