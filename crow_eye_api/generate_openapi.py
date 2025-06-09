#!/usr/bin/env python3
"""
Generate OpenAPI documentation for Crow's Eye API
"""

import json
import yaml
from fastapi.openapi.utils import get_openapi
from crow_eye_api.main import app

def generate_openapi_spec():
    """Generate OpenAPI specification for the API."""
    
    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title="Crow's Eye Web Application API",
        version="1.0.0",
        description="""
# Crow's Eye Web Application API

A comprehensive social media management platform API that provides:

## Features
- **Post Management**: Create, schedule, and manage social media posts
- **Media Processing**: AI-powered media editing and optimization
- **Multi-Platform Support**: Instagram, Facebook, BlueSky, Snapchat, Pinterest, TikTok, YouTube
- **AI Content Generation**: Automated captions, hashtags, and content suggestions
- **Analytics**: Detailed performance metrics and engagement tracking
- **Scheduling**: Automated posting with flexible scheduling options
- **Templates**: Reusable content templates with variable substitution
- **Bulk Operations**: Efficient batch processing for multiple posts

## Authentication
The API supports both JWT tokens and API keys:
- **JWT**: `Authorization: Bearer <jwt_token>`
- **API Key**: `X-API-Key: <api_key>`

## Demo Mode
When no valid authentication is provided, the API returns mock data for demonstration purposes.
Look for the `X-Demo-Mode: true` header in responses.

## Rate Limiting
- Rate limits are enforced per user/API key
- Check response headers for current limits:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling
All endpoints return consistent error responses:
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

## Platform Support
### Instagram
- Posts, Stories, Reels
- Image and video optimization
- Hashtag recommendations
- Story templates

### Facebook
- Page posting
- Event creation
- Group posting (with permissions)
- Link previews

### BlueSky
- AT Protocol integration
- Custom feeds
- Thread creation
- Decentralized identity

### Snapchat
- Snap creation
- Story posting
- Spotlight content
- AR lens integration

### Pinterest
- Pin creation
- Board management
- Story Pins
- Shopping integration

### TikTok
- Video posting
- Trend analysis
- Hashtag challenges
- Music integration

### YouTube
- Video uploads
- Shorts creation
- Community posts
- Premiere scheduling
        """,
        routes=app.routes,
    )
    
    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "Crow's Eye API Support",
        "email": "support@crowseye.com",
        "url": "https://crowseye.com/support"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    openapi_schema["servers"] = [
        {
            "url": "https://crow-eye-api-605899951231.us-central1.run.app",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    # Add custom headers to responses
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                for response in operation["responses"].values():
                    if isinstance(response, dict):
                        response["headers"] = {
                            "X-Demo-Mode": {
                                "description": "Indicates if the response is from demo mode",
                                "schema": {"type": "boolean"}
                            },
                            "X-RateLimit-Limit": {
                                "description": "Maximum requests allowed",
                                "schema": {"type": "integer"}
                            },
                            "X-RateLimit-Remaining": {
                                "description": "Remaining requests in current window",
                                "schema": {"type": "integer"}
                            },
                            "X-RateLimit-Reset": {
                                "description": "Time when rate limit resets (Unix timestamp)",
                                "schema": {"type": "integer"}
                            }
                        }
    
    return openapi_schema

def save_openapi_spec():
    """Save OpenAPI specification to files."""
    spec = generate_openapi_spec()
    
    # Save as JSON
    with open("openapi.json", "w") as f:
        json.dump(spec, f, indent=2)
    
    # Save as YAML
    with open("openapi.yaml", "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    
    print("OpenAPI specification generated:")
    print("- openapi.json")
    print("- openapi.yaml")
    print(f"- Total endpoints: {len([path for path in spec['paths']])}")
    print(f"- Total operations: {sum(len(methods) for methods in spec['paths'].values())}")

if __name__ == "__main__":
    save_openapi_spec() 