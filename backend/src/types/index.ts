import { Request } from 'express';

// User Types
export interface UserProfile {
  id: string;
  email: string;
  displayName: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  plan: 'free' | 'creator' | 'pro';
  createdAt: string;
  lastLoginAt: string;
}

export interface AuthUser extends UserProfile {
  // Additional auth-specific fields can be added here
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  displayName: string;
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}

export interface AuthenticatedRequest extends Request {
  user?: UserProfile;
}

// Media Types
export interface MediaItem {
  id: string;
  name: string;
  type: 'image' | 'video' | 'audio';
  url: string;
  thumbnail?: string;
  size: number;
  createdAt: string;
  tags: string[];
}

export interface MediaUploadRequest {
  file: Express.Multer.File;
  metadata?: string;
}

// Gallery Types
export interface GalleryItem {
  id: string;
  title: string;
  images: string[];
  createdAt: string;
}

export interface CreateGalleryRequest {
  title: string;
  images: string[];
}

// Story Types
export interface Story {
  id: string;
  title: string;
  content: string;
  media: string[];
  createdAt: string;
}

export interface CreateStoryRequest {
  title: string;
  content: string;
  media: string[];
}

// Highlight Reel Types
export interface HighlightReel {
  id: string;
  title: string;
  clips: string[];
  duration: number;
  createdAt: string;
}

export interface CreateHighlightRequest {
  title: string;
  clips: string[];
  duration: number;
}

// Analytics Types
export interface TopPost {
  id: string;
  title: string;
  views: number;
  likes: number;
  platform: string;
}

export interface PlatformStats {
  platform: string;
  posts: number;
  engagement: number;
}

export interface AnalyticsResponse {
  totalPosts: number;
  totalViews: number;
  totalLikes: number;
  totalComments: number;
  engagementRate: number;
  topPosts: TopPost[];
  platformStats: PlatformStats[];
}

// Marketing Tool Types
export interface RecentActivity {
  id: string;
  action: string;
  timestamp: string;
  type: 'success' | 'info' | 'warning';
}

export interface MarketingToolStats {
  totalPosts: number;
  scheduledPosts: number;
  aiGenerated: number;
  engagementRate: number;
  socialAccounts: number;
  mediaFiles: number;
  recentActivity: RecentActivity[];
  subscriptionTier: string;
  aiCreditsRemaining: number;
  aiEditsRemaining: number;
}

export interface CreatePostRequest {
  content: string;
  platforms: string[];
  hashtags: string[];
  mediaFiles: string[];
  scheduledFor?: string;
}

export interface CreatePostResponse {
  success: boolean;
  postId: string;
}

// Error Types
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// Database Types (internal)
export type UserPlan = 'FREE' | 'CREATOR' | 'PRO';
export type MediaType = 'IMAGE' | 'VIDEO' | 'AUDIO';
export type ActivityType = 'SUCCESS' | 'INFO' | 'WARNING' | 'ERROR';

// JWT Types
export interface JWTPayload {
  userId: string;
  email: string;
  plan: string;
  iat?: number;
  exp?: number;
}

export interface RefreshTokenPayload {
  userId: string;
  tokenId: string;
  iat?: number;
  exp?: number;
} 