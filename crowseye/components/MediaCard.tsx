import { useState } from 'react';

interface MediaCardProps {
  id: number;
  name: string;
  url: string;
  type: 'photo' | 'video' | 'post';
  date: string;
  duration?: string;
  caption?: string;
  onSelect?: (id: number) => void;
  isSelected?: boolean;
}

const MediaCard: React.FC<MediaCardProps> = ({
  id,
  name,
  url,
  type,
  date,
  duration,
  caption,
  onSelect,
  isSelected = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const handleClick = () => {
    if (onSelect) {
      onSelect(id);
    }
  };
  
  return (
    <div 
      className={`border rounded-lg overflow-hidden bg-gray-50 transition ${
        isSelected ? 'ring-2 ring-purple-500 border-purple-400' : 'hover:shadow-md'
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <div className="h-48 bg-gray-200 relative">
        {/* This would be a real image/video in production */}
        <div className="absolute inset-0 flex items-center justify-center text-gray-500">
          {type === 'photo' && 'Photo Preview'}
          {type === 'video' && 'Video Preview'}
          {type === 'post' && 'Post Preview'}
        </div>
        
        {isHovered && (
          <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
            <button 
              className="bg-white text-purple-800 px-4 py-2 rounded-md text-sm font-medium"
              onClick={(e) => {
                e.stopPropagation();
                // View details logic would go here
              }}
            >
              View Details
            </button>
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="font-medium text-gray-900 mb-1">{name}</h3>
        
        {caption && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-1">{caption}</p>
        )}
        
        <div className="flex justify-between text-sm text-gray-500">
          <span>Added: {date}</span>
          {duration && <span>Duration: {duration}</span>}
        </div>
      </div>
    </div>
  );
};

export default MediaCard; 