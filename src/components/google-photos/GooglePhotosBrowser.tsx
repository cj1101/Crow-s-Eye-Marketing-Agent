import React, { useState, useEffect } from 'react';
import { 
  Button, Card, CardContent, CardHeader, CardTitle, Input, 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Checkbox, Badge, Alert, AlertDescription, Tabs, TabsContent, TabsList, TabsTrigger
} from '@/components/ui';
import { 
  Search, Filter, Download, Grid, List, Calendar, 
  Image, Video, ChevronLeft, ChevronRight, Loader2 
} from 'lucide-react';

interface GooglePhotosMediaItem {
  id: string;
  filename: string;
  description?: string;
  media_type: 'image' | 'video';
  mime_type: string;
  creation_time?: string;
  width?: number;
  height?: number;
  base_url: string;
  product_url?: string;
}

interface GooglePhotosAlbum {
  id: string;
  title: string;
  media_items_count: number;
  cover_photo_base_url?: string;
}

interface GooglePhotosBrowserProps {
  onSelectionChange?: (selectedItems: GooglePhotosMediaItem[]) => void;
  onImport?: (selectedItems: GooglePhotosMediaItem[], options: ImportOptions) => void;
}

interface ImportOptions {
  import_to_section: 'raw' | 'post-ready';
  apply_ai_tagging: boolean;
  create_gallery: boolean;
  gallery_name?: string;
}

export const GooglePhotosBrowser: React.FC<GooglePhotosBrowserProps> = ({
  onSelectionChange,
  onImport
}) => {
  const [mediaItems, setMediaItems] = useState<GooglePhotosMediaItem[]>([]);
  const [albums, setAlbums] = useState<GooglePhotosAlbum[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [naturalQuery, setNaturalQuery] = useState('');
  const [selectedAlbum, setSelectedAlbum] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextPageToken, setNextPageToken] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('browse');

  // Import options
  const [importOptions, setImportOptions] = useState<ImportOptions>({
    import_to_section: 'raw',
    apply_ai_tagging: true,
    create_gallery: false,
    gallery_name: ''
  });

  useEffect(() => {
    loadAlbums();
    loadMediaItems();
  }, []);

  useEffect(() => {
    onSelectionChange?.(Array.from(selectedItems).map(id => 
      mediaItems.find(item => item.id === id)!
    ).filter(Boolean));
  }, [selectedItems, mediaItems, onSelectionChange]);

  const loadAlbums = async () => {
    try {
      const response = await fetch('/api/v1/google-photos/albums', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAlbums(data.albums || []);
      }
    } catch (err) {
      console.error('Error loading albums:', err);
    }
  };

  const loadMediaItems = async (albumId?: string, pageToken?: string, append = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (albumId && albumId !== 'all') params.append('album_id', albumId);
      if (pageToken) params.append('page_token', pageToken);
      params.append('page_size', '50');

      const response = await fetch(`/api/v1/google-photos/media?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (append) {
          setMediaItems(prev => [...prev, ...data.media_items]);
        } else {
          setMediaItems(data.media_items || []);
        }
        setNextPageToken(data.next_page_token);
      } else {
        throw new Error('Failed to load media items');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load media');
    } finally {
      setIsLoading(false);
    }
  };

  const searchMedia = async (query: string, isNatural = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = isNatural ? '/api/v1/google-photos/search/natural' : '/api/v1/google-photos/search';
      const body = isNatural 
        ? { query, page_size: 50 }
        : { 
            query, 
            album_id: selectedAlbum !== 'all' ? selectedAlbum : undefined,
            page_size: 50 
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        const data = await response.json();
        setMediaItems(data.media_items || []);
        setNextPageToken(data.next_page_token);
      } else {
        throw new Error('Search failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      searchMedia(searchQuery);
    } else {
      loadMediaItems(selectedAlbum !== 'all' ? selectedAlbum : undefined);
    }
  };

  const handleNaturalSearch = () => {
    if (naturalQuery.trim()) {
      searchMedia(naturalQuery, true);
    }
  };

  const handleAlbumChange = (albumId: string) => {
    setSelectedAlbum(albumId);
    setSelectedItems(new Set());
    loadMediaItems(albumId !== 'all' ? albumId : undefined);
  };

  const handleItemSelect = (itemId: string) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(itemId)) {
      newSelection.delete(itemId);
    } else {
      newSelection.add(itemId);
    }
    setSelectedItems(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedItems.size === mediaItems.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(mediaItems.map(item => item.id)));
    }
  };

  const handleImport = () => {
    const selectedMedia = Array.from(selectedItems).map(id => 
      mediaItems.find(item => item.id === id)!
    ).filter(Boolean);

    onImport?.(selectedMedia, importOptions);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString();
  };

  const getMediaIcon = (mediaType: string) => {
    return mediaType === 'video' ? <Video className="h-4 w-4" /> : <Image className="h-4 w-4" />;
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Google Photos Browser</span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              >
                {viewMode === 'grid' ? <List className="h-4 w-4" /> : <Grid className="h-4 w-4" />}
              </Button>
              {selectedItems.size > 0 && (
                <Badge variant="secondary">
                  {selectedItems.size} selected
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="browse">Browse & Search</TabsTrigger>
              <TabsTrigger value="import">Import Settings</TabsTrigger>
            </TabsList>

            <TabsContent value="browse" className="space-y-4">
              {/* Search and Filter Controls */}
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search photos and videos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearch} disabled={isLoading}>
                    <Search className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Try: 'Show me photos from Paris 2023' or 'Find videos with animals'"
                    value={naturalQuery}
                    onChange={(e) => setNaturalQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleNaturalSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleNaturalSearch} disabled={isLoading} variant="outline">
                    🧠 AI Search
                  </Button>
                </div>

                <div className="flex gap-2 items-center">
                  <Select value={selectedAlbum} onValueChange={handleAlbumChange}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="All Photos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Photos</SelectItem>
                      {albums.map(album => (
                        <SelectItem key={album.id} value={album.id}>
                          {album.title} ({album.media_items_count})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {mediaItems.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSelectAll}
                    >
                      {selectedItems.size === mediaItems.length ? 'Deselect All' : 'Select All'}
                    </Button>
                  )}
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Media Grid/List */}
              {isLoading && mediaItems.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                  <span className="ml-2 text-gray-600">Loading media...</span>
                </div>
              ) : (
                <div className={
                  viewMode === 'grid' 
                    ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
                    : "space-y-2"
                }>
                  {mediaItems.map(item => (
                    <Card 
                      key={item.id} 
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedItems.has(item.id) ? 'ring-2 ring-blue-500' : ''
                      }`}
                      onClick={() => handleItemSelect(item.id)}
                    >
                      {viewMode === 'grid' ? (
                        <div className="relative">
                          <img
                            src={`${item.base_url}=w300-h300-c`}
                            alt={item.filename}
                            className="w-full h-48 object-cover rounded-t-lg"
                          />
                          <div className="absolute top-2 left-2">
                            <Checkbox 
                              checked={selectedItems.has(item.id)}
                              onChange={() => {}}
                              className="bg-white/80"
                            />
                          </div>
                          <div className="absolute top-2 right-2">
                            {getMediaIcon(item.media_type)}
                          </div>
                          <CardContent className="p-2">
                            <p className="text-sm font-medium truncate">{item.filename}</p>
                            <p className="text-xs text-gray-500">{formatDate(item.creation_time)}</p>
                          </CardContent>
                        </div>
                      ) : (
                        <CardContent className="p-4 flex items-center gap-4">
                          <Checkbox 
                            checked={selectedItems.has(item.id)}
                            onChange={() => {}}
                          />
                          <img
                            src={`${item.base_url}=w80-h80-c`}
                            alt={item.filename}
                            className="w-16 h-16 object-cover rounded"
                          />
                          <div className="flex-1">
                            <p className="font-medium">{item.filename}</p>
                            <p className="text-sm text-gray-500">{formatDate(item.creation_time)}</p>
                            <div className="flex items-center gap-2 mt-1">
                              {getMediaIcon(item.media_type)}
                              <span className="text-xs text-gray-400">{item.mime_type}</span>
                              {item.width && item.height && (
                                <span className="text-xs text-gray-400">
                                  {item.width}×{item.height}
                                </span>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  ))}
                </div>
              )}

              {/* Load More */}
              {nextPageToken && (
                <div className="flex justify-center">
                  <Button
                    variant="outline"
                    onClick={() => loadMediaItems(
                      selectedAlbum !== 'all' ? selectedAlbum : undefined,
                      nextPageToken,
                      true
                    )}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Loading...
                      </>
                    ) : (
                      'Load More'
                    )}
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="import" className="space-y-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Import To</label>
                  <Select 
                    value={importOptions.import_to_section} 
                    onValueChange={(value: 'raw' | 'post-ready') => 
                      setImportOptions(prev => ({ ...prev, import_to_section: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="raw">Raw Media (for editing)</SelectItem>
                      <SelectItem value="post-ready">Post-Ready (ready to publish)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="ai-tagging"
                    checked={importOptions.apply_ai_tagging}
                    onCheckedChange={(checked) =>
                      setImportOptions(prev => ({ ...prev, apply_ai_tagging: !!checked }))
                    }
                  />
                  <label htmlFor="ai-tagging" className="text-sm">
                    Apply AI tagging to imported media
                  </label>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="create-gallery"
                      checked={importOptions.create_gallery}
                      onCheckedChange={(checked) =>
                        setImportOptions(prev => ({ ...prev, create_gallery: !!checked }))
                      }
                    />
                    <label htmlFor="create-gallery" className="text-sm">
                      Create gallery from imported media
                    </label>
                  </div>
                  
                  {importOptions.create_gallery && (
                    <Input
                      placeholder="Gallery name (optional)"
                      value={importOptions.gallery_name}
                      onChange={(e) =>
                        setImportOptions(prev => ({ ...prev, gallery_name: e.target.value }))
                      }
                      className="ml-6"
                    />
                  )}
                </div>

                <div className="pt-4 border-t">
                  <Button
                    onClick={handleImport}
                    disabled={selectedItems.size === 0}
                    className="w-full"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Import {selectedItems.size} Selected Item{selectedItems.size !== 1 ? 's' : ''}
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}; 