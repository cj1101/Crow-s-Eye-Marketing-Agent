// Mock media library API
import { MediaItem } from '../features/galleryGenerator';

// Simulated database for media (in-memory storage)
let mockMediaStorage: {
  raw_photos: MediaItem[];
  raw_videos: MediaItem[];
  post_ready: Array<{
    id: number;
    name: string;
    type: 'single' | 'carousel' | 'story';
    media: MediaItem[];
    caption: string;
    date: string;
  }>;
} = {
  raw_photos: [
    { 
      id: 1, 
      url: '/placeholder-image-1.jpg', 
      type: 'photo', 
      date: '2023-10-15',
      metadata: {
        width: 1920,
        height: 1080,
        fileSize: 2456000,
      }
    },
    { 
      id: 2, 
      url: '/placeholder-image-2.jpg', 
      type: 'photo', 
      date: '2023-10-14',
      metadata: {
        width: 1920,
        height: 1080,
        fileSize: 1890000,
      }
    },
    { 
      id: 3, 
      url: '/placeholder-image-3.jpg', 
      type: 'photo', 
      date: '2023-10-12',
      metadata: {
        width: 1920,
        height: 1080,
        fileSize: 3120000,
      }
    },
  ],
  raw_videos: [
    { 
      id: 4, 
      url: '/placeholder-video-1.mp4', 
      type: 'video', 
      date: '2023-10-10',
      metadata: {
        width: 1920,
        height: 1080,
        duration: '0:45',
        fileSize: 15640000,
      }
    },
    { 
      id: 5, 
      url: '/placeholder-video-2.mp4', 
      type: 'video', 
      date: '2023-10-08',
      metadata: {
        width: 1920,
        height: 1080,
        duration: '2:30',
        fileSize: 34560000,
      }
    },
  ],
  post_ready: [
    { 
      id: 6, 
      name: 'Beach day post', 
      type: 'carousel',
      media: [
        { 
          id: 1, 
          url: '/placeholder-image-1.jpg', 
          type: 'photo', 
          date: '2023-10-15',
        },
        { 
          id: 2, 
          url: '/placeholder-image-2.jpg', 
          type: 'photo', 
          date: '2023-10-14',
        }
      ],
      caption: 'Perfect day at the beach! #summer #ocean', 
      date: '2023-10-16'
    },
  ]
};

// API functions for media library
export const getMediaLibrary = async () => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  return mockMediaStorage;
};

export const addMediaItem = async (item: MediaItem, category: 'raw_photos' | 'raw_videos') => {
  // Validate the category
  if (!['raw_photos', 'raw_videos'].includes(category)) {
    throw new Error('Invalid category');
  }
  
  // Validate the item
  if (!item.url || !item.type) {
    throw new Error('Invalid media item');
  }
  
  // Add the item to the appropriate category
  mockMediaStorage[category].push({
    ...item,
    id: Date.now() + Math.floor(Math.random() * 1000), // Generate a unique ID
  });
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  return { success: true };
};

export const createPost = async (
  name: string,
  type: 'single' | 'carousel' | 'story',
  mediaIds: number[],
  caption: string
) => {
  // Collect the media items from their IDs
  const allMedia = [...mockMediaStorage.raw_photos, ...mockMediaStorage.raw_videos];
  const selectedMedia = allMedia.filter(item => mediaIds.includes(item.id));
  
  if (selectedMedia.length === 0) {
    throw new Error('No valid media items selected');
  }
  
  // Create a new post
  const newPost = {
    id: Date.now() + Math.floor(Math.random() * 1000),
    name,
    type,
    media: selectedMedia,
    caption,
    date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
  };
  
  // Add it to the post_ready collection
  mockMediaStorage.post_ready.push(newPost);
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 400));
  
  return { success: true, post: newPost };
};

export const searchMedia = async (query: string) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // In a real implementation, this would use a proper search algorithm
  // For now, we'll just do a simple case-insensitive match on media names/metadata
  const lowerQuery = query.toLowerCase();
  
  const matchingPhotos = mockMediaStorage.raw_photos.filter(photo => 
    photo.metadata?.tags?.some(tag => tag.toLowerCase().includes(lowerQuery)) || 
    photo.date?.toLowerCase().includes(lowerQuery)
  );
  
  const matchingVideos = mockMediaStorage.raw_videos.filter(video => 
    video.metadata?.tags?.some(tag => tag.toLowerCase().includes(lowerQuery)) || 
    video.date?.toLowerCase().includes(lowerQuery) ||
    video.metadata?.duration?.toLowerCase().includes(lowerQuery)
  );
  
  return {
    photos: matchingPhotos,
    videos: matchingVideos
  };
}; 