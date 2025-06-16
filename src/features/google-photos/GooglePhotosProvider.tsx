import React, { createContext, useContext, useState, useEffect } from 'react';

interface GooglePhotosConnection {
  id: number;
  google_email: string;
  connection_date: string;
  last_sync_date?: string;
  is_active: boolean;
}

interface GooglePhotosContextType {
  isConnected: boolean;
  connection: GooglePhotosConnection | null;
  isLoading: boolean;
  error: string | null;
  checkConnection: () => Promise<void>;
  disconnect: () => Promise<void>;
}

const GooglePhotosContext = createContext<GooglePhotosContextType | undefined>(undefined);

export const useGooglePhotos = () => {
  const context = useContext(GooglePhotosContext);
  if (!context) {
    throw new Error('useGooglePhotos must be used within a GooglePhotosProvider');
  }
  return context;
};

interface GooglePhotosProviderProps {
  children: React.ReactNode;
}

export const GooglePhotosProvider: React.FC<GooglePhotosProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connection, setConnection] = useState<GooglePhotosConnection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkConnection = async () => {
    setIsLoading(true);
    setError(null);

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
        } else {
          setConnection(null);
          setIsConnected(false);
        }
      } else if (response.status === 404) {
        // No connection found
        setConnection(null);
        setIsConnected(false);
      } else {
        throw new Error('Failed to check connection status');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection check failed');
      setIsConnected(false);
      setConnection(null);
    } finally {
      setIsLoading(false);
    }
  };

  const disconnect = async () => {
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
      } else {
        throw new Error('Failed to disconnect');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Disconnection failed');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const value: GooglePhotosContextType = {
    isConnected,
    connection,
    isLoading,
    error,
    checkConnection,
    disconnect
  };

  return (
    <GooglePhotosContext.Provider value={value}>
      {children}
    </GooglePhotosContext.Provider>
  );
}; 