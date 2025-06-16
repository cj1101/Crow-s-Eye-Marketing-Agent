# 🌟 Google Photos Integration for Crow's Eye

This guide covers the complete Google Photos integration that allows users to seamlessly import photos and videos from their Google Photos account into Crow's Eye.

## 🧩 Architecture Overview

The integration consists of:
- **Backend API**: FastAPI endpoints for OAuth2, browsing, and importing
- **Database Models**: Extended media models with Google Photos metadata
- **React Components**: User-friendly interface for connection and browsing
- **Service Layer**: Google Photos API interactions and media processing
- **Natural Language Search**: AI-powered query parsing for intuitive searching

## 🚀 Setup Instructions

### 1. Google Cloud Console Setup

1. **Create a Google Cloud Project** (if you don't have one):
   ```bash
   # Go to https://console.cloud.google.com/
   # Create a new project or select existing one
   ```

2. **Enable Google Photos Library API**:
   ```bash
   # In Google Cloud Console:
   # APIs & Services > Library > Search "Photos Library API" > Enable
   ```

3. **Create OAuth 2.0 Credentials**:
   ```bash
   # APIs & Services > Credentials > Create Credentials > OAuth 2.0 Client IDs
   # Application type: Web application
   # Authorized redirect URIs: 
   #   - http://localhost:3000/auth/google-photos/callback (development)
   #   - https://yourdomain.com/auth/google-photos/callback (production)
   ```

4. **Configure OAuth Consent Screen**:
   ```bash
   # APIs & Services > OAuth consent screen
   # Add required scopes:
   #   - https://www.googleapis.com/auth/photoslibrary.readonly
   #   - https://www.googleapis.com/auth/photoslibrary.sharing
   ```

### 2. Environment Configuration

Add these environment variables to your `.env` file:

```env
# Google Photos OAuth2 Configuration
GOOGLE_PHOTOS_CLIENT_ID=your_google_photos_client_id
GOOGLE_PHOTOS_CLIENT_SECRET=your_google_photos_client_secret
GOOGLE_PHOTOS_REDIRECT_URI=http://localhost:3000/auth/google-photos/callback

# For production, use your actual domain:
# GOOGLE_PHOTOS_REDIRECT_URI=https://yourdomain.com/auth/google-photos/callback
```

### 3. Database Migration

The integration adds new database tables and columns:

```sql
-- New Google Photos connection table
CREATE TABLE google_photos_connections (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    google_user_id VARCHAR(255),
    google_email VARCHAR(255),
    connection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Extended media_items table
ALTER TABLE media_items ADD COLUMN google_photos_id VARCHAR(255) UNIQUE;
ALTER TABLE media_items ADD COLUMN google_photos_metadata JSON;
ALTER TABLE media_items ADD COLUMN import_source VARCHAR(50) DEFAULT 'manual';
ALTER TABLE media_items ADD COLUMN import_date TIMESTAMP;

-- Indexes for performance
CREATE INDEX idx_media_items_google_photos_id ON media_items(google_photos_id);
CREATE INDEX idx_media_items_import_source ON media_items(import_source);
CREATE INDEX idx_google_photos_connections_user_id ON google_photos_connections(user_id);
```

### 4. Install Dependencies

Make sure these packages are installed:

```bash
pip install google-auth-oauthlib google-api-python-client
```

These are already added to `requirements.txt` in the integration.

## 🔧 API Endpoints

### Authentication Endpoints

- `GET /api/v1/google-photos/auth/url` - Get OAuth2 authorization URL
- `POST /api/v1/google-photos/auth/callback` - Handle OAuth2 callback
- `GET /api/v1/google-photos/connection` - Get connection status
- `DELETE /api/v1/google-photos/connection` - Disconnect account

### Media Browsing Endpoints

- `GET /api/v1/google-photos/albums` - List user's albums
- `GET /api/v1/google-photos/media` - Get media items (with optional album filter)
- `POST /api/v1/google-photos/search` - Advanced search with filters
- `POST /api/v1/google-photos/search/natural` - Natural language search

### Import Endpoints

- `POST /api/v1/google-photos/import` - Import selected media items
- `GET /api/v1/google-photos/imported` - List imported media

## 🎨 Frontend Components

### GooglePhotosConnect
Handles OAuth2 authentication flow:
```tsx
import { GooglePhotosConnect } from '@/components/google-photos';

<GooglePhotosConnect 
  onConnectionChange={(connected) => setIsConnected(connected)}
/>
```

### GooglePhotosBrowser
Full-featured media browser with search:
```tsx
import { GooglePhotosBrowser } from '@/components/google-photos';

<GooglePhotosBrowser
  onSelectionChange={(items) => setSelected(items)}
  onImport={(items, options) => handleImport(items, options)}
/>
```

### GooglePhotosIntegration
Complete integration component:
```tsx
import { GooglePhotosIntegration } from '@/components/google-photos';

<GooglePhotosIntegration
  onMediaImported={(count, galleryId) => handleSuccess(count, galleryId)}
/>
```

## 🧠 Natural Language Search

Users can search with natural language queries:

- **"Show me photos from Paris 2023"** - Searches for photos with location/date filters
- **"Find videos with animals"** - Content category filtering
- **"Photos from last summer"** - Date range queries
- **"My selfies from vacation"** - Multiple filters combined

The system parses these queries and converts them to Google Photos API filters.

## 🔐 Security & Privacy

### OAuth2 Flow
1. User clicks "Connect Google Photos"
2. Redirected to Google OAuth consent screen
3. User grants read-only access to photos
4. Authorization code exchanged for access/refresh tokens
5. Tokens stored securely (encrypted in production)

### Data Handling
- **Read-only access**: Only viewing and downloading permissions
- **No permanent storage**: Media files are temporarily downloaded for import
- **User control**: Users can disconnect anytime
- **Metadata preservation**: Original EXIF data and timestamps maintained

### Token Management
- Automatic token refresh when expired
- Secure storage of refresh tokens
- Proper error handling for invalid/expired tokens

## 📱 User Experience Flow

### 1. Connection Phase
```
User → "Connect Google Photos" → OAuth Flow → Connected State
```

### 2. Browsing Phase
```
Connected → Browse Albums → Search Media → Select Items
```

### 3. Import Phase
```
Selected Items → Configure Import Options → Import → Success Notification
```

### 4. Integration Phase
```
Imported Media → AI Tagging → Gallery Creation → Use in Workflows
```

## 🎯 Import Options

Users can customize their import:

### Import Destination
- **Raw Media**: For further editing and processing
- **Post-Ready**: Ready for immediate publishing

### AI Integration
- **Auto-tagging**: Apply AI tags to imported media
- **Smart categorization**: Organize by content type
- **Metadata extraction**: Preserve Google Photos data

### Gallery Creation
- **Auto-gallery**: Create galleries from import batches
- **Custom naming**: User-defined gallery names
- **Smart grouping**: Group by date, location, or content

## 🌐 Integration with Existing Features

### Media Processing
- Imported media works with all existing video/image processing
- AI enhancement and optimization available
- Platform-specific formatting supported

### Workflow Integration
- Use imported media in highlight reels
- Include in automated gallery generation
- Apply existing tagging and search capabilities

### Export & Publishing
- Imported media can be published to all supported platforms
- Maintains original quality and metadata
- Optimized for each platform's requirements

## 📊 Analytics & Tracking

The integration tracks:
- Connection status and last sync dates
- Import success/failure rates
- Most used import options
- Popular search queries
- Media usage in workflows

## 🔧 Troubleshooting

### Common Issues

#### "Failed to get authorization URL"
- Check `GOOGLE_PHOTOS_CLIENT_ID` is set correctly
- Verify Google Photos Library API is enabled
- Ensure OAuth consent screen is configured

#### "Authentication failed"
- Check redirect URI matches exactly (including protocol)
- Verify client secret is correct
- Ensure user has granted all required permissions

#### "Failed to load media"
- Check token expiration and refresh
- Verify API quotas haven't been exceeded
- Ensure user has photos in their account

#### "Import failed"
- Check Google Cloud Storage permissions
- Verify sufficient storage space
- Check network connectivity for large imports

### Debug Mode
Enable debug logging for troubleshooting:
```python
logging.getLogger("crow_eye_api.services.google_photos_service").setLevel(logging.DEBUG)
```

## 🚧 Future Enhancements

### Planned Features
- **Batch operations**: Import entire albums with one click
- **Sync scheduling**: Automatic periodic imports
- **Smart suggestions**: AI-recommended imports based on usage
- **Advanced filters**: Face recognition, object detection
- **Collaborative imports**: Share import collections with team members

### Performance Optimizations
- **Lazy loading**: Load media thumbnails on demand
- **Caching**: Cache API responses for better performance
- **Background processing**: Async import processing
- **Compression**: Optimize storage usage

## 📝 Testing

### Manual Testing Checklist
- [ ] OAuth flow completes successfully
- [ ] Albums load correctly
- [ ] Media search works with various queries
- [ ] Natural language search interprets queries correctly
- [ ] Import process completes without errors
- [ ] Imported media appears in correct sections
- [ ] AI tagging is applied when enabled
- [ ] Galleries are created when requested
- [ ] Disconnection works properly

### Automated Tests
```bash
# Run Google Photos integration tests
python -m pytest tests/test_google_photos_integration.py -v
```

## 📚 API Documentation

Full API documentation is available in the FastAPI docs:
```
http://localhost:8000/docs#/Google%20Photos
```

The integration adds a dedicated "Google Photos" section to the API documentation with interactive testing capabilities.

## 🤝 Support

For issues with the Google Photos integration:

1. Check this guide for common solutions
2. Review the API logs for specific error messages
3. Verify Google Cloud Console configuration
4. Test with minimal permissions first
5. Check Google Photos API quotas and limits

## 🎉 Congratulations!

You now have a fully functional Google Photos integration that allows users to seamlessly import their photos and videos into Crow's Eye, complete with natural language search, AI tagging, and seamless workflow integration! 