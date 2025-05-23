// Media utilities for handling uploads, formatting, and processing

import { MediaItem } from '../features/galleryGenerator';

// Function to format file size in human-readable format
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Function to determine file type (image or video)
export const getMediaType = (file: File): 'photo' | 'video' | null => {
  if (file.type.startsWith('image/')) {
    return 'photo';
  } else if (file.type.startsWith('video/')) {
    return 'video';
  }
  return null;
};

// Function to create a thumbnail from a file
export const createThumbnail = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          resolve(e.target.result as string);
        } else {
          reject(new Error('Failed to create thumbnail'));
        }
      };
      reader.onerror = () => reject(new Error('Error reading file'));
      reader.readAsDataURL(file);
    } else if (file.type.startsWith('video/')) {
      // For videos, we'd create a thumbnail using the video element
      // This is a simplified version
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        video.currentTime = 1; // Seek to 1 second
      };
      
      video.onseeked = () => {
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          try {
            const thumbnail = canvas.toDataURL('image/jpeg');
            resolve(thumbnail);
          } catch (e) {
            reject(new Error('Failed to create video thumbnail'));
          }
        } else {
          reject(new Error('Canvas context not available'));
        }
      };
      
      video.onerror = () => reject(new Error('Error loading video'));
      
      video.src = URL.createObjectURL(file);
      video.load();
    } else {
      reject(new Error('Unsupported file type'));
    }
  });
};

// Convert File objects to MediaItem format
export const filesToMediaItems = async (files: File[]): Promise<MediaItem[]> => {
  const mediaItems: MediaItem[] = [];
  
  for (const file of files) {
    const type = getMediaType(file);
    
    if (type) {
      try {
        const url = await createThumbnail(file);
        const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        
        mediaItems.push({
          id: Date.now() + Math.floor(Math.random() * 1000), // Simple unique ID
          url,
          type,
          date,
          metadata: {
            fileSize: file.size,
            // We would extract more metadata in a real implementation
            // For videos: duration, resolution, etc.
            // For images: dimensions, EXIF data, etc.
          }
        });
      } catch (error) {
        console.error('Error processing file:', error);
        // Continue with other files
      }
    }
  }
  
  return mediaItems;
};

// Function to enhance a photo (simple mock)
export const enhancePhoto = (photoUrl: string): Promise<string> => {
  return new Promise((resolve) => {
    // In a real implementation, this would call an API or use a library
    // For now, we'll just simulate a delay
    setTimeout(() => {
      // Just return the original URL for this mock
      resolve(photoUrl);
    }, 500);
  });
}; 