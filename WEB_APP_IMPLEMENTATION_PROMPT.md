# 🦅 Crow's Eye Marketing Agent - Web App Implementation Prompt

## Project Overview
Create a modern, responsive React web application that serves as the frontend for the Crow's Eye Marketing Agent. The app should provide a comprehensive interface for AI-powered social media content creation, management, and analytics.

## 🎯 Core Requirements

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + Headless UI
- **State Management**: Zustand + React Query
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Lucide React + Heroicons
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod validation

### 🏗️ Architecture & Structure
```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI elements (Button, Input, Modal, etc.)
│   ├── layout/          # Layout components (Header, Sidebar, etc.)
│   ├── media/           # Media-related components
│   ├── posts/           # Post management components
│   ├── ai/              # AI features components
│   └── analytics/       # Analytics and charts
├── pages/               # Page components
├── services/            # API services and utilities
├── hooks/               # Custom React hooks
├── stores/              # Zustand stores
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── assets/              # Static assets
```

## 🌟 Key Features to Implement

### 1. Dashboard
- **Overview Cards**: Active posts, media library size, recent highlights, analytics summary
- **Quick Actions**: Upload media, create post, generate highlight, view analytics
- **Recent Activity Feed**: Latest posts, uploads, and AI generations
- **Performance Metrics**: Engagement rates, content performance charts

### 2. Media Management
- **Drag & Drop Upload**: Support images, videos, and audio files
- **Media Library**: Grid/list view with filtering and search
- **Media Preview**: Lightbox with metadata display
- **Batch Operations**: Select multiple files for bulk actions
- **AI Analysis**: Display AI-generated tags and descriptions

### 3. Content Creation & Management
- **Post Creator**: Rich form with media selection, caption input, platform targeting
- **AI Integration**: Generate captions, optimize content, create highlights
- **Platform Optimization**: Preview how content appears on different platforms
- **Scheduling**: Calendar interface for scheduling posts
- **Bulk Operations**: Mass edit, delete, or schedule posts

### 4. AI-Powered Features
- **Highlight Generator**: Upload media and generate video highlights with AI analysis
- **Caption Generation**: AI-powered caption creation with customization options
- **Content Optimization**: Suggest improvements for different platforms
- **Hashtag Suggestions**: AI-generated relevant hashtags
- **Trend Analysis**: AI insights on content performance

### 5. Analytics & Insights
- **Performance Dashboard**: Charts showing engagement, reach, and growth
- **Content Analytics**: Individual post performance metrics
- **Trend Analysis**: Identify best-performing content types
- **Export Features**: Download reports as PDF/CSV
- **Real-time Updates**: Live analytics with WebSocket integration

### 6. Settings & Configuration
- **API Configuration**: Backend connection settings
- **Platform Integration**: Social media account connections
- **AI Settings**: Customize AI behavior and preferences
- **User Preferences**: Theme, notifications, display options

## 🎨 Design Requirements

### Visual Design
- **Modern & Clean**: Minimalist design with plenty of white space
- **Professional**: Suitable for business use with polished aesthetics
- **Responsive**: Mobile-first approach, works on all screen sizes
- **Dark Mode**: Toggle between light and dark themes
- **Accessibility**: WCAG 2.1 AA compliance

### Color Scheme
```css
Primary: #3B82F6 (Blue)
Secondary: #6B7280 (Gray)
Success: #10B981 (Green)
Warning: #F59E0B (Amber)
Error: #EF4444 (Red)
Background: #F9FAFB (Light Gray)
```

### Typography
- **Primary Font**: Inter (Google Fonts)
- **Headings**: Font weights 600-700
- **Body Text**: Font weight 400-500
- **Code/Monospace**: JetBrains Mono

## 🔌 API Integration

### Base API Configuration
```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-project.uc.r.appspot.com' 
  : 'http://localhost:8000';
```

### Key API Endpoints to Integrate
- `GET /health` - Health check
- `GET /api/v1/health` - API health check
- `POST /api/v1/media/upload` - Upload media files
- `GET /api/v1/media` - Fetch media library
- `POST /api/v1/posts` - Create new post
- `GET /api/v1/posts` - Fetch posts
- `POST /api/v1/ai/generate-highlight` - Generate video highlights
- `POST /api/v1/ai/generate-caption` - Generate captions
- `GET /api/v1/analytics` - Fetch analytics data

### Error Handling
- Implement comprehensive error handling with user-friendly messages
- Retry mechanisms for failed requests
- Offline detection and appropriate fallbacks
- Loading states for all async operations

## 🧩 Component Examples

### 1. Media Upload Component
```typescript
interface MediaUploadProps {
  onUpload: (files: File[]) => void;
  acceptedTypes: string[];
  maxSize: number;
  multiple?: boolean;
}

const MediaUpload: React.FC<MediaUploadProps> = ({ ... }) => {
  // Implement drag & drop functionality
  // File validation and preview
  // Upload progress indication
  // Error handling
};
```

### 2. AI Highlight Generator
```typescript
interface HighlightGeneratorProps {
  mediaId: string;
  onGenerated: (highlight: HighlightData) => void;
}

const HighlightGenerator: React.FC<HighlightGeneratorProps> = ({ ... }) => {
  // Media selection interface
  // AI processing indicator
  // Preview generated highlight
  // Customization options
};
```

### 3. Analytics Dashboard
```typescript
interface AnalyticsDashboardProps {
  timeRange: TimeRange;
  filters: AnalyticsFilters;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ ... }) => {
  // Chart components using Recharts
  // Filtering and date range selection
  // Export functionality
  // Real-time data updates
};
```

## 📱 Responsive Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px - 1440px
- **Large Desktop**: 1440px+

## 🔐 Security Considerations
- Input validation on all forms
- XSS prevention
- CSRF protection
- Secure token storage
- API request sanitization

## 🚀 Performance Optimization
- Code splitting with React.lazy()
- Image optimization and lazy loading
- Virtual scrolling for large lists
- Debounced search inputs
- Efficient re-rendering with React.memo()

## 🧪 Testing Strategy
- Unit tests for utility functions
- Component testing with React Testing Library
- Integration tests for API calls
- E2E testing with Playwright/Cypress
- Accessibility testing

## 📦 Deployment
- Build optimization for production
- Environment variable configuration
- CDN integration for assets
- Progressive Web App (PWA) features
- Continuous deployment pipeline

## 🎯 Implementation Priority

### Phase 1 (MVP)
1. Basic layout and navigation
2. Media upload and library
3. Simple post creation
4. AI highlight generation
5. Basic analytics dashboard

### Phase 2 (Enhanced Features)
1. Advanced post management
2. Scheduling functionality
3. Detailed analytics
4. User settings and preferences
5. Performance optimizations

### Phase 3 (Advanced Features)
1. Real-time updates
2. Advanced AI features
3. Collaboration tools
4. Advanced analytics
5. Mobile app considerations

## 📚 Additional Resources
- **API Documentation**: Available at `/docs` endpoint
- **Design System**: Use Tailwind CSS utility classes
- **Component Library**: Build reusable components following atomic design principles
- **State Management**: Use Zustand for global state, React Query for server state

---

**Objective**: Create a production-ready, user-friendly web application that seamlessly integrates with the Crow's Eye API to provide a comprehensive social media marketing management experience. 