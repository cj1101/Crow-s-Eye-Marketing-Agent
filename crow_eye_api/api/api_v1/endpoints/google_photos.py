"""
Google Photos API endpoints for Crow's Eye.
Handles OAuth2 authentication, browsing, and importing media from Google Photos.
"""

import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.api.api_v1.dependencies import get_current_active_user, get_db
from crow_eye_api.models.user import User
from crow_eye_api.schemas import google_photos as schemas
from crow_eye_api.services.google_photos_service import google_photos_service
from crow_eye_api.services.ai import ai_service
from crow_eye_api.crud.google_photos import google_photos_crud

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def google_photos_health_check():
    """Google Photos service health check."""
    try:
        from crow_eye_api.core.config import settings
        
        # Check if Google Photos is configured
        if not settings.GOOGLE_PHOTOS_CLIENT_ID or not settings.GOOGLE_PHOTOS_CLIENT_SECRET:
            return {
                "status": "error",
                "service": "google_photos",
                "error": "Google Photos OAuth2 credentials not configured",
                "configured": False
            }
        
        return {
            "status": "ok",
            "service": "google_photos",
            "configured": True,
            "endpoints": ["auth", "albums", "media", "search", "import"]
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "google_photos",
            "error": str(e),
            "configured": False
        }


@router.get("/auth/url", response_model=schemas.GooglePhotosAuthURL)
async def get_google_photos_auth_url(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get Google Photos OAuth2 authorization URL.
    """
    try:
        # Generate a state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        auth_url = google_photos_service.get_authorization_url(state=state)
        
        return schemas.GooglePhotosAuthURL(
            auth_url=auth_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.post("/auth/callback", response_model=schemas.GooglePhotosConnection)
async def google_photos_auth_callback(
    token_data: schemas.GooglePhotosTokenExchange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Handle Google Photos OAuth2 callback and store tokens.
    """
    try:
        # Exchange code for tokens
        token_info = await google_photos_service.exchange_code_for_tokens(
            code=token_data.code,
            state=token_data.state
        )
        
        # Extract token info
        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']
        expires_at = token_info.get('expires_at')
        user_info = token_info['user_info']
        
        # Parse expiry date
        from datetime import datetime
        token_expires_at = None
        if expires_at:
            token_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        # Store connection in database
        connection = await google_photos_crud.create_connection(
            db=db,
            user_id=current_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            google_user_id=user_info.get('id', ''),
            google_email=user_info.get('email', '')
        )
        
        return schemas.GooglePhotosConnection.model_validate(connection)
        
    except Exception as e:
        logger.error(f"Error in auth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/connection", response_model=Optional[schemas.GooglePhotosConnection])
async def get_google_photos_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's Google Photos connection status.
    """
    try:
        connection = await google_photos_crud.get_connection_by_user_id(
            db=db,
            user_id=current_user.id
        )
        
        if not connection:
            return None
            
        return schemas.GooglePhotosConnection.model_validate(connection)
        
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection status"
        )


@router.delete("/connection")
async def disconnect_google_photos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Disconnect Google Photos account.
    """
    try:
        connection = await google_photos_crud.get_connection_by_user_id(
            db=db,
            user_id=current_user.id
        )
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Google Photos connection found"
            )
        
        await google_photos_crud.delete_connection(db=db, connection_id=connection.id)
        
        return {"success": True, "message": "Google Photos disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Google Photos"
        )


async def _get_valid_access_token(db: AsyncSession, user_id: int) -> str:
    """Helper function to get valid access token, refreshing if needed."""
    connection = await google_photos_crud.get_connection_by_user_id(db, user_id)
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Photos not connected. Please connect your account first."
        )
    
    # Check if token needs refresh
    from datetime import datetime, timezone
    if connection.token_expires_at and connection.token_expires_at <= datetime.now(timezone.utc):
        try:
            token_info = await google_photos_service.refresh_access_token(
                connection.refresh_token
            )
            
            # Update connection with new token
            expires_at = None
            if token_info.get('expires_at'):
                expires_at = datetime.fromisoformat(token_info['expires_at'].replace('Z', '+00:00'))
            
            await google_photos_crud.update_connection(
                db=db,
                connection_id=connection.id,
                access_token=token_info['access_token'],
                refresh_token=connection.refresh_token,
                token_expires_at=expires_at,
                google_user_id=connection.google_user_id,
                google_email=connection.google_email
            )
            
            return token_info['access_token']
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh access token. Please reconnect your Google Photos account."
            )
    
    return connection.access_token


@router.get("/albums", response_model=schemas.GooglePhotosAlbumsResponse)
async def get_google_photos_albums(
    page_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's Google Photos albums.
    """
    try:
        access_token = await _get_valid_access_token(db, current_user.id)
        
        albums_data = await google_photos_service.get_albums(
            access_token=access_token,
            page_token=page_token
        )
        
        # Convert to schema format
        albums = []
        for album in albums_data.get('albums', []):
            albums.append(schemas.GooglePhotosAlbum(
                id=album.get('id'),
                title=album.get('title', 'Untitled Album'),
                product_url=album.get('productUrl'),
                is_writable=album.get('isWriteable', False),
                media_items_count=album.get('mediaItemsCount', 0),
                cover_photo_base_url=album.get('coverPhotoBaseUrl'),
                cover_photo_media_item_id=album.get('coverPhotoMediaItemId')
            ))
        
        return schemas.GooglePhotosAlbumsResponse(
            albums=albums,
            next_page_token=albums_data.get('next_page_token'),
            total_albums=albums_data.get('total_albums', len(albums))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting albums: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Google Photos albums"
        )


@router.get("/media", response_model=schemas.GooglePhotosMediaItemsResponse)
async def get_google_photos_media(
    album_id: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get media items from Google Photos.
    """
    try:
        access_token = await _get_valid_access_token(db, current_user.id)
        
        media_data = await google_photos_service.get_media_items(
            access_token=access_token,
            album_id=album_id,
            page_token=page_token,
            page_size=min(page_size, 100)  # Limit to prevent abuse
        )
        
        # Convert to schema format
        media_items = []
        for item in media_data.get('media_items', []):
            media_items.append(schemas.GooglePhotosMediaItem(
                id=item['id'],
                filename=item['filename'],
                description=item.get('description', ''),
                media_type=item['media_type'],
                mime_type=item['mime_type'],
                creation_time=item.get('creation_time'),
                width=item.get('width'),
                height=item.get('height'),
                base_url=item['base_url'],
                product_url=item.get('product_url'),
                metadata=schemas.GooglePhotosMediaMetadata(
                    creation_time=item.get('creation_time'),
                    width=item.get('width'),
                    height=item.get('height'),
                    photo=item.get('metadata', {}).get('photo'),
                    video=item.get('metadata', {}).get('video')
                ) if item.get('metadata') else None
            ))
        
        return schemas.GooglePhotosMediaItemsResponse(
            media_items=media_items,
            next_page_token=media_data.get('next_page_token'),
            total_items=media_data.get('total_items', len(media_items))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Google Photos media"
        )


@router.post("/search", response_model=schemas.GooglePhotosSearchResponse)
async def search_google_photos_media(
    search_request: schemas.GooglePhotosSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search media items in Google Photos with advanced filters.
    """
    try:
        access_token = await _get_valid_access_token(db, current_user.id)
        
        # Parse filters from request
        date_filter = None
        if search_request.start_date or search_request.end_date:
            date_filter = {}
            if search_request.start_date:
                from datetime import datetime
                start_date = datetime.fromisoformat(search_request.start_date)
                date_filter['ranges'] = [{
                    'startDate': {
                        'year': start_date.year,
                        'month': start_date.month,
                        'day': start_date.day
                    }
                }]
                if search_request.end_date:
                    end_date = datetime.fromisoformat(search_request.end_date)
                    date_filter['ranges'][0]['endDate'] = {
                        'year': end_date.year,
                        'month': end_date.month,
                        'day': end_date.day
                    }
        
        content_filter = None
        if search_request.content_categories:
            content_filter = {
                'includedContentCategories': search_request.content_categories
            }
        
        # Search media items
        search_results = await google_photos_service.search_media_items(
            access_token=access_token,
            query=search_request.query,
            date_filter=date_filter,
            content_filter=content_filter,
            page_token=search_request.page_token
        )
        
        # Convert to schema format
        media_items = []
        for item in search_results.get('media_items', []):
            media_items.append(schemas.GooglePhotosMediaItem(
                id=item['id'],
                filename=item['filename'],
                description=item.get('description', ''),
                media_type=item['media_type'],
                mime_type=item['mime_type'],
                creation_time=item.get('creation_time'),
                width=item.get('width'),
                height=item.get('height'),
                base_url=item['base_url'],
                product_url=item.get('product_url'),
                metadata=schemas.GooglePhotosMediaMetadata(
                    creation_time=item.get('creation_time'),
                    width=item.get('width'),
                    height=item.get('height'),
                    photo=item.get('metadata', {}).get('photo'),
                    video=item.get('metadata', {}).get('video')
                ) if item.get('metadata') else None
            ))
        
        return schemas.GooglePhotosSearchResponse(
            media_items=media_items,
            next_page_token=search_results.get('next_page_token'),
            total_items=search_results.get('total_items', len(media_items)),
            query=search_request.query,
            filters_applied={
                'date_filter': date_filter,
                'content_filter': content_filter
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search Google Photos media"
        )


@router.post("/search/natural", response_model=schemas.GooglePhotosSearchResponse)
async def natural_language_search(
    query_data: schemas.NaturalLanguageQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search Google Photos using natural language queries.
    Examples: "Show me photos from Paris 2023", "Find videos with animals"
    """
    try:
        access_token = await _get_valid_access_token(db, current_user.id)
        
        # Parse natural language query into filters
        filters = google_photos_service.parse_natural_language_query(query_data.query)
        
        # Search with parsed filters
        search_results = await google_photos_service.search_media_items(
            access_token=access_token,
            query=query_data.query,
            date_filter=filters.get('date_filter'),
            content_filter=filters.get('content_filter'),
            page_token=query_data.page_token
        )
        
        # Convert to schema format
        media_items = []
        for item in search_results.get('media_items', []):
            media_items.append(schemas.GooglePhotosMediaItem(
                id=item['id'],
                filename=item['filename'],
                description=item.get('description', ''),
                media_type=item['media_type'],
                mime_type=item['mime_type'],
                creation_time=item.get('creation_time'),
                width=item.get('width'),
                height=item.get('height'),
                base_url=item['base_url'],
                product_url=item.get('product_url'),
                metadata=schemas.GooglePhotosMediaMetadata(
                    creation_time=item.get('creation_time'),
                    width=item.get('width'),
                    height=item.get('height'),
                    photo=item.get('metadata', {}).get('photo'),
                    video=item.get('metadata', {}).get('video')
                ) if item.get('metadata') else None
            ))
        
        return schemas.GooglePhotosSearchResponse(
            media_items=media_items,
            next_page_token=search_results.get('next_page_token'),
            total_items=search_results.get('total_items', len(media_items)),
            query=query_data.query,
            filters_applied=filters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in natural language search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search Google Photos with natural language"
        )


async def _import_media_item_task(
    access_token: str,
    media_item_data: dict,
    user_id: int,
    apply_ai_tagging: bool,
    db: AsyncSession
) -> dict:
    """Background task to import a single media item."""
    try:
        # Download and store media
        gcs_path = await google_photos_service.download_media_item(
            access_token=access_token,
            media_item=media_item_data,
            user_id=user_id
        )
        
        # Create media item in database
        media_item = await google_photos_crud.create_imported_media(
            db=db,
            user_id=user_id,
            filename=media_item_data.get('filename', f"google_photos_{media_item_data['id']}"),
            original_filename=media_item_data.get('filename', ''),
            gcs_path=gcs_path,
            thumbnail_path=None,  # Could generate thumbnails here
            media_type=media_item_data['media_type'],
            file_size=0,  # Would need to get from downloaded content
            width=media_item_data.get('width'),
            height=media_item_data.get('height'),
            duration=None,  # Would need to extract for videos
            google_photos_id=media_item_data['id'],
            google_photos_metadata=media_item_data.get('metadata', {}),
            is_post_ready=False
        )
        
        # Apply AI tagging if requested
        if apply_ai_tagging:
            try:
                # Generate AI tags for the imported media
                # This would integrate with your existing AI tagging service
                # ai_tags = await ai_service.generate_tags_for_media(media_item.id)
                # Update media item with AI tags
                pass
            except Exception as e:
                logger.warning(f"Failed to apply AI tagging to imported media {media_item.id}: {e}")
        
        return {
            'success': True,
            'crow_eye_media_id': media_item.id,
            'google_photos_id': media_item_data['id']
        }
        
    except Exception as e:
        logger.error(f"Failed to import media item {media_item_data.get('id', 'unknown')}: {e}")
        return {
            'success': False,
            'google_photos_id': media_item_data.get('id', 'unknown'),
            'error': str(e)
        }


@router.post("/import", response_model=schemas.GooglePhotosImportResponse)
async def import_google_photos_media(
    import_request: schemas.GooglePhotosImportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import selected media items from Google Photos to Crow's Eye.
    """
    try:
        access_token = await _get_valid_access_token(db, current_user.id)
        
        # Get detailed info for each media item to import
        media_items_data = []
        for media_id in import_request.media_item_ids:
            # Check if already imported
            existing = await google_photos_crud.get_imported_media_by_google_id(
                db=db,
                google_photos_id=media_id,
                user_id=current_user.id
            )
            if existing:
                continue  # Skip already imported items
                
            # Get media item details
            try:
                media_data = await google_photos_service.get_media_items(
                    access_token=access_token,
                    album_id=None,
                    page_token=None,
                    page_size=1
                )
                # In a real implementation, you'd need to get individual media item details
                # For now, we'll create a placeholder
                media_items_data.append({
                    'id': media_id,
                    'filename': f'google_photos_{media_id}',
                    'media_type': 'image',  # Would determine from actual data
                    'base_url': 'placeholder',
                    'metadata': {}
                })
            except Exception as e:
                logger.warning(f"Failed to get details for media item {media_id}: {e}")
                continue
        
        # Import media items (simplified version)
        imported_media_ids = []
        failed_imports = []
        
        for media_item_data in media_items_data:
            try:
                # Create a simplified import for demonstration
                media_item = await google_photos_crud.create_imported_media(
                    db=db,
                    user_id=current_user.id,
                    filename=media_item_data['filename'],
                    original_filename=media_item_data['filename'],
                    gcs_path=f"google_photos/{current_user.id}/{media_item_data['id']}",
                    thumbnail_path=None,
                    media_type=media_item_data['media_type'],
                    file_size=0,
                    width=None,
                    height=None,
                    duration=None,
                    google_photos_id=media_item_data['id'],
                    google_photos_metadata=media_item_data.get('metadata', {}),
                    is_post_ready=import_request.import_to_section == "post-ready"
                )
                
                imported_media_ids.append(media_item.id)
                
            except Exception as e:
                failed_imports.append({
                    media_item_data['id']: str(e)
                })
        
        # Create gallery if requested
        gallery_id = None
        if import_request.create_gallery and imported_media_ids:
            try:
                gallery_name = import_request.gallery_name or f"Google Photos Import {len(imported_media_ids)} items"
                gallery = await google_photos_crud.create_gallery_from_imported_media(
                    db=db,
                    user_id=current_user.id,
                    name=gallery_name,
                    media_ids=imported_media_ids
                )
                gallery_id = gallery.id
            except Exception as e:
                logger.warning(f"Failed to create gallery: {e}")
        
        return schemas.GooglePhotosImportResponse(
            success=len(imported_media_ids) > 0,
            imported_count=len(imported_media_ids),
            failed_count=len(failed_imports),
            imported_media_ids=imported_media_ids,
            failed_imports=failed_imports,
            gallery_id=gallery_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import Google Photos media"
        )


@router.get("/imported", response_model=List[schemas.MediaItemImportDetails])
async def get_imported_media(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of media imported from Google Photos.
    """
    try:
        imported_media = await google_photos_crud.get_imported_media_by_user(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        result = []
        for media in imported_media:
            result.append(schemas.MediaItemImportDetails(
                crow_eye_media_id=media.id,
                google_photos_id=media.google_photos_id,
                filename=media.filename,
                media_type=media.media_type,
                imported_at=media.import_date,
                import_source=media.import_source,
                ai_tags=media.ai_tags,
                gallery_ids=[]  # Would need to query galleries
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting imported media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get imported media"
        ) 