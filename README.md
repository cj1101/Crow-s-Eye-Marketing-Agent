# 🦅 Crow's Eye Marketing Agent

<div align="center">
  <h3>AI-Powered Social Media Management Platform</h3>
  <p>Multi-platform content creation, scheduling, and analytics with cutting-edge AI integration</p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![PySide6](https://img.shields.io/badge/PySide6-6.9-green.svg)](https://www.qt.io/qt-for-python)
  [![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://ai.google.dev)
</div>

## ✨ Features

### 🎯 **Multi-Platform Social Media Management**
- **Instagram**: Posts, Stories, Reels with advanced scheduling
- **TikTok**: Videos and Photo Carousels with trending optimization  
- **Pinterest**: Pins and Board management with SEO optimization
- **YouTube**: Video uploads, Shorts, and channel management
- **BlueSky**: Decentralized social posting with AT Protocol
- **Google Business**: Local business updates and posts

### 🤖 **Advanced AI Content Creation**
- **Imagen 3 Integration**: Generate stunning images from text prompts
- **Veo Video Generation**: Create professional videos with AI (latest models)
- **Smart Content Optimization**: AI-powered hashtags, captions, and timing
- **Performance Analytics**: AI-driven insights and recommendations
- **Content Enhancement**: Automatic image editing and video processing

### 📊 **Professional Features**
- **Subscription Management**: Tiered access control (Free/Pro/Enterprise)
- **Advanced Analytics**: Cross-platform performance tracking
- **Bulk Operations**: Mass content creation and scheduling
- **Team Collaboration**: Multi-user workspace management
- **Video Processing**: Thumbnail generation, highlight reels, editing suite

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** 
- **FFmpeg** (for video processing)
- **Git** (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cj1101/Crow-s-Eye-Marketing-Agent.git
   cd Crow-s-Eye-Marketing-Agent
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Create .env file with your API keys
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Launch the application**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Required API Keys
- **Google API Key**: Imagen 3, Veo, YouTube integration
- **Meta App Credentials**: Instagram and Facebook
- **TikTok API**: Video and carousel posting
- **Pinterest API**: Pin and board management
- **BlueSky Credentials**: Decentralized social posting

### Environment Setup
Create a `.env` file in the root directory:
```env
# Google AI Services
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Social Media APIs
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
TIKTOK_CLIENT_KEY=your_tiktok_client_key
PINTEREST_APP_ID=your_pinterest_app_id

# Optional: Database
DATABASE_URL=sqlite:///./data/crow_eye.db
```

## 📁 Project Architecture

```
📦 Crow's Eye Marketing Agent
├── 🐍 src/                     # Core Python application
│   ├── 🔌 api/                 # Social platform integrations
│   ├── ⚡ features/            # Core business logic
│   ├── 🎨 ui/                  # PySide6 user interface  
│   ├── ⚙️ config/              # Configuration management
│   ├── 🛠️ utils/               # Utility functions
│   └── 📦 resources/           # Assets and styles
├── 🌐 backend/                 # FastAPI REST API server
├── 📚 docs/                    # Documentation
├── 🧪 tests/                   # Test suites
├── 🎨 assets/                  # Static assets
├── 🌍 translations/            # Internationalization
└── 🚀 deployment/              # Deployment configurations
```

## 🎮 Usage Guide

### 1. **First Launch**
- Run `python main.py` to start the application
- Complete the initial setup wizard
- Connect your social media accounts using the unified connection dialog

### 2. **Content Creation**
- Use AI tools to generate images with Imagen 3
- Create videos with Veo AI video generation
- Edit and enhance content with built-in tools
- Preview content across different platforms

### 3. **Publishing & Scheduling**
- Schedule posts for optimal engagement times
- Use bulk operations for multiple posts
- Monitor real-time posting status
- Track cross-platform performance

### 4. **Analytics & Optimization**
- View comprehensive analytics dashboard
- Get AI-powered insights and recommendations
- Export detailed performance reports
- Optimize content strategy based on data

## 🧪 Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

### Development Mode
```bash
# Start with debug logging
python main.py --debug

# Run specific components
python -m src.ui.main_window  # UI only
python -m src.api.server      # API server only
```

### Building for Production
```bash
# Create executable with PyInstaller
python -m PyInstaller breadsmith_marketing_tool.spec

# The executable will be in dist/
```

## 🔒 Security & Privacy

- **Local Data Storage**: All user data stored locally by default
- **API Key Encryption**: Secure credential management
- **GDPR Compliant**: Privacy-first design
- **No Data Collection**: Optional telemetry only
- **Secure Authentication**: OAuth 2.0 for social media platforms

## 📖 API Documentation

The application includes a FastAPI backend server for advanced features:

### Core Endpoints
- `GET /api/health` - Health check
- `POST /api/auth/login` - User authentication
- `GET /api/platforms` - List connected platforms
- `POST /api/content/generate` - AI content generation
- `GET /api/analytics` - Performance analytics

For complete API documentation, visit `/docs` when running the server.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs on [GitHub Issues](https://github.com/cj1101/Crow-s-Eye-Marketing-Agent/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/cj1101/Crow-s-Eye-Marketing-Agent/discussions)

## 🙏 Acknowledgments

- **Google AI**: Imagen 3 and Veo integration
- **Meta**: Instagram and Facebook APIs
- **TikTok**: Video platform integration
- **Pinterest**: Visual discovery platform
- **BlueSky**: Decentralized social protocol
- **Qt/PySide6**: Cross-platform UI framework

---

<div align="center">

**🦅 Crow's Eye Marketing Agent** - *Empowering creators with AI-driven social media management*

<p>Made with ❤️ for content creators and social media professionals</p>
<p>© 2024 Crow's Eye Marketing Agent. All rights reserved.</p>

</div>