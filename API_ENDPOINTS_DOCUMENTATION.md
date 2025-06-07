# Crow's Eye API Endpoints Documentation

## Base URL
- **Production**: `https://api.crowseye.tech`
- **Development**: `http://localhost:8000`

## Authentication
All endpoints except login require an `Authorization: Bearer <token>` header.

## Available Endpoints

### Authentication

#### Login
- **POST** `/auth/login`
- **Body**: 
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": {
      "user_id": "user_1234",
      "email": "user@example.com",
      "username": "user",
      "subscription": {...}
    }
  }
  ```

#### Get Current User
- **GET** `/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
  ```json
  {
    "user_id": "user_1234",
    "email": "user@example.com",
    "username": "user",
    "subscription_tier": "SPARK",
    "subscription_status": "active"
  }
  ```

#### Logout
- **POST** `/auth/logout`
- **Response**: `{"message": "Successfully logged out"}`

### Media Management

#### List Media
- **GET** `/media`
- **Query Params**: 
  - `media_type`: IMAGE, VIDEO, AUDIO (optional)
  - `limit`: number (default: 20)
  - `offset`: number (default: 0)
- **Response**: Array of media items

#### Upload Media
- **POST** `/media/upload`
- **Form Data**: 
  - `file`: binary file
  - `title`: string (optional)
  - `description`: string (optional)
- **Response**: Created media item

#### Get Media by ID
- **GET** `/media/{media_id}`
- **Response**: Single media item

#### Update Media
- **PUT** `/media/{media_id}`
- **Body**: 
  ```json
  {
    "title": "New Title",
    "description": "New Description"
  }
  ```

#### Delete Media
- **DELETE** `/media/{media_id}`

### Gallery Management

#### List Galleries
- **GET** `/gallery`
- **Query Params**: 
  - `limit`: number (default: 20)
  - `offset`: number (default: 0)
- **Response**: Array of galleries

#### Create Gallery
- **POST** `/gallery`
- **Body**:
  ```json
  {
    "title": "My Gallery",
    "description": "Gallery description",
    "media_ids": ["media_id_1", "media_id_2"]
  }
  ```

#### Get Gallery by ID
- **GET** `/gallery/{gallery_id}`

#### Update Gallery
- **PUT** `/gallery/{gallery_id}`
- **Body**: Same as create

#### Delete Gallery
- **DELETE** `/gallery/{gallery_id}`

### Stories Management

#### List Stories
- **GET** `/stories`
- **Query Params**: 
  - `limit`: number (default: 20)
  - `offset`: number (default: 0)
- **Response**: Array of stories

#### Create Story
- **POST** `/stories`
- **Body**:
  ```json
  {
    "title": "My Story",
    "content": "Story content",
    "media_ids": ["media_id_1"],
    "hashtags": ["#marketing", "#socialmedia"]
  }
  ```

#### Get Story by ID
- **GET** `/stories/{story_id}`

#### Update Story
- **PUT** `/stories/{story_id}`

#### Delete Story
- **DELETE** `/stories/{story_id}`

### Highlights Management

#### List Highlights
- **GET** `/highlights`
- **Query Params**: 
  - `limit`: number (default: 20)
  - `offset`: number (default: 0)

#### Create Highlight
- **POST** `/highlights`
- **Body**:
  ```json
  {
    "title": "My Highlight",
    "media_ids": ["media_id_1", "media_id_2"]
  }
  ```

#### Get Highlight by ID
- **GET** `/highlights/{highlight_id}`

#### Update Highlight
- **PUT** `/highlights/{highlight_id}`

#### Delete Highlight
- **DELETE** `/highlights/{highlight_id}`

### Audio Processing

#### Convert Text to Speech
- **POST** `/audio/text-to-speech`
- **Body**:
  ```json
  {
    "text": "Text to convert",
    "voice": "en-US-Standard-A"
  }
  ```
- **Response**: Audio file URL

#### Get Available Voices
- **GET** `/audio/voices`
- **Response**: Array of available voices

### Analytics

#### Get Analytics Overview
- **GET** `/analytics/overview`
- **Query Params**:
  - `start_date`: ISO date string
  - `end_date`: ISO date string
- **Response**: Analytics data

#### Get Platform Analytics
- **GET** `/analytics/platforms/{platform}`
- **Platforms**: instagram, facebook, twitter, linkedin

#### Get Content Performance
- **GET** `/analytics/content/{content_type}/{content_id}`
- **Content Types**: story, gallery, highlight

### Admin Functions

#### Get System Status
- **GET** `/admin/status`
- **Response**: System health and status

#### Get User Activity
- **GET** `/admin/activity`
- **Query Params**:
  - `user_id`: string (optional)
  - `limit`: number (default: 50)

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden (insufficient subscription tier)
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error

## Rate Limits

Rate limits vary by subscription tier:
- **Spark (Free)**: 100 requests/hour
- **Creator**: 1000 requests/hour
- **Pro Agency**: 5000 requests/hour
- **Enterprise**: Unlimited

## CORS Configuration

Allowed origins:
- `http://localhost:3000`
- `https://*.crowseye.tech`
- `https://crowseye.tech`