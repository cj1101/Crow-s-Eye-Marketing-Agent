// This would be connected to an AI service in a real implementation
// For now, we'll implement a simple mock service

export interface MediaItem {
  id: number;
  url: string;
  type: 'photo' | 'video';
  selected?: boolean;
  date?: string;
  metadata?: {
    width?: number;
    height?: number;
    duration?: string;
    fileSize?: number;
    tags?: string[];
  };
}

export interface GalleryGenerationOptions {
  prompt: string;  // This is now the gallery focus
  enhancePhotos?: boolean;
  maxItems?: number;
}

export interface GalleryGenerationResult {
  selectedItems: MediaItem[];
  suggestedCaption?: string;
}

// Mock function to simulate AI-based selection
export const generateGallery = async (
  mediaItems: MediaItem[],
  options: GalleryGenerationOptions
): Promise<GalleryGenerationResult> => {
  // In a real implementation, this would call an AI service
  return new Promise((resolve) => {
    // Simulate API call delay
    setTimeout(() => {
      // Simple logic to simulate AI selection based on the prompt
      let selectedItems: MediaItem[] = [];
      
      // Parse the prompt for keywords
      const focus = options.prompt.toLowerCase();
      
      // If focus contains "best", select items with even IDs
      if (focus.includes('best')) {
        selectedItems = mediaItems.filter(item => item.id % 2 === 0);
      } 
      // If focus specifies a number, select that many items
      else if (/select [0-9]+ items/.test(focus)) {
        const match = focus.match(/select ([0-9]+) items/);
        const count = match ? parseInt(match[1]) : 3;
        selectedItems = mediaItems.slice(0, Math.min(count, mediaItems.length));
      }
      // Default selection
      else {
        // Select random items, between 3-5 items
        const count = Math.floor(Math.random() * 3) + 3;
        const shuffled = [...mediaItems].sort(() => 0.5 - Math.random());
        selectedItems = shuffled.slice(0, count);
      }
      
      // Add selected flag to the items
      selectedItems = selectedItems.map(item => ({
        ...item,
        selected: true
      }));
      
      // Generate a random caption based on the prompt
      let suggestedCaption = '';
      
      if (focus.includes('winter')) {
        suggestedCaption = 'Embracing the winter vibes! ❄️ #WinterWonderland #CozyDays';
      } else if (focus.includes('summer')) {
        suggestedCaption = 'Summer days are the best days! ☀️ #SummerVibes #BeachLife';
      } else if (focus.includes('food')) {
        suggestedCaption = 'Delicious adventures! 🍕 #FoodieLife #YumYum';
      } else {
        suggestedCaption = 'Capturing moments that matter. ✨ #LifeWellLived #Memories';
      }
      
      resolve({
        selectedItems,
        suggestedCaption
      });
    }, 1500); // Simulate 1.5s API delay
  });
};

// Generate a caption based on selected images and tone prompt
export const generateCaption = async (
  mediaItems: MediaItem[],
  tonePrompt: string
): Promise<string> => {
  // In a real implementation, this would call an AI service
  return new Promise((resolve) => {
    setTimeout(() => {
      let caption = '';
      
      const tone = tonePrompt.toLowerCase();
      
      if (tone.includes('professional')) {
        caption = 'Presenting our latest work. Quality and attention to detail in every aspect.';
      } else if (tone.includes('casual')) {
        caption = 'Just another day doing what we love! Check out these cool shots!';
      } else if (tone.includes('funny') || tone.includes('humorous')) {
        caption = 'When they said "act natural" but you forgot what that means... 😂 #WeekendVibes';
      } else if (tone.includes('inspirational')) {
        caption = 'Every journey begins with a single step. Embrace the path less traveled. ✨ #Inspiration';
      } else {
        caption = 'Sharing some moments from our recent adventures. Hope you enjoy! #LifeInFrames';
      }
      
      resolve(caption);
    }, 1000);
  });
}; 