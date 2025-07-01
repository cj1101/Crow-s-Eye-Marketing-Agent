# Gemini AI Content Generation API

## Overview

The Gemini Content Generation API provides comprehensive AI-powered content creation using Google's Gemini Vision model. This endpoint analyzes images, generates contextual captions, creates relevant hashtags, and applies basic media editing.

## Endpoints

### 1. Content Generation (Authenticated)
```
POST /api/v1/ai/generate-content
```

### 2. Content Generation (Demo - No Auth)
```
POST /api/v1/ai/generate-content-demo
```

## Request Format

**Content-Type:** `multipart/form-data`

### Form Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_instructions` | string | ✅ | User's tone/style instruction (e.g., "be funny", "professional tone") |
| `platforms` | array[string] | ✅ | Target platforms (e.g., ["instagram", "facebook"]) |
| `enable_hashtag_generation` | boolean | ❌ | Whether to generate hashtags (default: true) |
| `media_edit_instructions` | string | ❌ | Optional media editing requests (e.g., "make it brighter") |
| `media_files` | file[] | ✅ | Uploaded images (currently supports images only) |
| `context_files` | file[] | ❌ | Brand guidelines or context files (text files) |

### Supported Platforms

- `instagram` (2200 char limit)
- `facebook` (63206 char limit)
- `twitter` (280 char limit)
- `linkedin` (3000 char limit)
- `tiktok` (4000 char limit)
- `youtube` (5000 char limit)
- `pinterest` (500 char limit)
- `snapchat` (250 char limit)

### Media Editing Instructions

The API supports basic image editing operations:

- **Brightness:** "make it brighter", "brighten the image", "make it darker"
- **Contrast:** "more contrast", "increase contrast", "less contrast", "softer"
- **Color:** "more vibrant", "saturate", "desaturate", "less colorful"
- **Filters:** "blur", "sharpen", "vintage", "sepia"
- **Rotation:** "rotate 90", "rotate 180", "rotate 270"
- **Cropping:** "crop square", "make it square"

## Response Format

```json
{
  "caption": "AI-generated unique caption",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
  "edited_media": [
    {
      "url": "/api/media/generated/edited_filename.jpg",
      "original_filename": "original.jpg",
      "edit_applied": "Applied: make it brighter and more vibrant"
    }
  ],
  "analysis": {
    "image_description": "Detailed description of what Gemini saw in the image",
    "detected_mood": "happy",
    "suggested_tone": "casual and fun"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `caption` | string | AI-generated caption optimized for target platforms |
| `hashtags` | array[string] | 5-10 relevant hashtags (without # symbol) |
| `edited_media` | array[object] | Information about edited media files |
| `analysis` | object | Gemini's analysis of the uploaded image |

## Request Examples

### JavaScript/Fetch Example

```javascript
const formData = new FormData();
formData.append('context_instructions', 'be funny and engaging');
formData.append('platforms', 'instagram');
formData.append('platforms', 'facebook');
formData.append('enable_hashtag_generation', true);
formData.append('media_edit_instructions', 'make it brighter and more vibrant');
formData.append('media_files', imageFile, 'image.jpg');

// Authenticated endpoint
const response = await fetch('/api/v1/ai/generate-content', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

// Demo endpoint (no auth)
const demoResponse = await fetch('/api/v1/ai/generate-content-demo', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Generated caption:', result.caption);
console.log('Hashtags:', result.hashtags);
console.log('Detected mood:', result.analysis.detected_mood);
```

### Python Example

```python
import requests

files = {
    'media_files': ('image.jpg', open('image.jpg', 'rb'), 'image/jpeg')
}

data = {
    'context_instructions': 'be professional and informative',
    'platforms': ['linkedin'],
    'enable_hashtag_generation': True,
    'media_edit_instructions': 'enhance colors and contrast'
}

# Authenticated endpoint
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com/api/v1/ai/generate-content',
    files=files,
    data=data,
    headers=headers
)

# Demo endpoint (no auth)
demo_response = requests.post(
    'https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com/api/v1/ai/generate-content-demo',
    files=files,
    data=data
)

result = response.json()
print(f"Caption: {result['caption']}")
print(f"Hashtags: {', '.join(result['hashtags'])}")
```

### cURL Example

```bash
# Demo endpoint (no auth required)
curl -X POST "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com/api/v1/ai/generate-content-demo" \
  -F "context_instructions=be inspiring and motivational" \
  -F "platforms=instagram" \
  -F "platforms=pinterest" \
  -F "enable_hashtag_generation=true" \
  -F "media_edit_instructions=apply vintage filter" \
  -F "media_files=@image.jpg"

# Authenticated endpoint
curl -X POST "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com/api/v1/ai/generate-content" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "context_instructions=be casual and friendly" \
  -F "platforms=facebook" \
  -F "platforms=twitter" \
  -F "enable_hashtag_generation=true" \
  -F "media_files=@image.jpg"
```

## Response Examples

### Successful Response

```json
{
  "caption": "Golden hour glow on a mountain of carbs. ✨ Seriously, look at this spread! The rustic charm of that sourdough, the perfect golden-brown baguettes, and those adorable pretzel twists... it's like a bakery threw up in the most beautiful way possible! 🥖🥨🍞 I'm pretty sure this is what heaven's breakfast table looks like. Who else is suddenly craving fresh bread and can't decide which piece to grab first? 🤔",
  "hashtags": [
    "FreshlyBakedBread",
    "SourdoughLove", 
    "BreadMaking",
    "HomemadeBread",
    "BakeryLife",
    "CarbsAreLife",
    "BreadLover",
    "PerfectBaking",
    "ArtisanBread",
    "PretzelPerfection"
  ],
  "edited_media": [
    {
      "url": "/api/media/generated/edited_12345678_image.jpg",
      "original_filename": "image.jpg",
      "edit_applied": "Applied: make it brighter and more vibrant"
    }
  ],
  "analysis": {
    "image_description": "Here's a detailed analysis of the image: The image is a flat lay overhead shot of a variety of freshly baked bread and baking ingredients. The composition includes several sourdough bread slices with their characteristic holes and golden-brown crust, baguette pieces, pretzel-shaped bread, and what appears to be some eggs and flour scattered around. The lighting is warm and natural, creating an inviting, rustic atmosphere. The overall mood is cozy and artisanal, suggesting home baking or an artisan bakery setting.",
    "detected_mood": "cozy",
    "suggested_tone": "casual and fun"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "At least one media file is required",
  "request_id": "abc123",
  "timestamp": 1640995200.0
}
```

## Integration Guide

### Frontend Integration Steps

1. **File Upload Component**
   ```javascript
   const handleFileUpload = (files) => {
     const formData = new FormData();
     files.forEach(file => {
       formData.append('media_files', file);
     });
     return formData;
   };
   ```

2. **Context Instructions Input**
   ```javascript
   const contextOptions = [
     'be funny and engaging',
     'professional and informative', 
     'casual and friendly',
     'inspiring and motivational',
     'witty and clever'
   ];
   ```

3. **Platform Selection**
   ```javascript
   const platformOptions = [
     { value: 'instagram', label: 'Instagram', limit: 2200 },
     { value: 'facebook', label: 'Facebook', limit: 63206 },
     { value: 'twitter', label: 'Twitter', limit: 280 },
     { value: 'linkedin', label: 'LinkedIn', limit: 3000 }
   ];
   ```

4. **Media Editing Options**
   ```javascript
   const editingOptions = [
     'make it brighter',
     'more vibrant colors',
     'apply vintage filter',
     'increase contrast',
     'crop to square'
   ];
   ```

### Real-time Preview

Display generated content immediately:

```javascript
const displayResults = (result) => {
  // Show caption with character count
  document.getElementById('caption').innerHTML = result.caption;
  document.getElementById('char-count').textContent = `${result.caption.length} characters`;
  
  // Display hashtags
  const hashtagsElement = document.getElementById('hashtags');
  hashtagsElement.innerHTML = result.hashtags.map(tag => `#${tag}`).join(' ');
  
  // Show image analysis
  document.getElementById('mood').textContent = result.analysis.detected_mood;
  document.getElementById('tone').textContent = result.analysis.suggested_tone;
  
  // Display edited media
  if (result.edited_media.length > 0) {
    const editedImage = document.getElementById('edited-image');
    editedImage.src = result.edited_media[0].url;
    editedImage.style.display = 'block';
  }
};
```

## Best Practices

### 1. Context Instructions
- Be specific about tone and style
- Examples: "be funny and relatable", "professional but engaging", "inspiring and motivational"
- Avoid vague instructions like "good" or "nice"

### 2. Platform Optimization
- Always specify target platforms for optimal character limits
- Consider platform-specific tone (LinkedIn = professional, TikTok = casual)

### 3. Image Quality
- Use high-quality images for better Gemini analysis
- Ensure images are well-lit and clear
- Supported formats: JPG, JPEG, PNG, GIF, WEBP

### 4. Error Handling
```javascript
try {
  const response = await generateContent(formData);
  if (response.ok) {
    const result = await response.json();
    displayResults(result);
  } else {
    handleError(await response.json());
  }
} catch (error) {
  console.error('Generation failed:', error);
  showErrorMessage('Content generation failed. Please try again.');
}
```

### 5. Performance Optimization
- Show loading indicators (Gemini analysis can take 10-30 seconds)
- Implement retry logic for network failures
- Cache results to avoid regenerating identical content

### 6. User Experience
- Preview generated content before posting
- Allow users to regenerate with different instructions
- Provide character count for different platforms
- Show confidence scores from analysis

## Rate Limits

- **Authenticated users:** 100 requests per hour
- **Demo endpoint:** 10 requests per hour per IP
- **File size limit:** 10MB per image
- **Timeout:** 90 seconds per request

## Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | Bad Request | Missing required fields or invalid file format |
| 401 | Unauthorized | Invalid or missing authentication token |
| 413 | Payload Too Large | File size exceeds 10MB limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Gemini API error or server issue |

## Troubleshooting

### Common Issues

1. **"No response from Gemini"**
   - Check if GEMINI_API_KEY is configured
   - Verify image file is valid and not corrupted
   - Try with a smaller image file

2. **"Caption generation failed"**
   - Ensure context_instructions are not empty
   - Try simpler editing instructions
   - Check if image contains recognizable content

3. **"Authentication failed"**
   - Verify Bearer token is valid and not expired
   - Use demo endpoint for testing without auth

4. **Slow response times**
   - Normal for Gemini Vision analysis (10-60 seconds)
   - Implement proper loading states
   - Consider timeout handling

## Testing

Use the demo endpoint for development and testing:

```bash
# Quick test with curl
curl -X POST "http://localhost:8002/api/v1/ai/generate-content-demo" \
  -F "context_instructions=be funny" \
  -F "platforms=instagram" \
  -F "media_files=@test_image.jpg"
```

## Production URLs

- **Base URL:** `https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com`
- **Health Check:** `/health`
- **API Documentation:** `/docs`
- **Generate Content:** `/api/v1/ai/generate-content`
- **Demo Endpoint:** `/api/v1/ai/generate-content-demo` 