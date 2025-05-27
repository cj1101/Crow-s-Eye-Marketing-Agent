# 🐦‍⬛ Crow's Eye Marketing Platform

> *A smart marketing automation platform for creators and small businesses*

Crow's Eye is a comprehensive social media marketing tool focused on visual content for Instagram, Facebook, LinkedIn, and X (Twitter). Built with a critical lens on social media, it provides industry-best tools to help creators survive in the current landscape while encouraging healthier media habits.

## ✨ Features

### 🟢 Free Tier
- **📁 Media Library**: Upload and organize raw photos, videos, and post-ready content
- **🧠 Smart Gallery Generator**: AI-powered gallery creation with natural language prompts
- **📲 Post Formatting**: Single image, carousel, and story optimization
- **🔍 Smart Media Search**: Google Photos-like content search
- **🌍 Multi-Language Support**: 11 languages including Spanish, French, German, and more

### 💎 Pro Tier ($5/month)
- **🎬 Veo Video Generator**: Google Veo 3 AI video generation with quality presets
- **🎞 Highlight Reel Generator**: AI-powered video editing and highlight creation
- **🎧 Audio Importer**: Natural language audio editing and overlay
- **🎥 Story Assistant**: Automatic story formatting and optimization
- **📊 Performance Analytics**: Internal tracking and CSV/JSON exports
- **👥 Multi-User Collaboration**: Team workspaces and role-based permissions

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crow-eye-marketing.git
   cd crow-eye-marketing
   ```

2. **Install dependencies**
   ```bash
   pip install -r deployment/requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Alternative Launch Methods
- **With scheduling**: `python scripts/run_with_scheduling.py`
- **Windows batch**: `scripts/run_app.bat`

## 📁 Project Structure

```
crow-eye-marketing/
├── 📁 src/                     # Source code
│   ├── 📁 components/          # UI components
│   │   ├── dialogs/            # Dialog windows
│   │   ├── common/             # Shared UI elements
│   │   ├── media/              # Media-specific components
│   │   └── forms/              # Form components
│   ├── 📁 features/            # Core business logic
│   │   ├── authentication/     # OAuth and auth logic
│   │   ├── posting/            # Social media posting
│   │   ├── scheduling/         # Post scheduling
│   │   ├── media_processing/   # Media handling
│   │   └── gallery/            # Gallery generation
│   ├── 📁 api/                 # External API integrations
│   │   ├── meta/               # Facebook/Instagram API
│   │   ├── twitter/            # X (Twitter) API
│   │   ├── linkedin/           # LinkedIn API
│   │   └── ai/                 # AI service integrations
│   ├── 📁 utils/               # Utility functions
│   ├── 📁 models/              # Data models
│   ├── 📁 config/              # Configuration
│   └── 📁 core/                # Core application logic
├── 📁 assets/                  # Static assets
│   ├── icons/                  # Application icons
│   ├── styles/                 # Stylesheets
│   └── images/                 # Static images
├── 📁 translations/            # Internationalization
├── 📁 tests/                   # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── 📁 scripts/                 # Utility scripts
├── 📁 data/                    # Application data
│   ├── templates/              # Template files
│   └── samples/                # Sample data
├── 📁 deployment/              # Deployment configs
└── 📁 docs/                    # Documentation
```

## 🔧 Configuration

### API Keys Setup
The application supports multiple social media platforms:

1. **Meta (Facebook/Instagram)**: OAuth 2.0 authentication
2. **X (Twitter)**: API v2 with OAuth 2.0
3. **LinkedIn**: OAuth 2.0 authentication
4. **AI Services**: Gemini API for content generation

### API Keys Setup

**🎉 No Setup Required!** This application comes with shared API keys so you can start using it immediately without any configuration.

#### Shared API Keys (Default)
- **Gemini AI**: Included for caption generation and image editing
- **Google Veo**: Included for video generation
- **Ready to use**: Just download and run!

#### Optional: Use Your Own API Keys
If you want to use your own API keys (for higher usage limits or billing control), you can set environment variables:

```bash
# Optional - only if you want to use your own keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_google_api_key_for_veo
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
```

The application will automatically use your keys if provided, otherwise it falls back to the shared keys.

### 🎬 Veo Video Generation
For detailed setup and usage of the Veo video generation feature, see the [Veo Integration Guide](VEO_INTEGRATION_GUIDE.md).

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Integration tests
python tests/integration/comprehensive_connection_test.py

# Unit tests
python -m pytest tests/unit/

# All tests
python -m pytest tests/
```

## 🌍 Internationalization

Crow's Eye supports 11 languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Dutch (nl)
- Portuguese (pt)
- Italian (it)
- Mandarin (zh)
- Cantonese (zh-HK)
- Japanese (ja)
- Korean (ko)
- Russian (ru)

Language files are located in the `translations/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🧠 Philosophy

> "This product is the best on the market *until people wake up*."

Crow's Eye is a tool for survival in a system that rewards inauthenticity. Our goal is not to entrench ourselves in that system, but to make it easier for creators to move through it — and eventually beyond it.

## 🔗 Links

- [Documentation](docs/)
- [API Reference](docs/api/)
- [User Guide](docs/user_guide/)
- [Development Guide](docs/development/)

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for creators who want to survive and thrive in the digital landscape.**