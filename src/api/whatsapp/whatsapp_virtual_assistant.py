"""
WhatsApp Virtual Assistant for automated customer service and help desk.
Uses AI to provide intelligent responses and manage customer inquiries.
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from PySide6.QtCore import QObject, Signal

from ...api.ai.gemini_handler import GeminiHandler
from ...config import constants as const

# Constants for intent detection
INTENT_KEYWORDS = {
    'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
    'pricing': ['price', 'cost', 'pricing', 'quote', 'estimate', 'rate', 'fee', 'charge'],
    'services': ['service', 'offer', 'do', 'provide', 'help with', 'specialize'],
    'scheduling': ['schedule', 'appointment', 'meeting', 'consultation', 'call', 'demo'],
    'support': ['help', 'support', 'issue', 'problem', 'trouble', 'question'],
    'contact': ['contact', 'phone', 'email', 'address', 'location', 'hours'],
    'feedback': ['feedback', 'review', 'testimonial', 'opinion', 'experience']
}

# Keywords that trigger escalation to human agents
ESCALATION_KEYWORDS = [
    'human', 'agent', 'representative', 'manager', 'speak to someone',
    'not working', 'problem', 'complaint', 'refund', 'cancel', 
    'urgent', 'emergency', 'help me', 'frustrated'
]

# Emotional indicators for escalation
ANGER_INDICATORS = [
    'angry', 'mad', 'furious', 'terrible', 'awful', 'worst', 'hate'
]

# Default business information
DEFAULT_BUSINESS_INFO = {
    'name': 'Breadsmith Marketing',
    'industry': 'Digital Marketing & Social Media Management',
    'services': [
        'Social Media Management',
        'Content Creation', 
        'Digital Marketing Strategy',
        'Influencer Marketing',
        'Brand Development',
        'Analytics & Reporting'
    ],
    'contact': {
        'email': 'support@breadsmith.com',
        'phone': '+1-555-0123',
        'website': 'https://breadsmith.com',
        'hours': 'Monday-Friday 9AM-6PM EST'
    },
    'locations': 'Remote services worldwide',
    'languages': ['English', 'Spanish', 'French']
}

# Default assistant configuration
DEFAULT_ASSISTANT_CONFIG = {
    'name': 'Bread Assistant',
    'personality': 'Professional, helpful, friendly, and knowledgeable',
    'capabilities': [
        'Answer questions about services',
        'Provide pricing information', 
        'Schedule consultations',
        'Troubleshoot common issues',
        'Escalate complex issues to human agents',
        'Collect feedback and testimonials'
    ],
    'response_style': 'conversational_professional',
    'max_response_length': 300,
    'greeting_enabled': True,
    'follow_up_enabled': True
}

class WhatsAppVirtualAssistantSignals(QObject):
    """Signals for WhatsApp Virtual Assistant operations."""
    response_generated = Signal(str, str, dict)  # user_id, response, metadata
    escalation_requested = Signal(str, str, dict)  # user_id, reason, context
    conversation_started = Signal(str, dict)  # user_id, user_info
    status_update = Signal(str)

class WhatsAppVirtualAssistant:
    """AI-powered virtual assistant for WhatsApp customer service."""
    
    def __init__(self, api_handler=None):
        """Initialize the virtual assistant."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = WhatsAppVirtualAssistantSignals()
        self.api_handler = api_handler
        self.ai_handler = GeminiHandler()
        
        # Conversation memory - in production, use a database
        self.conversations = {}
        
        # Configuration
        self.business_info = self._load_business_info()
        self.assistant_config = self._load_assistant_config()
        
        # Keywords for escalation to human agents
        self.escalation_keywords = ESCALATION_KEYWORDS
    
    def _load_business_info(self) -> Dict[str, Any]:
        """Load business information for the virtual assistant."""
        return DEFAULT_BUSINESS_INFO.copy()
    
    def _load_assistant_config(self) -> Dict[str, Any]:
        """Load assistant configuration and personality."""
        return DEFAULT_ASSISTANT_CONFIG.copy()
    
    def process_message(self, user_id: str, message: str, context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Process incoming message and generate appropriate response.
        
        Args:
            user_id: WhatsApp user ID
            message: User's message text
            context: Additional context from WhatsApp
            
        Returns:
            Tuple of (response_text, response_metadata)
        """
        try:
            # Clean and normalize the message
            cleaned_message = self._clean_message(message)
            
            # Check if this is a new conversation
            if user_id not in self.conversations:
                self._start_new_conversation(user_id, context)
            
            # Update conversation history
            self._add_to_conversation(user_id, 'user', cleaned_message)
            
            # Check for escalation keywords
            if self._should_escalate(cleaned_message):
                return self._handle_escalation(user_id, cleaned_message, context)
            
            # Detect message intent
            intent = self._detect_intent(cleaned_message)
            
            # Generate AI response based on intent and context
            response = self._generate_ai_response(user_id, cleaned_message, intent, context)
            
            # Add response to conversation history
            self._add_to_conversation(user_id, 'assistant', response)
            
            # Prepare response metadata
            metadata = {
                'intent': intent,
                'escalated': False,
                'response_type': 'ai_generated',
                'confidence': 0.8,
                'processing_time': datetime.now().isoformat()
            }
            
            self.signals.response_generated.emit(user_id, response, metadata)
            return response, metadata
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I'm having technical difficulties. Please try again in a moment, or type 'human' to speak with one of our team members."
            return error_response, {'error': True, 'escalated': False}
    
    def _clean_message(self, message: str) -> str:
        """Clean and normalize the message text."""
        if not message:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', message.strip())
        
        # Remove common WhatsApp artifacts
        cleaned = re.sub(r'^\[.*?\]\s*', '', cleaned)  # Remove timestamps
        cleaned = re.sub(r'https?://\S+', '[LINK]', cleaned)  # Replace URLs
        
        return cleaned
    
    def _start_new_conversation(self, user_id: str, context: Dict[str, Any] = None):
        """Start a new conversation with a user."""
        contact_info = context.get('contacts', [{}])[0] if context else {}
        
        conversation = {
            'user_id': user_id,
            'started_at': datetime.now().isoformat(),
            'messages': [],
            'context': context or {},
            'user_info': {
                'name': contact_info.get('profile', {}).get('name', 'Customer'),
                'phone': user_id
            },
            'escalated': False,
            'satisfaction_score': None
        }
        
        self.conversations[user_id] = conversation
        self.signals.conversation_started.emit(user_id, conversation['user_info'])
        
        self.logger.info(f"Started new conversation with user {user_id}")
    
    def _add_to_conversation(self, user_id: str, role: str, message: str):
        """Add a message to the conversation history."""
        if user_id in self.conversations:
            self.conversations[user_id]['messages'].append({
                'role': role,
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
    
    def _should_escalate(self, message: str) -> bool:
        """Check if the message should be escalated to a human agent."""
        message_lower = message.lower()
        
        # Check for escalation keywords
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True
        
        # Check for emotional indicators (anger, frustration)
        if any(indicator in message_lower for indicator in ANGER_INDICATORS):
            return True
        
        # Check for complex technical issues
        if len(message.split()) > 50:  # Very long messages might need human attention
            return True
        
        return False
    
    def _detect_intent(self, message: str) -> str:
        """Detect the intent of the user's message."""
        message_lower = message.lower()
        
        # Check against defined intent keywords
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        # Additional specific patterns
        if any(word in message_lower for word in ['how much', '$']):
            return 'pricing'
        if any(word in message_lower for word in ['what do you do', 'book']):
            return 'services' if 'what do you do' in message_lower else 'scheduling'
        
        return 'general_inquiry'
    
    def _generate_ai_response(self, user_id: str, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Generate AI-powered response based on message and intent."""
        try:
            # Get conversation history for context
            conversation_history = self.conversations.get(user_id, {}).get('messages', [])
            user_name = self.conversations.get(user_id, {}).get('user_info', {}).get('name', 'Customer')
            
            # Build context for AI
            system_prompt = self._build_system_prompt(intent, user_name)
            conversation_context = self._build_conversation_context(conversation_history)
            
            # Generate response using AI
            full_prompt = f"{system_prompt}\n\nConversation history:\n{conversation_context}\n\nUser message: {message}\n\nResponse:"
            
            ai_response = self.ai_handler.generate_response(full_prompt)
            
            # Post-process the response
            processed_response = self._post_process_response(ai_response, intent)
            
            return processed_response
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(intent)
    
    def _build_system_prompt(self, intent: str, user_name: str) -> str:
        """Build system prompt for AI based on intent and context."""
        base_prompt = f"""You are {self.assistant_config['name']}, a professional virtual assistant for {self.business_info['name']}.

Business Information:
- Company: {self.business_info['name']}
- Industry: {self.business_info['industry']}
- Services: {', '.join(self.business_info['services'])}
- Contact: {self.business_info['contact']['email']} | {self.business_info['contact']['phone']}
- Hours: {self.business_info['contact']['hours']}
- Website: {self.business_info['contact']['website']}

Your personality: {self.assistant_config['personality']}

Instructions:
1. Be helpful, professional, and friendly
2. Keep responses under {self.assistant_config['max_response_length']} characters
3. Always provide accurate information about our services
4. If you can't help, suggest contacting our human team
5. Use the customer's name ({user_name}) when appropriate
6. Include relevant contact information when helpful
"""
        
        # Add intent-specific instructions
        intent_prompts = {
            'greeting': "Provide a warm greeting and ask how you can help today.",
            'pricing': "Provide clear pricing information and offer to schedule a consultation for detailed quotes.",
            'service_inquiry': "Explain our services clearly and how they can benefit the customer.",
            'scheduling': "Help schedule a consultation or meeting. Get preferred dates/times.",
            'support': "Provide helpful troubleshooting or escalate to human support if needed.",
            'contact_info': "Provide accurate contact information and hours.",
            'feedback': "Thank them for feedback and encourage them to share more details."
        }
        
        specific_prompt = intent_prompts.get(intent, "Respond helpfully to their inquiry.")
        
        return f"{base_prompt}\n\nSpecific task: {specific_prompt}"
    
    def _build_conversation_context(self, messages: List[Dict]) -> str:
        """Build conversation context from message history."""
        if not messages:
            return "This is the start of the conversation."
        
        context_lines = []
        for msg in messages[-5:]:  # Last 5 messages for context
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def _post_process_response(self, response: str, intent: str) -> str:
        """Post-process AI response for quality and consistency."""
        if not response:
            return self._get_fallback_response(intent)
        
        # Clean up the response
        response = response.strip()
        
        # Ensure proper length
        if len(response) > self.assistant_config['max_response_length']:
            # Truncate at last complete sentence
            sentences = response.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ".") <= self.assistant_config['max_response_length']:
                    truncated += sentence + "."
                else:
                    break
            response = truncated.strip()
        
        # Add helpful closing for certain intents
        if intent == 'support' and 'human' not in response.lower():
            response += "\n\nIf you need further assistance, type 'human' to speak with our team."
        
        return response
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response when AI fails."""
        fallback_responses = {
            'greeting': f"Hello! Welcome to {self.business_info['name']}. How can I help you today?",
            'pricing': f"I'd be happy to discuss our pricing. Please contact us at {self.business_info['contact']['email']} for detailed information.",
            'service_inquiry': f"We offer {', '.join(self.business_info['services'][:3])} and more. Visit {self.business_info['contact']['website']} for details.",
            'scheduling': f"I'd love to help you schedule a consultation. Please call us at {self.business_info['contact']['phone']} or email {self.business_info['contact']['email']}.",
            'support': "I'm here to help! Please describe your issue, or type 'human' to speak with our support team.",
            'contact_info': f"You can reach us at {self.business_info['contact']['phone']} or {self.business_info['contact']['email']}. Hours: {self.business_info['contact']['hours']}",
            'feedback': "Thank you for your feedback! We value your input and use it to improve our services."
        }
        
        return fallback_responses.get(intent, f"Thank you for contacting {self.business_info['name']}. How can I assist you today?")
    
    def _handle_escalation(self, user_id: str, message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Handle escalation to human agent."""
        if user_id in self.conversations:
            self.conversations[user_id]['escalated'] = True
        
        escalation_reason = "User requested human assistance"
        if any(word in message.lower() for word in ['problem', 'issue', 'complaint']):
            escalation_reason = "Technical support required"
        elif any(word in message.lower() for word in ['angry', 'frustrated', 'terrible']):
            escalation_reason = "Customer service escalation"
        
        # Emit escalation signal
        self.signals.escalation_requested.emit(user_id, escalation_reason, context or {})
        
        response = f"""I understand you'd like to speak with a human team member. I'm connecting you with our support team now.

📞 You can also reach us directly:
• Phone: {self.business_info['contact']['phone']}
• Email: {self.business_info['contact']['email']}
• Hours: {self.business_info['contact']['hours']}

Someone from our team will be with you shortly!"""
        
        metadata = {
            'escalated': True,
            'escalation_reason': escalation_reason,
            'response_type': 'escalation',
            'processing_time': datetime.now().isoformat()
        }
        
        return response, metadata
    
    def get_conversation_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary for a user."""
        if user_id not in self.conversations:
            return None
        
        conversation = self.conversations[user_id]
        message_count = len(conversation['messages'])
        
        return {
            'user_id': user_id,
            'user_info': conversation['user_info'],
            'started_at': conversation['started_at'],
            'message_count': message_count,
            'escalated': conversation['escalated'],
            'last_message_at': conversation['messages'][-1]['timestamp'] if message_count > 0 else None,
            'satisfaction_score': conversation.get('satisfaction_score')
        }
    
    def set_satisfaction_score(self, user_id: str, score: int) -> bool:
        """Set customer satisfaction score for a conversation."""
        if user_id in self.conversations:
            self.conversations[user_id]['satisfaction_score'] = score
            return True
        return False
    
    def get_active_conversations(self) -> List[Dict[str, Any]]:
        """Get list of active conversations."""
        active = []
        for user_id, conv in self.conversations.items():
            if not conv.get('ended', False):
                active.append(self.get_conversation_summary(user_id))
        return active 