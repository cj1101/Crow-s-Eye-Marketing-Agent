# 🚀 Deployment Guide - Crow's Eye Marketing Suite

This guide covers deployment to both GitHub and Firebase for the complete Crow's Eye Marketing Suite.

## 📋 Prerequisites

- Git account and access to GitHub
- Firebase account and CLI tools
- Node.js 18+ installed
- PostgreSQL database (Neon.tech recommended)

## 🔐 Super User Account Created

✅ **Super User Account**: `charlie@suarezhouse.net`
- **Password**: `CrowsEye2024!` (Change after first login)
- **Plan**: PRO (Full access to all features)
- **Role**: Super Admin

## 🐙 GitHub Deployment

### 1. Create GitHub Repository

```bash
# If repository doesn't exist, create it on GitHub first
# Then connect local repository
git remote add origin https://github.com/charliesuarez/crows-eye-marketing-suite.git
```

### 2. Push to GitHub

```bash
# Push main branch
git push -u origin main

# Create and push develop branch
git checkout -b develop
git push -u origin develop
```

### 3. Repository Structure

```
crows-eye-marketing-suite/
├── backend/                 # Node.js/TypeScript API
│   ├── src/                # Source code
│   ├── prisma/             # Database schema & migrations
│   ├── package.json        # Dependencies
│   └── ...
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── package.json            # Root package.json
├── README.md              # Main documentation
└── DEPLOYMENT_GUIDE.md    # This file
```

## 🔥 Firebase Website Deployment

### 1. Install Firebase CLI

```bash
npm install -g firebase-tools
```

### 2. Login to Firebase

```bash
firebase login
```

### 3. Navigate to Website Directory

```bash
cd "C:\Users\charl\CodingProjets\Crow's Eye Website"
```

### 4. Initialize Firebase Project

```bash
# If not already initialized
firebase init hosting

# Select options:
# - Use existing project: crows-eye-website
# - Public directory: public or dist
# - Single-page app: Yes
# - Set up automatic builds: No (for now)
```

### 5. Build and Deploy

```bash
# Build the website
npm run build

# Deploy to Firebase
firebase deploy
```

## 🌐 Backend API Deployment Options

### Option 1: Railway

1. Connect GitHub repository to Railway
2. Set environment variables:
   ```
   DATABASE_URL=your_neon_database_url
   JWT_SECRET=your_jwt_secret
   JWT_REFRESH_SECRET=your_refresh_secret
   NODE_ENV=production
   ```
3. Deploy automatically from GitHub

### Option 2: Vercel

1. Connect GitHub repository to Vercel
2. Set build command: `cd backend && npm run build`
3. Set output directory: `backend/dist`
4. Configure environment variables

### Option 3: Heroku

1. Create Heroku app
2. Add PostgreSQL addon or use external Neon database
3. Configure environment variables
4. Deploy via Git

## 🗄️ Database Setup (Neon.tech)

### Current Configuration

- **Provider**: Neon.tech (PostgreSQL)
- **Connection**: Already configured and working
- **Migrations**: Applied and seeded with sample data

### Environment Variables Required

```env
DATABASE_URL="postgresql://username:password@host/database"
JWT_SECRET="your-super-secret-jwt-key"
JWT_REFRESH_SECRET="your-super-secret-refresh-key"
PORT=3000
NODE_ENV=production
```

## 📊 API Endpoints Available

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - User logout

### Media Management
- `GET /api/media` - List media items
- `POST /api/media/upload` - Upload media
- `DELETE /api/media/:id` - Delete media
- `PUT /api/media/:id` - Update media

### Content Management
- `GET /api/posts` - List posts
- `POST /api/posts` - Create post
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post

### Galleries & Stories
- `GET /api/galleries` - List galleries
- `POST /api/galleries` - Create gallery
- `GET /api/stories` - List stories
- `POST /api/stories` - Create story

## 🔧 Development vs Production

### Development
```bash
# Start development server
npm run dev

# Start with environment variables
$env:DATABASE_URL="postgresql://..."; $env:JWT_SECRET="dev-secret"; npm run dev
```

### Production
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🚨 Security Checklist

- ✅ Environment variables configured
- ✅ JWT secrets generated and secured
- ✅ Database credentials protected
- ✅ CORS configured for production
- ✅ Rate limiting implemented
- ✅ Input validation active

## 📈 Monitoring & Analytics

### Application Monitoring
- Implement logging with Winston (already configured)
- Set up error tracking (Sentry recommended)
- Monitor API performance
- Track user activity

### Database Monitoring
- Monitor Neon database performance
- Set up connection pooling
- Track query performance

## 🔄 CI/CD Pipeline (Recommended)

### GitHub Actions Workflow

```yaml
name: Deploy Crow's Eye Marketing Suite

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd backend
          npm install
      
      - name: Build
        run: |
          cd backend
          npm run build
      
      - name: Deploy to Railway/Vercel
        # Configure based on chosen platform
```

## 📞 Support & Maintenance

### Regular Tasks
- Monitor database performance
- Update dependencies monthly
- Review and rotate JWT secrets quarterly
- Backup database regularly (Neon handles this)

### Emergency Procedures
- Database failover: Neon provides automatic failover
- API downtime: Check Railway/Vercel status
- Security incidents: Rotate all secrets immediately

## 🎯 Next Steps

1. **Push to GitHub**: Complete the repository setup
2. **Deploy Website**: Use Firebase hosting for the frontend
3. **Deploy API**: Choose Railway, Vercel, or Heroku for backend
4. **Configure Domain**: Set up custom domain for production
5. **SSL Certificate**: Ensure HTTPS is enabled
6. **Monitoring**: Set up application and database monitoring

## 📝 Notes

- Super user account created and ready for use
- Database is already seeded with sample data
- All API endpoints tested and working
- Ready for production deployment

---

**Deployment Status**: ✅ Ready for Production
**Super User**: charlie@suarezhouse.net (PRO Plan)
**Database**: Connected and Operational
**API**: Fully Functional 