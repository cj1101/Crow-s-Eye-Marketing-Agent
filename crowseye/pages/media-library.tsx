import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

// This would come from an API in a real implementation
const mockMedia = {
  raw_photos: [
    { id: 1, name: 'Beach photo 1', url: '/placeholder-image-1.jpg', date: '2023-10-15' },
    { id: 2, name: 'Mountain view', url: '/placeholder-image-2.jpg', date: '2023-10-14' },
    { id: 3, name: 'Sunset at lake', url: '/placeholder-image-3.jpg', date: '2023-10-12' },
  ],
  raw_videos: [
    { id: 1, name: 'Beach walk', url: '/placeholder-video-1.mp4', duration: '0:45', date: '2023-10-10' },
    { id: 2, name: 'Cooking show', url: '/placeholder-video-2.mp4', duration: '2:30', date: '2023-10-08' },
  ],
  post_ready: [
    { 
      id: 1, 
      name: 'Beach day post', 
      type: 'carousel',
      media: ['/placeholder-image-1.jpg', '/placeholder-image-2.jpg'],
      caption: 'Perfect day at the beach! #summer #ocean', 
      date: '2023-10-16'
    },
  ]
};

export default function MediaLibrary() {
  const [activeTab, setActiveTab] = useState('raw_photos');
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    // In a real implementation, this would handle file uploads
    console.log('Files selected:', e.target.files);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Media Library | Crow's Eye</title>
        <meta name="description" content="Organize and manage your media content" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Media Library</h1>
          <Link href="/" className="text-purple-600 hover:text-purple-800">
            Back to Home
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row justify-between mb-6">
            <div className="mb-4 md:mb-0">
              <label htmlFor="file-upload" className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition cursor-pointer">
                Upload New Media
                <input 
                  id="file-upload" 
                  type="file" 
                  multiple 
                  className="hidden" 
                  onChange={handleFileUpload}
                  accept="image/*,video/*"
                />
              </label>
            </div>
            <div className="relative">
              <input
                type="text"
                placeholder="Search media..."
                className="pl-10 pr-4 py-2 border rounded-md w-full md:w-64"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <span className="absolute left-3 top-2.5 text-gray-400">
                {/* Search icon would go here */}
                🔍
              </span>
            </div>
          </div>

          <div className="border-b border-gray-200 mb-6">
            <nav className="flex -mb-px">
              <button
                className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'raw_photos' 
                    ? 'border-purple-500 text-purple-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('raw_photos')}
              >
                Raw Photos
              </button>
              <button
                className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'raw_videos' 
                    ? 'border-purple-500 text-purple-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('raw_videos')}
              >
                Raw Videos
              </button>
              <button
                className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'post_ready' 
                    ? 'border-purple-500 text-purple-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('post_ready')}
              >
                Post-Ready Content
              </button>
            </nav>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {activeTab === 'raw_photos' && mockMedia.raw_photos.map(photo => (
              <div key={photo.id} className="border rounded-lg overflow-hidden bg-gray-50 hover:shadow-md transition">
                <div className="h-48 bg-gray-200 flex items-center justify-center">
                  {/* In a real app, this would be an actual image */}
                  <div className="text-gray-500">Photo Preview</div>
                </div>
                <div className="p-4">
                  <h3 className="font-medium text-gray-900">{photo.name}</h3>
                  <p className="text-sm text-gray-500">Added: {photo.date}</p>
                </div>
              </div>
            ))}

            {activeTab === 'raw_videos' && mockMedia.raw_videos.map(video => (
              <div key={video.id} className="border rounded-lg overflow-hidden bg-gray-50 hover:shadow-md transition">
                <div className="h-48 bg-gray-200 flex items-center justify-center">
                  {/* In a real app, this would be a video thumbnail */}
                  <div className="text-gray-500">Video Preview</div>
                </div>
                <div className="p-4">
                  <h3 className="font-medium text-gray-900">{video.name}</h3>
                  <p className="text-sm text-gray-500">
                    Duration: {video.duration} • Added: {video.date}
                  </p>
                </div>
              </div>
            ))}

            {activeTab === 'post_ready' && mockMedia.post_ready.map(post => (
              <div key={post.id} className="border rounded-lg overflow-hidden bg-gray-50 hover:shadow-md transition">
                <div className="h-48 bg-gray-200 flex items-center justify-center">
                  {/* In a real app, this would show the post content */}
                  <div className="text-gray-500">{post.type.charAt(0).toUpperCase() + post.type.slice(1)} Preview</div>
                </div>
                <div className="p-4">
                  <h3 className="font-medium text-gray-900">{post.name}</h3>
                  <p className="text-sm text-gray-500 line-clamp-2">{post.caption}</p>
                  <p className="text-sm text-gray-500 mt-1">Added: {post.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
} 