"""
Google OAuth Helper Utility

This module provides utilities to integrate Google OAuth services with the main application.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GoogleOAuthHelper:
    """Helper class for Google OAuth integration."""
    
    def __init__(self):
        """Initialize the Google OAuth helper."""
        self.load_environment_config()
    
    def load_environment_config(self):
        """Load Google OAuth configuration from environment variables."""
        self.config = {
            'google_photos': {
                'client_id': os.getenv('GOOGLE_PHOTOS_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_PHOTOS_CLIENT_SECRET'),
                'redirect_uri': os.getenv('GOOGLE_PHOTOS_REDIRECT_URI', 'http://localhost:8080/auth/google-photos/callback')
            },
            'youtube': {
                'client_id': os.getenv('YOUTUBE_CLIENT_ID'),
                'client_secret': os.getenv('YOUTUBE_CLIENT_SECRET'),
                'redirect_uri': os.getenv('YOUTUBE_REDIRECT_URI', 'http://localhost:8080/auth/youtube/callback')
            },
            'google_business': {
                'client_id': os.getenv('GOOGLE_BUSINESS_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_BUSINESS_CLIENT_SECRET'),
                'redirect_uri': os.getenv('GOOGLE_BUSINESS_REDIRECT_URI', 'http://localhost:8080/auth/google-business/callback')
            }
        }
    
    def is_service_configured(self, service_name: str) -> bool:
        """Check if a Google service is properly configured."""
        service_config = self.config.get(service_name, {})
        return bool(service_config.get('client_id') and service_config.get('client_secret'))
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific Google service."""
        return self.config.get(service_name, {})
    
    def get_configured_services(self) -> list:
        """Get list of configured Google services."""
        configured = []
        for service_name in self.config:
            if self.is_service_configured(service_name):
                configured.append(service_name)
        return configured
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration and return status."""
        status = {
            'configured_services': [],
            'missing_services': [],
            'recommendations': []
        }
        
        for service_name, service_config in self.config.items():
            if self.is_service_configured(service_name):
                status['configured_services'].append(service_name)
            else:
                status['missing_services'].append(service_name)
                
                missing_fields = []
                if not service_config.get('client_id'):
                    missing_fields.append('client_id')
                if not service_config.get('client_secret'):
                    missing_fields.append('client_secret')
                
                if missing_fields:
                    env_var_prefix = service_name.upper().replace('_', '_')
                    status['recommendations'].append({
                        'service': service_name,
                        'message': f"Set {env_var_prefix}_CLIENT_ID and {env_var_prefix}_CLIENT_SECRET in your .env file"
                    })
        
        return status
    
    def setup_service_credentials(self, service_name: str, client_id: str, client_secret: str) -> bool:
        """Setup credentials for a Google service (in-memory only)."""
        try:
            if service_name in self.config:
                self.config[service_name]['client_id'] = client_id
                self.config[service_name]['client_secret'] = client_secret
                
                # Also set environment variables for this session
                env_prefix = service_name.upper().replace('_', '_')
                os.environ[f'{env_prefix}_CLIENT_ID'] = client_id
                os.environ[f'{env_prefix}_CLIENT_SECRET'] = client_secret
                
                logger.info(f"Configured credentials for {service_name}")
                return True
            else:
                logger.error(f"Unknown service: {service_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to setup credentials for {service_name}: {e}")
            return False

# Global instance
google_oauth_helper = GoogleOAuthHelper()

def get_google_oauth_helper() -> GoogleOAuthHelper:
    """Get the global Google OAuth helper instance."""
    return google_oauth_helper

def check_google_services_status() -> Dict[str, Any]:
    """Check the status of Google services configuration."""
    return google_oauth_helper.validate_environment()

def is_google_service_configured(service_name: str) -> bool:
    """Check if a specific Google service is configured."""
    return google_oauth_helper.is_service_configured(service_name) 