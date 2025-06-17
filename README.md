# 🦅 Crow's Eye Marketing Agent

<div align="center">
  <h3>Complete AI-Powered Social Media Management Platform</h3>
  <p>Multi-platform content creation, scheduling, analytics, and automation with cutting-edge AI integration</p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
  [![PySide6](https://img.shields.io/badge/PySide6-6.9-green.svg)](https://www.qt.io/qt-for-python)
  [![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://ai.google.dev)
</div>

## 📋 Table of Contents
- [Features Overview](#-features-overview)
- [Complete Application Map](#-complete-application-map)
- [Installation Guide](#-installation-guide)
- [Desktop Application](#-desktop-application)
- [API Documentation](#-api-documentation)
- [Platform Integrations](#-platform-integrations)
- [Development](#-development)
- [Deployment](#-deployment)
- [Usage Examples](#-usage-examples)

## ✨ Features Overview

### 🎯 **Multi-Platform Social Media Management**
- **Instagram**: Posts, Stories, Reels, Carousels with advanced scheduling
- **TikTok**: Videos and Photo Carousels with trending optimization  
- **Pinterest**: Pins and Board management with SEO optimization
- **YouTube**: Video uploads, Shorts, and channel management
- **BlueSky**: Decentralized social posting with AT Protocol
- **Google Business**: Local business updates and posts
- **Threads**: Meta's Twitter alternative integration
- **Snapchat**: Snap and Story posting
- **WhatsApp Business**: Automated messaging and status updates

### 🤖 **Advanced AI Content Creation**
- **Imagen 3 Integration**: Generate stunning images from text prompts
- **Veo Video Generation**: Create professional videos with AI (Google's latest models)
- **Smart Content Optimization**: AI-powered hashtags, captions, and timing
- **Performance Analytics**: AI-driven insights and recommendations
- **Content Enhancement**: Automatic image editing and video processing
- **Highlight Reel Generator**: AI-powered video compilation creation
- **Story Assistant**: AI-generated story content and formatting

### 📊 **Professional Features**
- **Subscription Management**: Tiered access control (Free/Pro/Enterprise)
- **Advanced Analytics**: Cross-platform performance tracking
- **Bulk Operations**: Mass content creation and scheduling
- **Team Collaboration**: Multi-user workspace management
- **Video Processing**: Thumbnail generation, highlight reels, editing suite
- **Google Photos Integration**: Direct import and management
- **Media Library**: Organized asset management with AI tagging
- **Template System**: Reusable post templates and presets

## 🗺️ Complete Application Map

### **Desktop Application (PySide6)**

#### **Main Window** (`main_window.py`)
- **Header Section**
  - Logo and branding
  - User authentication status
  - Language selector (10 languages supported)
  - Theme toggle (Dark/Light mode)

- **Subscription Status Widget**
  - Current tier display (Free/Pro/Enterprise)
  - Usage limits and remaining quota
  - Upgrade button → Opens upgrade dialog

- **Media Section (Left Panel)**
  - **Media Display Area**
    - Current media preview
    - Toggle between original/edited view
    - Drag & drop functionality
  - **Media Control Buttons**
    - `Select Media` → Opens file browser
    - `Edit Image` → Opens image editing dialog
    - `Add to Library` → Saves to media library
    - `Remove Media` → Clears current selection

- **Text Sections (Right Panel)**
  - **Caption Generator**
    - Text input area
    - AI enhancement button
    - Character count display
    - Platform-specific formatting options
  - **Context Files Panel**
    - Knowledge base file selector
    - Upload context documents
    - AI training data management
  - **Post Options**
    - Platform selection checkboxes
    - Scheduling options
    - Post type selection (Post/Story/Reel)

- **Button Section (Bottom)**
  - `Generate` → Creates AI-powered content
  - `Cancel` → Stops current operation
  - `Login` → Opens authentication dialog
  - `Connect Platforms` → Opens platform connection dialog
  - `Open Library` → Opens media library window
  - `Schedule Posts` → Opens scheduling panel
  - `Knowledge Base` → Opens knowledge management
  - `Settings` → Opens application settings

#### **Menu Bar**
- **File Menu**
  - `New Project` → Creates new content project
  - `Open Library` → Opens media library
  - `Export Data` → Exports user data
  - `Import Settings` → Imports configuration
  - `Exit` → Closes application

- **Edit Menu**
  - `Undo/Redo` → Standard editing operations
  - `Copy/Paste` → Content operations
  - `Select All` → Selects all content
  - `Find/Replace` → Text search operations

- **View Menu**
  - `Toggle Media View` → Shows/hides media panel
  - `Toggle Fullscreen` → Fullscreen mode
  - `Zoom In/Out` → Content scaling
  - `Reset View` → Default layout

- **Tools Menu**
  - `AI Content Generator` → Opens AI tools
  - `Bulk Operations` → Mass content processing
  - `Analytics Dashboard` → Performance metrics
  - `Compliance Checker` → Platform compliance
  - `Video Processor` → Video editing tools
  - `Audio Overlay` → Audio editing tools
  - `Thumbnail Generator` → Video thumbnail creation
  - `Highlight Reel Creator` → Video compilation
  - `Story Assistant` → Story content creation
  - `Custom Media Upload` → Advanced upload options

- **Settings Menu**
  - `API Configuration` → API key management
  - `Platform Settings` → Social media accounts
  - `Subscription Settings` → Billing and features
  - `Language` → Localization options
  - `Theme` → Visual appearance
  - `Factory Reset` → Reset all settings

- **Help Menu**
  - `User Guide` → Opens documentation
  - `Privacy Policy` → Privacy information
  - `About` → Application information
  - `Check Updates` → Version checking

### **Dialog Windows**

#### **Authentication Dialogs**
1. **Modern Login Dialog** (`modern_login_dialog.py`)
   - Email/username input
   - Password input with visibility toggle
   - Remember me checkbox
   - Login button
   - Create account link
   - Forgot password link

2. **Unified Connection Dialog** (`unified_connection_dialog.py`)
   - Platform selection tabs
   - OAuth authentication flows
   - API key configuration
   - Connection status indicators
   - Test connection buttons
   - Save credentials options

#### **Content Creation Dialogs**
3. **Create Post Dialog** (`create_post_dialog.py`)
   - Media upload area
   - Caption editor with AI assistance
   - Platform selection grid
   - Publishing options
   - Preview button
   - Schedule later option

4. **Create Media Dialog** (`create_media_dialog.py`)
   - AI image generation
   - Prompt input field
   - Style selection dropdown
   - Aspect ratio options
   - Generate button
   - Download/save options

5. **Enhanced Carousel Builder** (`enhanced_carousel_builder.py`)
   - Multi-image selection
   - Drag & drop reordering
   - Individual image editing
   - Transition effects
   - Caption per slide
   - Preview carousel

#### **AI-Powered Dialogs**
6. **Story Assistant Dialog** (`story_assistant_dialog.py`)
   - Story type selection
   - AI content generation
   - Template library
   - Custom prompts
   - Platform optimization
   - Batch story creation

7. **Highlight Reel Dialog** (`highlight_reel_dialog.py`)
   - Video selection from library
   - AI highlight detection
   - Manual clip selection
   - Transition effects
   - Music overlay
   - Export options

8. **Audio Overlay Dialog** (`audio_overlay_dialog.py`)
   - Audio file upload
   - Volume control sliders
   - Fade in/out options
   - Audio trimming tools
   - Preview playback
   - Export settings

#### **Management Dialogs**
9. **Scheduling Dialog** (`scheduling_dialog.py`)
   - Calendar view
   - Time zone selection
   - Recurring post options
   - Platform-specific timing
   - Batch scheduling
   - Schedule preview

10. **Analytics Dashboard Dialog** (`analytics_dashboard_dialog.py`)
    - Performance metrics charts
    - Engagement statistics
    - Platform comparison
    - Date range selector
    - Export reports
    - AI insights panel

11. **Compliance Dialog** (`compliance_dialog.py`)
    - Platform requirements check
    - Content compliance status
    - Automated fixes
    - Manual override options
    - Compliance history
    - Export compliance report

#### **Media Management Dialogs**
12. **Gallery Viewer Dialog** (`gallery_viewer_dialog.py`)
    - Grid/list view toggle
    - Search and filter options
    - Bulk selection tools
    - Delete/organize options
    - Export selected media
    - AI tagging display

13. **Image Edit Dialog** (`image_edit_dialog.py`)
    - Crop/resize tools
    - Filter applications
    - Color adjustments
    - Text overlay options
    - Undo/redo functionality
    - Save/export options

14. **Video Processing Dialog** (`video_processing_dialog.py`)
    - Video trimming
    - Quality adjustment
    - Format conversion
    - Thumbnail extraction
    - Preview window
    - Processing progress

#### **Utility Dialogs**
15. **Google Photos Browser Dialog** (`google_photos_browser_dialog.py`)
    - Google Photos authentication
    - Album browsing
    - Photo/video selection
    - Bulk import options
    - Search functionality
    - Direct posting integration

16. **Thumbnail Selector Dialog** (`thumbnail_selector_dialog.py`)
    - AI-generated thumbnails
    - Custom thumbnail upload
    - Template selection
    - Text overlay options
    - Preview comparisons
    - A/B testing setup

17. **Custom Media Upload Dialog** (`custom_media_upload_dialog.py`)
    - Drag & drop upload
    - Multiple file selection
    - Progress tracking
    - Metadata editing
    - Quality settings
    - Batch processing

### **API Endpoints** (FastAPI Backend)

#### **Authentication Endpoints** (`/api/v1/`)
- `POST /login` → User authentication
- `POST /logout` → User logout
- `GET /users/me` → Current user info
- `PUT /users/me` → Update user profile

#### **Media Management** (`/api/v1/media/`)
- `GET /` → List all media
- `POST /upload` → Upload new media
- `GET /{id}` → Get specific media
- `PUT /{id}` → Update media metadata
- `DELETE /{id}` → Delete media
- `POST /{id}/process` → Process media with AI

#### **AI Services** (`/api/v1/ai/`)
- `POST /generate-image` → Generate images with Imagen 3
- `POST /generate-video` → Generate videos with Veo
- `POST /generate-caption` → AI caption generation
- `POST /generate-hashtags` → Hashtag suggestions
- `POST /enhance-image` → Image enhancement
- `POST /create-highlight` → Video highlight creation
- `POST /optimize-content` → Content optimization

#### **Social Media Platforms** (`/api/v1/platforms/`)
- `GET /` → List connected platforms
- `POST /{platform}/connect` → Connect platform account
- `GET /{platform}/status` → Check connection status
- `POST /{platform}/post` → Publish to platform
- `GET /{platform}/analytics` → Platform analytics
- `GET /requirements` → Platform-specific requirements

#### **Content Scheduling** (`/api/v1/schedules/`)
- `GET /` → List scheduled posts
- `POST /` → Create scheduled post
- `PUT /{id}` → Update scheduled post
- `DELETE /{id}` → Cancel scheduled post
- `POST /{id}/execute` → Execute schedule immediately

#### **Analytics** (`/api/v1/analytics/`)
- `GET /overview` → Overall performance metrics
- `GET /platform/{platform}` → Platform-specific analytics
- `GET /posts/{post_id}` → Individual post analytics
- `GET /reports/export` → Export analytics report

#### **Google Photos Integration** (`/api/v1/google-photos/`)
- `GET /auth` → Google Photos authentication
- `GET /albums` → List Google Photos albums
- `GET /media` → List Google Photos media
- `POST /import` → Import from Google Photos
- `GET /search` → Search Google Photos

#### **Bulk Operations** (`/api/v1/bulk/`)
- `POST /upload` → Bulk media upload
- `POST /schedule` → Bulk scheduling
- `POST /process` → Bulk media processing
- `GET /status/{job_id}` → Check bulk operation status

#### **Platform Compliance** (`/api/v1/compliance/`)
- `POST /check` → Check content compliance
- `POST /fix` → Auto-fix compliance issues
- `GET /requirements/{platform}` → Platform requirements
- `GET /history` → Compliance check history

## 🚀 Installation Guide

### Prerequisites
- **Python 3.8+** with pip
- **FFmpeg** (for video processing)
- **Git** (for cloning the repository)
- **Google Cloud Account** (for AI services)
- **Social Media API Keys** (for platform integrations)

### Quick Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/charliesuarez/crows-eye-marketing-suite.git
   cd crows-eye-marketing-suite/social_media_tool_v5_noMeta_final
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy environment template
   copy templates/meta_credentials_template.json .env
   
   # Edit with your API keys
   notepad .env  # Windows
   nano .env     # Linux/Mac
   ```

4. **Initialize database**
   ```bash
   python initialize_minimal_db.py
   ```

5. **Launch the application**
   ```bash
   # Desktop Application
   python main.py
   
   # API Server
   python start_api.py
   
   # Both (recommended)
   python scripts/run_with_scheduling.py
   ```

### Environment Configuration

Create `.env` file with these variables:
```env
# Google AI Services
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket_name

# Social Media APIs
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
TIKTOK_CLIENT_ID=your_tiktok_client_id
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
PINTEREST_APP_ID=your_pinterest_app_id
PINTEREST_APP_SECRET=your_pinterest_app_secret
YOUTUBE_API_KEY=your_youtube_api_key
BLUESKY_USERNAME=your_bluesky_username
BLUESKY_PASSWORD=your_bluesky_password

# Database Configuration
DATABASE_URL=sqlite:///./data/crow_eye.db
# For PostgreSQL: postgresql+asyncpg://user:pass@localhost/dbname

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: External Services
WEBHOOK_URL=your_webhook_url
ANALYTICS_ENDPOINT=your_analytics_endpoint
```

## 🖥️ Desktop Application

### Main Interface Walkthrough

1. **Launch Application**: Run `python main.py`
2. **First-Time Setup**:
   - Choose language from dropdown (top-right)
   - Click `Login` to authenticate
   - Click `Connect Platforms` to link social media accounts
   - Select media from `Select Media` button
   - Enter caption in text area
   - Click `Generate` to create AI-enhanced content

3. **Content Creation Workflow**:
   - **Step 1**: Select or upload media (images/videos)
   - **Step 2**: Add context files for AI training
   - **Step 3**: Generate AI-powered captions and hashtags
   - **Step 4**: Select target platforms
   - **Step 5**: Schedule or post immediately

4. **Advanced Features**:
   - **Library Management**: Organize all media assets
   - **Bulk Operations**: Process multiple posts simultaneously
   - **Analytics**: Track performance across platforms
   - **Compliance**: Ensure platform-specific requirements

### Keyboard Shortcuts
- `Ctrl+N`: New project
- `Ctrl+O`: Open library
- `Ctrl+S`: Save current work
- `Ctrl+G`: Generate content
- `Ctrl+L`: Open library
- `Ctrl+K`: Open knowledge base
- `F5`: Refresh content
- `F11`: Toggle fullscreen

## 🌐 API Documentation

### Running the API Server

```bash
# Development server
python crow_eye_api/main.py

# Production server with Gunicorn
gunicorn -k uvicorn.workers.UvicornWorker crow_eye_api.main:app

# Using the provided script
python start_api.py
```

### API Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Interactive Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

### Authentication
Most endpoints require authentication via JWT tokens:

```python
# Login to get token
response = requests.post("/api/v1/login", {
    "username": "your_username",
    "password": "your_password"
})
token = response.json()["access_token"]

# Use token in headers
headers = {"Authorization": f"Bearer {token}"}
```

### Example API Usage

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Generate AI image
response = requests.post(f"{BASE_URL}/ai/generate-image", 
    headers=headers,
    json={
        "prompt": "A professional headshot for LinkedIn",
        "style": "professional",
        "aspect_ratio": "1:1"
    }
)

# Schedule a post
response = requests.post(f"{BASE_URL}/schedules/", 
    headers=headers,
    json={
        "content": "Check out our latest product!",
        "media_ids": ["media_123"],
        "platforms": ["instagram", "facebook"],
        "scheduled_time": "2024-12-25T12:00:00Z"
    }
)
```

## 🔗 Platform Integrations

### Instagram
- **Features**: Posts, Stories, Reels, IGTV
- **Requirements**: Business account, Meta App approval
- **Setup**: Connect via Meta Business API
- **Limitations**: Publishing API requires app review

### TikTok
- **Features**: Video posts, photo carousels
- **Requirements**: TikTok for Business account
- **Setup**: TikTok Content Posting API
- **Limitations**: Video duration 15s-10min

### Pinterest
- **Features**: Pins, boards, story pins
- **Requirements**: Pinterest Business account
- **Setup**: Pinterest API v5
- **Limitations**: 25 API calls per day (free tier)

### YouTube
- **Features**: Video uploads, thumbnails, playlists
- **Requirements**: YouTube channel, Google Cloud project
- **Setup**: YouTube Data API v3
- **Limitations**: Daily quota limits

### BlueSky
- **Features**: Text posts, image posts
- **Requirements**: BlueSky account
- **Setup**: AT Protocol integration
- **Limitations**: Decentralized network limitations

### Google Business
- **Features**: Local posts, events, offers
- **Requirements**: Google My Business account
- **Setup**: Google My Business API
- **Limitations**: Location-based posting only

## 🛠️ Development

### Project Structure
```
social_media_tool_v5_noMeta_final/
├── 🐍 src/                     # Desktop application source
│   ├── 🔌 api/                 # Platform API integrations
│   ├── ⚡ features/            # Core business logic
│   ├── 🎨 ui/                  # PySide6 user interface
│   ├── ⚙️ config/              # Configuration management
│   ├── 🛠️ utils/               # Utility functions
│   └── 📦 resources/           # Assets and styles
├── 🌐 crow_eye_api/            # FastAPI REST API server
│   ├── 📡 api/                 # API endpoints
│   ├── 🏗️ core/                # Core configuration
│   ├── 💾 crud/                # Database operations
│   ├── 📊 models/              # Database models
│   ├── 📋 schemas/             # Pydantic schemas
│   └── 🔧 services/            # Business services
├── 📚 docs/                    # Documentation
├── 🧪 tests/                   # Test suites
├── 🎨 assets/                  # Static assets
├── 🌍 translations/            # Internationalization
├── 📦 data/                    # Application data
└── 🚀 scripts/                 # Deployment scripts
```

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov
   ```

2. **Set up pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Run tests**
   ```bash
   # All tests
   pytest tests/ -v
   
   # Unit tests only
   pytest tests/unit/ -v
   
   # Integration tests
   pytest tests/integration/ -v
   
   # API tests
   pytest tests/api/ -v
   ```

4. **Code quality checks**
   ```bash
   # Format code
   black src/ crow_eye_api/
   
   # Check imports
   isort src/ crow_eye_api/
   
   # Lint code
   flake8 src/ crow_eye_api/
   
   # Type checking
   mypy src/ crow_eye_api/
   ```

### Adding New Features

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Implement feature** following the existing patterns
3. **Add tests** for new functionality
4. **Update documentation** including this README
5. **Submit pull request** with detailed description

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🚀 Deployment

### Google Cloud Deployment

1. **Set up Google Cloud Project**
   ```bash
   gcloud project create your-project-id
   gcloud config set project your-project-id
   gcloud services enable appengine.googleapis.com
   ```

2. **Deploy API to App Engine**
   ```bash
   # Using provided script
   python deploy_to_gcloud.py
   
   # Manual deployment
   gcloud app deploy app.yaml
   ```

3. **Set up Cloud SQL (optional)**
   ```bash
   gcloud sql instances create crow-eye-db --database-version=POSTGRES_13
   gcloud sql databases create crow_eye --instance=crow-eye-db
   ```

### Docker Deployment

1. **Build Docker image**
   ```bash
   docker build -t crow-eye-api .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Deploy to cloud platforms**
   ```bash
   # AWS ECS
   aws ecs create-service --service-name crow-eye-api
   
   # Google Cloud Run
   gcloud run deploy --image gcr.io/project-id/crow-eye-api
   
   # Azure Container Instances
   az container create --name crow-eye-api
   ```

### Desktop Application Packaging

1. **Create executable with PyInstaller**
   ```bash
   python -m PyInstaller --onefile --windowed main.py
   ```

2. **Create installer** (Windows)
   ```bash
   # Using NSIS
   makensis installer.nsi
   ```

3. **Create app bundle** (macOS)
   ```bash
   python setup.py py2app
   ```

## 💡 Usage Examples

### Basic Content Creation
```python
# Desktop app workflow
1. Launch app: python main.py
2. Login with credentials
3. Select media file
4. Add caption: "Check out our new product! #innovation"
5. Select platforms: Instagram, Facebook
6. Click Generate for AI enhancement
7. Click Schedule or Post Now
```

### API Integration
```python
import requests

# Create scheduled post via API
api_url = "http://localhost:8000/api/v1"
headers = {"Authorization": "Bearer your_token"}

# Upload media
files = {'file': open('image.jpg', 'rb')}
media_response = requests.post(f"{api_url}/media/upload", 
                              files=files, headers=headers)
media_id = media_response.json()['id']

# Schedule post
post_data = {
    "content": "Exciting news coming soon! 🚀",
    "media_ids": [media_id],
    "platforms": ["instagram", "twitter"],
    "scheduled_time": "2024-12-25T12:00:00Z"
}
requests.post(f"{api_url}/schedules/", json=post_data, headers=headers)
```

### Bulk Operations
```python
# Bulk upload and schedule
media_files = ['img1.jpg', 'img2.jpg', 'img3.jpg']
captions = ['Caption 1', 'Caption 2', 'Caption 3']

for media, caption in zip(media_files, captions):
    # Upload media
    files = {'file': open(media, 'rb')}
    media_resp = requests.post(f"{api_url}/media/upload", 
                              files=files, headers=headers)
    
    # Schedule post
    post_data = {
        "content": caption,
        "media_ids": [media_resp.json()['id']],
        "platforms": ["instagram"],
        "scheduled_time": f"2024-12-{25+i}T12:00:00Z"
    }
    requests.post(f"{api_url}/schedules/", json=post_data, headers=headers)
```

## 🔒 Security & Privacy

- **Local Data Storage**: All user data stored locally by default
- **API Key Encryption**: Secure credential management with bcrypt
- **GDPR Compliant**: Privacy-first design with data export options
- **No Data Collection**: Optional telemetry only with user consent
- **Secure Authentication**: OAuth 2.0 for social media platforms
- **Rate Limiting**: API protection against abuse
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Protection**: Parameterized queries throughout

## 📖 API Rate Limits

### Free Tier
- 100 requests per hour
- 5 AI generations per day
- 10 scheduled posts per month

### Pro Tier
- 1000 requests per hour
- 100 AI generations per day
- 1000 scheduled posts per month

### Enterprise Tier
- 10000 requests per hour
- Unlimited AI generations
- Unlimited scheduled posts

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Documentation**: [Full Documentation](./docs/)
- **Issues**: [GitHub Issues](https://github.com/charliesuarez/crows-eye-marketing-suite/issues)
- **Email**: charlie@suarezhouse.net
- **Discord**: [Community Server](https://discord.gg/your-server)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google AI team for Imagen 3 and Veo APIs
- FastAPI community for excellent framework
- Qt/PySide6 team for desktop UI framework
- Social media platform APIs for integration support

---

<div align="center">
  <p>Made with ❤️ by Charles Suarez</p>
  <p>⭐ Star this repo if you find it helpful!</p>
</div>