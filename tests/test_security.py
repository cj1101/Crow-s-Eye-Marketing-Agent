import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch

from crow_eye_api.main import app
from crow_eye_api.core import security


@pytest.mark.asyncio
class TestSecurityFeatures:
    """Comprehensive security testing suite."""

    async def test_password_strength_validation(self):
        """Test password strength validation."""
        # Weak passwords should fail
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "Password",
            "Password1",
            "qwerty123"
        ]
        
        for password in weak_passwords:
            is_valid, error = security.validate_password_strength(password)
            assert not is_valid, f"Password '{password}' should be rejected"
            assert error, "Error message should be provided"
        
        # Strong passwords should pass
        strong_passwords = [
            "MySecure!Pass123",
            "Tr0ub4dor&3",
            "Complex!Password#456"
        ]
        
        for password in strong_passwords:
            is_valid, error = security.validate_password_strength(password)
            assert is_valid, f"Password '{password}' should be accepted: {error}"

    async def test_input_sanitization(self):
        """Test input sanitization against XSS and injection."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "\x00\x01\x02malicious",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)"
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = security.sanitize_input(malicious_input)
            assert "<script>" not in sanitized
            assert "javascript:" not in sanitized
            assert "\x00" not in sanitized

    async def test_email_validation(self):
        """Test email validation."""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "a" * 250 + "@domain.com"  # Too long
        ]
        
        for email in valid_emails:
            assert security.validate_email(email), f"Email '{email}' should be valid"
        
        for email in invalid_emails:
            assert not security.validate_email(email), f"Email '{email}' should be invalid"

    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Make rapid requests to trigger rate limiting
            responses = []
            for i in range(10):
                response = await client.get("/health")
                responses.append(response.status_code)
            
            # All should succeed with normal rate limits
            assert all(status == 200 for status in responses)
            
            # Test auth rate limiting with invalid credentials
            auth_responses = []
            for i in range(6):  # Exceed auth rate limit (5 attempts)
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "wrongpassword"}
                )
                auth_responses.append(response.status_code)
            
            # Later requests should be rate limited
            assert 429 in auth_responses[-2:], "Rate limiting should trigger for auth endpoints"

    async def test_jwt_security(self):
        """Test JWT token security features."""
        # Test token creation
        token_data = {"sub": "test@example.com"}
        token = security.create_access_token(token_data)
        
        assert token, "Token should be created"
        
        # Verify token
        decoded = security.verify_token(token)
        assert decoded is not None, "Token should be verifiable"
        assert decoded.username == "test@example.com"
        
        # Test invalid token
        invalid_decoded = security.verify_token("invalid.token.here")
        assert invalid_decoded is None, "Invalid token should return None"

    async def test_security_headers(self):
        """Test that security headers are properly set."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            response = await client.get("/health")
            
            # Check security headers
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy",
                "Content-Security-Policy",
                "Permissions-Policy"
            ]
            
            for header in expected_headers:
                assert header in response.headers, f"Security header '{header}' missing"

    async def test_auth_endpoint_security(self):
        """Test authentication endpoint security."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test registration with weak password
            weak_password_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "weak",
                    "name": "Test User"
                }
            )
            
            assert weak_password_response.status_code == 200
            data = weak_password_response.json()
            assert not data["success"]
            assert "password" in data["error"].lower()

    async def test_sql_injection_protection(self):
        """Test protection against SQL injection."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # SQL injection attempts
            injection_attempts = [
                "user@example.com'; DROP TABLE users; --",
                "admin@test.com' OR '1'='1",
                "test@example.com' UNION SELECT * FROM users --"
            ]
            
            for injection in injection_attempts:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": injection,
                        "password": "anypassword"
                    }
                )
                
                # Should not cause server error
                assert response.status_code in [200, 422], f"SQL injection caused server error: {injection}"

    async def test_cors_configuration(self):
        """Test CORS configuration."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test preflight request
            response = await client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            # Should allow the request
            assert "Access-Control-Allow-Origin" in response.headers

    async def test_request_size_limits(self):
        """Test request size limits."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test large request body
            large_data = "x" * 10000  # 10KB
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "StrongPass123!",
                    "name": large_data
                }
            )
            
            # Should handle gracefully (name gets truncated by sanitization)
            assert response.status_code == 200

    async def test_error_information_disclosure(self):
        """Test that errors don't leak sensitive information."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test with malformed request
            response = await client.post(
                "/api/v1/auth/login",
                json={"invalid": "data"}
            )
            
            data = response.json()
            
            # Should not contain sensitive information
            assert "traceback" not in str(data).lower()
            assert "database" not in str(data).lower()
            assert "sql" not in str(data).lower()

    async def test_timing_attack_protection(self):
        """Test protection against timing attacks."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Test login timing for existing vs non-existing users
            import time
            
            # Login attempt with non-existing user
            start_time = time.time()
            await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "anypassword"
                }
            )
            nonexistent_time = time.time() - start_time
            
            # Login attempt with invalid password for existing user
            # (would need a real user in DB for proper test)
            start_time = time.time()
            await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            wrong_password_time = time.time() - start_time
            
            # Timing difference should be minimal (< 100ms difference)
            timing_diff = abs(nonexistent_time - wrong_password_time)
            assert timing_diff < 0.1, f"Timing difference too large: {timing_diff}s"


@pytest.mark.asyncio
class TestLoadTesting:
    """Load testing for the API."""

    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Create multiple concurrent requests
            tasks = []
            for i in range(20):
                task = client.get("/health")
                tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            successful = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            
            # At least 80% should succeed
            assert successful >= 16, f"Only {successful}/20 requests succeeded"

    async def test_memory_usage_stability(self):
        """Test that memory usage remains stable under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Make many requests
            for i in range(100):
                await client.get("/health")
                
                # Check memory every 20 requests
                if i % 20 == 0:
                    current_memory = process.memory_info().rss
                    memory_growth = current_memory - initial_memory
                    
                    # Memory growth should be reasonable (< 50MB)
                    assert memory_growth < 50 * 1024 * 1024, f"Memory growth too large: {memory_growth} bytes" 