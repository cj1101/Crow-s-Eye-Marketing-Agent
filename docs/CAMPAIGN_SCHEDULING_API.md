# Campaign Scheduling API Documentation

## Overview

The Campaign Scheduling API provides comprehensive campaign management functionality with intelligent scheduling, queue management, and calendar views. This system replaces and enhances the basic scheduling features with advanced campaign capabilities.

## Key Features

- **Campaign Management**: Create, update, and manage social media campaigns
- **Intelligent Scheduling**: Automatic post scheduling based on campaign rules
- **Queue Management**: View and manage upcoming posts in campaigns
- **Calendar View**: Visual calendar interface for scheduled posts
- **Platform Optimization**: Optimize posting times for different platforms
- **Bulk Operations**: Schedule multiple posts at once
- **Analytics**: Track campaign performance and statistics

## Campaign Structure

### Campaign Types

1. **Individual Scheduled Posts**: Manually scheduled posts with specific times
2. **Queue-based Posts**: Posts automatically scheduled based on campaign rules
3. **Mixed Campaigns**: Combination of manually scheduled and queue-based posts

### Campaign Rules

- **Posting Frequency**: 1-10 posts per day
- **Posting Times**: Specific times (e.g., 09:00, 13:00, 18:00)
- **Platform Selection**: Choose which platforms to post to
- **Weekend/Holiday Handling**: Skip weekends or holidays
- **Time Randomization**: Add randomness to posting times
- **Minimum Intervals**: Ensure minimum time between posts

## API Endpoints

### Campaign Management

#### Create Campaign
```http
POST /api/v1/campaigns/
```

**Request Body:**
```json
{
  "name": "Daily Social Media Blitz",
  "description": "High-frequency posting across all platforms",
  "start_date": "2024-01-01T09:00:00Z",
  "end_date": "2024-01-31T18:00:00Z",
  "timezone": "UTC",
  "posts_per_day": 3,
  "posting_times": ["09:00", "13:00", "18:00"],
  "platforms": ["instagram", "facebook", "twitter", "linkedin"],
  "skip_weekends": false,
  "skip_holidays": true,
  "minimum_interval_minutes": 120,
  "randomize_times": false,
  "randomize_order": false,
  "content_sources": {
    "media_library": true,
    "ai_generated": true
  },
  "auto_generate_content": true,
  "content_themes": ["business", "motivation", "tips"]
}
```

**Response:**
```json
{
  "id": "campaign_123",
  "name": "Daily Social Media Blitz",
  "description": "High-frequency posting across all platforms",
  "start_date": "2024-01-01T09:00:00Z",
  "end_date": "2024-01-31T18:00:00Z",
  "timezone": "UTC",
  "posts_per_day": 3,
  "posting_times": ["09:00", "13:00", "18:00"],
  "platforms": ["instagram", "facebook", "twitter", "linkedin"],
  "skip_weekends": false,
  "skip_holidays": true,
  "minimum_interval_minutes": 120,
  "randomize_times": false,
  "randomize_order": false,
  "content_sources": {
    "media_library": true,
    "ai_generated": true
  },
  "auto_generate_content": true,
  "content_themes": ["business", "motivation", "tips"],
  "status": "draft",
  "total_posts_planned": 90,
  "total_posts_published": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "user_id": 123
}
```

#### Get All Campaigns
```http
GET /api/v1/campaigns/
```

**Query Parameters:**
- `status` (optional): Filter by campaign status (draft, active, paused, completed, cancelled)
- `active_only` (optional): Show only active campaigns (boolean)

#### Get Single Campaign with Posts
```http
GET /api/v1/campaigns/{campaign_id}
```

**Query Parameters:**
- `include_posts` (optional): Include scheduled posts (default: true)

**Response:**
```json
{
  "id": "campaign_123",
  "name": "Daily Social Media Blitz",
  "description": "High-frequency posting across all platforms",
  // ... campaign fields ...
  "scheduled_posts": [
    {
      "id": "post_1",
      "campaign_id": "campaign_123",
      "caption": "Engaging post #1 for your audience! 🚀",
      "hashtags": ["business", "motivation", "success"],
      "media_urls": ["https://example.com/media_1.jpg"],
      "media_types": ["image"],
      "scheduled_time": "2024-01-01T09:00:00Z",
      "platforms": ["instagram", "facebook"],
      "is_manually_scheduled": false,
      "campaign_position": 1,
      "is_ai_generated": true,
      "generation_prompt": "Create engaging business content",
      "context_files": [],
      "status": "scheduled",
      "published_at": null,
      "error_message": null,
      "retry_count": 0,
      "platform_post_ids": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "user_id": 123
    }
  ]
}
```

#### Update Campaign
```http
PUT /api/v1/campaigns/{campaign_id}
```

#### Delete Campaign
```http
DELETE /api/v1/campaigns/{campaign_id}
```

#### Toggle Campaign Status
```http
POST /api/v1/campaigns/{campaign_id}/toggle
```

### Calendar Functionality

#### Get Campaign Calendar (All Campaigns)
```http
GET /api/v1/campaigns/calendar
```

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `campaign_ids` (optional): Filter by specific campaign IDs

**Response:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "days": [
    {
      "date": "2024-01-01",
      "posts": [
        {
          "id": "post_1",
          "campaign_id": "campaign_123",
          "campaign_name": "Daily Social Media Blitz",
          "time": "09:00",
          "caption": "New Year motivation post!",
          "platforms": ["instagram", "facebook"],
          "status": "scheduled",
          "is_manually_scheduled": false,
          "media_count": 1
        }
      ],
      "total_posts": 1
    }
  ],
  "total_posts": 90
}
```

#### Get Single Campaign Calendar
```http
GET /api/v1/campaigns/{campaign_id}/calendar
```

### Queue Management

#### Get Campaign Queue
```http
GET /api/v1/campaigns/{campaign_id}/queue
```

**Query Parameters:**
- `limit` (optional): Maximum number of posts to return (default: 50)

**Response:**
```json
{
  "campaign_id": "campaign_123",
  "campaign_name": "Daily Social Media Blitz",
  "posts": [
    {
      "id": "queue_post_1",
      "campaign_id": "campaign_123",
      "campaign_name": "Daily Social Media Blitz",
      "caption": "Queued post #1 ready to go! 🎯",
      "hashtags": ["business", "growth", "success"],
      "media_urls": ["https://example.com/queue_media_1.jpg"],
      "platforms": ["instagram", "facebook"],
      "scheduled_time": "2024-01-01T09:00:00Z",
      "status": "queued",
      "position_in_queue": 1,
      "is_manually_scheduled": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_queued": 15,
  "next_post_time": "2024-01-01T09:00:00Z"
}
```

### Post Management within Campaigns

#### Add Post to Campaign
```http
POST /api/v1/campaigns/{campaign_id}/posts
```

**Request Body:**
```json
{
  "campaign_id": "campaign_123",
  "caption": "New post for the campaign!",
  "hashtags": ["business", "success"],
  "media_urls": ["https://example.com/media.jpg"],
  "media_types": ["image"],
  "scheduled_time": "2024-01-01T15:00:00Z",
  "platforms": ["instagram", "facebook"],
  "is_manually_scheduled": true,
  "campaign_position": 5,
  "is_ai_generated": false,
  "generation_prompt": null,
  "context_files": []
}
```

#### Update Campaign Post
```http
PUT /api/v1/campaigns/{campaign_id}/posts/{post_id}
```

#### Delete Campaign Post
```http
DELETE /api/v1/campaigns/{campaign_id}/posts/{post_id}
```

### Bulk Operations

#### Bulk Schedule Posts
```http
POST /api/v1/campaigns/{campaign_id}/bulk-schedule
```

**Request Body:**
```json
{
  "campaign_id": "campaign_123",
  "auto_schedule": true,
  "posts": [
    {
      "caption": "First bulk post",
      "hashtags": ["bulk", "scheduling"],
      "media_urls": ["https://example.com/media1.jpg"],
      "media_types": ["image"],
      "platforms": ["instagram", "facebook"],
      "generation_prompt": "Create engaging content",
      "context_files": []
    },
    {
      "caption": "Second bulk post",
      "hashtags": ["automation", "social"],
      "media_urls": ["https://example.com/media2.jpg"],
      "media_types": ["image"],
      "platforms": ["instagram", "twitter"],
      "scheduled_time": "2024-01-01T16:00:00Z"
    }
  ]
}
```

### Analytics

#### Get Campaign Analytics
```http
GET /api/v1/campaigns/analytics
```

**Response:**
```json
{
  "campaigns": [
    {
      "campaign_id": "campaign_123",
      "campaign_name": "Daily Social Media Blitz",
      "total_posts_planned": 90,
      "total_posts_published": 45,
      "total_posts_failed": 2,
      "posts_this_week": 12,
      "posts_this_month": 45,
      "completion_percentage": 50.0,
      "avg_posts_per_day": 2.1,
      "next_post_time": "2024-01-01T13:00:00Z",
      "status": "active"
    }
  ],
  "total_active_campaigns": 2,
  "total_posts_this_week": 25,
  "total_posts_this_month": 120,
  "most_active_campaign": "Daily Social Media Blitz"
}
```

## Campaign Configuration Examples

### High-Frequency Business Campaign
```json
{
  "name": "Business Growth Campaign",
  "posts_per_day": 5,
  "posting_times": ["08:00", "11:00", "14:00", "17:00", "20:00"],
  "platforms": ["linkedin", "twitter", "facebook"],
  "skip_weekends": false,
  "minimum_interval_minutes": 180,
  "content_themes": ["business", "growth", "tips", "motivation"]
}
```

### Product Launch Campaign
```json
{
  "name": "Product Launch 2024",
  "posts_per_day": 2,
  "posting_times": ["10:00", "16:00"],
  "platforms": ["instagram", "facebook", "twitter", "linkedin"],
  "skip_weekends": true,
  "skip_holidays": true,
  "randomize_times": true,
  "content_themes": ["product", "launch", "announcement", "features"]
}
```

### Weekend Social Campaign
```json
{
  "name": "Weekend Vibes",
  "posts_per_day": 1,
  "posting_times": ["11:00"],
  "platforms": ["instagram", "tiktok"],
  "skip_weekends": false,
  "randomize_times": true,
  "content_themes": ["lifestyle", "weekend", "fun", "casual"]
}
```

## Platform-Specific Optimizations

The system automatically optimizes posting times based on platform best practices:

### Instagram
- **Peak Hours**: 11 AM, 1 PM, 5 PM, 7 PM
- **Avoid Hours**: 3-6 AM
- **Best Days**: Tuesday-Thursday

### Facebook
- **Peak Hours**: 9 AM, 1 PM, 3 PM
- **Avoid Hours**: 2-5 AM
- **Best Days**: Wednesday-Friday

### Twitter
- **Peak Hours**: 9 AM, 12 PM, 5-6 PM
- **Avoid Hours**: 1-5 AM
- **Best Days**: Tuesday-Thursday

### LinkedIn
- **Peak Hours**: 8-9 AM, 12 PM, 5-6 PM
- **Avoid Hours**: 10 PM-6 AM
- **Best Days**: Tuesday-Thursday

### TikTok
- **Peak Hours**: 6-9 PM
- **Avoid Hours**: 2-7 AM
- **Best Days**: Tuesday-Thursday

### YouTube
- **Peak Hours**: 2-3 PM, 8-9 PM
- **Avoid Hours**: 2-6 AM
- **Best Days**: Thursday-Saturday

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "CAMPAIGN_NOT_FOUND",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limits

- **Campaign Creation**: 10 campaigns per hour
- **Post Scheduling**: 100 posts per hour
- **Calendar Requests**: 60 requests per minute
- **Analytics Requests**: 30 requests per minute

## Best Practices

### Campaign Planning
1. **Start Small**: Begin with 1-2 posts per day and scale up
2. **Test Timing**: Use analytics to find optimal posting times for your audience
3. **Content Variety**: Mix different content types and themes
4. **Platform Specific**: Tailor content for each platform's audience

### Scheduling Strategy
1. **Buffer Time**: Leave gaps between posts for engagement
2. **Time Zones**: Consider your audience's time zones
3. **Peak Hours**: Schedule important posts during peak engagement times
4. **Consistency**: Maintain regular posting schedules

### Queue Management
1. **Content Pipeline**: Keep a healthy queue of ready-to-post content
2. **Review Process**: Regularly review and update queued posts
3. **Backup Content**: Have evergreen content ready for gaps
4. **Performance Monitoring**: Track which posts perform best

## Integration Examples

### JavaScript/React
```javascript
// Create a new campaign
const createCampaign = async (campaignData) => {
  const response = await fetch('/api/v1/campaigns/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(campaignData)
  });
  return response.json();
};

// Get calendar view
const getCalendar = async (startDate, endDate) => {
  const response = await fetch(
    `/api/v1/campaigns/calendar?start_date=${startDate}&end_date=${endDate}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.json();
};
```

### Python
```python
import requests

# Create campaign
campaign_data = {
    "name": "My Campaign",
    "posts_per_day": 2,
    "platforms": ["instagram", "facebook"],
    "start_date": "2024-01-01T09:00:00Z",
    "end_date": "2024-01-31T18:00:00Z"
}

response = requests.post(
    "https://api.example.com/api/v1/campaigns/",
    json=campaign_data,
    headers={"Authorization": f"Bearer {token}"}
)

campaign = response.json()
```

## Migration from Legacy Schedules

If you're upgrading from the legacy schedule system:

1. **Export Existing Schedules**: Use the `/api/v1/schedules/` endpoint to get current schedules
2. **Convert to Campaigns**: Map schedule data to campaign format
3. **Migrate Posts**: Convert scheduled posts to campaign posts
4. **Update Frontend**: Switch to new campaign endpoints
5. **Test Thoroughly**: Verify all functionality works as expected

The legacy schedule endpoints remain available for backward compatibility but are deprecated.

## Support and Troubleshooting

### Common Issues

1. **Campaign Not Starting**: Check start date and campaign status
2. **Posts Not Scheduling**: Verify platform configurations and posting times
3. **Calendar Not Loading**: Check date range parameters
4. **Analytics Missing**: Ensure campaign has published posts

### Getting Help

- **API Documentation**: This document and OpenAPI spec
- **Support Email**: support@example.com
- **Status Page**: status.example.com
- **Community Forum**: community.example.com

---

**Last Updated**: January 2024  
**API Version**: v1.1.0  
**Documentation Version**: 1.0 