import React from 'react';
import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { MediaItem } from '../features/galleryGenerator';

// Mock data for selected images, explicitly typed
const mockSelectedImages: MediaItem[] = [
  { id: 1, url: '/placeholder-image-1.jpg', type: 'photo', selected: true },
  { id: 2, url: '/placeholder-image-2.jpg', type: 'photo', selected: true },
  { id: 3, url: '/placeholder-image-3.jpg', type: 'photo', selected: false },
  { id: 4, url: '/placeholder-image-4.jpg', type: 'photo', selected: false },
  { id: 5, url: '/placeholder-image-5.jpg', type: 'photo', selected: false },
];

export default function GalleryGenerator(): JSX.Element {
  const [prompt, setPrompt] = useState<string>('');
  const [enhancePhotos, setEnhancePhotos] = useState<boolean>(true);
  const [selectedImages, setSelectedImages] = useState<MediaItem[]>(mockSelectedImages);
  const [generatedCaption, setGeneratedCaption] = useState<string>('');
  const [captionPrompt, setCaptionPrompt] = useState<string>('');
  const [generatingGallery, setGeneratingGallery] = useState<boolean>(false);
  
  const handleGenerate = (): void => {
    // In a real implementation, this would call an API
    setGeneratingGallery(true);
    
    // Simulate API call
    setTimeout(() => {
      // Update selected images based on prompt
      const newSelectedImages = selectedImages.map((img: MediaItem) => ({
        ...img,
        selected: [1, 2, 5].includes(img.id) // Simulate AI selection based on prompt
      }));
      
      setSelectedImages(newSelectedImages);
      setGeneratedCaption('Beautiful day out exploring nature! The perfect balance of adventure and relaxation. #NatureLovers #Wanderlust');
      setGeneratingGallery(false);
    }, 2000);
  };
  
  const toggleImageSelection = (id: number): void => {
    setSelectedImages(
      selectedImages.map((img: MediaItem) => 
        img.id === id ? { ...img, selected: !img.selected } : img
      )
    );
  };
  
  const handleCaptionGenerate = (): void => {
    // In a real implementation, this would call an AI service
    setGeneratedCaption('Beautiful day out exploring nature! The perfect balance of adventure and relaxation. #NatureLovers #Wanderlust');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Gallery Generator | Crow&apos;s Eye</title>
        <meta name="description" content="Generate perfect galleries with AI assistance" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Gallery Generator</h1>
          <Link href="/" className="text-purple-600 hover:text-purple-800">
            Back to Home
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">AI Gallery Generation</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gallery Focus
                </label>
                <textarea
                  className="w-full border rounded-md p-2 h-24"
                  placeholder="e.g., Pick the best 5 for a winter campaign"
                  value={prompt}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                ></textarea>
              </div>
              
              <div className="flex items-center mb-6">
                <input
                  type="checkbox"
                  id="enhance"
                  className="mr-2"
                  checked={enhancePhotos}
                  onChange={() => setEnhancePhotos(!enhancePhotos)}
                />
                <label htmlFor="enhance" className="text-sm text-gray-700">
                  Auto-enhance photos
                </label>
              </div>
              
              <button
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded hover:bg-indigo-700 transition"
                onClick={handleGenerate}
                disabled={generatingGallery}
              >
                {generatingGallery ? 'Generating...' : 'Generate Gallery'}
              </button>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Caption Generator</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tone Prompt
                </label>
                <input
                  type="text"
                  className="w-full border rounded-md p-2"
                  placeholder="e.g., Energetic and conversational"
                  value={captionPrompt}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCaptionPrompt(e.target.value)}
                />
              </div>
              
              <button
                className="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 transition mb-4"
                onClick={handleCaptionGenerate}
              >
                Generate Caption
              </button>
              
              {generatedCaption && (
                <div className="border rounded-md p-3 bg-gray-50">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Generated Caption
                  </label>
                  <p className="text-gray-800">{generatedCaption}</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Selected Media</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {selectedImages.map((image: MediaItem) => (
                  <div 
                    key={image.id} 
                    className={`border rounded-lg overflow-hidden ${
                      image.selected ? 'border-indigo-500 ring-2 ring-indigo-300' : 'border-gray-200'
                    }`}
                    onClick={() => toggleImageSelection(image.id)}
                  >
                    <div className="h-40 bg-gray-200 flex items-center justify-center">
                      {/* In a real app, this would be an actual image */}
                      <div className="text-gray-500">Image {image.id}</div>
                    </div>
                    <div className="p-2 bg-white flex justify-between items-center">
                      <div className="text-sm text-gray-500">
                        {image.selected ? 'Selected' : 'Not selected'}
                      </div>
                      <div className={`h-4 w-4 rounded-full ${
                        image.selected ? 'bg-indigo-500' : 'bg-gray-200'
                      }`}></div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-8 flex justify-end">
                <button className="bg-green-600 text-white py-2 px-6 rounded hover:bg-green-700 transition">
                  Save Gallery
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 