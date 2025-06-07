/**
 * Crow's Eye API Configuration for Frontend
 * This file should be included in your frontend project
 */

// API Configuration
const API_CONFIG = {
  // Change this based on your environment
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // API Endpoints
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/auth/login',
      LOGOUT: '/auth/logout',
      ME: '/auth/me'
    },
    
    // Media Management
    MEDIA: {
      LIST: '/media',
      UPLOAD: '/media/upload',
      GET: (id) => `/media/${id}`,
      UPDATE: (id) => `/media/${id}`,
      DELETE: (id) => `/media/${id}`
    },
    
    // Gallery Management
    GALLERY: {
      LIST: '/gallery',
      CREATE: '/gallery',
      GET: (id) => `/gallery/${id}`,
      UPDATE: (id) => `/gallery/${id}`,
      DELETE: (id) => `/gallery/${id}`
    },
    
    // Stories Management
    STORIES: {
      LIST: '/stories',
      CREATE: '/stories',
      GET: (id) => `/stories/${id}`,
      UPDATE: (id) => `/stories/${id}`,
      DELETE: (id) => `/stories/${id}`
    },
    
    // Highlights Management
    HIGHLIGHTS: {
      LIST: '/highlights',
      CREATE: '/highlights',
      GET: (id) => `/highlights/${id}`,
      UPDATE: (id) => `/highlights/${id}`,
      DELETE: (id) => `/highlights/${id}`
    },
    
    // Audio Processing
    AUDIO: {
      TEXT_TO_SPEECH: '/audio/text-to-speech',
      VOICES: '/audio/voices'
    },
    
    // Analytics
    ANALYTICS: {
      OVERVIEW: '/analytics/overview',
      PLATFORM: (platform) => `/analytics/platforms/${platform}`,
      CONTENT: (type, id) => `/analytics/content/${type}/${id}`
    },
    
    // Admin
    ADMIN: {
      STATUS: '/admin/status',
      ACTIVITY: '/admin/activity'
    }
  },
  
  // Request headers
  getHeaders: (token = null) => {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  },
  
  // Helper function to build full URL
  buildUrl: (endpoint, queryParams = {}) => {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const params = new URLSearchParams(queryParams);
    return params.toString() ? `${url}?${params}` : url;
  }
};

// API Client Class
class CrowsEyeAPI {
  constructor() {
    this.token = localStorage.getItem('crowseye_token');
  }
  
  // Set authentication token
  setToken(token) {
    this.token = token;
    localStorage.setItem('crowseye_token', token);
  }
  
  // Clear authentication token
  clearToken() {
    this.token = null;
    localStorage.removeItem('crowseye_token');
  }
  
  // Generic request method
  async request(endpoint, options = {}) {
    const url = API_CONFIG.buildUrl(endpoint, options.params);
    
    const config = {
      method: options.method || 'GET',
      headers: API_CONFIG.getHeaders(this.token),
      ...options
    };
    
    // Remove params from config as they're already in the URL
    delete config.params;
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }
  
  // Authentication methods
  async login(email, password) {
    const response = await this.request(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }
  
  async logout() {
    await this.request(API_CONFIG.ENDPOINTS.AUTH.LOGOUT, {
      method: 'POST'
    });
    this.clearToken();
  }
  
  async getCurrentUser() {
    return await this.request(API_CONFIG.ENDPOINTS.AUTH.ME);
  }
  
  // Media methods
  async getMedia(params = {}) {
    return await this.request(API_CONFIG.ENDPOINTS.MEDIA.LIST, { params });
  }
  
  async uploadMedia(file, title = '', description = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);
    
    const response = await fetch(
      API_CONFIG.buildUrl(API_CONFIG.ENDPOINTS.MEDIA.UPLOAD),
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        body: formData
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return await response.json();
  }
  
  async updateMedia(id, updates) {
    return await this.request(API_CONFIG.ENDPOINTS.MEDIA.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteMedia(id) {
    return await this.request(API_CONFIG.ENDPOINTS.MEDIA.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Gallery methods
  async getGalleries(params = {}) {
    return await this.request(API_CONFIG.ENDPOINTS.GALLERY.LIST, { params });
  }
  
  async createGallery(data) {
    return await this.request(API_CONFIG.ENDPOINTS.GALLERY.CREATE, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async updateGallery(id, updates) {
    return await this.request(API_CONFIG.ENDPOINTS.GALLERY.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteGallery(id) {
    return await this.request(API_CONFIG.ENDPOINTS.GALLERY.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Stories methods
  async getStories(params = {}) {
    return await this.request(API_CONFIG.ENDPOINTS.STORIES.LIST, { params });
  }
  
  async createStory(data) {
    return await this.request(API_CONFIG.ENDPOINTS.STORIES.CREATE, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async updateStory(id, updates) {
    return await this.request(API_CONFIG.ENDPOINTS.STORIES.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteStory(id) {
    return await this.request(API_CONFIG.ENDPOINTS.STORIES.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Analytics methods
  async getAnalyticsOverview(startDate, endDate) {
    return await this.request(API_CONFIG.ENDPOINTS.ANALYTICS.OVERVIEW, {
      params: { start_date: startDate, end_date: endDate }
    });
  }
  
  async getPlatformAnalytics(platform) {
    return await this.request(API_CONFIG.ENDPOINTS.ANALYTICS.PLATFORM(platform));
  }
}

// Export for use in frontend
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API_CONFIG, CrowsEyeAPI };
} else {
  window.API_CONFIG = API_CONFIG;
  window.CrowsEyeAPI = CrowsEyeAPI;
}