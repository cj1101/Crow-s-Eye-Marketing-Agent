# 🐦‍⬛ Crow's Eye Marketing Platform API

> *REST API for the Crow's Eye marketing automation platform*

A comprehensive FastAPI service that exposes all Crow's Eye marketing features through REST endpoints with tier-based access control and JWT authentication.

## ✨ Features

### 🔐 Authentication & Authorization
- **JWT Authentication**: 30-day access tokens with HS256 signing
- **Tier-based Access Control**: Automatic feature gating based on subscription tiers
- **BYO API Key Support**: Enterprise customers can use custom API keys
- **Secure Endpoints**: All endpoints protected with proper authentication

### 📊 Subscription Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | Media library, smart galleries, story formatting |
| **Creator** | $9/mo | + 30-sec highlight reels, custom audio imports |
| **Pro** | $19/mo | + Performance analytics, CSV/JSON exports |
| **Enterprise** | Custom | + Multi-account support, SLA, priority support |

### 🛠 API Endpoints

#### Authentication (`/auth`)
- `POST /auth/login` - Login with email/password, returns JWT token
- `GET /auth/me` - Get current user information
- `POST /auth/logout` - Logout (client-side token removal)

#### Media Management (`/media`) - **Free+**
- `POST /media/` - Upload media files (images, videos)
- `GET /media/` - List user's media files
- `GET /media/{id}` - Get media file information
- `DELETE /media/{id}` - Delete media file

#### Smart Galleries (`/gallery`) - **Free+**
- `POST /gallery/` - Create AI-powered gallery from prompt
- `GET /gallery/` - List user's galleries
- `GET /gallery/{id}` - Get gallery details
- `PUT /gallery/{id}` - Update gallery
- `DELETE /gallery/{id}` - Delete gallery

#### Story Formatting (`/stories`) - **Free+**
- `POST /stories/` - Create formatted stories for social media
- `GET /stories/` - List user's stories
- `GET /stories/{id}` - Get story details
- `GET /stories/templates/` - List available story templates
- `DELETE /stories/{id}` - Delete story

#### Highlight Reels (`/highlights`) - **Creator+**
- `POST /highlights/` - Create 30-second highlight reels
- `GET /highlights/` - List user's highlight reels
- `GET /highlights/{id}` - Get highlight reel details
- `GET /highlights/styles/` - List available styles
- `GET /highlights/{id}/status` - Get processing status
- `DELETE /highlights/{id}` - Delete highlight reel

#### Audio Import (`/audio`) - **Creator+**
- `POST /audio/import` - Import custom audio files
- `GET /audio/` - List user's audio files
- `GET /audio/{id}` - Get audio file details
- `POST /audio/edit` - Edit audio with natural language
- `GET /audio/effects/` - List available audio effects
- `GET /audio/{id}/analyze` - Analyze audio properties
- `DELETE /audio/{id}` - Delete audio file

#### Analytics (`/analytics`) - **Pro+**
- `GET /analytics/` - Get performance analytics
- `POST /analytics/export` - Export data (CSV/JSON)
- `GET /analytics/insights` - Get AI-powered insights
- `GET /analytics/competitors` - Get competitor analysis
- `GET /analytics/reports/summary` - Get executive summary

#### Admin (`/admin`) - **Enterprise Only**
- `GET /admin/accounts` - List organization accounts
- `POST /admin/accounts` - Create new team member account
- `GET /admin/accounts/{id}` - Get account details
- `PUT /admin/accounts/{id}` - Update account
- `DELETE /admin/accounts/{id}` - Delete/deactivate account
- `POST /admin/accounts/{id}/reset-password` - Reset password
- `GET /admin/usage/summary` - Get usage summary
- `GET /admin/billing/usage` - Get billing information

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or conda

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crow-eye-marketing
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API server**
   ```bash
   # Linux/Mac
   ./scripts/start_api.sh
   
   # Windows
   scripts\start_api.bat
   
   # Or manually
   uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Origins
CORS_ORIGINS=http://localhost:3000,https://crowseye.tech
```

### Docker Deployment

```bash
# Build the image
docker build -t crow-eye-api .

# Run the container
docker run -p 8000:8000 \
  -e JWT_SECRET_KEY=your-secret-key \
  crow-eye-api
```

## 📖 API Usage Examples

### Authentication

```bash
# Login to get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "creator@example.com",
    "password": "password123"
  }'

# Response
{
  "access_token": "your_jwt_token_here",
  "token_type": "bearer",
  "user": {
    "user_id": "user_1234",
    "email": "creator@example.com",
    "subscription": {
      "tier": "creator"
    }
  }
}
```

### Using the API with Authentication

```bash
# Set your token
TOKEN="your-jwt-token-here"

# Create a smart gallery
curl -X POST "http://localhost:8000/gallery/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Best 5 photos for a winter campaign",
    "max_items": 5,
    "generate_caption": true
  }'

# Upload media
curl -X POST "http://localhost:8000/media/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/image.jpg"

# Create highlight reel (Creator+ only)
curl -X POST "http://localhost:8000/highlights/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "media_ids": ["media_1", "media_2", "media_3"],
    "duration": 30,
    "style": "dynamic",
    "music_style": "upbeat"
  }'
```

### Enterprise BYO API Key

```bash
# Use custom API key (Enterprise feature)
curl -X GET "http://localhost:8000/admin/accounts" \
  -H "X-USER-API-KEY: your-custom-api-key"
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/api/ -v

# Run specific test file
pytest tests/api/test_auth.py -v

# Run with coverage
pytest tests/api/ --cov=crow_eye_api --cov-report=html
```

## 📊 OpenAPI Specification

The complete API specification is available at:
- **Interactive Docs**: http://localhost:8000/docs
- **JSON Spec**: `docs/openapi.json`
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Tier-based Authorization**: Automatic feature access control
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic models for request/response validation
- **Rate Limiting**: Built-in protection against abuse (Enterprise)

## 🚀 Deployment

### GitHub Actions CI/CD

The repository includes automated CI/CD with GitHub Actions:
- **Testing**: Runs pytest on all pull requests
- **Linting**: Code quality checks with flake8
- **Docker Build**: Builds and pushes container images
- **Deployment**: Automated deployment to production

### Production Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Using Kubernetes
kubectl apply -f k8s/

# Using cloud platforms
# See deployment/ directory for platform-specific configs
```

## 📈 Monitoring & Observability

- **Health Checks**: `/health` endpoint for load balancer checks
- **Structured Logging**: JSON logs for easy parsing
- **Metrics**: Built-in FastAPI metrics
- **Error Tracking**: Global exception handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest tests/api/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Enterprise Support**: Contact your account manager

---

**Built with ❤️ using FastAPI, Pydantic, and modern Python practices.** 