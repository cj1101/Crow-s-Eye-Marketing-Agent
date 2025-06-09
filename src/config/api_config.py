"""
API Configuration for the Desktop Application
"""
import os
from typing import Optional

class APIConfig:
    """Configuration for API endpoints used by the desktop application."""
    
    # Default to the deployed Google Cloud API
    DEFAULT_API_BASE_URL = "https://crows-eye-api-2mgwzdcmnq-uc.a.run.app"
    
    # Fallback to local for development
    LOCAL_API_BASE_URL = "http://localhost:8000"
    
    def __init__(self):
        """Initialize API configuration."""
        self.base_url = self._get_api_base_url()
        self.api_v1_url = f"{self.base_url}/api/v1"
        self.timeout = 30  # seconds
        self.max_retries = 3
    
    def _get_api_base_url(self) -> str:
        """
        Get the API base URL from environment or use defaults.
        
        Priority:
        1. CROWS_EYE_API_URL environment variable
        2. Check if local API is running (if USE_LOCAL_API=true)
        3. Use deployed Google Cloud API (default)
        """
        # Check environment variable first
        env_url = os.getenv('CROWS_EYE_API_URL')
        if env_url:
            return env_url.rstrip('/')
        
        # Check if we should use local API
        use_local = os.getenv('USE_LOCAL_API', 'false').lower() == 'true'
        if use_local:
            return self.LOCAL_API_BASE_URL
        
        # Default to deployed API
        return self.DEFAULT_API_BASE_URL
    
    def get_endpoint(self, path: str) -> str:
        """Get full URL for an API endpoint."""
        return f"{self.api_v1_url}/{path.lstrip('/')}"
    
    def is_local_api(self) -> bool:
        """Check if using local API."""
        return 'localhost' in self.base_url or '127.0.0.1' in self.base_url
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to the API."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return True, f"Connected to API at {self.base_url}"
            else:
                return False, f"API returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to API at {self.base_url}"
        except Exception as e:
            return False, f"Error testing API connection: {str(e)}"

# Global instance
api_config = APIConfig() 