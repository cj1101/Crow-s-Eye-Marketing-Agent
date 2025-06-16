import React, { useState, useEffect } from 'react';
import { Button, Card, CardContent, CardHeader, CardTitle, Alert, AlertDescription } from '@/components/ui';
import { ExternalLink, Camera, CheckCircle, AlertCircle } from 'lucide-react';

interface GooglePhotosConnection {
  id: number;
  google_email: string;
  connection_date: string;
  last_sync_date?: string;
  is_active: boolean;
}

interface GooglePhotosConnectProps {
  onConnectionChange?: (connected: boolean) => void;
}

export const GooglePhotosConnect: React.FC<GooglePhotosConnectProps> = ({ 
  onConnectionChange 
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connection, setConnection] = useState<GooglePhotosConnection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch('/api/v1/google-photos/connection', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const connectionData = await response.json();
        if (connectionData) {
          setConnection(connectionData);
          setIsConnected(true);
          onConnectionChange?.(true);
        }
      }
    } catch (err) {
      console.error('Error checking connection status:', err);
    }
  };

  const handleConnect = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get authorization URL
      const response = await fetch('/api/v1/google-photos/auth/url', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get authorization URL');
      }

      const { auth_url } = await response.json();
      
      // Open popup window for OAuth
      const popup = window.open(
        auth_url,
        'google-photos-auth',
        'width=600,height=600,scrollbars=yes,resizable=yes'
      );

      // Listen for popup to close
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          setIsLoading(false);
          // Check if connection was successful
          setTimeout(() => {
            checkConnectionStatus();
          }, 1000);
        }
      }, 1000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/google-photos/connection', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        setConnection(null);
        setIsConnected(false);
        onConnectionChange?.(false);
      } else {
        throw new Error('Failed to disconnect');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Disconnection failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="h-5 w-5" />
          Google Photos Integration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isConnected && connection ? (
          <div className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4 text-green-500" />
              <AlertDescription>
                <div className="space-y-1">
                  <p className="font-medium">Connected to Google Photos</p>
                  <p className="text-sm text-gray-600">
                    Account: {connection.google_email}
                  </p>
                  <p className="text-sm text-gray-600">
                    Connected: {new Date(connection.connection_date).toLocaleDateString()}
                  </p>
                  {connection.last_sync_date && (
                    <p className="text-sm text-gray-600">
                      Last sync: {new Date(connection.last_sync_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleDisconnect}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                {isLoading ? 'Disconnecting...' : 'Disconnect'}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-center py-6">
              <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Connect Your Google Photos</h3>
              <p className="text-gray-600 mb-6">
                Import your favorite photos and videos directly from Google Photos to use in your Crow's Eye projects.
              </p>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-6">
                <h4 className="font-medium mb-2">🔒 Privacy & Security</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Read-only access to your photos</li>
                  <li>• No photos are stored permanently</li>
                  <li>• You can disconnect anytime</li>
                  <li>• Only you can see your imported media</li>
                </ul>
              </div>

              <Button
                onClick={handleConnect}
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 flex items-center gap-2 mx-auto"
              >
                {isLoading ? (
                  'Connecting...'
                ) : (
                  <>
                    Connect Google Photos
                    <ExternalLink className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        <div className="text-xs text-gray-500 text-center">
          By connecting, you agree to Google's Terms of Service and Privacy Policy
        </div>
      </CardContent>
    </Card>
  );
}; 