# 🐦‍⬛ Crow's Eye Marketing Suite API

> *Complete REST API backend for the Crow's Eye social media management platform*

A comprehensive Node.js/Express API that provides all the backend functionality for the Crow's Eye Marketing Suite, including authentication, media management, analytics, and social media tools.

## ✨ Features

### 🔐 Authentication & Security
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Password Hashing**: bcrypt for secure password storage
- **Rate Limiting**: Protection against abuse and DDoS attacks
- **CORS Configuration**: Secure cross-origin resource sharing
- **Input Validation**: Comprehensive request validation with express-validator

### 📊 Core Functionality
- **User Management**: Registration, login, profile management
- **Media Library**: Upload, organize, and manage media files
- **Smart Galleries**: AI-powered photo organization
- **Story Formatter**: Create formatted social media stories
- **Highlight Reels**: Generate video highlight reels
- **Analytics**: Performance tracking and insights
- **Marketing Tools**: Post creation and scheduling

### 🛠 Technical Stack
- **Runtime**: Node.js 18+ with TypeScript
- **Framework**: Express.js with comprehensive middleware
- **Database**: PostgreSQL with Prisma ORM
- **Authentication**: JWT with bcrypt
- **File Storage**: Configurable (local/S3/GCS)
- **Documentation**: Swagger/OpenAPI 3.0
- **Testing**: Jest with supertest
- **Containerization**: Docker with multi-stage builds

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- PostgreSQL database
- Redis (optional, for caching)

### Installation

1. **Clone and setup**
   ```bash
   cd backend
   npm install
   ```

2. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```bash
   # Generate Prisma client
   npm run generate
   
   # Run migrations
   npm run migrate
   
   # Seed with sample data
   npm run db:seed
   ```

4. **Start Development Server**
   ```bash
   npm run dev
   ```

5. **Access the API**
   - **API Server**: http://localhost:3001
   - **API Documentation**: http://localhost:3001/docs
   - **Health Check**: http://localhost:3001/health

## 🐳 Docker Development

### Using Docker Compose (Recommended)

```bash
# Start all services (API, PostgreSQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Optional Tools
```bash
# Start with database management tools
docker-compose --profile tools up -d

# Access tools:
# - pgAdmin: http://localhost:5050
# - Redis Commander: http://localhost:8081
```

## 📖 API Documentation

### Authentication Endpoints

```bash
# Register new user
POST /auth/signup
{
  "email": "user@example.com",
  "password": "password123",
  "displayName": "John Doe"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# Logout
POST /auth/logout
# Requires: Authorization: Bearer <token>
```

### Media Management

```bash
# Upload media file
POST /media
Content-Type: multipart/form-data
# Form data: file, metadata (optional)

# Get user's media
GET /media
# Requires: Authorization: Bearer <token>

# Delete media
DELETE /media/:id
# Requires: Authorization: Bearer <token>
```

### Gallery Management

```bash
# Create gallery
POST /galleries
{
  "title": "My Gallery",
  "images": ["media_id_1", "media_id_2"]
}

# Get galleries
GET /galleries
# Requires: Authorization: Bearer <token>
```

### Analytics

```bash
# Get analytics data
GET /analytics
# Requires: Authorization: Bearer <token>

# Returns:
{
  "totalPosts": 25,
  "totalViews": 1500,
  "totalLikes": 120,
  "engagementRate": 8.5,
  "topPosts": [...],
  "platformStats": [...]
}
```

## 🗄 Database Schema

### Core Models
- **User**: Authentication and profile data
- **MediaItem**: Uploaded files and metadata
- **Gallery**: Photo collections
- **Story**: Formatted social media content
- **HighlightReel**: Video compilations
- **Post**: Social media posts
- **PostAnalytics**: Performance metrics

### Relationships
- Users have many media items, galleries, stories, posts
- Galleries contain multiple media items
- Posts can have multiple media attachments
- Analytics track post performance across platforms

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run specific test file
npm test -- auth.test.ts
```

### Test Accounts
After running `npm run db:seed`:
- **Free User**: free@example.com (password: password123)
- **Creator User**: creator@example.com (password: password123)
- **Pro User**: pro@example.com (password: password123)

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/crow_eye_db"

# JWT Configuration
JWT_SECRET="your-secret-key"
JWT_REFRESH_SECRET="your-refresh-secret"
JWT_EXPIRES_IN="24h"
JWT_REFRESH_EXPIRES_IN="30d"

# Server
PORT=3001
NODE_ENV=development
CORS_ORIGINS="http://localhost:3000,https://crows-eye-website.web.app"

# File Storage (optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=your-bucket
```

### Database Commands

```bash
# Create new migration
npm run migrate

# Deploy migrations (production)
npm run migrate:deploy

# Reset database
npm run db:reset

# Generate Prisma client
npm run generate
```

## 🚀 Deployment

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Docker Production

```bash
# Build production image
docker build -t crow-eye-api --target production .

# Run production container
docker run -p 3001:3001 \
  -e DATABASE_URL="your-db-url" \
  -e JWT_SECRET="your-secret" \
  crow-eye-api
```

### Environment Setup

1. **Database**: Set up PostgreSQL instance
2. **Environment Variables**: Configure all required variables
3. **File Storage**: Configure S3/GCS for file uploads
4. **Monitoring**: Set up logging and health checks
5. **SSL**: Configure HTTPS in production

## 📊 API Endpoints Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/signup` | POST | Register new user | No |
| `/auth/login` | POST | User login | No |
| `/auth/logout` | POST | User logout | Yes |
| `/user/profile` | GET | Get user profile | Yes |
| `/user/profile` | PUT | Update profile | Yes |
| `/media` | GET | List media files | Yes |
| `/media` | POST | Upload media | Yes |
| `/media/:id` | DELETE | Delete media | Yes |
| `/galleries` | GET | List galleries | Yes |
| `/galleries` | POST | Create gallery | Yes |
| `/stories` | GET | List stories | Yes |
| `/stories` | POST | Create story | Yes |
| `/highlights` | GET | List highlight reels | Yes |
| `/highlights` | POST | Create highlight reel | Yes |
| `/analytics` | GET | Get analytics data | Yes |
| `/marketing-tool/stats` | GET | Get marketing stats | Yes |
| `/marketing-tool/posts` | POST | Create post | Yes |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`npm test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: http://localhost:3001/docs
- **Issues**: GitHub Issues
- **Email**: support@crowseye.tech

---

**Built with ❤️ using Node.js, Express, TypeScript, and Prisma.** 