#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script.
Tests both local and deployed versions of the Crow's Eye API.
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

def test_endpoint(base_url: str, endpoint: str, method: str = "GET") -> Tuple[int, str, str]:
    """Test a single endpoint and return status code, response, and error."""
    url = f"{base_url}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, timeout=10)
        elif method == "PUT":
            response = requests.put(url, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return 0, "", f"Unsupported method: {method}"
        
        return response.status_code, response.text[:500], ""
    except Exception as e:
        return 0, "", str(e)

def main():
    """Main testing function."""
    
    # URLs to test
    local_url = "http://localhost:8000"
    deployed_url = "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com"
    
    # Endpoints to test
    endpoints = [
        # Root level endpoints
        "/",
        "/health", 
        "/test",
        "/docs",
        "/redoc",
        "/api/v1/openapi.json",
        
        # API v1 endpoints
        "/api/v1/health",
        "/api/v1/users/me",
        "/api/v1/media",
        "/api/v1/galleries",
        "/api/v1/ai",
        "/api/v1/posts",
        "/api/v1/platforms",
        "/api/v1/context-files",
        "/api/v1/schedules",
        "/api/v1/analytics",
        "/api/v1/templates",
        "/api/v1/webhooks",
        "/api/v1/bulk",
        "/api/v1/previews",
        "/api/v1/compliance",
        "/api/v1/google-photos",
    ]
    
    print("🔍 COMPREHENSIVE API ENDPOINT TESTING")
    print("=" * 60)
    
    for url_name, base_url in [("LOCAL", local_url), ("DEPLOYED", deployed_url)]:
        print(f"\n🌐 Testing {url_name} API: {base_url}")
        print("-" * 50)
        
        working_endpoints = []
        broken_endpoints = []
        
        for endpoint in endpoints:
            status_code, response, error = test_endpoint(base_url, endpoint)
            
            if error:
                print(f"❌ {endpoint} - ERROR: {error}")
                broken_endpoints.append((endpoint, f"ERROR: {error}"))
            elif status_code == 200:
                print(f"✅ {endpoint} - OK")
                working_endpoints.append(endpoint)
            elif status_code == 404:
                print(f"🔍 {endpoint} - NOT FOUND")
                broken_endpoints.append((endpoint, "404 Not Found"))
            elif status_code == 401:
                print(f"🔒 {endpoint} - UNAUTHORIZED (Expected for protected endpoints)")
                working_endpoints.append(endpoint)
            elif status_code == 422:
                print(f"📝 {endpoint} - VALIDATION ERROR (Expected for some endpoints)")
                working_endpoints.append(endpoint)
            else:
                print(f"⚠️  {endpoint} - STATUS {status_code}")
                broken_endpoints.append((endpoint, f"Status {status_code}"))
        
        print(f"\n📊 {url_name} SUMMARY:")
        print(f"✅ Working: {len(working_endpoints)}")
        print(f"❌ Issues: {len(broken_endpoints)}")
        
        if broken_endpoints:
            print(f"\n🔧 {url_name} ISSUES TO FIX:")
            for endpoint, issue in broken_endpoints:
                print(f"  - {endpoint}: {issue}")

if __name__ == "__main__":
    main() 