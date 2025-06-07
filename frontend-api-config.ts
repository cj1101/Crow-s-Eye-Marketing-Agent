/**
 * Crow's Eye API Configuration for Frontend (TypeScript)
 * This file should be included in your frontend project
 */

// API Response Types
export interface User {
  user_id: string;
  email: string;
  username: string;
  subscription: {
    tier: 'SPARK' | 'CREATOR' | 'PRO_AGENCY' | 'ENTERPRISE';
    start_date: string;
    status: string;
  };
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MediaItem {
  id: string;
  title: string;
  description?: string;
  url: string;
  thumbnail_url?: string;
  type: 'IMAGE' | 'VIDEO' | 'AUDIO';
  size: number;
  duration?: number;
  created_at: string;
  updated_at: string;
}

export interface Gallery {
  id: string;
  title: string;
  description?: string;
  media_ids: string[];
  media?: MediaItem[];
  created_at: string;
  updated_at: string;
}

export interface Story {
  id: string;
  title: string;
  content: string;
  media_ids: string[];
  media?: MediaItem[];
  hashtags: string[];
  created_at: string;
  updated_at: string;
  scheduled_at?: string;
  published_at?: string;
  status: 'DRAFT' | 'SCHEDULED' | 'PUBLISHED';
}

export interface Highlight {
  id: string;
  title: string;
  media_ids: string[];
  media?: MediaItem[];
  created_at: string;
  updated_at: string;
}

export interface AnalyticsData {
  total_views: number;
  total_likes: number;
  total_shares: number;
  total_comments: number;
  engagement_rate: number;
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// API Configuration
export const API_CONFIG = {
  // Change this based on your environment
  BASE_URL: (typeof window !== 'undefined' && (window as any).REACT_APP_API_URL) || 
            'http://localhost:8000',
  
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
      GET: (id: string) => `/media/${id}`,
      UPDATE: (id: string) => `/media/${id}`,
      DELETE: (id: string) => `/media/${id}`
    },
    
    // Gallery Management
    GALLERY: {
      LIST: '/gallery',
      CREATE: '/gallery',
      GET: (id: string) => `/gallery/${id}`,
      UPDATE: (id: string) => `/gallery/${id}`,
      DELETE: (id: string) => `/gallery/${id}`
    },
    
    // Stories Management
    STORIES: {
      LIST: '/stories',
      CREATE: '/stories',
      GET: (id: string) => `/stories/${id}`,
      UPDATE: (id: string) => `/stories/${id}`,
      DELETE: (id: string) => `/stories/${id}`
    },
    
    // Highlights Management
    HIGHLIGHTS: {
      LIST: '/highlights',
      CREATE: '/highlights',
      GET: (id: string) => `/highlights/${id}`,
      UPDATE: (id: string) => `/highlights/${id}`,
      DELETE: (id: string) => `/highlights/${id}`
    },
    
    // Audio Processing
    AUDIO: {
      TEXT_TO_SPEECH: '/audio/text-to-speech',
      VOICES: '/audio/voices'
    },
    
    // Analytics
    ANALYTICS: {
      OVERVIEW: '/analytics/overview',
      PLATFORM: (platform: string) => `/analytics/platforms/${platform}`,
      CONTENT: (type: string, id: string) => `/analytics/content/${type}/${id}`
    },
    
    // Admin
    ADMIN: {
      STATUS: '/admin/status',
      ACTIVITY: '/admin/activity'
    }
  },
  
  // Request headers
  getHeaders: (token: string | null = null): HeadersInit => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  },
  
  // Helper function to build full URL
  buildUrl: (endpoint: string, queryParams: Record<string, any> = {}): string => {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const params = new URLSearchParams(queryParams);
    return params.toString() ? `${url}?${params}` : url;
  }
} as const;

// Request Options Interface
interface RequestOptions {
  method?: string;
  params?: Record<string, any>;
  body?: any;
  headers?: HeadersInit;
}

// API Client Class
export class CrowsEyeAPI {
  private token: string | null;
  
  constructor() {
    this.token = localStorage.getItem('crowseye_token');
  }
  
  // Set authentication token
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('crowseye_token', token);
  }
  
  // Clear authentication token
  clearToken(): void {
    this.token = null;
    localStorage.removeItem('crowseye_token');
  }
  
  // Generic request method
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = API_CONFIG.buildUrl(endpoint, options.params);
    
    const config: RequestInit = {
      method: options.method || 'GET',
      headers: API_CONFIG.getHeaders(this.token),
    };
    
    if (options.body && options.method !== 'GET') {
      config.body = options.body;
    }
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }
  
  // Authentication methods
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (response.access_token) {
      this.setToken(response.access_token);
    }
    
    return response;
  }
  
  async logout(): Promise<void> {
    await this.request(API_CONFIG.ENDPOINTS.AUTH.LOGOUT, {
      method: 'POST'
    });
    this.clearToken();
  }
  
  async getCurrentUser(): Promise<User> {
    return await this.request<User>(API_CONFIG.ENDPOINTS.AUTH.ME);
  }
  
  // Media methods
  async getMedia(params: { 
    media_type?: 'IMAGE' | 'VIDEO' | 'AUDIO';
    limit?: number;
    offset?: number;
  } = {}): Promise<MediaItem[]> {
    return await this.request<MediaItem[]>(API_CONFIG.ENDPOINTS.MEDIA.LIST, { params });
  }
  
  async uploadMedia(file: File, title?: string, description?: string): Promise<MediaItem> {
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
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return await response.json();
  }
  
  async getMediaById(id: string): Promise<MediaItem> {
    return await this.request<MediaItem>(API_CONFIG.ENDPOINTS.MEDIA.GET(id));
  }
  
  async updateMedia(id: string, updates: Partial<MediaItem>): Promise<MediaItem> {
    return await this.request<MediaItem>(API_CONFIG.ENDPOINTS.MEDIA.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteMedia(id: string): Promise<void> {
    return await this.request<void>(API_CONFIG.ENDPOINTS.MEDIA.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Gallery methods
  async getGalleries(params: { 
    limit?: number;
    offset?: number;
  } = {}): Promise<Gallery[]> {
    return await this.request<Gallery[]>(API_CONFIG.ENDPOINTS.GALLERY.LIST, { params });
  }
  
  async createGallery(data: {
    title: string;
    description?: string;
    media_ids: string[];
  }): Promise<Gallery> {
    return await this.request<Gallery>(API_CONFIG.ENDPOINTS.GALLERY.CREATE, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async getGalleryById(id: string): Promise<Gallery> {
    return await this.request<Gallery>(API_CONFIG.ENDPOINTS.GALLERY.GET(id));
  }
  
  async updateGallery(id: string, updates: Partial<Gallery>): Promise<Gallery> {
    return await this.request<Gallery>(API_CONFIG.ENDPOINTS.GALLERY.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteGallery(id: string): Promise<void> {
    return await this.request<void>(API_CONFIG.ENDPOINTS.GALLERY.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Stories methods
  async getStories(params: { 
    limit?: number;
    offset?: number;
  } = {}): Promise<Story[]> {
    return await this.request<Story[]>(API_CONFIG.ENDPOINTS.STORIES.LIST, { params });
  }
  
  async createStory(data: {
    title: string;
    content: string;
    media_ids?: string[];
    hashtags?: string[];
  }): Promise<Story> {
    return await this.request<Story>(API_CONFIG.ENDPOINTS.STORIES.CREATE, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async getStoryById(id: string): Promise<Story> {
    return await this.request<Story>(API_CONFIG.ENDPOINTS.STORIES.GET(id));
  }
  
  async updateStory(id: string, updates: Partial<Story>): Promise<Story> {
    return await this.request<Story>(API_CONFIG.ENDPOINTS.STORIES.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteStory(id: string): Promise<void> {
    return await this.request<void>(API_CONFIG.ENDPOINTS.STORIES.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Highlights methods
  async getHighlights(params: { 
    limit?: number;
    offset?: number;
  } = {}): Promise<Highlight[]> {
    return await this.request<Highlight[]>(API_CONFIG.ENDPOINTS.HIGHLIGHTS.LIST, { params });
  }
  
  async createHighlight(data: {
    title: string;
    media_ids: string[];
  }): Promise<Highlight> {
    return await this.request<Highlight>(API_CONFIG.ENDPOINTS.HIGHLIGHTS.CREATE, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async getHighlightById(id: string): Promise<Highlight> {
    return await this.request<Highlight>(API_CONFIG.ENDPOINTS.HIGHLIGHTS.GET(id));
  }
  
  async updateHighlight(id: string, updates: Partial<Highlight>): Promise<Highlight> {
    return await this.request<Highlight>(API_CONFIG.ENDPOINTS.HIGHLIGHTS.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }
  
  async deleteHighlight(id: string): Promise<void> {
    return await this.request<void>(API_CONFIG.ENDPOINTS.HIGHLIGHTS.DELETE(id), {
      method: 'DELETE'
    });
  }
  
  // Analytics methods
  async getAnalyticsOverview(startDate: string, endDate: string): Promise<AnalyticsData> {
    return await this.request<AnalyticsData>(API_CONFIG.ENDPOINTS.ANALYTICS.OVERVIEW, {
      params: { start_date: startDate, end_date: endDate }
    });
  }
  
  async getPlatformAnalytics(platform: 'instagram' | 'facebook' | 'twitter' | 'linkedin'): Promise<AnalyticsData> {
    return await this.request<AnalyticsData>(API_CONFIG.ENDPOINTS.ANALYTICS.PLATFORM(platform));
  }
}

// Create and export a default instance
export const apiClient = new CrowsEyeAPI();