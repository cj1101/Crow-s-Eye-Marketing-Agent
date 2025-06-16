#!/usr/bin/env python3
"""Simple API endpoint testing script."""

import urllib.request
import urllib.error

def test_url(url):
    """Test a URL and return status."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status = response.status
            content = response.read().decode('utf-8')[:200]
            return status, content, None
    except urllib.error.HTTPError as e:
        return e.code, str(e), None
    except Exception as e:
        return 0, "", str(e)

def main():
    deployed_url = "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com"
    
    endpoints = [
        "/",
        "/health", 
        "/test",
        "/docs",
        "/api/v1/health",
    ]
    
    print("🔍 TESTING DEPLOYED API ENDPOINTS")
    print("=" * 50)
    
    for endpoint in endpoints:
        url = f"{deployed_url}{endpoint}"
        status, content, error = test_url(url)
        
        if error:
            print(f"❌ {endpoint} - ERROR: {error}")
        elif status == 200:
            print(f"✅ {endpoint} - OK: {content[:100]}...")
        else:
            print(f"⚠️  {endpoint} - STATUS {status}: {content[:100]}...")

if __name__ == "__main__":
    main() 