# Social Media Platform Integrations

## Overview

The Breadsmith Marketing Tool now supports **9+ social media platforms** with official API integrations, providing comprehensive social media management capabilities.

## Supported Platforms

### ✅ Fully Integrated Platforms

| Platform | API Type | Media Support | Character Limit | Special Features |
|----------|----------|---------------|-----------------|------------------|
| **Instagram** | Graph API | Images, Videos | 2,200 chars | Business account required |
| **Facebook** | Graph API | Images, Videos, Text | 63,206 chars | Meta ecosystem |
| **LinkedIn** | LinkedIn API | Images, Videos, Text | 3,000 chars | Professional network |
| **X (Twitter)** | X API v2 | Images, Videos, Text | 280 chars | Real-time updates |
| **TikTok** | TikTok for Developers | Videos only | 2,200 chars | Video-first platform |
| **Pinterest** | Pinterest API v5 | Images, Videos | 500 chars | Board management |
| **BlueSky** | AT Protocol | Images, Text | 300 chars | Decentralized social |
| **Threads** | Meta Graph API | Images, Videos, Text | 500 chars | Meta ecosystem |
| **Google My Business** | Google My Business API | Images, Videos, Text | 1,500 chars | Location-based |

## Implementation Details

### 🏗️ Architecture

```
src/api/
├── instagram/          # Instagram Graph API integration
├── tiktok/            # TikTok for Developers API
├── google_business/   # Google My Business API
├── bluesky/          # AT Protocol (BlueSky)
├── pinterest/        # Pinterest API v5
├── threads/          # Threads API (Meta)
├── meta/             # Original Meta integration
├── linkedin/         # LinkedIn API
└── twitter/          # X (Twitter) API v2
```

### 🔧 Core Components

#### 1. **API Handlers**
Each platform has a dedicated handler with:
- **Authentication management**
- **Media validation**
- **Posting functionality**
- **Error handling**
- **Progress tracking**
- **Logout/cleanup**

#### 2. **Unified Posting Handler**
- **Single interface** for all platforms
- **Concurrent posting** support
- **Platform availability** checking
- **Error aggregation**
- **Progress monitoring**

#### 3. **Factory Reset Integration**
- **Complete credential cleanup**
- **Platform-specific logout**
- **GDPR/CCPA compliance**
- **Data deletion callbacks**

#### 4. **UI Integration**
- **Platform selection** in all dialogs
- **Real-time availability** checking
- **Error message display**
- **Progress tracking**

## Platform-Specific Features

### 📸 Instagram API
```python
# Features:
- Instagram Graph API for business accounts
- Container-based posting workflow
- Image and video support (8MB/100MB limits)
- Caption support up to 2,200 characters
- Business account requirement
```

### 🎵 TikTok API
```python
# Features:
- TikTok for Developers API
- Video-only platform (4GB limit)
- Chunked upload for large files
- Privacy controls (public/private)
- Content posting API workflow
```

### 🏢 Google My Business API
```python
# Features:
- Location-based posting
- Business updates and announcements
- Photo and video support (10MB/100MB)
- Call-to-action buttons
- Multi-location management
```

### 🦋 BlueSky API
```python
# Features:
- AT Protocol decentralized network
- Image support (1MB limit, no video)
- Text posts up to 300 characters
- Username/password authentication
- Blob upload for media
```

### 📌 Pinterest API
```python
# Features:
- Pinterest API v5
- Pin creation with board management
- Image and video support (32MB/2GB)
- Board selection and creation
- Rich pin metadata
```

### 🧵 Threads API
```python
# Features:
- Meta Graph API ecosystem
- Text and media posts (500 char limit)
- Container-based posting
- Integration with Meta infrastructure
- Image and video support
```

## Configuration

### 🔑 API Credentials Setup

Each platform requires specific credentials stored in JSON files:

```
meta_credentials.json          # Facebook/Instagram
linkedin_credentials.json      # LinkedIn
x_credentials.json            # X (Twitter)
instagram_credentials.json    # Instagram API
tiktok_credentials.json       # TikTok
google_business_credentials.json  # Google My Business
bluesky_credentials.json      # BlueSky
pinterest_credentials.json    # Pinterest
threads_credentials.json      # Threads
```

### 📋 Required Credentials by Platform

#### Instagram API
```json
{
  "access_token": "your_access_token",
  "instagram_business_account_id": "your_business_account_id"
}
```

#### TikTok
```json
{
  "access_token": "your_access_token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

#### Google My Business
```json
{
  "access_token": "your_access_token",
  "refresh_token": "your_refresh_token",
  "location_name": "accounts/your_account/locations/your_location"
}
```

#### BlueSky
```json
{
  "username": "your_username.bsky.social",
  "password": "your_app_password"
}
```

#### Pinterest
```json
{
  "access_token": "your_access_token",
  "default_board_id": "your_board_id",
  "website_url": "https://your-website.com"
}
```

#### Threads
```json
{
  "access_token": "your_access_token",
  "threads_user_id": "your_threads_user_id"
}
```

## Usage Examples

### 🚀 Basic Posting

```python
from src.features.posting.unified_posting_handler import UnifiedPostingHandler

# Initialize handler
handler = UnifiedPostingHandler()

# Post to multiple platforms
platforms = ["instagram", "tiktok", "pinterest", "bluesky"]
results = handler.post_to_platforms(
    platforms=platforms,
    media_path="path/to/your/media.jpg",
    caption="Your amazing content!",
    is_video=False
)

# Check results
for platform, (success, message) in results.items():
    if success:
        print(f"✅ {platform}: {message}")
    else:
        print(f"❌ {platform}: {message}")
```

### 🔍 Platform Availability

```python
# Check which platforms are available
available = handler.get_available_platforms()
for platform, is_available in available.items():
    status = "✅ Available" if is_available else "❌ Not Available"
    print(f"{platform}: {status}")
```

### 📏 Platform Limits

```python
# Get platform-specific limits
limits = handler.get_platform_limits()
for platform, platform_limits in limits.items():
    print(f"{platform}:")
    print(f"  Max caption: {platform_limits['max_caption_length']} chars")
    print(f"  Max image: {platform_limits['max_image_size'] / (1024*1024):.1f}MB")
    print(f"  Requires media: {platform_limits['requires_media']}")
```

## Factory Reset & Compliance

### 🏭 Complete Data Deletion

```python
from src.handlers.compliance_handler import ComplianceHandler

compliance = ComplianceHandler()

# Perform factory reset (deletes ALL data)
success = compliance.factory_reset()
if success:
    print("✅ Factory reset completed")
    print("🗑️ All credentials and data deleted")
else:
    print("❌ Factory reset failed")
```

### 📊 Compliance Status

```python
# Check compliance status
status = compliance.get_compliance_status()
print(f"Deletion requests: {status['deletion_requests_count']}")
print(f"Export requests: {status['export_requests_count']}")
print(f"Factory resets: {status['factory_resets_count']}")
```

## UI Integration

### 🖥️ Updated Dialogs

All UI dialogs now include all platforms:

1. **Custom Media Upload Dialog** - Platform selection with availability checking
2. **Post Preview Dialog** - Multi-platform posting options
3. **Post Options Dialog** - Platform selection for scheduled posts

### 🎨 Platform Selection UI

```python
# Platform checkboxes are automatically generated
# with real-time availability checking:

✅ Instagram (Available)
✅ Facebook (Available)
❌ LinkedIn (Not Available - Credentials needed)
❌ TikTok (Not Available - Credentials needed)
✅ Pinterest (Available)
# ... etc
```

## Error Handling

### 🚨 Common Error Types

1. **Authentication Errors**
   - Missing credentials
   - Expired tokens
   - Invalid permissions

2. **Media Validation Errors**
   - File size too large
   - Unsupported format
   - Platform-specific restrictions

3. **API Errors**
   - Rate limiting
   - Network issues
   - Platform-specific errors

### 🔧 Error Recovery

```python
# Each handler provides detailed error information
success, message = handler.post_media(media_path, caption)
if not success:
    if "authentication" in message.lower():
        print("🔑 Please check your credentials")
    elif "file size" in message.lower():
        print("📏 Media file is too large")
    elif "rate limit" in message.lower():
        print("⏰ Rate limited, try again later")
```

## Testing

### 🧪 Test Suite

Run the comprehensive test suite:

```bash
python test_integrations.py
```

The test suite verifies:
- ✅ All API handlers initialize correctly
- ✅ Unified posting handler integration
- ✅ Factory reset functionality
- ✅ UI dialog imports
- ✅ Platform-specific features

## Performance Considerations

### ⚡ Optimization Features

1. **Concurrent Posting** - Post to multiple platforms simultaneously
2. **Progress Tracking** - Real-time upload progress
3. **Error Aggregation** - Collect all errors for batch handling
4. **Credential Caching** - Avoid repeated file reads
5. **Media Validation** - Pre-validate before upload

### 📊 Platform Limits Summary

| Platform | Max Image | Max Video | Max Caption | Video Only | Image Only |
|----------|-----------|-----------|-------------|------------|------------|
| Instagram | 8MB | 100MB | 2,200 | ❌ | ❌ |
| TikTok | N/A | 4GB | 2,200 | ✅ | ❌ |
| Pinterest | 32MB | 2GB | 500 | ❌ | ❌ |
| BlueSky | 1MB | N/A | 300 | ❌ | ✅ |
| Google Business | 10MB | 100MB | 1,500 | ❌ | ❌ |
| Threads | 8MB | 100MB | 500 | ❌ | ❌ |

## Security & Privacy

### 🔒 Security Features

1. **Credential Encryption** - Secure storage of API keys
2. **Factory Reset** - Complete data deletion
3. **GDPR Compliance** - Data export and deletion
4. **Audit Logging** - Track all operations
5. **Error Sanitization** - No sensitive data in logs

### 🛡️ Privacy Controls

1. **Data Retention** - Configurable retention periods
2. **Third-party Sharing** - No data sharing with third parties
3. **User Rights** - Export, deletion, correction rights
4. **Consent Management** - Granular permission controls

## Troubleshooting

### 🔍 Common Issues

1. **"Platform Not Available"**
   - Check credentials file exists
   - Verify API keys are valid
   - Ensure proper permissions

2. **"Media Validation Failed"**
   - Check file size limits
   - Verify supported formats
   - Ensure file exists and is readable

3. **"Authentication Failed"**
   - Refresh access tokens
   - Check API key permissions
   - Verify account status

### 📞 Support

For platform-specific issues:
- **Instagram/Facebook/Threads**: Meta Developer Documentation
- **TikTok**: TikTok for Developers Support
- **LinkedIn**: LinkedIn Developer Support
- **X**: X Developer Platform
- **Pinterest**: Pinterest Developer Documentation
- **BlueSky**: AT Protocol Documentation
- **Google My Business**: Google My Business API Support

## Future Enhancements

### 🚀 Planned Features

1. **Additional Platforms**
   - YouTube Shorts
   - Snapchat
   - Discord
   - Telegram

2. **Advanced Features**
   - Scheduled posting
   - Content optimization
   - Analytics integration
   - A/B testing

3. **Enterprise Features**
   - Team collaboration
   - Approval workflows
   - Brand management
   - Compliance reporting

---

## 📝 Summary

The Breadsmith Marketing Tool now provides comprehensive social media management with:

- ✅ **9+ Platform Support** - All major social media platforms
- ✅ **Official APIs** - Using official platform APIs for reliability
- ✅ **Unified Interface** - Single interface for all platforms
- ✅ **Factory Reset** - Complete GDPR/CCPA compliance
- ✅ **Modern UI** - Updated dialogs with all platforms
- ✅ **Error Handling** - Comprehensive error management
- ✅ **Performance** - Optimized for speed and reliability

The integration is **production-ready** and provides a solid foundation for comprehensive social media management! 🎉 