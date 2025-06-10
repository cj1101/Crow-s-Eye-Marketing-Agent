# Platform Compliance Guide

## Overview

This guide provides comprehensive compliance information for all supported social media platforms. Ensuring compliance is critical before connecting to platform APIs to avoid account suspension, rate limiting, or legal issues.

## Supported Platforms

### ✅ Fully Compliant Platforms

| Platform | API Version | Status | Business Account | Verification | GDPR | CCPA |
|----------|-------------|--------|------------------|--------------|------|------|
| **Instagram** | v18.0 | ✅ Active | ✅ Required | ❌ Optional | ✅ Yes | ✅ Yes |
| **Facebook** | v18.0 | ✅ Active | ❌ Optional | ❌ Optional | ✅ Yes | ✅ Yes |
| **TikTok** | v1.3 | ✅ Active | ✅ Required | ✅ Required | ✅ Yes | ✅ Yes |
| **Pinterest** | v5 | ✅ Active | ✅ Required | ❌ Optional | ✅ Yes | ✅ Yes |
| **BlueSky** | AT Protocol | ✅ Active | ❌ Optional | ❌ Optional | ✅ Yes | ❌ No |
| **Threads** | v1.0 | ✅ Active | ❌ Optional | ❌ Optional | ✅ Yes | ✅ Yes |
| **Google My Business** | v4.9 | ✅ Active | ✅ Required | ✅ Required | ✅ Yes | ✅ Yes |
| **LinkedIn** | v2 | ✅ Active | ❌ Optional | ❌ Optional | ✅ Yes | ✅ Yes |
| **X (Twitter)** | v2 | ✅ Active | ❌ Optional | ❌ Optional | ✅ Yes | ✅ Yes |

## Platform-Specific Requirements

### 📸 Instagram

**API Requirements:**
- **Version:** Graph API v18.0
- **Authentication:** OAuth2 with Instagram Basic Display API
- **Business Account:** Required for posting
- **Required Scopes:** `instagram_basic`, `instagram_content_publish`

**Content Limits:**
- **Caption:** 2,200 characters max
- **Hashtags:** 30 max
- **Media per post:** 10 max
- **Links:** Not supported in captions

**Media Requirements:**
- **Images:** JPG/PNG, 8MB max, 1080x1080 max resolution
- **Videos:** MP4/MOV, 100MB max, 60 seconds max, 1080x1080 max

**Rate Limits:**
- **Per minute:** 60 requests
- **Per hour:** 200 requests  
- **Per day:** 4,800 requests
- **Burst limit:** 10 requests
- **Cooldown:** 60 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Audit logging required
- 📅 Data retention: 90 days

### 📘 Facebook

**API Requirements:**
- **Version:** Graph API v18.0
- **Authentication:** OAuth2 with Pages API
- **Business Account:** Optional
- **Required Scopes:** `pages_manage_posts`, `pages_read_engagement`

**Content Limits:**
- **Caption:** 63,206 characters max
- **Hashtags:** 30 max
- **Media per post:** 10 max
- **Links:** Supported

**Media Requirements:**
- **Images:** JPG/PNG/GIF, 8MB max, 2048x2048 max resolution
- **Videos:** MP4/MOV/AVI, 4GB max, 240 seconds max, 1920x1080 max

**Rate Limits:**
- **Per minute:** 60 requests
- **Per hour:** 200 requests
- **Per day:** 4,800 requests
- **Burst limit:** 10 requests
- **Cooldown:** 60 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Political ads disclosure required
- 📅 Data retention: 90 days

### 🎵 TikTok

**API Requirements:**
- **Version:** TikTok for Developers v1.3
- **Authentication:** OAuth2
- **Business Account:** Required
- **Verification:** Required
- **Required Scopes:** `video.upload`, `user.info.basic`

**Content Limits:**
- **Caption:** 2,200 characters max
- **Hashtags:** 100 max
- **Media per post:** 1 (video only)
- **Links:** Not supported
- **Scheduling:** Not supported

**Media Requirements:**
- **Videos:** MP4/MOV/WebM, 4GB max, 3-180 seconds, 1080x1920 max, 9:16 aspect ratio

**Rate Limits:**
- **Per minute:** 20 requests
- **Per hour:** 100 requests
- **Per day:** 1,000 requests
- **Burst limit:** 5 requests
- **Cooldown:** 180 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ COPPA compliant
- ✅ Content moderation required
- 🚫 Geographic restrictions: China, India
- 📅 Data retention: 30 days

### 📌 Pinterest

**API Requirements:**
- **Version:** Pinterest API v5
- **Authentication:** OAuth2
- **Business Account:** Required
- **Required Scopes:** `pins:read`, `pins:write`, `boards:read`

**Content Limits:**
- **Caption:** 500 characters max
- **Hashtags:** 20 max
- **Media per post:** 1
- **Links:** Supported
- **Mentions:** Not supported

**Media Requirements:**
- **Images:** JPG/PNG, 32MB max, 2048x2048 max, 2:3/1:1/3:4 aspect ratios
- **Videos:** MP4/MOV, 2GB max, 4-15 seconds, 9:16/1:1 aspect ratios

**Rate Limits:**
- **Per minute:** 10 requests
- **Per hour:** 200 requests
- **Per day:** 1,000 requests
- **Burst limit:** 3 requests
- **Cooldown:** 300 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Affiliate link disclosure required
- 📅 Data retention: 365 days

### 🦋 BlueSky

**API Requirements:**
- **Version:** AT Protocol
- **Authentication:** Username/Password (App Password)
- **Business Account:** Optional
- **Required Scopes:** None

**Content Limits:**
- **Caption:** 300 characters max
- **Hashtags:** 10 max
- **Media per post:** 4
- **Links:** Supported
- **Scheduling:** Not supported

**Media Requirements:**
- **Images:** JPG/PNG, 1MB max, 2000x2000 max
- **Videos:** Not supported

**Rate Limits:**
- **Per minute:** 30 requests
- **Per hour:** 300 requests
- **Per day:** 5,000 requests
- **Burst limit:** 10 requests
- **Cooldown:** 120 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ❌ CCPA not applicable (decentralized)
- ❌ Content moderation optional
- ❌ Audit logging not required
- 📅 Data retention: Decentralized (no central retention)

### 🧵 Threads

**API Requirements:**
- **Version:** Threads API v1.0 (Meta Graph API)
- **Authentication:** OAuth2
- **Business Account:** Optional
- **Required Scopes:** `threads_basic`, `threads_content_publish`

**Content Limits:**
- **Caption:** 500 characters max
- **Hashtags:** 30 max
- **Media per post:** 10
- **Links:** Supported
- **Scheduling:** Not supported

**Media Requirements:**
- **Images:** JPG/PNG, 8MB max, 1080x1080 max
- **Videos:** MP4/MOV, 100MB max, 60 seconds max, 1080x1080 max

**Rate Limits:**
- **Per minute:** 60 requests
- **Per hour:** 200 requests
- **Per day:** 4,800 requests
- **Burst limit:** 10 requests
- **Cooldown:** 60 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Paid partnership disclosure required
- 📅 Data retention: 90 days

### 🏢 Google My Business

**API Requirements:**
- **Version:** Google My Business API v4.9
- **Authentication:** OAuth2
- **Business Account:** Required
- **Verification:** Required
- **Required Scopes:** `https://www.googleapis.com/auth/business.manage`

**Content Limits:**
- **Caption:** 1,500 characters max
- **Hashtags:** 10 max
- **Media per post:** 10
- **Links:** Supported
- **Mentions:** Not supported

**Media Requirements:**
- **Images:** JPG/PNG, 10MB max, 250x250 min, 10240x10240 max
- **Videos:** MP4/MOV, 100MB max, 30 seconds max

**Rate Limits:**
- **Per minute:** 60 requests
- **Per hour:** 1,000 requests
- **Per day:** 10,000 requests
- **Burst limit:** 20 requests
- **Cooldown:** 60 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Business update disclosure required
- 📅 Data retention: 365 days

### 💼 LinkedIn

**API Requirements:**
- **Version:** LinkedIn API v2
- **Authentication:** OAuth2
- **Business Account:** Optional
- **Required Scopes:** `w_member_social`, `r_liteprofile`

**Content Limits:**
- **Caption:** 3,000 characters max
- **Hashtags:** 3 max (recommended)
- **Media per post:** 9
- **Links:** Supported

**Media Requirements:**
- **Images:** JPG/PNG, 5MB max, 200x200 min, 7680x4320 max
- **Videos:** MP4/MOV, 200MB max, 3-600 seconds, 1920x1080 max

**Rate Limits:**
- **Per minute:** 30 requests
- **Per hour:** 500 requests
- **Per day:** 2,000 requests
- **Burst limit:** 10 requests
- **Cooldown:** 120 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Professional content disclosure required
- 📅 Data retention: 730 days

### 🐦 X (Twitter)

**API Requirements:**
- **Version:** X API v2
- **Authentication:** OAuth2
- **Business Account:** Optional
- **Required Scopes:** `tweet.read`, `tweet.write`, `users.read`

**Content Limits:**
- **Caption:** 280 characters max
- **Hashtags:** 2 max (recommended)
- **Media per post:** 4
- **Links:** Supported

**Media Requirements:**
- **Images:** JPG/PNG/GIF, 5MB max, 4096x4096 max
- **Videos:** MP4/MOV, 512MB max, 140 seconds max, 1920x1200 max

**Rate Limits:**
- **Per minute:** 50 requests
- **Per hour:** 300 requests
- **Per day:** 2,400 requests
- **Burst limit:** 15 requests
- **Cooldown:** 60 seconds

**Compliance Requirements:**
- ✅ GDPR compliant
- ✅ CCPA compliant
- ✅ Content moderation required
- ✅ Political ads disclosure required
- 📅 Data retention: 30 days

## Content Policy Compliance

### 🚫 Prohibited Content (All Platforms)

**Universal Restrictions:**
- Adult/explicit content
- Violence and graphic content
- Hate speech and harassment
- Spam and misleading content
- Copyright infringement
- Illegal activities

**Platform-Specific Restrictions:**

**TikTok Additional:**
- Dangerous acts and challenges
- Misinformation about health/safety

**Facebook/Instagram Additional:**
- Political misinformation
- COVID-19 misinformation

**LinkedIn Additional:**
- Fake news and misinformation
- Non-professional content

### ✅ Required Disclosures

**Paid Partnerships:**
- Instagram: #ad, #sponsored, #partnership
- Facebook: Branded content tool
- TikTok: #ad, #sponsored
- Pinterest: #ad, #sponsored
- Threads: #ad, #sponsored
- LinkedIn: #sponsored, #ad
- X: #ad, #sponsored

**Affiliate Links:**
- Pinterest: #affiliate required
- All platforms: FTC compliance recommended

## Authentication Setup

### 🔐 OAuth2 Platforms

**Instagram, Facebook, Threads:**
```json
{
  "client_id": "your_app_id",
  "client_secret": "your_app_secret",
  "access_token": "user_access_token",
  "redirect_uri": "https://your-app.com/callback"
}
```

**TikTok:**
```json
{
  "client_key": "your_client_key",
  "client_secret": "your_client_secret",
  "access_token": "user_access_token",
  "refresh_token": "refresh_token"
}
```

**Pinterest:**
```json
{
  "app_id": "your_app_id",
  "app_secret": "your_app_secret",
  "access_token": "user_access_token",
  "refresh_token": "refresh_token"
}
```

**Google My Business:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "access_token": "user_access_token",
  "refresh_token": "refresh_token",
  "location_name": "accounts/123/locations/456"
}
```

**LinkedIn:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "access_token": "user_access_token",
  "refresh_token": "refresh_token"
}
```

**X (Twitter):**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "access_token": "user_access_token",
  "refresh_token": "refresh_token"
}
```

### 🔑 Username/Password Platforms

**BlueSky:**
```json
{
  "username": "your_username.bsky.social",
  "password": "your_app_password"
}
```

## Rate Limiting Best Practices

### 📊 Implementation Guidelines

1. **Respect Platform Limits**
   - Never exceed documented rate limits
   - Implement exponential backoff
   - Monitor rate limit headers

2. **Efficient Request Management**
   - Batch requests when possible
   - Cache responses appropriately
   - Use webhooks instead of polling

3. **Error Handling**
   - Handle 429 (Too Many Requests) gracefully
   - Implement retry logic with delays
   - Log rate limit violations

### 🔄 Rate Limit Monitoring

```python
# Example rate limit tracking
rate_limits = {
    "instagram": {
        "requests_per_minute": 60,
        "current_usage": 0,
        "reset_time": datetime.now() + timedelta(minutes=1)
    }
}
```

## Privacy and Data Protection

### 🛡️ GDPR Compliance

**Required Features:**
- ✅ Data export functionality
- ✅ Data deletion (right to be forgotten)
- ✅ Consent management
- ✅ Privacy policy
- ✅ Data processing transparency

**Implementation:**
```python
# GDPR compliance methods
def export_user_data(user_id):
    """Export all user data in machine-readable format"""
    pass

def delete_user_data(user_id):
    """Permanently delete all user data"""
    pass

def get_user_consent(user_id):
    """Check user consent status"""
    pass
```

### 🏛️ CCPA Compliance

**Required Features:**
- ✅ Do not sell data option
- ✅ Data disclosure requirements
- ✅ Consumer rights implementation
- ✅ Opt-out mechanisms

### 📋 Data Retention Policies

| Platform | Retention Period | Auto-Deletion |
|----------|------------------|---------------|
| Instagram | 90 days | ✅ Yes |
| Facebook | 90 days | ✅ Yes |
| TikTok | 30 days | ✅ Yes |
| Pinterest | 365 days | ✅ Yes |
| BlueSky | N/A (Decentralized) | ❌ No |
| Threads | 90 days | ✅ Yes |
| Google My Business | 365 days | ✅ Yes |
| LinkedIn | 730 days | ✅ Yes |
| X (Twitter) | 30 days | ✅ Yes |

## Testing and Validation

### 🧪 Compliance Testing

**Automated Tests:**
```bash
# Run comprehensive compliance check
python test_platform_compliance.py

# Test specific platform
python test_platform_compliance.py --platform instagram

# Test content validation
python test_content_validation.py
```

**Manual Verification:**
1. ✅ API credentials validation
2. ✅ Rate limiting functionality
3. ✅ Content policy enforcement
4. ✅ Privacy controls
5. ✅ Error handling

### 📊 Monitoring and Alerts

**Key Metrics:**
- API response times
- Rate limit usage
- Error rates
- Compliance violations
- User consent rates

**Alert Thresholds:**
- Rate limit usage > 80%
- Error rate > 5%
- Compliance score < 90%

## Troubleshooting

### 🔍 Common Issues

**Authentication Failures:**
- ❌ Invalid credentials
- ❌ Expired tokens
- ❌ Insufficient permissions
- ❌ App not approved

**Rate Limiting:**
- ❌ Exceeding request limits
- ❌ Burst limit violations
- ❌ Insufficient cooldown periods

**Content Violations:**
- ❌ Caption too long
- ❌ Too many hashtags
- ❌ Unsupported media format
- ❌ File size too large

### 🛠️ Solutions

**Token Refresh:**
```python
def refresh_access_token(platform, refresh_token):
    """Refresh expired access token"""
    # Platform-specific refresh logic
    pass
```

**Rate Limit Handling:**
```python
def handle_rate_limit(platform, retry_after):
    """Handle rate limit with exponential backoff"""
    time.sleep(min(retry_after * 2, 300))  # Max 5 minutes
```

**Content Validation:**
```python
def validate_content(platform, content):
    """Validate content against platform requirements"""
    requirements = get_platform_requirements(platform)
    # Validation logic
    return validation_result
```

## Compliance Checklist

### ✅ Pre-Launch Checklist

**API Integration:**
- [ ] Latest API versions implemented
- [ ] All required scopes configured
- [ ] Token refresh mechanisms working
- [ ] Error handling implemented

**Rate Limiting:**
- [ ] Rate limiters configured for all platforms
- [ ] Exponential backoff implemented
- [ ] Monitoring and alerting set up
- [ ] Burst limit handling working

**Content Validation:**
- [ ] Caption length validation
- [ ] Hashtag count validation
- [ ] Media format validation
- [ ] File size validation

**Privacy Compliance:**
- [ ] GDPR features implemented
- [ ] CCPA features implemented
- [ ] Data retention policies configured
- [ ] User consent mechanisms working

**Security:**
- [ ] Credentials encrypted at rest
- [ ] HTTPS for all API calls
- [ ] Audit logging enabled
- [ ] Access controls implemented

### 🔄 Ongoing Maintenance

**Monthly Tasks:**
- [ ] Review API changelog for updates
- [ ] Check compliance scores
- [ ] Update deprecated endpoints
- [ ] Review rate limit usage

**Quarterly Tasks:**
- [ ] Full compliance audit
- [ ] Security review
- [ ] Performance optimization
- [ ] Documentation updates

## Support and Resources

### 📚 Platform Documentation

- **Instagram:** [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- **Facebook:** [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- **TikTok:** [TikTok for Developers](https://developers.tiktok.com/)
- **Pinterest:** [Pinterest API](https://developers.pinterest.com/)
- **BlueSky:** [AT Protocol](https://atproto.com/)
- **Threads:** [Threads API](https://developers.facebook.com/docs/threads)
- **Google My Business:** [Google My Business API](https://developers.google.com/my-business)
- **LinkedIn:** [LinkedIn API](https://docs.microsoft.com/en-us/linkedin/)
- **X:** [X API](https://developer.twitter.com/en/docs)

### 🆘 Emergency Contacts

**Critical Issues:**
- API outages: Check platform status pages
- Compliance violations: Contact platform support immediately
- Security incidents: Follow incident response plan

**Support Channels:**
- Platform developer forums
- Official support tickets
- Community Discord/Slack channels
- Stack Overflow for technical issues

---

**Last Updated:** December 2024  
**Version:** 2.0  
**Next Review:** March 2025