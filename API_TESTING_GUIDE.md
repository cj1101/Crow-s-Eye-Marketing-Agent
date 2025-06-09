# Crow Eye API Testing Guide

## Prerequisites

1. **Environment Setup**
   - Copy the example environment variables and create your own `.env` file:
   ```bash
   # Create your .env file in the project root with these values:
   DATABASE_URL="sqlite+aiosqlite:///./data/crow_eye.db"
   JWT_SECRET_KEY="your-super-secret-jwt-key-change-this-in-production"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   API_V1_STR="/api/v1"
   PROJECT_NAME="Crow Eye API"
   ```

2. **Start the Server**
   ```bash
   uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API Documentation**
   - Open your browser to: http://localhost:8000/docs
   - This gives you the interactive Swagger UI

## Step-by-Step Testing Guide

### 1. Create a New User Account

**Method 1: Using curl**
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

**Method 2: Using the Swagger UI**
1. Go to http://localhost:8000/docs
2. Find the "Users" section
3. Click on "POST /api/v1/users/"
4. Click "Try it out"
5. Enter user data:
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123",
     "full_name": "Test User"
   }
   ```
6. Click "Execute"

### 2. Login to Get Access Token

**Method 1: Using curl**
```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

**Method 2: Using Swagger UI**
1. Go to http://localhost:8000/docs
2. Find the "Login" section
3. Click on "POST /api/v1/login/access-token"
4. Click "Try it out"
5. Enter credentials:
   - username: `test@example.com`
   - password: `testpassword123`
6. Click "Execute"
7. Copy the `access_token` from the response

### 3. Test Authenticated Endpoints

Once you have an access token, you can test protected endpoints:

**Method 1: Using curl with Bearer token**
```bash
# Get current user info
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Get health check
curl -X GET "http://localhost:8000/api/v1/health"

# Get media items (empty at first)
curl -X GET "http://localhost:8000/api/v1/media/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Method 2: Using Swagger UI**
1. In the Swagger UI, click the "Authorize" button at the top
2. Enter: `Bearer YOUR_ACCESS_TOKEN_HERE`
3. Click "Authorize"
4. Now you can test any protected endpoint by clicking "Try it out"

### 4. Test All Available Endpoints

#### Users Endpoints
- `POST /api/v1/users/` - Create user (no auth required)
- `GET /api/v1/users/me` - Get current user (requires auth)

#### Login Endpoints
- `POST /api/v1/login/access-token` - Login (no auth required)

#### Media Endpoints (all require auth)
- `GET /api/v1/media/` - Get all media items
- `POST /api/v1/media/search` - Search media
- `GET /api/v1/media/{media_id}` - Get specific media item
- `PUT /api/v1/media/{media_id}` - Update media item
- `DELETE /api/v1/media/{media_id}` - Delete media item
- `POST /api/v1/media/upload` - Upload media (placeholder)

#### Gallery Endpoints (all require auth)
- `GET /api/v1/galleries/` - Get all galleries
- `POST /api/v1/galleries/` - Create gallery
- `GET /api/v1/galleries/{gallery_id}` - Get specific gallery
- `PUT /api/v1/galleries/{gallery_id}` - Update gallery
- `DELETE /api/v1/galleries/{gallery_id}` - Delete gallery

#### AI Endpoints (all require auth)
- `POST /api/v1/ai/captions/generate` - Generate AI captions
- `POST /api/v1/ai/tags/generate` - Generate AI tags
- `POST /api/v1/ai/highlights/generate` - Generate AI highlights

#### Health Check
- `GET /api/v1/health` - Health check (no auth required)

## Common Issues and Solutions

### Issue 1: ImportError on Startup
**Error**: `ImportError: cannot import name 'get_current_active_user'`
**Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`

### Issue 2: Authentication Errors
**Error**: 401 Unauthorized
**Solution**: 
1. Make sure you created a user account first
2. Login to get a valid access token
3. Use the token in the Authorization header: `Bearer YOUR_TOKEN`

### Issue 3: Database Errors
**Error**: Database connection issues
**Solution**: The database will be created automatically on first startup in the `data/` directory

### Issue 4: Token Expiration
**Error**: Token expired
**Solution**: Login again to get a new access token

## Environment Variables for Production

For production deployment, make sure to set these environment variables:

```bash
# Strong JWT secret (generate a random string)
JWT_SECRET_KEY="your-very-strong-secret-key"

# Database URL for production (PostgreSQL recommended)
DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"

# Google Cloud settings
GOOGLE_CLOUD_PROJECT="your-actual-project-id"
GOOGLE_CLOUD_STORAGE_BUCKET="your-actual-bucket-name"
```

## Next Steps

Once basic authentication is working:
1. Test all endpoints with sample data
2. Implement Google Cloud Storage integration
3. Add AI features (OpenAI/Google AI)
4. Deploy to Google Cloud Run

## Quick Test Script

Here's a complete test script you can run:

```bash
#!/bin/bash

# 1. Create user
echo "Creating user..."
curl -s -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

echo -e "\n"

# 2. Login
echo "Logging in..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123" | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. Test authenticated endpoint
echo "Testing authenticated endpoint..."
curl -s -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n"

# 4. Test health check
echo "Testing health check..."
curl -s -X GET "http://localhost:8000/api/v1/health"

echo -e "\n"
```

Save this as `test_api.sh` and run with `bash test_api.sh` 