# 🗄️ Crow's Eye Database Integration Guide

This guide explains how to set up and use the centralized PostgreSQL database for consistent data across all Crow's Eye platforms (website, desktop app, and API).

## 🎯 Overview

Your Crow's Eye platform now uses a **centralized PostgreSQL database** instead of JSON files, ensuring:

- ✅ **Data Consistency** across website, desktop app, and future platforms
- ✅ **Real-time Synchronization** between all applications
- ✅ **Scalable Architecture** for future growth
- ✅ **Data Integrity** with proper relationships and constraints
- ✅ **Performance Optimization** with indexes and query optimization

## 📊 Database Schema

The database includes these main tables:

### Core Tables
- **`users`** - User accounts and profiles
- **`media_items`** - All media files (images, videos, audio)
- **`galleries`** - Media collections
- **`stories`** - Story content
- **`highlight_reels`** - Video highlight reels
- **`posts`** - Social media posts
- **`post_analytics`** - Performance metrics

### Supporting Tables
- **`refresh_tokens`** - Authentication tokens
- **`gallery_media`** - Gallery-media relationships
- **`story_media`** - Story-media relationships
- **`highlight_media`** - Highlight-media relationships
- **`post_media`** - Post-media relationships
- **`activities`** - User activity logs

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install Python database dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for backend)
cd backend
npm install
```

### 2. Configure Database Connection

Create a `.env` file in your project root:

```env
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/crow_eye_db"

# Or for cloud databases:
# DATABASE_URL="postgresql://user:pass@host:5432/dbname?sslmode=require"
```

### 3. Set Up Database

```bash
# Option 1: Run the setup script
python scripts/setup_database.py

# Option 2: Use Prisma (if using Node.js backend)
cd backend
npx prisma db push
npx prisma generate
```

### 4. Migrate Existing Data

```bash
# Migrate your existing JSON data to PostgreSQL
python scripts/migrate_json_to_db.py
```

### 5. Start the API

```bash
# Start the FastAPI server
python -m uvicorn crow_eye_api.main:app --reload --port 8000
```

## 🔧 Configuration Options

### Local Development
```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/crow_eye_dev"
```

### Production (Railway/Heroku)
```env
DATABASE_URL="postgresql://user:pass@host:port/dbname?sslmode=require"
```

### Docker
```env
DATABASE_URL="postgresql://crow_eye:password@db:5432/crow_eye_db"
```

## 📱 Platform Integration

### Desktop Application
The desktop app now connects to the API for all data operations:

```python
# Example: Fetching media from API instead of JSON
import requests

def get_user_media():
    response = requests.get("http://localhost:8000/media/", 
                          headers={"Authorization": f"Bearer {token}"})
    return response.json()
```

### Website Integration
The Next.js website connects to the same API:

```typescript
// Example: API call from website
const fetchMedia = async () => {
  const response = await fetch('/api/media', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

### Mobile App (Future)
Any future mobile app will use the same API endpoints for consistent data access.

## 🔄 Data Migration Details

### What Gets Migrated

1. **User Data** (`data/users.json` → `users` table)
   - Email addresses
   - Display names
   - Subscription tiers
   - User preferences

2. **Media Library** (`data/library.json` → `media_items` table)
   - All images, videos, and audio files
   - File metadata (size, dimensions, tags)
   - Upload dates and captions

3. **Scheduled Posts** (`data/scheduled_posts.json` → `posts` table)
   - Post content and hashtags
   - Scheduled publication times
   - Target platforms

### Migration Process

```bash
# Run the migration script
python scripts/migrate_json_to_db.py

# Expected output:
🚀 Starting data migration from JSON to PostgreSQL...
✅ Database connection established
📁 Migrating users...
  ✅ Migrated user: user@example.com (ID: abc123)
📁 Migrating media library...
  ✅ Migrated media: image1.jpg
📁 Migrating scheduled posts...
  ✅ Migrated post: Fresh bread today...

📊 Migration Summary:
  Users: 5 migrated
  Media items: 23 migrated
  Posts: 8 migrated

✅ Migration completed successfully!
```

## 🔍 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Refresh token

### Media Management
- `GET /media/` - List user media
- `POST /media/` - Upload new media
- `GET /media/{id}` - Get specific media
- `DELETE /media/{id}` - Delete media

### Gallery Management
- `GET /gallery/` - List user galleries
- `POST /gallery/` - Create new gallery
- `GET /gallery/{id}` - Get gallery details
- `PUT /gallery/{id}` - Update gallery
- `DELETE /gallery/{id}` - Delete gallery

### Content Creation
- `GET /stories/` - List user stories
- `POST /stories/` - Create new story
- `GET /highlights/` - List highlight reels
- `POST /highlights/` - Create highlight reel

## 🛠️ Development Workflow

### 1. Database Changes
When you need to modify the database schema:

```bash
# 1. Update the Prisma schema
vim backend/prisma/schema.prisma

# 2. Generate migration
cd backend
npx prisma migrate dev --name "your_change_description"

# 3. Update the Python database service
vim crow_eye_api/database.py
```

### 2. Testing
```bash
# Test database connection
python -c "from crow_eye_api.database import db_manager; import asyncio; asyncio.run(db_manager.connect())"

# Test API endpoints
curl -X GET "http://localhost:8000/health"
```

### 3. Backup and Restore
```bash
# Backup database
pg_dump $DATABASE_URL > backup.sql

# Restore database
psql $DATABASE_URL < backup.sql
```

## 🔒 Security Considerations

### Environment Variables
Never commit database credentials to version control:

```bash
# Add to .gitignore
.env
.env.local
.env.production
```

### Connection Security
- Use SSL connections in production
- Implement connection pooling
- Set up proper firewall rules
- Use strong passwords and rotate them regularly

### API Security
- JWT token authentication
- Rate limiting
- Input validation
- SQL injection prevention (using parameterized queries)

## 📈 Performance Optimization

### Database Indexes
The setup script creates optimized indexes for:
- User lookups by email
- Media queries by user and type
- Post queries by schedule and status
- Activity logs by user and date

### Connection Pooling
The database manager uses connection pooling:
- Minimum 1 connection
- Maximum 10 connections
- 60-second command timeout

### Caching Strategy
Consider implementing Redis caching for:
- Frequently accessed media metadata
- User session data
- API response caching

## 🚨 Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   pg_isready -h localhost -p 5432
   
   # Verify connection string
   echo $DATABASE_URL
   ```

2. **Migration Errors**
   ```bash
   # Check existing data format
   python -c "import json; print(json.load(open('data/library.json')))"
   
   # Run migration with verbose output
   python scripts/migrate_json_to_db.py --verbose
   ```

3. **API Connection Issues**
   ```bash
   # Test API health
   curl http://localhost:8000/health
   
   # Check logs
   tail -f app_log.log
   ```

### Database Recovery
If you need to reset the database:

```bash
# 1. Backup current data
python scripts/backup_database.py

# 2. Reset database
python scripts/setup_database.py

# 3. Re-migrate data
python scripts/migrate_json_to_db.py
```

## 🎉 Benefits Achieved

With this database integration, you now have:

1. **Unified Data Layer** - All platforms use the same database
2. **Real-time Sync** - Changes appear instantly across all apps
3. **Scalability** - Can handle thousands of users and media files
4. **Data Integrity** - Proper relationships and constraints
5. **Future-Proof** - Easy to add new platforms and features
6. **Professional Architecture** - Industry-standard database design

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the API logs: `tail -f app_log.log`
3. Test database connectivity: `python scripts/test_db_connection.py`
4. Verify environment variables are set correctly

The database integration ensures your Crow's Eye platform is ready for scale and provides a consistent experience across all current and future applications! 🚀 