# 🚀 Crow's Eye Desktop → Website Migration Guide

## 📋 Overview

This guide documents **every feature, algorithm, and workflow** from your desktop application so you can replicate the exact functionality on your website. This is a complete technical blueprint of how each feature works.

---

## 🎯 **1. AI CONTENT GENERATION SYSTEM**

### **Core Algorithm: `generate_content_with_gemini()`**

**Location:** `crow_eye_api/services/ai_content_service.py:168-297`

#### **How It Works:**
1. **Image Analysis** → Uses Gemini Vision to analyze uploaded images
2. **Context Processing** → Processes brand guidelines and context files
3. **Platform Optimization** → Adapts content for specific platform character limits
4. **Caption Generation** → Creates unique, engaging captions
5. **Hashtag Generation** → Generates relevant hashtags using AI

#### **Key Parameters:**
```python
platform_limits = {
    "instagram": 2200,
    "facebook": 63206,
    "twitter": 280,
    "linkedin": 3000,
    "tiktok": 4000,
    "youtube": 5000,
    "pinterest": 500,
    "snapchat": 250
}
```

#### **Prompt Engineering Strategy:**
```python
caption_prompt = f"""Based on this image analysis: {image_analysis.get('image_description', '')}

User instruction: {context_instructions}
Target platforms: {', '.join(platforms)}
Character limit: {max_chars} characters
{f"Additional context: {context_content}" if context_content else ""}

Generate a unique, engaging caption that:
- References specific details from the image
- Matches the requested tone ({context_instructions})
- Feels authentic and conversational
- Includes relevant emojis naturally
- Ends with an engaging question or call-to-action
- Varies significantly from any previous captions
- Stays within {max_chars} characters

IMPORTANT: Be creative and unique. Avoid generic templates. Make it feel personal and engaging."""
```

#### **Website Implementation:**
- Use Google Gemini Vision API for image analysis
- Implement character limit validation per platform
- Add context file upload functionality
- Create tone/style selection interface
- Implement caption uniqueness checking

---

## 🎬 **2. HIGHLIGHT GENERATION SYSTEM**

### **Core Algorithm: `generate_highlight_reel()`**

**Location:** `crow_eye_api/services/highlight.py:33-232`

#### **How It Works:**
1. **Video Download** → Downloads video from storage to temp location
2. **VideoHandler Import** → Dynamically imports desktop VideoHandler
3. **Motion Analysis** → Analyzes video for high-motion segments
4. **Scene Detection** → Identifies interesting scenes using AI
5. **Highlight Assembly** → Combines best segments into highlight reel
6. **Style Application** → Applies requested style (dynamic, minimal, elegant)
7. **Upload Result** → Saves to cloud storage

#### **Key Parameters:**
```python
target_duration: int = 30,           # Target duration in seconds
highlight_type: str = "story",       # "story", "reel", "short"
style: str = "dynamic",              # "dynamic", "minimal", "elegant"
include_text: bool = True,           # Text overlays
include_music: bool = False,         # Background music
context_padding: float = 2.0         # Context before/after scenes
```

#### **Motion Detection Algorithm:**
```python
def _calculate_frame_motion(self, frames: List[np.ndarray]) -> float:
    # Convert frames to grayscale
    gray_frames = [np.dot(frame[...,:3], [0.299, 0.587, 0.114]) for frame in frames]
    
    # Calculate motion as average frame difference
    motion_scores = []
    for i in range(len(gray_frames) - 1):
        diff = np.abs(gray_frames[i+1] - gray_frames[i])
        motion_score = np.mean(diff) / 255.0  # Normalize to 0-1
        motion_scores.append(motion_score)
    
    return np.mean(motion_scores) if motion_scores else 0.0
```

#### **Website Implementation:**
- Use FFmpeg for video processing
- Implement motion detection algorithms
- Add style templates (dynamic, minimal, elegant)
- Create progress tracking for long operations
- Implement thumbnail generation

---

## 📅 **3. CAMPAIGN SCHEDULING SYSTEM**

### **Core Algorithm: Campaign Management**

**Location:** `crow_eye_api/models/schedule.py` & `crow_eye_api/services/campaign_service.py`

#### **How It Works:**
1. **Campaign Creation** → Define posting rules and schedules
2. **Time Slot Calculation** → Distribute posts across campaign duration
3. **Platform Optimization** → Adjust times for platform best practices
4. **Queue Management** → Maintain ordered list of upcoming posts
5. **Intelligent Scheduling** → Skip weekends/holidays based on rules

#### **Campaign Rules Engine:**
```python
class Campaign:
    posts_per_day: int = 1              # 1-10 posts per day
    posting_times: JSON                 # ["09:00", "13:00", "18:00"]
    platforms: JSON                     # ["instagram", "tiktok", "facebook"]
    skip_weekends: bool = False         # Skip Saturday/Sunday
    skip_holidays: bool = False         # Skip holidays
    minimum_interval_minutes: int = 60  # Min time between posts
    randomize_times: bool = False       # Add randomness
    randomize_order: bool = False       # Randomize post order
```

#### **Scheduling Algorithm:**
1. Calculate total days in campaign period
2. Determine posting slots per day based on `posts_per_day`
3. Apply platform-specific optimal times
4. Filter out weekends/holidays if enabled
5. Add randomization if requested
6. Ensure minimum intervals between posts

#### **Website Implementation:**
- Create campaign wizard interface
- Implement calendar view for scheduled posts
- Add platform-specific time optimization
- Create queue management dashboard
- Implement holiday/weekend filtering

---

## 📊 **4. ANALYTICS & TRACKING SYSTEM**

### **Core Algorithm: Performance Tracking**

**Location:** `src/handlers/analytics_handler.py:18-149`

#### **How It Works:**
1. **Post Creation Tracking** → Assigns unique ID to each post
2. **Metrics Collection** → Tracks views, likes, shares, comments
3. **Engagement Calculation** → Computes engagement rates
4. **Performance History** → Maintains historical data
5. **Export Functionality** → Generates CSV reports

#### **Tracked Metrics:**
```python
metrics = {
    "views": 0,
    "likes": 0,
    "shares": 0,
    "comments": 0,
    "saves": 0,
    "clicks": 0,
    "reach": 0,
    "impressions": 0
}
```

#### **Analytics Data Structure:**
```python
analytics_data = {
    "version": "1.0",
    "created": datetime.now().isoformat(),
    "posts": {},
    "galleries": {},
    "videos": {},
    "summary_stats": {
        "total_posts": 0,
        "total_galleries": 0,
        "total_videos": 0,
        "total_interactions": 0
    }
}
```

#### **Website Implementation:**
- Create analytics dashboard with charts
- Implement real-time metrics updates
- Add performance comparison tools
- Create automated reporting
- Implement export functionality

---

## 📱 **5. UNIFIED POSTING SYSTEM**

### **Core Algorithm: Multi-Platform Posting**

**Location:** `src/features/posting/unified_posting_handler.py:32-226`

#### **How It Works:**
1. **Platform Detection** → Identifies target platforms
2. **Content Optimization** → Adapts content for each platform
3. **Parallel Posting** → Posts to multiple platforms simultaneously
4. **Error Handling** → Manages platform-specific errors
5. **Status Tracking** → Reports success/failure for each platform

#### **Supported Platforms:**
```python
platforms = {
    'instagram': MetaPostingHandler,
    'facebook': MetaPostingHandler,
    'tiktok': TikTokAPIHandler,
    'google_business': GoogleBusinessAPIHandler,
    'bluesky': BlueSkyAPIHandler,
    'pinterest': PinterestAPIHandler,
    'threads': ThreadsAPIHandler,
    'youtube': YouTubeAPIHandler
}
```

#### **Posting Workflow:**
```python
def post_to_platforms(self, platforms: List[str], media_path: str, 
                     caption: str, is_video: bool = False) -> Dict[str, Tuple[bool, str]]:
    results = {}
    for platform in platforms:
        try:
            # Optimize content for platform
            optimized_content = self.optimizer_factory.optimize_for_platform(
                platform, media_path, caption, is_video
            )
            
            # Post to platform
            success, message = self._post_to_single_platform(
                platform, optimized_content['media_path'], 
                optimized_content['caption'], is_video
            )
            
            results[platform] = (success, message)
        except Exception as e:
            results[platform] = (False, str(e))
    
    return results
```

#### **Website Implementation:**
- Create platform selection interface
- Implement content optimization per platform
- Add progress tracking for multi-platform posts
- Create error handling and retry logic
- Implement posting queue management

---

## 🎨 **6. MEDIA PROCESSING SYSTEM**

### **Core Algorithm: Video Processing**

**Location:** `src/features/media_processing/video_handler.py:22-1056`

#### **How It Works:**
1. **Video Analysis** → Analyzes video properties and content
2. **Frame Extraction** → Extracts frames for analysis
3. **Motion Detection** → Identifies high-motion segments
4. **Scene Segmentation** → Breaks video into logical scenes
5. **Quality Enhancement** → Applies filters and improvements
6. **Format Optimization** → Converts to platform-specific formats

#### **Video Processing Pipeline:**
```python
def process_video_with_services(self, video_path: str, 
                               selected_services: Dict[str, bool]) -> Tuple[bool, str, str]:
    """
    Available services:
    - color_correction: Enhance colors and contrast
    - stabilization: Reduce camera shake
    - noise_reduction: Remove video noise
    - auto_crop: Intelligent cropping
    - speed_adjustment: Change playback speed
    - format_conversion: Convert to different formats
    """
```

#### **Motion Analysis Algorithm:**
```python
def _prefilter_segments_by_motion(self, clip, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    # Extract frames from each segment
    # Calculate motion scores using frame differencing
    # Select segments with motion above threshold
    # Return filtered segments sorted by motion score
```

#### **Website Implementation:**
- Use FFmpeg for video processing
- Implement web-based video player
- Add real-time processing progress
- Create video editing interface
- Implement format conversion tools

---

## 📝 **7. POST CREATION WORKFLOW**

### **Core Algorithm: Post Assembly**

**Location:** `src/ui/dialogs/post_creation_dialog.py:681-880`

#### **How It Works:**
1. **Media Selection** → User selects image/video
2. **Content Generation** → AI generates caption and hashtags
3. **Platform Selection** → User chooses target platforms
4. **Scheduling Options** → Post now, queue, or schedule
5. **Library Addition** → Saves to content library
6. **Publishing** → Executes posting workflow

#### **Post Data Structure:**
```python
post_data = {
    "caption": str,
    "instructions": str,
    "editing_instructions": str,
    "context_files": List[str],
    "platforms": List[str],
    "creation_date": str,
    "media_type": str,
    "scheduled_time": Optional[str],
    "publish_immediately": bool,
    "add_to_queue": bool
}
```

#### **Publishing Workflow:**
```python
def _add_to_library_and_publish(self, post_data):
    # 1. Add to library first
    self._add_to_library_with_data(post_data)
    
    # 2. Handle publishing based on options
    if post_data.get('publish_immediately'):
        # Immediate publishing
        self.unified_posting_handler.post_to_platforms(...)
    elif post_data.get('add_to_queue'):
        # Add to scheduling queue
        self.scheduler.add_to_queue(post_data)
    else:
        # Scheduled post
        self.scheduler.schedule_post(post_data)
```

#### **Website Implementation:**
- Create drag-and-drop media upload
- Implement AI content generation interface
- Add platform selection with previews
- Create scheduling calendar interface
- Implement content library management

---

## 🔧 **8. MEDIA EDITING SYSTEM**

### **Core Algorithm: Image Enhancement**

**Location:** `crow_eye_api/services/ai_content_service.py:297-367`

#### **How It Works:**
1. **Instruction Parsing** → Analyzes natural language instructions
2. **Filter Application** → Applies PIL-based image filters
3. **Enhancement Processing** → Brightness, contrast, saturation adjustments
4. **Effect Application** → Vintage, sepia, black & white effects
5. **Quality Optimization** → Optimizes for web/mobile viewing

#### **Editing Operations:**
```python
async def _apply_basic_edits(self, image: Image.Image, instructions: str) -> Image.Image:
    instructions_lower = instructions.lower()
    
    # Brightness adjustments
    if "brighter" in instructions_lower:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.3)
    
    # Contrast adjustments
    if "contrast" in instructions_lower:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
    
    # Saturation adjustments
    if "vibrant" in instructions_lower:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.4)
    
    # Filter effects
    if "vintage" in instructions_lower:
        image = self._apply_vintage_filter(image)
    
    return image
```

#### **Website Implementation:**
- Create web-based image editor
- Implement real-time preview
- Add preset filters and effects
- Create natural language processing for edit instructions
- Implement undo/redo functionality

---

## 🗂️ **9. CONTENT LIBRARY SYSTEM**

### **Core Algorithm: Library Management**

**Location:** Various library management files

#### **How It Works:**
1. **Media Indexing** → Catalogs all uploaded media
2. **Metadata Extraction** → Extracts EXIF, duration, dimensions
3. **AI Tagging** → Automatically tags content
4. **Search & Filter** → Enables content discovery
5. **Organization** → Folders, collections, categories

#### **Library Data Structure:**
```python
library_item = {
    "id": str,
    "filename": str,
    "media_type": str,  # "image", "video", "audio"
    "file_size": int,
    "dimensions": {"width": int, "height": int},
    "duration": Optional[float],
    "ai_tags": List[str],
    "caption": Optional[str],
    "metadata": Dict[str, Any],
    "is_post_ready": bool,
    "created_at": str,
    "last_used": Optional[str]
}
```

#### **Website Implementation:**
- Create grid/list view for media library
- Implement search and filtering
- Add batch operations
- Create folder/collection system
- Implement AI-powered tagging

---

## 🚀 **10. DEPLOYMENT & INFRASTRUCTURE**

### **Current Architecture:**
- **Backend:** FastAPI with PostgreSQL
- **Storage:** Google Cloud Storage
- **AI:** Google Gemini Vision API
- **Deployment:** Google Cloud App Engine

### **Migration Checklist:**

#### **✅ Phase 1: Core Features**
- [ ] AI Content Generation with Gemini Vision
- [ ] Multi-platform posting system
- [ ] Basic media library
- [ ] User authentication and subscriptions

#### **✅ Phase 2: Advanced Features**
- [ ] Highlight generation system
- [ ] Campaign scheduling
- [ ] Analytics dashboard
- [ ] Media editing tools

#### **✅ Phase 3: Optimization**
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Advanced analytics
- [ ] Bulk operations

---

## 📋 **11. IMPLEMENTATION PRIORITIES**

### **High Priority (Core Functionality):**
1. **AI Content Generation** - Your main differentiator
2. **Multi-Platform Posting** - Core business value
3. **Media Library** - Essential for content management
4. **User Authentication** - Required for access control

### **Medium Priority (Enhanced Experience):**
1. **Scheduling System** - Valuable for users
2. **Basic Analytics** - Important for user retention
3. **Media Editing** - Nice-to-have enhancement
4. **Highlight Generation** - Advanced feature

### **Low Priority (Polish):**
1. **Advanced Analytics** - Can be added later
2. **Bulk Operations** - Convenience feature
3. **Advanced Scheduling** - Power user feature

---

## 🔗 **12. API ENDPOINTS TO PRESERVE**

Keep these existing API endpoints that are working well:

```
POST /api/v1/ai/generate-content         # AI content generation
POST /api/v1/posts/                      # Post creation
GET  /api/v1/media/                      # Media library
POST /api/v1/campaigns/                  # Campaign management
GET  /api/v1/analytics/                  # Analytics data
POST /api/v1/auth/login                  # Authentication
GET  /api/v1/subscription                # Subscription status
```

---

## 💡 **Next Steps**

1. **Review this guide** - Make sure I captured everything correctly
2. **Prioritize features** - Decide what to implement first
3. **Design website UI** - Create mockups based on desktop functionality
4. **Start with AI content generation** - It's your core differentiator
5. **Migrate user data** - Ensure seamless transition

Would you like me to elaborate on any specific feature or create detailed implementation specs for particular components? 