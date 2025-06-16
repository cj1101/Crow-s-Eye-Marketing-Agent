# 🦅 Crow's Eye Full Stack Integration Prompt

## Overview
You are tasked with creating a modern, responsive web application that integrates with the Crow's Eye API backend. This system provides advanced media processing, content analysis, and social media management capabilities.

## Backend API Capabilities
The Crow's Eye API (running on port 8000) provides these key features:

### 🎬 Media Processing & Analysis
- **Video highlight generation** with AI-powered scene detection
- **Example-based highlight creation** using reference segments
- **Long-form content processing** (2-5 minute highlights from 1-3 hour content)
- **Story clips creation** optimized for social platforms
- **Video thumbnail generation** with smart frame selection
- **Audio overlay capabilities** for enhanced content

### 📸 Google Photos Integration
- **OAuth2 authentication** with Google Photos API
- **Media import and synchronization** from Google Photos albums
- **Smart tagging and categorization** of imported media
- **Natural language search** across media collections
- **Metadata extraction and analysis**

### 🔍 Content Analysis
- **AI-powered content understanding** using Gemini models
- **Scene detection and classification**
- **Motion analysis and action sequence identification**
- **Semantic search capabilities** across all media

### 📊 Analytics & Reporting
- **Processing metrics and performance tracking**
- **User engagement analytics**
- **Content performance insights**
- **Export capabilities for various formats**

## Required Web Application Features

### 🎨 User Interface Requirements
1. **Modern, responsive design** using React/Vue.js/Angular with Tailwind CSS
2. **Dark/light theme support** with user preference persistence
3. **Drag-and-drop interfaces** for media upload and management
4. **Real-time progress indicators** for processing operations
5. **Interactive media galleries** with filtering and search
6. **Mobile-first responsive design** for all devices

### 🔐 Authentication & Security
1. **Multi-provider OAuth integration** (Google, GitHub, etc.)
2. **JWT-based session management** with refresh tokens
3. **Role-based access control** (admin, user, viewer)
4. **API rate limiting and security headers**
5. **GDPR-compliant data handling**

### 📁 Media Management Interface
1. **Upload interface** with progress tracking and batch processing
2. **Media library** with grid/list views, sorting, and filtering
3. **Preview functionality** for videos, images, and audio
4. **Metadata editing** capabilities with bulk operations
5. **Collection management** with custom folders and tags

### 🎬 Video Processing Workflows
1. **Highlight reel generator** with customizable duration and style presets
2. **Example-based processing** with reference segment selection
3. **Long-form content processor** with cost estimation and optimization
4. **Story clips creator** with platform-specific optimization
5. **Batch processing queues** with priority management

### 📸 Google Photos Integration UI
1. **OAuth connection flow** with clear permission explanations
2. **Album browser** with thumbnail previews and selection tools
3. **Import wizard** with progress tracking and conflict resolution
4. **Sync status dashboard** showing import history and errors
5. **Search interface** with natural language query support

### 📊 Analytics Dashboard
1. **Processing statistics** with charts and graphs
2. **Performance metrics** tracking API usage and response times
3. **User activity logs** with filtering and export options
4. **System health monitoring** with real-time status indicators
5. **Export tools** for reports in various formats

## Technical Implementation Requirements

### 🏗️ Frontend Architecture
```typescript
// Tech Stack Recommendations
- Framework: Next.js 14+ with App Router or Vue 3 with Nuxt 3
- Styling: Tailwind CSS with custom component library
- State Management: Zustand/Pinia with persistent storage
- HTTP Client: Axios with interceptors for auth and error handling
- File Upload: react-dropzone or vue-dropzone with chunked uploads
- Media Player: Video.js or custom HTML5 video implementation
- Charts: Chart.js or D3.js for analytics visualization
```

### 🔧 API Integration
```javascript
// Example API service structure
class CrowsEyeAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.api = axios.create({
      baseURL: baseURL + '/api/v1',
      timeout: 30000
    });
  }

  // Media processing endpoints
  async generateHighlights(videoFile, options) { }
  async createStoryClips(videoFile, maxDuration) { }
  async processLongForm(videoFile, targetDuration, prompt) { }
  
  // Google Photos integration
  async connectGooglePhotos() { }
  async importFromAlbum(albumId, filters) { }
  async searchMedia(query) { }
  
  // Analytics and reporting
  async getProcessingStats() { }
  async exportReport(format, dateRange) { }
}
```

### 🗄️ State Management
```javascript
// Example store structure
const mediaStore = {
  state: {
    uploadQueue: [],
    processingJobs: [],
    mediaLibrary: [],
    googlePhotosAuth: null,
    currentProject: null
  },
  actions: {
    uploadMedia, processVideo, syncGooglePhotos,
    searchContent, exportProject
  }
}
```

## Key User Workflows to Implement

### 🎬 Video Processing Workflow
1. User uploads video files via drag-drop or file picker
2. System displays video preview with basic metadata
3. User selects processing type (highlight reel, story clips, long-form)
4. Configuration panel shows options (duration, style, AI prompts)
5. Processing starts with real-time progress and ETA
6. Results displayed with preview and download options
7. Analytics tracked and displayed in user dashboard

### 📸 Google Photos Integration Workflow
1. User initiates Google Photos connection via OAuth flow
2. System displays available albums with thumbnail previews
3. User selects albums/photos to import with filtering options
4. Import process shows progress with error handling
5. Imported media appears in library with full metadata
6. Search functionality allows natural language queries
7. Sync status and history available in dedicated dashboard

### 📊 Analytics & Reporting Workflow
1. Dashboard shows processing statistics and system health
2. Users can filter data by date range, project, or processing type
3. Interactive charts display trends and performance metrics
4. Export functionality generates reports in PDF/CSV/JSON formats
5. Real-time notifications for completed jobs and system alerts

## Performance & Optimization Requirements

### ⚡ Frontend Performance
- **Lazy loading** for media galleries and large datasets
- **Virtual scrolling** for large lists and grids
- **Image optimization** with WebP/AVIF support and responsive images
- **Code splitting** with route-based chunks
- **Service worker** for offline functionality and caching

### 🔄 API Optimization
- **Request/response caching** with appropriate headers
- **Pagination** for large datasets with infinite scroll
- **WebSocket connections** for real-time updates
- **File chunking** for large media uploads
- **Background job processing** with status updates

## Security & Privacy Considerations

### 🔒 Data Protection
- **End-to-end encryption** for sensitive media content
- **Secure file storage** with access controls and expiration
- **Privacy-first design** with minimal data collection
- **GDPR compliance** with data export and deletion tools
- **Regular security audits** and dependency updates

## Deployment & DevOps

### 🚀 Production Setup
```yaml
# Docker Compose example
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
  
  backend:
    build: ./crow_eye_api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://...
      - GOOGLE_PHOTOS_CLIENT_ID=...
```

### 📦 CI/CD Pipeline
- **Automated testing** with unit, integration, and E2E tests
- **Code quality checks** with ESLint, Prettier, and TypeScript
- **Security scanning** for dependencies and container images
- **Performance monitoring** with Lighthouse and Core Web Vitals
- **Automated deployments** with rollback capabilities

## Success Metrics & KPIs

### 📈 User Experience Metrics
- **Page load times** < 2 seconds for critical paths
- **Media processing success rate** > 95%
- **User task completion rate** > 90%
- **System uptime** > 99.5%
- **API response times** < 500ms for 95th percentile

## Additional Considerations

### 🌐 Accessibility
- **WCAG 2.1 AA compliance** with screen reader support
- **Keyboard navigation** for all interactive elements
- **High contrast mode** support
- **Alternative text** for all media content
- **Focus management** for dynamic content updates

### 🔧 Extensibility
- **Plugin architecture** for custom processing workflows
- **API webhook support** for third-party integrations
- **Custom export formats** and processing options
- **White-label customization** capabilities
- **Multi-tenant architecture** for SaaS deployment

This comprehensive integration should result in a professional, scalable web application that fully leverages the powerful Crow's Eye API backend while providing an exceptional user experience across all supported features and workflows. 