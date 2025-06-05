#!/usr/bin/env python3
"""
Generate OpenAPI specification for Crow's Eye API.
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from crow_eye_api.main import app

def main():
    """Generate and save OpenAPI specification."""
    print("🔧 Generating OpenAPI specification...")
    
    # Generate OpenAPI spec
    openapi_spec = app.openapi()
    
    # Create docs directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Save OpenAPI spec
    with open('docs/openapi.json', 'w') as f:
        json.dump(openapi_spec, f, indent=2)
    
    print('✅ OpenAPI specification generated at docs/openapi.json')
    print(f'📊 Found {len(openapi_spec.get("paths", {}))} API endpoints')
    
    # Print summary of endpoints
    paths = openapi_spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                summary = details.get('summary', 'No summary')
                print(f"  {method.upper()} {path} - {summary}")

if __name__ == "__main__":
    main() 