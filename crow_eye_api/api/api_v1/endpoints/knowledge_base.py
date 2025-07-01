"""
Knowledge Base and Responder API endpoints.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ....core.security import has_platform_access
from ....api.api_v1.dependencies import get_current_active_user, get_db
from ....schemas.user import User
from ....schemas.knowledge_base import (
    # Knowledge File schemas
    KnowledgeFileCreate, KnowledgeFileUpdate, KnowledgeFileResponse, KnowledgeFileListResponse,
    KnowledgeBaseUploadRequest, KnowledgeBaseSearchRequest, KnowledgeBaseSearchResponse,
    BulkKnowledgeFileDeleteRequest, BulkKnowledgeFileDeleteResponse,
    
    # Responder Configuration schemas
    ResponderConfigurationCreate, ResponderConfigurationUpdate, ResponderConfigurationResponse,
    
    # Responder Conversation schemas
    ResponderConversationResponse, ConversationListResponse, ConversationDetailResponse,
    
    # Message processing schemas
    MessageProcessRequest, MessageProcessResponse,
    
    # Analytics schemas
    ResponderAnalyticsRequest, ResponderAnalyticsResponse
)
from ....crud.crud_knowledge_base import (
    crud_knowledge_file, crud_responder_config, crud_responder_conversation,
    crud_responder_message, responder_service
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Knowledge File endpoints
@router.post("/knowledge-files/upload", response_model=KnowledgeFileResponse)
async def upload_knowledge_file(
    request: KnowledgeBaseUploadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> KnowledgeFileResponse:
    """Upload a knowledge base file."""
    # Check access permissions
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        # Create knowledge file
        file_create = KnowledgeFileCreate(
            original_filename=request.filename,
            content=request.file_content,
            file_type=request.file_type,
            file_size=len(request.file_content.encode('utf-8'))
        )
        
        knowledge_file = crud_knowledge_file.create(
            db, obj_in=file_create, user_id=current_user.id
        )
        
        logger.info(f"Knowledge file uploaded: {knowledge_file.id} for user {current_user.id}")
        return KnowledgeFileResponse.from_orm(knowledge_file)
        
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload knowledge file")

@router.get("/knowledge-files", response_model=KnowledgeFileListResponse)
async def get_knowledge_files(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> KnowledgeFileListResponse:
    """Get knowledge files for the current user."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        files = crud_knowledge_file.get_multi(
            db, user_id=current_user.id, skip=skip, limit=limit
        )
        
        # Convert to response format (without content to save bandwidth)
        file_responses = []
        for file in files:
            file_response = KnowledgeFileResponse.from_orm(file)
            file_response.content = None  # Don't include content in list view
            file_responses.append(file_response)
        
        return KnowledgeFileListResponse(files=file_responses, total=len(files))
        
    except Exception as e:
        logger.error(f"Error fetching knowledge files: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge files")

@router.get("/knowledge-files/{file_id}", response_model=KnowledgeFileResponse)
async def get_knowledge_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> KnowledgeFileResponse:
    """Get a specific knowledge file with content."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        knowledge_file = crud_knowledge_file.get(
            db, file_id=file_id, user_id=current_user.id
        )
        
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="Knowledge file not found")
        
        return KnowledgeFileResponse.from_orm(knowledge_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching knowledge file: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge file")

@router.put("/knowledge-files/{file_id}", response_model=KnowledgeFileResponse)
async def update_knowledge_file(
    file_id: str,
    file_update: KnowledgeFileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> KnowledgeFileResponse:
    """Update a knowledge file."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        knowledge_file = crud_knowledge_file.get(
            db, file_id=file_id, user_id=current_user.id
        )
        
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="Knowledge file not found")
        
        updated_file = crud_knowledge_file.update(
            db, db_obj=knowledge_file, obj_in=file_update
        )
        
        logger.info(f"Knowledge file updated: {file_id} for user {current_user.id}")
        return KnowledgeFileResponse.from_orm(updated_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge file: {e}")
        raise HTTPException(status_code=500, detail="Failed to update knowledge file")

@router.delete("/knowledge-files/{file_id}")
async def delete_knowledge_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete a knowledge file."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        knowledge_file = crud_knowledge_file.remove(
            db, file_id=file_id, user_id=current_user.id
        )
        
        if not knowledge_file:
            raise HTTPException(status_code=404, detail="Knowledge file not found")
        
        logger.info(f"Knowledge file deleted: {file_id} for user {current_user.id}")
        return {"message": "Knowledge file deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge file: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge file")

@router.post("/knowledge-files/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_files(
    search_request: KnowledgeBaseSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> KnowledgeBaseSearchResponse:
    """Search knowledge files by content."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        files = crud_knowledge_file.search(
            db, user_id=current_user.id, query=search_request.query, limit=search_request.limit
        )
        
        results = []
        for file in files:
            results.append({
                "id": file.id,
                "filename": file.original_filename,
                "file_type": file.file_type,
                "content_preview": file.content[:200] + "..." if len(file.content) > 200 else file.content,
                "upload_timestamp": file.upload_timestamp
            })
        
        return KnowledgeBaseSearchResponse(
            results=results,
            total=len(results),
            query=search_request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge files: {e}")
        raise HTTPException(status_code=500, detail="Failed to search knowledge files")

@router.post("/knowledge-files/bulk-delete", response_model=BulkKnowledgeFileDeleteResponse)
async def bulk_delete_knowledge_files(
    request: BulkKnowledgeFileDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BulkKnowledgeFileDeleteResponse:
    """Bulk delete knowledge files."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Knowledge base access requires an active subscription"
        )
    
    try:
        deleted_count = 0
        errors = []
        
        for file_id in request.file_ids:
            try:
                result = crud_knowledge_file.remove(
                    db, file_id=file_id, user_id=current_user.id
                )
                if result:
                    deleted_count += 1
                else:
                    errors.append(f"File {file_id} not found")
            except Exception as e:
                errors.append(f"Error deleting file {file_id}: {str(e)}")
        
        logger.info(f"Bulk deleted {deleted_count} knowledge files for user {current_user.id}")
        return BulkKnowledgeFileDeleteResponse(deleted_count=deleted_count, errors=errors)
        
    except Exception as e:
        logger.error(f"Error bulk deleting knowledge files: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete knowledge files")

# Responder Configuration endpoints
@router.post("/responder/config", response_model=ResponderConfigurationResponse)
async def create_responder_config(
    config_create: ResponderConfigurationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponderConfigurationResponse:
    """Create a responder configuration."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        # Deactivate existing configurations if this one is being set as active
        if config_create.is_active:
            existing_configs = crud_responder_config.get_multi(db, user_id=current_user.id)
            for config in existing_configs:
                if config.is_active:
                    crud_responder_config.update(
                        db, db_obj=config, 
                        obj_in=ResponderConfigurationUpdate(is_active=False)
                    )
        
        responder_config = crud_responder_config.create(
            db, obj_in=config_create, user_id=current_user.id
        )
        
        logger.info(f"Responder config created: {responder_config.id} for user {current_user.id}")
        return ResponderConfigurationResponse.from_orm(responder_config)
        
    except Exception as e:
        logger.error(f"Error creating responder config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create responder configuration")

@router.get("/responder/config", response_model=ResponderConfigurationResponse)
async def get_active_responder_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponderConfigurationResponse:
    """Get the active responder configuration."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        config = crud_responder_config.get_active(db, user_id=current_user.id)
        
        if not config:
            raise HTTPException(status_code=404, detail="No active responder configuration found")
        
        return ResponderConfigurationResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching responder config: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch responder configuration")

@router.put("/responder/config/{config_id}", response_model=ResponderConfigurationResponse)
async def update_responder_config(
    config_id: str,
    config_update: ResponderConfigurationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponderConfigurationResponse:
    """Update a responder configuration."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        config = crud_responder_config.get(db, config_id=config_id, user_id=current_user.id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Responder configuration not found")
        
        # If setting this config as active, deactivate others
        if config_update.is_active:
            existing_configs = crud_responder_config.get_multi(db, user_id=current_user.id)
            for existing_config in existing_configs:
                if existing_config.id != config_id and existing_config.is_active:
                    crud_responder_config.update(
                        db, db_obj=existing_config,
                        obj_in=ResponderConfigurationUpdate(is_active=False)
                    )
        
        updated_config = crud_responder_config.update(
            db, db_obj=config, obj_in=config_update
        )
        
        logger.info(f"Responder config updated: {config_id} for user {current_user.id}")
        return ResponderConfigurationResponse.from_orm(updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating responder config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update responder configuration")

# Message Processing endpoints
@router.post("/responder/process-message", response_model=MessageProcessResponse)
async def process_message(
    request: MessageProcessRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> MessageProcessResponse:
    """Process an incoming message and generate a response."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        response, metadata = responder_service.process_message(
            db, request=request, user_id=current_user.id
        )
        
        return MessageProcessResponse(
            response=response,
            intent=metadata.get("intent", "unknown"),
            confidence=metadata.get("confidence", 0.0),
            escalated=metadata.get("escalated", False),
            conversation_id=metadata.get("conversation_id", ""),
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# Conversation Management endpoints
@router.get("/responder/conversations", response_model=ConversationListResponse)
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ConversationListResponse:
    """Get conversations for the current user."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        conversations = crud_responder_conversation.get_multi(
            db, user_id=current_user.id, skip=skip, limit=limit, status=status
        )
        
        # Get counts
        all_conversations = crud_responder_conversation.get_multi(db, user_id=current_user.id)
        active_count = len([c for c in all_conversations if c.status == "active"])
        escalated_count = len([c for c in all_conversations if c.status == "escalated"])
        
        conversation_responses = [
            ResponderConversationResponse.from_orm(conv) for conv in conversations
        ]
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=len(all_conversations),
            active_count=active_count,
            escalated_count=escalated_count
        )
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@router.get("/responder/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ConversationDetailResponse:
    """Get detailed conversation with messages."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        conversation = crud_responder_conversation.get(
            db, conversation_id=conversation_id, user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = crud_responder_message.get_conversation_messages(
            db, conversation_id=conversation_id
        )
        
        from ....schemas.knowledge_base import ResponderMessageResponse
        message_responses = [
            ResponderMessageResponse.from_orm(msg) for msg in messages
        ]
        
        return ConversationDetailResponse(
            conversation=ResponderConversationResponse.from_orm(conversation),
            messages=message_responses,
            total_messages=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation details")

# Analytics endpoints
@router.post("/responder/analytics", response_model=ResponderAnalyticsResponse)
async def get_responder_analytics(
    request: ResponderAnalyticsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponderAnalyticsResponse:
    """Get responder analytics."""
    if not has_platform_access(current_user.subscription_tier):
        raise HTTPException(
            status_code=403,
            detail="Responder functionality requires an active subscription"
        )
    
    try:
        analytics = crud_responder_conversation.get_analytics(
            db,
            user_id=current_user.id,
            start_date=request.start_date,
            end_date=request.end_date,
            platform=request.platform
        )
        
        # Calculate average response time (placeholder - would need message timestamps)
        average_response_time = 30.0  # seconds
        
        # Get top intents (placeholder - would analyze messages)
        top_intents = [
            {"intent": "greeting", "count": 25},
            {"intent": "pricing", "count": 20},
            {"intent": "services", "count": 18}
        ]
        
        return ResponderAnalyticsResponse(
            total_conversations=analytics["total_conversations"],
            active_conversations=analytics["active_conversations"],
            escalated_conversations=analytics["escalated_conversations"],
            average_response_time=average_response_time,
            satisfaction_scores=analytics["satisfaction_scores"],
            top_intents=top_intents,
            platform_breakdown=analytics["platform_breakdown"],
            period={
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching responder analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch responder analytics") 