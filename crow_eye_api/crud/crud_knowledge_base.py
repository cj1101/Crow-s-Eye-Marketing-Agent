"""
CRUD operations for Knowledge Base and Responder functionality.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from ..models.knowledge_base import (
    KnowledgeFile, ResponderConfiguration, ResponderConversation, ResponderMessage
)
from ..schemas.knowledge_base import (
    KnowledgeFileCreate, KnowledgeFileUpdate,
    ResponderConfigurationCreate, ResponderConfigurationUpdate,
    ResponderConversationCreate, ResponderConversationUpdate,
    ResponderMessageCreate, MessageProcessRequest
)

logger = logging.getLogger(__name__)

# Knowledge File CRUD operations
class CRUDKnowledgeFile:
    """CRUD operations for knowledge files."""
    
    def create(self, db: Session, *, obj_in: KnowledgeFileCreate, user_id: str) -> KnowledgeFile:
        """Create a new knowledge file."""
        # Generate a safe filename
        safe_filename = self._generate_safe_filename(obj_in.original_filename)
        
        db_obj = KnowledgeFile(
            user_id=user_id,
            filename=safe_filename,
            original_filename=obj_in.original_filename,
            content=obj_in.content,
            file_type=obj_in.file_type,
            file_size=obj_in.file_size
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, *, file_id: str, user_id: str) -> Optional[KnowledgeFile]:
        """Get a knowledge file by ID."""
        return db.query(KnowledgeFile).filter(
            and_(KnowledgeFile.id == file_id, KnowledgeFile.user_id == user_id)
        ).first()
    
    def get_multi(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeFile]:
        """Get multiple knowledge files for a user."""
        return db.query(KnowledgeFile).filter(
            KnowledgeFile.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def update(
        self, db: Session, *, db_obj: KnowledgeFile, obj_in: KnowledgeFileUpdate
    ) -> KnowledgeFile:
        """Update a knowledge file."""
        if obj_in.content is not None:
            db_obj.content = obj_in.content
        if obj_in.original_filename is not None:
            db_obj.original_filename = obj_in.original_filename
            db_obj.filename = self._generate_safe_filename(obj_in.original_filename)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, file_id: str, user_id: str) -> Optional[KnowledgeFile]:
        """Delete a knowledge file."""
        obj = db.query(KnowledgeFile).filter(
            and_(KnowledgeFile.id == file_id, KnowledgeFile.user_id == user_id)
        ).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def search(
        self, db: Session, *, user_id: str, query: str, limit: int = 10
    ) -> List[KnowledgeFile]:
        """Search knowledge files by content."""
        return db.query(KnowledgeFile).filter(
            and_(
                KnowledgeFile.user_id == user_id,
                or_(
                    KnowledgeFile.content.contains(query),
                    KnowledgeFile.original_filename.contains(query)
                )
            )
        ).limit(limit).all()
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """Generate a safe filename."""
        # Remove dangerous characters and normalize
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)
        return f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe_name}"

# Responder Configuration CRUD operations
class CRUDResponderConfiguration:
    """CRUD operations for responder configurations."""
    
    def create(
        self, db: Session, *, obj_in: ResponderConfigurationCreate, user_id: str
    ) -> ResponderConfiguration:
        """Create a new responder configuration."""
        db_obj = ResponderConfiguration(
            user_id=user_id,
            **obj_in.dict()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(
        self, db: Session, *, config_id: str, user_id: str
    ) -> Optional[ResponderConfiguration]:
        """Get a responder configuration by ID."""
        return db.query(ResponderConfiguration).filter(
            and_(ResponderConfiguration.id == config_id, ResponderConfiguration.user_id == user_id)
        ).first()
    
    def get_active(self, db: Session, *, user_id: str) -> Optional[ResponderConfiguration]:
        """Get the active responder configuration for a user."""
        return db.query(ResponderConfiguration).filter(
            and_(
                ResponderConfiguration.user_id == user_id,
                ResponderConfiguration.is_active == True
            )
        ).first()
    
    def get_multi(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[ResponderConfiguration]:
        """Get multiple responder configurations for a user."""
        return db.query(ResponderConfiguration).filter(
            ResponderConfiguration.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def update(
        self, db: Session, *, db_obj: ResponderConfiguration, obj_in: ResponderConfigurationUpdate
    ) -> ResponderConfiguration:
        """Update a responder configuration."""
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(
        self, db: Session, *, config_id: str, user_id: str
    ) -> Optional[ResponderConfiguration]:
        """Delete a responder configuration."""
        obj = db.query(ResponderConfiguration).filter(
            and_(ResponderConfiguration.id == config_id, ResponderConfiguration.user_id == user_id)
        ).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

# Responder Conversation CRUD operations
class CRUDResponderConversation:
    """CRUD operations for responder conversations."""
    
    def create(
        self, db: Session, *, obj_in: ResponderConversationCreate, user_id: str
    ) -> ResponderConversation:
        """Create a new responder conversation."""
        db_obj = ResponderConversation(
            user_id=user_id,
            **obj_in.dict()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(
        self, db: Session, *, conversation_id: str, user_id: str
    ) -> Optional[ResponderConversation]:
        """Get a responder conversation by ID."""
        return db.query(ResponderConversation).filter(
            and_(ResponderConversation.id == conversation_id, ResponderConversation.user_id == user_id)
        ).first()
    
    def get_by_platform_user(
        self, db: Session, *, platform_user_id: str, platform: str, user_id: str
    ) -> Optional[ResponderConversation]:
        """Get a conversation by platform user ID."""
        return db.query(ResponderConversation).filter(
            and_(
                ResponderConversation.platform_user_id == platform_user_id,
                ResponderConversation.platform == platform,
                ResponderConversation.user_id == user_id,
                ResponderConversation.status != "closed"
            )
        ).first()
    
    def get_multi(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100,
        status: Optional[str] = None
    ) -> List[ResponderConversation]:
        """Get multiple responder conversations for a user."""
        query = db.query(ResponderConversation).filter(ResponderConversation.user_id == user_id)
        
        if status:
            query = query.filter(ResponderConversation.status == status)
        
        return query.order_by(desc(ResponderConversation.last_activity)).offset(skip).limit(limit).all()
    
    def update(
        self, db: Session, *, db_obj: ResponderConversation, obj_in: ResponderConversationUpdate
    ) -> ResponderConversation:
        """Update a responder conversation."""
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db_obj.last_activity = datetime.utcnow()
        if obj_in.status == "escalated" and db_obj.escalated_at is None:
            db_obj.escalated_at = datetime.utcnow()
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_analytics(
        self, db: Session, *, user_id: str, start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None, platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversation analytics."""
        query = db.query(ResponderConversation).filter(ResponderConversation.user_id == user_id)
        
        if start_date:
            query = query.filter(ResponderConversation.started_at >= start_date)
        if end_date:
            query = query.filter(ResponderConversation.started_at <= end_date)
        if platform:
            query = query.filter(ResponderConversation.platform == platform)
        
        conversations = query.all()
        
        total = len(conversations)
        active = len([c for c in conversations if c.status == "active"])
        escalated = len([c for c in conversations if c.status == "escalated"])
        
        # Calculate satisfaction scores
        satisfaction_scores = {}
        for conv in conversations:
            if conv.satisfaction_score:
                score = str(conv.satisfaction_score)
                satisfaction_scores[score] = satisfaction_scores.get(score, 0) + 1
        
        # Platform breakdown
        platform_breakdown = {}
        for conv in conversations:
            platform_breakdown[conv.platform] = platform_breakdown.get(conv.platform, 0) + 1
        
        return {
            "total_conversations": total,
            "active_conversations": active,
            "escalated_conversations": escalated,
            "satisfaction_scores": satisfaction_scores,
            "platform_breakdown": platform_breakdown
        }

# Responder Message CRUD operations
class CRUDResponderMessage:
    """CRUD operations for responder messages."""
    
    def create(self, db: Session, *, obj_in: ResponderMessageCreate) -> ResponderMessage:
        """Create a new responder message."""
        db_obj = ResponderMessage(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_conversation_messages(
        self, db: Session, *, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[ResponderMessage]:
        """Get messages for a conversation."""
        return db.query(ResponderMessage).filter(
            ResponderMessage.conversation_id == conversation_id
        ).order_by(ResponderMessage.timestamp).offset(skip).limit(limit).all()

# Responder Service for message processing
class ResponderService:
    """Service for processing responder messages and generating responses."""
    
    def __init__(self):
        self.conversation_crud = CRUDResponderConversation()
        self.message_crud = CRUDResponderMessage()
        self.config_crud = CRUDResponderConfiguration()
        self.knowledge_crud = CRUDKnowledgeFile()
    
    def process_message(
        self, db: Session, *, request: MessageProcessRequest, user_id: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Process an incoming message and generate a response."""
        try:
            # Get or create conversation
            conversation = self.conversation_crud.get_by_platform_user(
                db, 
                platform_user_id=request.platform_user_id,
                platform=request.platform,
                user_id=user_id
            )
            
            if not conversation:
                # Create new conversation
                conversation_create = ResponderConversationCreate(
                    platform_user_id=request.platform_user_id,
                    platform=request.platform,
                    conversation_data=request.context
                )
                conversation = self.conversation_crud.create(
                    db, obj_in=conversation_create, user_id=user_id
                )
            
            # Save user message
            user_message = ResponderMessageCreate(
                conversation_id=conversation.id,
                role="user",
                content=request.message,
                message_metadata=request.context
            )
            self.message_crud.create(db, obj_in=user_message)
            
            # Get responder configuration
            config = self.config_crud.get_active(db, user_id=user_id)
            if not config:
                response = "I'm sorry, but the virtual assistant is not configured. Please contact support."
                metadata = {"error": "No active responder configuration"}
                return response, metadata
            
            # Process message and generate response
            response, metadata = self._generate_response(
                db, request.message, config, conversation, user_id
            )
            
            # Save assistant response
            assistant_message = ResponderMessageCreate(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
                intent=metadata.get("intent"),
                confidence=int(metadata.get("confidence", 0) * 100),
                message_metadata=metadata
            )
            self.message_crud.create(db, obj_in=assistant_message)
            
            # Update conversation
            conversation_update = ResponderConversationUpdate(
                status="escalated" if metadata.get("escalated") else "active"
            )
            self.conversation_crud.update(db, db_obj=conversation, obj_in=conversation_update)
            
            return response, {
                **metadata,
                "conversation_id": conversation.id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm sorry, but I'm having trouble processing your message. Please try again.", {
                "error": str(e),
                "intent": "error",
                "confidence": 0.0,
                "escalated": True
            }
    
    def _generate_response(
        self, db: Session, message: str, config: ResponderConfiguration,
        conversation: ResponderConversation, user_id: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate a response based on configuration and knowledge base."""
        # Simple intent detection based on keywords
        intent = self._detect_intent(message, config)
        confidence = 0.8 if intent != "unknown" else 0.1
        
        # Check for escalation
        if self._should_escalate(message, config):
            return self._get_escalation_response(config), {
                "intent": intent,
                "confidence": confidence,
                "escalated": True,
                "escalation_reason": "keyword_trigger"
            }
        
        # Generate response from knowledge base
        response = self._get_knowledge_response(db, message, intent, config, user_id)
        
        return response, {
            "intent": intent,
            "confidence": confidence,
            "escalated": False,
            "response_type": "knowledge_base" if intent != "unknown" else "fallback"
        }
    
    def _detect_intent(self, message: str, config: ResponderConfiguration) -> str:
        """Detect intent from message."""
        message_lower = message.lower()
        
        # Check knowledge base for intent patterns
        knowledge_base = config.knowledge_base
        for intent_name, intent_data in knowledge_base.items():
            triggers = intent_data.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in message_lower:
                    return intent_name
        
        return "unknown"
    
    def _should_escalate(self, message: str, config: ResponderConfiguration) -> bool:
        """Check if message should be escalated to human."""
        message_lower = message.lower()
        escalation_keywords = config.escalation_keywords or []
        
        return any(keyword.lower() in message_lower for keyword in escalation_keywords)
    
    def _get_knowledge_response(
        self, db: Session, message: str, intent: str, config: ResponderConfiguration, user_id: str
    ) -> str:
        """Get response from knowledge base."""
        knowledge_base = config.knowledge_base
        
        if intent in knowledge_base:
            responses = knowledge_base[intent].get("responses", [])
            if responses:
                # Use first response (could implement rotation/selection logic)
                response_template = responses[0]
                return self._format_response(response_template, config.business_info)
        
        # Fallback to searching knowledge files
        knowledge_files = self.knowledge_crud.search(db, user_id=user_id, query=message, limit=3)
        if knowledge_files:
            return f"Based on our information: {knowledge_files[0].content[:200]}... Would you like more details?"
        
        return "I'm sorry, but I don't have specific information about that. Please contact our support team for assistance."
    
    def _format_response(self, template: str, business_info: Dict[str, Any]) -> str:
        """Format response template with business information."""
        try:
            # Simple template formatting
            formatted = template
            for key, value in business_info.items():
                if isinstance(value, list):
                    value = "\n• ".join(value)
                elif isinstance(value, dict):
                    # Handle nested dict (like contact info)
                    if key == "contact":
                        for contact_key, contact_value in value.items():
                            formatted = formatted.replace(f"{{{contact_key}}}", str(contact_value))
                    continue
                formatted = formatted.replace(f"{{{key}}}", str(value))
            return formatted
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return template
    
    def _get_escalation_response(self, config: ResponderConfiguration) -> str:
        """Get escalation response."""
        return "I understand you need additional assistance. I'm connecting you with one of our team members who will be able to help you shortly."

# Create instances
crud_knowledge_file = CRUDKnowledgeFile()
crud_responder_config = CRUDResponderConfiguration()
crud_responder_conversation = CRUDResponderConversation()
crud_responder_message = CRUDResponderMessage()
responder_service = ResponderService() 