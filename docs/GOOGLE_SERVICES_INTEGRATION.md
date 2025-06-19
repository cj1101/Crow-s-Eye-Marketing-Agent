# Google Services Integration Guide

This guide explains how to integrate YouTube, Google Photos, and Google My Business with your social media management tool. Each service can use a different Google account for maximum flexibility.

## Overview

The integration supports three Google services:
- **YouTube**: Upload videos and manage your YouTube channel (including YouTube Shorts)
- **Google Photos**: Access and import photos from your Google Photos library
- **Google My Business**: Manage Google My Business posts and locations

## Key Features

✅ **Separate Account Support**: Each service can use a different Google account  
✅ **Independent Authentication**: Authenticate each service separately  
✅ **Flexible Configuration**: Switch between different accounts per service  
✅ **Unified Management**: Manage all services from one interface  

## Setup Process

### 1. Google Cloud Console Setup

For each service you want to use, you'll need to create OAuth2 credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs:
   - **YouTube**: YouTube Data API v3
   - **Google Photos**: Photos Library API
   - **Google My Business**: My Business Business Information API
4. Go to "Credentials" and create OAuth2 client credentials
5. Add your redirect URIs (the app will provide these)

### 2. Backend API Endpoints

The following endpoints are available for each service:

#### Universal Google Services API (`/api/v1/google/`)
- `GET /services` - List all available Google services
- `GET /services/status` - Get status of all services
- `POST /services/{service_name}/auth/setup` - Setup OAuth2 credentials
- `GET /services/{service_name}/auth/authorize` - Get authorization URL
- `DELETE /services/{service_name}/auth/disconnect` - Disconnect service

#### YouTube API (`/api/v1/youtube/`)
- `GET /status` - Check YouTube connection status
- `POST /upload` - Upload video to YouTube
- `DELETE /auth/disconnect` - Disconnect YouTube

#### Google Photos API (`/api/v1/google-photos/`)
- `GET /connection` - Check Google Photos connection
- `GET /albums` - Get photo albums
- `GET /media` - Get media items
- `POST /import` - Import photos

#### Google My Business API (`/api/v1/google-business/`)
- `GET /status` - Check Google My Business status
- `GET /accounts` - Get business accounts
- `GET /locations` - Get business locations
- `POST /post` - Create business post

## Usage Examples

### 1. Setup YouTube (Account A)

```bash
# Setup credentials
curl -X POST "http://localhost:8000/api/v1/google/services/youtube/auth/setup" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "client_id=YOUR_YOUTUBE_CLIENT_ID" \
  -F "client_secret=YOUR_YOUTUBE_CLIENT_SECRET"

# Get authorization URL
curl -X GET "http://localhost:8000/api/v1/google/services/youtube/auth/authorize" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Visit the returned URL and complete authentication
```

### 2. Setup Google My Business (Account B)

```bash
# Setup different credentials for business account
curl -X POST "http://localhost:8000/api/v1/google/services/google_business/auth/setup" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "client_id=YOUR_BUSINESS_CLIENT_ID" \
  -F "client_secret=YOUR_BUSINESS_CLIENT_SECRET"

# Get authorization URL (will use different account)
curl -X GET "http://localhost:8000/api/v1/google/services/google_business/auth/authorize" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Upload Video to YouTube

```bash
curl -X POST "http://localhost:8000/api/v1/youtube/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "title=My Video Title" \
  -F "description=Video description" \
  -F "is_short=false"
```

### 4. Create Google My Business Post

```bash
curl -X POST "http://localhost:8000/api/v1/google-business/post" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "location_name=accounts/123/locations/456" \
  -F "summary=Check out our new product!" \
  -F "call_to_action=LEARN_MORE"
```

## Platform Requirements

Each platform has specific requirements:

### YouTube
- **Video formats**: MP4, MOV, AVI, WMV, FLV
- **Max file size**: 256GB
- **Max duration**: 12 hours
- **Min duration**: 33 seconds
- **YouTube Shorts**: Max 60 seconds, vertical aspect ratio (9:16)

### Google Photos
- **Access**: Read-only access to photos and albums
- **Import**: Can download and use photos in posts
- **Formats**: JPG, PNG, HEIC, and more

### Google My Business
- **Post types**: Text posts, photo posts, event posts
- **Character limit**: 1,500 characters
- **Media**: Images and videos supported

## Credential Management

### File Structure
Each service stores credentials separately:
```
google_youtube_credentials_{user_id}.json
google_youtube_token_{user_id}.json
google_google_photos_credentials_{user_id}.json
google_google_photos_token_{user_id}.json
google_google_business_credentials_{user_id}.json
google_google_business_token_{user_id}.json
```

### Security Features
- User-specific credential storage
- Automatic token refresh
- Secure state validation
- Separate scopes per service

## Troubleshooting

### Common Issues

1. **"Credentials not configured"**
   - Make sure you've run the setup endpoint for each service
   - Check that your OAuth2 credentials are correct

2. **"Authentication expired"**
   - The integration will try to refresh tokens automatically
   - If refresh fails, you'll need to re-authenticate

3. **"No YouTube channel found"**
   - Make sure the Google account has a YouTube channel
   - Some accounts may need to create a channel first

4. **"No Google My Business accounts found"**
   - Ensure the account has access to a Google My Business listing
   - Verify the correct scopes are enabled

### Testing Authentication

Check the status of all services:
```bash
curl -X GET "http://localhost:8000/api/v1/google/services/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Best Practices

1. **Account Organization**
   - Use your personal Google account for YouTube
   - Use your business Google account for Google My Business
   - Use a shared/team account for Google Photos

2. **Security**
   - Store OAuth2 credentials securely
   - Regularly review connected applications
   - Use separate projects in Google Cloud Console for different environments

3. **Content Strategy**
   - Import photos from Google Photos for consistent branding
   - Cross-post videos to YouTube and other platforms
   - Keep Google My Business posts updated for local SEO

## Support

For issues or questions:
1. Check the backend logs for detailed error messages
2. Verify API quotas in Google Cloud Console
3. Ensure all required APIs are enabled
4. Test with a simple API call first

## API Rate Limits

Be aware of Google's API quotas:
- **YouTube**: 10,000 quota units per day
- **Google Photos**: 10,000 requests per day
- **Google My Business**: Varies by endpoint

Monitor your usage in the Google Cloud Console to avoid hitting limits. 