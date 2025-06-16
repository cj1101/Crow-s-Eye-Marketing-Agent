import React, { useState } from 'react';
import { Card, CardContent, Alert, AlertDescription } from '@/components/ui';
import { CheckCircle, Camera, Download } from 'lucide-react';
import { GooglePhotosConnect } from './GooglePhotosConnect';
import { GooglePhotosBrowser } from './GooglePhotosBrowser';

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

interface ImportOptions {
  import_to_section: 'raw' | 'post-ready';
  apply_ai_tagging: boolean;
  create_gallery: boolean;
  gallery_name?: string;
}

interface GooglePhotosIntegrationProps {
  onMediaImported?: (importedCount: number, galleryId?: number) => void;
}

export const GooglePhotosIntegration: React.FC<GooglePhotosIntegrationProps> = ({
  onMediaImported
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [selectedItems, setSelectedItems] = useState<GooglePhotosMediaItem[]>([]);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    imported_count: number;
    failed_count: number;
    gallery_id?: number;
    message?: string;
  } | null>(null);

  const handleImport = async (items: GooglePhotosMediaItem[], options: ImportOptions) => {
    setIsImporting(true);
    setImportResult(null);

    try {
      const response = await fetch('/api/v1/google-photos/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          media_item_ids: items.map(item => item.id),
          import_to_section: options.import_to_section,
          apply_ai_tagging: options.apply_ai_tagging,
          create_gallery: options.create_gallery,
          gallery_name: options.gallery_name
        })
      });

      if (response.ok) {
        const result = await response.json();
        setImportResult({
          success: result.success,
          imported_count: result.imported_count,
          failed_count: result.failed_count,
          gallery_id: result.gallery_id,
          message: result.success 
            ? `Successfully imported ${result.imported_count} items!`
            : `Import completed with ${result.failed_count} failures.`
        });

        if (result.success) {
          onMediaImported?.(result.imported_count, result.gallery_id);
        }
      } else {
        throw new Error('Import failed');
      }
    } catch (err) {
      setImportResult({
        success: false,
        imported_count: 0,
        failed_count: items.length,
        message: err instanceof Error ? err.message : 'Import failed'
      });
    } finally {
      setIsImporting(false);
    }
  };

  if (!isConnected) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <Camera className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Import from Google Photos</h2>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            Connect your Google Photos account to import your favorite photos and videos 
            directly into Crow's Eye. All imported media will work seamlessly with your 
            existing workflows including AI tagging, gallery creation, and content enhancement.
          </p>
        </div>
        
        <GooglePhotosConnect onConnectionChange={setIsConnected} />

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-blue-600" />
              What you can do after connecting:
            </h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>• Browse your Google Photos albums and media</li>
              <li>• Search with natural language ("Show me photos from Paris 2023")</li>
              <li>• Import selected photos and videos to your raw media or post-ready sections</li>
              <li>• Automatically apply AI tagging to imported media</li>
              <li>• Create galleries from imported media collections</li>
              <li>• Use imported media in all existing Crow's Eye features</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Import Status */}
      {importResult && (
        <Alert variant={importResult.success ? "default" : "destructive"}>
          <AlertDescription>
            <div className="flex items-center gap-2">
              {importResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <Download className="h-4 w-4 text-red-500" />
              )}
              {importResult.message}
            </div>
            {importResult.success && importResult.gallery_id && (
              <p className="mt-2 text-sm">
                Created gallery with ID: {importResult.gallery_id}
              </p>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Connection Status */}
      <Card className="bg-green-50 border-green-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="font-medium">Google Photos Connected</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            You can now browse and import your Google Photos media.
          </p>
        </CardContent>
      </Card>

      {/* Browser Component */}
      <GooglePhotosBrowser
        onSelectionChange={setSelectedItems}
        onImport={handleImport}
      />

      {/* Import Status Overlay */}
      {isImporting && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-96">
            <CardContent className="p-6 text-center">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold mb-2">Importing Media...</h3>
              <p className="text-gray-600">
                Importing {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} from Google Photos.
                This may take a few moments.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}; 