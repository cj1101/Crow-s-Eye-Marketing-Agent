#!/usr/bin/env python3
"""
Simple test script to verify compliance endpoints are working.
"""

import requests
import time

def test_endpoints():
    """Test basic endpoint accessibility."""
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        ("/compliance/platforms/summary", "Enhanced Platform Summary"),
        ("/compliance/health-check", "Health Check"),
        ("/compliance/platform/instagram", "Instagram Platform Details"),
        ("/compliance/rate-limits", "Rate Limits"),
        ("/platform-compliance/platforms", "Original Platform List"),
    ]
    
    print("🔍 Testing Compliance Endpoints")
    print("-" * 50)
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {description}: Working")
                data = response.json()
                if "platforms_summary" in data:
                    total_platforms = data["platforms_summary"].get("total_platforms", 0)
                    print(f"   📊 Total platforms: {total_platforms}")
                elif "health_status" in data:
                    status = data["health_status"].get("system_status", "unknown")
                    print(f"   🏥 System status: {status}")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except requests.ConnectionError:
            print(f"❌ {description}: Connection refused (server not running?)")
        except requests.Timeout:
            print(f"❌ {description}: Timeout")
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
    
    # Test content validation
    print("\n🧪 Testing Content Validation")
    print("-" * 50)
    
    try:
        content_data = {
            "caption": "Test post #test",
            "hashtags": ["test"],
            "media_files": [{"type": "image", "size_mb": 2}]
        }
        
        response = requests.post(
            f"{base_url}/compliance/validate-content",
            json=content_data,
            params={"platforms": ["instagram"]},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Content Validation: Working")
            overall_valid = data.get("overall_valid", False)
            print(f"   📊 Content valid: {overall_valid}")
        else:
            print(f"❌ Content Validation: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.ConnectionError:
        print("❌ Content Validation: Connection refused")
    except Exception as e:
        print(f"❌ Content Validation: Error - {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Compliance Endpoint Test")
    print("=" * 60)
    
    # Wait a moment for server startup
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    test_endpoints()
    
    print("\n" + "=" * 60)
    print("✅ Compliance endpoint test completed!") 