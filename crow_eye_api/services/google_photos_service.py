"""
Google Photos Service for Crow's Eye API.
Handles OAuth2 authentication, browsing, and importing media from Google Photos.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from crow_eye_api.core.config import settings
from crow_eye_api.services.storage import storage_service


class GooglePhotosService:
    """Service for Google Photos integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # OAuth2 configuration
        self.client_id = settings.GOOGLE_PHOTOS_CLIENT_ID
        self.client_secret = settings.GOOGLE_PHOTOS_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_PHOTOS_REDIRECT_URI
        
        # Check if credentials are configured
        if not self.client_id or not self.client_secret:
            self.logger.warning("Google Photos OAuth2 credentials not configured")
            self.configured = False
        else:
            self.configured = True
        
        # Google Photos API scopes
        self.scopes = [
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'https://www.googleapis.com/auth/photoslibrary.sharing'
        ]
        
        # API endpoints
        self.auth_url = 'https://accounts.google.com/o/oauth2/auth'
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.photos_api_url = 'https://photoslibrary.googleapis.com/v1'
        
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate authorization URL for Google Photos OAuth2.
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            Authorization URL
        """
        if not self.configured:
            raise Exception("Google Photos OAuth2 credentials not configured. Please set GOOGLE_PHOTOS_CLIENT_ID and GOOGLE_PHOTOS_CLIENT_SECRET.")
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state
            )
            
            return auth_url
            
        except Exception as e:
            self.logger.error(f"Error generating authorization URL: {e}")
            raise
    
    async def exchange_code_for_tokens(self, code: str, state: str = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            state: Optional state parameter for verification
            
        Returns:
            Dictionary containing tokens and user info
        """
        if not self.configured:
            raise Exception("Google Photos OAuth2 credentials not configured. Please set GOOGLE_PHOTOS_CLIENT_ID and GOOGLE_PHOTOS_CLIENT_SECRET.")
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Get user info
            user_info = await self._get_user_info(credentials.token)
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
                'user_info': user_info
            }
            
        except Exception as e:
            self.logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token information
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=self.token_url,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the token
            request = Request()
            credentials.refresh(request)
            
            return {
                'access_token': credentials.token,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {e}")
            raise
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {access_token}'}
                async with session.get(
                    'https://www.googleapis.com/oauth2/v1/userinfo',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get user info: {response.status}")
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            raise
    
    async def get_albums(self, access_token: str, page_token: str = None) -> Dict[str, Any]:
        """
        Get user's Google Photos albums.
        
        Args:
            access_token: Google Photos access token
            page_token: Optional pagination token
            
        Returns:
            Albums data with pagination info
        """
        try:
            url = f"{self.photos_api_url}/albums"
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {'pageSize': 50}
            
            if page_token:
                params['pageToken'] = page_token
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'albums': data.get('albums', []),
                            'next_page_token': data.get('nextPageToken'),
                            'total_albums': len(data.get('albums', []))
                        }
                    else:
                        raise Exception(f"Failed to get albums: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error getting albums: {e}")
            raise
    
    async def get_media_items(
        self,
        access_token: str,
        album_id: str = None,
        page_token: str = None,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get media items from Google Photos.
        
        Args:
            access_token: Google Photos access token
            album_id: Optional album ID to filter by
            page_token: Optional pagination token
            page_size: Number of items per page
            
        Returns:
            Media items data with pagination info
        """
        try:
            url = f"{self.photos_api_url}/mediaItems"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            if album_id:
                # Search for media items in specific album
                url = f"{self.photos_api_url}/mediaItems:search"
                payload = {
                    'albumId': album_id,
                    'pageSize': page_size
                }
                if page_token:
                    payload['pageToken'] = page_token
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                        else:
                            raise Exception(f"Failed to get media items: {response.status}")
            else:
                # Get all media items
                params = {'pageSize': page_size}
                if page_token:
                    params['pageToken'] = page_token
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                        else:
                            raise Exception(f"Failed to get media items: {response.status}")
            
            # Process media items
            media_items = []
            for item in data.get('mediaItems', []):
                media_items.append({
                    'id': item.get('id'),
                    'filename': item.get('filename'),
                    'description': item.get('description', ''),
                    'media_type': 'image' if item.get('mimeType', '').startswith('image/') else 'video',
                    'mime_type': item.get('mimeType'),
                    'creation_time': item.get('mediaMetadata', {}).get('creationTime'),
                    'width': item.get('mediaMetadata', {}).get('width'),
                    'height': item.get('mediaMetadata', {}).get('height'),
                    'base_url': item.get('baseUrl'),
                    'product_url': item.get('productUrl'),
                    'metadata': item.get('mediaMetadata', {})
                })
            
            return {
                'media_items': media_items,
                'next_page_token': data.get('nextPageToken'),
                'total_items': len(media_items)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting media items: {e}")
            raise
    
    async def search_media_items(
        self,
        access_token: str,
        query: str = None,
        date_filter: Dict[str, Any] = None,
        content_filter: Dict[str, Any] = None,
        page_token: str = None
    ) -> Dict[str, Any]:
        """
        Search media items with natural language queries and filters.
        
        Args:
            access_token: Google Photos access token
            query: Natural language search query
            date_filter: Date range filter
            content_filter: Content category filter
            page_token: Optional pagination token
            
        Returns:
            Filtered media items
        """
        try:
            url = f"{self.photos_api_url}/mediaItems:search"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {'pageSize': 50}
            
            if page_token:
                payload['pageToken'] = page_token
            
            # Add filters
            filters = {}
            
            if date_filter:
                filters['dateFilter'] = date_filter
            
            if content_filter:
                filters['contentFilter'] = content_filter
            
            if filters:
                payload['filters'] = filters
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process and filter results based on natural language query
                        media_items = []
                        for item in data.get('mediaItems', []):
                            # Basic natural language matching
                            if query and query.lower() not in (item.get('filename', '').lower() + ' ' + 
                                                             item.get('description', '').lower()):
                                continue
                            
                            media_items.append({
                                'id': item.get('id'),
                                'filename': item.get('filename'),
                                'description': item.get('description', ''),
                                'media_type': 'image' if item.get('mimeType', '').startswith('image/') else 'video',
                                'mime_type': item.get('mimeType'),
                                'creation_time': item.get('mediaMetadata', {}).get('creationTime'),
                                'width': item.get('mediaMetadata', {}).get('width'),
                                'height': item.get('mediaMetadata', {}).get('height'),
                                'base_url': item.get('baseUrl'),
                                'product_url': item.get('productUrl'),
                                'metadata': item.get('mediaMetadata', {})
                            })
                        
                        return {
                            'media_items': media_items,
                            'next_page_token': data.get('nextPageToken'),
                            'total_items': len(media_items),
                            'query': query
                        }
                    else:
                        raise Exception(f"Failed to search media items: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error searching media items: {e}")
            raise
    
    async def download_media_item(
        self,
        access_token: str,
        media_item: Dict[str, Any],
        user_id: int
    ) -> str:
        """
        Download media item from Google Photos and store it.
        
        Args:
            access_token: Google Photos access token
            media_item: Media item metadata
            user_id: User ID for storage path
            
        Returns:
            GCS path of downloaded media
        """
        try:
            base_url = media_item.get('base_url')
            if not base_url:
                raise Exception("No base URL found for media item")
            
            # Determine download URL with appropriate parameters
            if media_item.get('media_type') == 'image':
                download_url = f"{base_url}=d"  # Download original image
            else:
                download_url = f"{base_url}=dv"  # Download video
            
            # Download the media
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Generate filename
                        original_filename = media_item.get('filename', f"google_photos_{media_item.get('id')}")
                        if not original_filename.split('.')[-1]:
                            # Add extension based on mime type
                            mime_type = media_item.get('mime_type', '')
                            if mime_type.startswith('image/'):
                                original_filename += '.jpg'
                            elif mime_type.startswith('video/'):
                                original_filename += '.mp4'
                        
                        # Store the media
                        gcs_path = await storage_service.store_media(
                            content=content,
                            filename=original_filename,
                            user_id=user_id,
                            content_type=media_item.get('mime_type', 'application/octet-stream')
                        )
                        
                        return gcs_path
                    else:
                        raise Exception(f"Failed to download media: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error downloading media item: {e}")
            raise
    
    def parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query into Google Photos API filters.
        
        Args:
            query: Natural language query (e.g., "photos from Paris 2023")
            
        Returns:
            Dictionary with parsed filters
        """
        filters = {}
        
        # Simple parsing logic - can be enhanced with NLP
        query_lower = query.lower()
        
        # Date parsing
        if '2023' in query:
            filters['date_filter'] = {
                'ranges': [{
                    'startDate': {'year': 2023, 'month': 1, 'day': 1},
                    'endDate': {'year': 2023, 'month': 12, 'day': 31}
                }]
            }
        elif '2024' in query:
            filters['date_filter'] = {
                'ranges': [{
                    'startDate': {'year': 2024, 'month': 1, 'day': 1},
                    'endDate': {'year': 2024, 'month': 12, 'day': 31}
                }]
            }
        
        # Content category parsing
        if any(word in query_lower for word in ['photo', 'image', 'picture']):
            filters['content_filter'] = {
                'includedContentCategories': ['PHOTOS']
            }
        elif any(word in query_lower for word in ['video', 'movie', 'clip']):
            filters['content_filter'] = {
                'includedContentCategories': ['VIDEOS']
            }
        elif any(word in query_lower for word in ['people', 'person', 'portrait']):
            filters['content_filter'] = {
                'includedContentCategories': ['PEOPLE']
            }
        elif any(word in query_lower for word in ['selfie', 'selfies']):
            filters['content_filter'] = {
                'includedContentCategories': ['SELFIES']
            }
        elif any(word in query_lower for word in ['animal', 'animals', 'pet', 'pets']):
            filters['content_filter'] = {
                'includedContentCategories': ['ANIMALS']
            }
        elif any(word in query_lower for word in ['landscape', 'nature', 'outdoor']):
            filters['content_filter'] = {
                'includedContentCategories': ['LANDSCAPES']
            }
        
        return filters


# Create service instance
google_photos_service = GooglePhotosService() 