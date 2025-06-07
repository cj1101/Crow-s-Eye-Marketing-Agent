# Frontend Integration Guide for Crow's Eye API

## Overview
This guide provides step-by-step instructions for connecting your website frontend to the Crow's Eye API backend. It covers configuration, authentication, and usage of all API endpoints.

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Configuration](#api-configuration)
3. [Authentication](#authentication)
4. [Using the API Client](#using-the-api-client)
5. [React/Next.js Integration](#reactnextjs-integration)
6. [Error Handling](#error-handling)
7. [Mobile App Integration](#mobile-app-integration)
8. [Deployment](#deployment)

## Quick Start

### 1. Copy API Configuration Files
Copy one of these files to your frontend project:
- `frontend-api-config.js` (for JavaScript projects)
- `frontend-api-config.ts` (for TypeScript projects)

### 2. Set Environment Variables
Create a `.env` file in your frontend project:

```env
REACT_APP_API_URL=https://api.crowseye.tech
# or for local development:
# REACT_APP_API_URL=http://localhost:8000
```

### 3. Install Dependencies
```bash
# If using axios (optional, but recommended)
npm install axios

# For TypeScript projects
npm install --save-dev @types/node
```

### 4. Basic Usage Example

```javascript
import { CrowsEyeAPI } from './frontend-api-config';

const api = new CrowsEyeAPI();

// Login
const loginUser = async () => {
  try {
    const response = await api.login('user@example.com', 'password123');
    console.log('Logged in:', response.user);
  } catch (error) {
    console.error('Login failed:', error);
  }
};

// Get media items
const getMedia = async () => {
  try {
    const media = await api.getMedia({ limit: 10 });
    console.log('Media items:', media);
  } catch (error) {
    console.error('Failed to get media:', error);
  }
};
```

## API Configuration

### Environment-Specific Configuration

```javascript
// frontend-api-config.js modification for multiple environments

const getApiUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    return 'https://api.crowseye.tech';
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

const API_CONFIG = {
  BASE_URL: getApiUrl(),
  // ... rest of config
};
```

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000`
- `https://*.crowseye.tech`
- `https://crowseye.tech`

If you're developing on a different port, update the CORS settings in the API.

## Authentication

### Login Flow

```javascript
// components/LoginForm.js
import React, { useState } from 'react';
import { CrowsEyeAPI } from '../frontend-api-config';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const api = new CrowsEyeAPI();
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.login(email, password);
      // Store user data in your app state (Redux, Context, etc.)
      localStorage.setItem('user', JSON.stringify(response.user));
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleLogin}>
      {error && <div className="error">{error}</div>}
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};
```

### Protected Routes

```javascript
// components/ProtectedRoute.js
import React, { useEffect, useState } from 'react';
import { CrowsEyeAPI } from '../frontend-api-config';

const ProtectedRoute = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const api = new CrowsEyeAPI();
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Redirect to login
        window.location.href = '/login';
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (!user) return null;
  
  return children;
};
```

## Using the API Client

### Media Management

```javascript
// Upload media
const uploadFile = async (file) => {
  try {
    const media = await api.uploadMedia(file, 'My Image', 'Description');
    console.log('Uploaded:', media);
    return media;
  } catch (error) {
    console.error('Upload failed:', error);
  }
};

// List media with filters
const getImages = async () => {
  const images = await api.getMedia({ 
    media_type: 'IMAGE',
    limit: 20,
    offset: 0 
  });
  return images;
};

// Delete media
const deleteMedia = async (mediaId) => {
  await api.deleteMedia(mediaId);
  // Refresh media list
};
```

### Content Creation

```javascript
// Create a story
const createStory = async () => {
  const story = await api.createStory({
    title: 'My Marketing Story',
    content: 'This is the story content with #hashtags',
    media_ids: ['media_id_1', 'media_id_2'],
    hashtags: ['#marketing', '#socialmedia']
  });
  return story;
};

// Create a gallery
const createGallery = async (imageIds) => {
  const gallery = await api.createGallery({
    title: 'Product Gallery',
    description: 'Our latest products',
    media_ids: imageIds
  });
  return gallery;
};
```

### Analytics

```javascript
// Get analytics data
const getAnalytics = async () => {
  const endDate = new Date().toISOString();
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  
  const analytics = await api.getAnalyticsOverview(startDate, endDate);
  return analytics;
};

// Get platform-specific analytics
const getInstagramAnalytics = async () => {
  const data = await api.getPlatformAnalytics('instagram');
  return data;
};
```

## React/Next.js Integration

### React Context for API

```javascript
// contexts/ApiContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import { CrowsEyeAPI } from '../frontend-api-config';

const ApiContext = createContext();

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within ApiProvider');
  }
  return context;
};

export const ApiProvider = ({ children }) => {
  const [api] = useState(new CrowsEyeAPI());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        // User not logged in
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, [api]);
  
  const login = async (email, password) => {
    const response = await api.login(email, password);
    setUser(response.user);
    return response;
  };
  
  const logout = async () => {
    await api.logout();
    setUser(null);
  };
  
  return (
    <ApiContext.Provider value={{
      api,
      user,
      loading,
      login,
      logout
    }}>
      {children}
    </ApiContext.Provider>
  );
};
```

### Using with Next.js

```javascript
// pages/_app.js
import { ApiProvider } from '../contexts/ApiContext';

function MyApp({ Component, pageProps }) {
  return (
    <ApiProvider>
      <Component {...pageProps} />
    </ApiProvider>
  );
}

export default MyApp;
```

### Custom Hooks

```javascript
// hooks/useMedia.js
import { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';

export const useMedia = (options = {}) => {
  const { api } = useApi();
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchMedia = async () => {
      try {
        setLoading(true);
        const data = await api.getMedia(options);
        setMedia(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMedia();
  }, [JSON.stringify(options)]);
  
  const refresh = async () => {
    const data = await api.getMedia(options);
    setMedia(data);
  };
  
  return { media, loading, error, refresh };
};
```

## Error Handling

### Global Error Handler

```javascript
// utils/errorHandler.js
export class ApiError extends Error {
  constructor(message, statusCode, details) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
  }
}

// Enhance the API client with better error handling
class EnhancedCrowsEyeAPI extends CrowsEyeAPI {
  async request(endpoint, options = {}) {
    try {
      return await super.request(endpoint, options);
    } catch (error) {
      // Handle specific error types
      if (error.message.includes('401')) {
        // Token expired, redirect to login
        this.clearToken();
        window.location.href = '/login';
      } else if (error.message.includes('403')) {
        // Insufficient permissions
        throw new ApiError(
          'You need to upgrade your subscription to access this feature',
          403
        );
      } else if (error.message.includes('429')) {
        // Rate limit
        throw new ApiError(
          'Too many requests. Please wait a moment and try again.',
          429
        );
      }
      throw error;
    }
  }
}
```

### Component Error Boundaries

```javascript
// components/ErrorBoundary.js
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-page">
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

## Mobile App Integration

### React Native

```javascript
// api/crowsEyeApi.js for React Native
import AsyncStorage from '@react-native-async-storage/async-storage';

class CrowsEyeAPIMobile extends CrowsEyeAPI {
  async setToken(token) {
    this.token = token;
    await AsyncStorage.setItem('crowseye_token', token);
  }
  
  async clearToken() {
    this.token = null;
    await AsyncStorage.removeItem('crowseye_token');
  }
  
  constructor() {
    super();
    // Load token from AsyncStorage
    this.loadToken();
  }
  
  async loadToken() {
    this.token = await AsyncStorage.getItem('crowseye_token');
  }
}
```

### Flutter

```dart
// lib/api/crows_eye_api.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class CrowsEyeAPI {
  static const String baseUrl = 'https://api.crowseye.tech';
  String? _token;
  
  CrowsEyeAPI() {
    _loadToken();
  }
  
  Future<void> _loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('crowseye_token');
  }
  
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      await _saveToken(data['access_token']);
      return data;
    } else {
      throw Exception('Login failed');
    }
  }
  
  Future<void> _saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('crowseye_token', token);
  }
}
```

## Deployment

### Production Configuration

1. **Update API URL** in your environment variables:
   ```bash
   REACT_APP_API_URL=https://api.crowseye.tech
   ```

2. **Build your frontend**:
   ```bash
   npm run build
   ```

3. **Deploy to Firebase Hosting**:
   ```bash
   firebase deploy --only hosting
   ```

4. **Deploy API to Google Cloud**:
   ```bash
   gcloud app deploy app.yaml
   ```

### Security Best Practices

1. **Never expose sensitive data** in frontend code
2. **Use HTTPS** for all API calls
3. **Implement request rate limiting** on the client side
4. **Validate all inputs** before sending to API
5. **Handle token expiration** gracefully

### Performance Optimization

1. **Cache API responses** where appropriate:
   ```javascript
   const cache = new Map();
   
   const getCachedData = async (key, fetcher, ttl = 60000) => {
     const cached = cache.get(key);
     if (cached && Date.now() - cached.timestamp < ttl) {
       return cached.data;
     }
     
     const data = await fetcher();
     cache.set(key, { data, timestamp: Date.now() });
     return data;
   };
   ```

2. **Implement pagination** for large lists
3. **Use debouncing** for search inputs
4. **Lazy load** media items

## Testing

### Test Your Integration

Run the test script to verify your API is working:

```bash
# Install dependencies
pip install requests

# Run tests
python test-crow-eye-api.py
```

### Frontend Testing

```javascript
// __tests__/api.test.js
import { CrowsEyeAPI } from '../frontend-api-config';

describe('Crows Eye API', () => {
  let api;
  
  beforeEach(() => {
    api = new CrowsEyeAPI();
  });
  
  test('login works correctly', async () => {
    const response = await api.login('test@example.com', 'password');
    expect(response).toHaveProperty('access_token');
    expect(response).toHaveProperty('user');
  });
  
  test('handles errors correctly', async () => {
    await expect(api.login('invalid', 'wrong')).rejects.toThrow();
  });
});
```

## Support

If you encounter any issues:
1. Check the browser console for errors
2. Verify the API is running with the health check endpoint
3. Ensure CORS is properly configured
4. Check that your authentication token is valid
5. Review the API documentation for endpoint details

For additional help, refer to the API documentation at `/docs` on your API server.