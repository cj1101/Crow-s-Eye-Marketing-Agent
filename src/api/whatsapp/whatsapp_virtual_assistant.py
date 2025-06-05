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

# Knowledge base for responses - only respond from this information
KNOWLEDGE_BASE = {
    'greeting': {
        'responses': [
            "Hello! Welcome to {business_name}. We specialize in {industry}. How can I help you today?",
            "Hi there! Thank you for contacting {business_name}. What can I assist you with?",
            "Good day! I'm here to help you with information about our digital marketing services. What would you like to know?"
        ],
        'triggers': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
    },
    'services': {
        'responses': [
            "We offer the following services:\n• {services}\n\nWhich service interests you most?",
            "Our main services include {services}. We're experts in {industry}. Would you like details about any specific service?",
            "At {business_name}, we provide {services}. Each service is tailored to help grow your business. What can I tell you more about?"
        ],
        'triggers': ['services', 'what do you do', 'what do you offer', 'help with', 'specialize', 'provide'],
        'details': {
            'social media management': "Our Social Media Management includes content planning, posting schedules, community management, and engagement strategies across all major platforms.",
            'content creation': "We create high-quality content including graphics, videos, blog posts, and social media posts that align with your brand voice and marketing goals.",
            'digital marketing strategy': "We develop comprehensive digital marketing strategies that include market analysis, competitor research, goal setting, and campaign planning.",
            'influencer marketing': "Our influencer marketing service connects you with relevant influencers in your industry to expand your reach and build authentic relationships.",
            'brand development': "We help develop and strengthen your brand identity, including logo design, brand guidelines, messaging, and visual consistency.",
            'analytics & reporting': "We provide detailed analytics and reporting to track your marketing performance, ROI, and provide actionable insights for improvement."
        }
    },
    'pricing': {
        'responses': [
            "Our pricing varies based on your specific needs and goals. I'd recommend scheduling a free consultation to discuss a custom package. Contact us at {phone} or {email}.",
            "We offer flexible pricing packages tailored to different business sizes and needs. For accurate pricing, please contact us at {email} or call {phone} for a personalized quote.",
            "Pricing depends on the services you need and the scope of your project. We'd be happy to provide a custom quote. Please reach out to {email} or {phone}."
        ],
        'triggers': ['price', 'cost', 'pricing', 'quote', 'estimate', 'rate', 'fee', 'charge', 'how much', '$']
    },
    'contact': {
        'responses': [
            "You can reach us at:\n📞 Phone: {phone}\n📧 Email: {email}\n🌐 Website: {website}\n🕒 Hours: {hours}",
            "Here's how to contact us:\n• Phone: {phone}\n• Email: {email}\n• Website: {website}\nOur business hours are {hours}",
            "Contact information:\nPhone: {phone}\nEmail: {email}\nWebsite: {website}\nWe're available {hours}"
        ],
        'triggers': ['contact', 'phone', 'email', 'address', 'location', 'hours', 'reach', 'call']
    },
    'scheduling': {
        'responses': [
            "I'd be happy to help you schedule a consultation! Please contact us at {phone} or email {email} to book an appointment. We're available {hours}.",
            "To schedule a meeting or consultation, please call {phone} or email {email}. We offer free initial consultations to discuss your needs.",
            "You can schedule a consultation by calling {phone} or emailing {email}. Our team is available {hours} to set up a meeting that works for you."
        ],
        'triggers': ['schedule', 'appointment', 'meeting', 'consultation', 'call', 'demo', 'book']
    },
    'support': {
        'responses': [
            "I'm here to help! Please describe your specific question or issue, and I'll do my best to assist you. For complex technical issues, I can connect you with our support team.",
            "What specific support do you need? I can help with general questions about our services. For technical issues, please contact {email} or type 'human' to speak with our team.",
            "I'm happy to help! Please let me know what you need assistance with. If I can't answer your question, I'll connect you with one of our specialists."
        ],
        'triggers': ['help', 'support', 'issue', 'problem', 'trouble', 'question', 'assist']
    },
    'feedback': {
        'responses': [
            "Thank you for your feedback! We value your input and use it to improve our services. If you'd like to share more details, please email us at {email}.",
            "We appreciate your feedback! Your experience is important to us. Feel free to share more at {email} or call {phone}.",
            "Thank you for taking the time to provide feedback. We'd love to hear more about your experience - please contact us at {email}."
        ],
        'triggers': ['feedback', 'review', 'testimonial', 'opinion', 'experience', 'rating']
    }
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
            
            # Generate response based on knowledge base
            response = self._generate_knowledge_response(user_id, cleaned_message, intent, context)
            
            # Add response to conversation history
            self._add_to_conversation(user_id, 'assistant', response)
            
            # Prepare response metadata
            metadata = {
                'intent': intent,
                'escalated': False,
                'response_type': 'knowledge_base' if intent != 'unknown' else 'unknown_query',
                'confidence': 1.0 if intent != 'unknown' else 0.0,
                'processing_time': datetime.now().isoformat()
            }
            
            self.signals.response_generated.emit(user_id, response, metadata)
            return response, metadata
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_response = self._get_unknown_response()
            return error_response, {'error': True, 'escalated': False, 'response_type': 'error'}
    
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
        """Detect the intent of the user's message based on knowledge base."""
        message_lower = message.lower()
        
        # Check against knowledge base triggers
        for intent, knowledge in KNOWLEDGE_BASE.items():
            triggers = knowledge.get('triggers', [])
            if any(trigger in message_lower for trigger in triggers):
                return intent
        
        return 'unknown'
    
    def _generate_knowledge_response(self, user_id: str, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Generate response based only on knowledge base information."""
        try:
            # If intent is unknown, we can't provide a response
            if intent == 'unknown':
                return self._get_unknown_response()
            
            # Get response from knowledge base
            knowledge = KNOWLEDGE_BASE.get(intent, {})
            responses = knowledge.get('responses', [])
            
            if not responses:
                return self._get_unknown_response()
            
            # Choose the first response (you could randomize this if desired)
            response_template = responses[0]
            
            # Check if user is asking about specific service details
            if intent == 'services':
                service_details = self._check_for_service_details(message)
                if service_details:
                    return service_details
            
            # Format response with business information
            formatted_response = self._format_response(response_template)
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error generating knowledge response: {e}")
            return self._get_unknown_response()
    
    def _check_for_service_details(self, message: str) -> Optional[str]:
        """Check if user is asking about specific service details."""
        message_lower = message.lower()
        services_details = KNOWLEDGE_BASE['services'].get('details', {})
        
        for service, details in services_details.items():
            # Check if the service name is mentioned in the message
            if service.replace(' ', '') in message_lower.replace(' ', '') or any(word in message_lower for word in service.split()):
                return f"About {service.title()}:\n{details}\n\nWould you like to know about our other services or schedule a consultation? Contact us at {self.business_info['contact']['phone']} or {self.business_info['contact']['email']}."
        
        return None
    
    def _format_response(self, response_template: str) -> str:
        """Format response template with business information."""
        # Prepare formatting variables
        format_vars = {
            'business_name': self.business_info['name'],
            'industry': self.business_info['industry'],
            'services': '\n• '.join(self.business_info['services']),
            'phone': self.business_info['contact']['phone'],
            'email': self.business_info['contact']['email'],
            'website': self.business_info['contact']['website'],
            'hours': self.business_info['contact']['hours']
        }
        
        try:
            return response_template.format(**format_vars)
        except KeyError as e:
            self.logger.warning(f"Missing format variable: {e}")
            return response_template
    
    def _get_unknown_response(self) -> str:
        """Get response when we don't have knowledge base information."""
        return f"""I'd be happy to help, but I can only provide information about our specific services and business details. 

I can help you with:
• Information about our services
• Pricing and consultation scheduling
• Contact information
• General business questions

For other questions or detailed assistance, please contact our team directly:
📞 {self.business_info['contact']['phone']}
📧 {self.business_info['contact']['email']}

Or type 'human' to speak with one of our specialists!"""
    

    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response from knowledge base."""
        if intent in KNOWLEDGE_BASE:
            responses = KNOWLEDGE_BASE[intent].get('responses', [])
            if responses:
                return self._format_response(responses[0])
        
        return self._get_unknown_response()
    
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