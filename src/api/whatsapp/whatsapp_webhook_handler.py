"""
WhatsApp Webhook Handler for processing incoming messages and events.
Handles webhook verification and message processing for the virtual help desk.
"""
import json
import logging
from threading import Thread
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from PySide6.QtCore import QObject, Signal

# Constants for webhook responses
WEBHOOK_RESPONSES = {
    'SERVICES': "We offer comprehensive social media management, content creation, digital marketing strategy, and more. What specific service interests you?",
    'PRICING': "Our pricing varies based on your needs. Would you like to schedule a consultation to discuss a custom package?", 
    'SUPPORT': "I'm here to help with any questions or issues. What do you need assistance with?",
    'HUMAN': "I'm connecting you with a human team member. Someone will be with you shortly!",
    'SELECTION_DEFAULT': "I received your selection. How else can I help you?",
    'UNSUPPORTED_MEDIA': "I received your {message_type} message, but I can only respond to text messages at the moment. Please send me a text message describing how I can help you!",
    'FALLBACK': "I apologize, but I'm having trouble processing your message. Please try again, or type 'human' to speak with our team."
}

# Webhook endpoints configuration
WEBHOOK_ENDPOINTS = [
    '/webhook (GET, POST)',
    '/health (GET)', 
    '/status (GET)'
]

class WhatsAppWebhookSignals(QObject):
    """Signals for WhatsApp webhook operations."""
    message_received = Signal(dict)  # webhook_data
    status_received = Signal(dict)  # status_data
    webhook_verified = Signal(str)  # verification_challenge
    webhook_error = Signal(str, str)  # operation, error_message

class WhatsAppWebhookHandler:
    """Handler for WhatsApp webhook events."""
    
    def __init__(self, api_handler=None, virtual_assistant=None):
        """Initialize the webhook handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = WhatsAppWebhookSignals()
        self.api_handler = api_handler
        self.virtual_assistant = virtual_assistant
        
        # Flask app for webhook
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Webhook server thread
        self.server_thread = None
        self.is_running = False
        
    def setup_routes(self):
        """Setup Flask routes for webhook endpoints."""
        
        @self.app.route('/webhook', methods=['GET'])
        def verify_webhook():
            """Verify webhook subscription with WhatsApp."""
            try:
                # Webhook verification
                mode = request.args.get('hub.mode')
                token = request.args.get('hub.verify_token')
                challenge = request.args.get('hub.challenge')
                
                self.logger.info(f"Webhook verification request: mode={mode}, token={token}")
                
                if self.api_handler:
                    verified_challenge = self.api_handler.verify_webhook(token, mode, challenge)
                    if verified_challenge:
                        self.signals.webhook_verified.emit(verified_challenge)
                        return verified_challenge
                
                self.signals.webhook_error.emit("verification", "Invalid verification token")
                return "Verification failed", 403
                
            except Exception as e:
                error_msg = f"Webhook verification error: {str(e)}"
                self.logger.error(error_msg)
                self.signals.webhook_error.emit("verification", error_msg)
                return "Internal error", 500
        
        @self.app.route('/webhook', methods=['POST'])
        def receive_webhook():
            """Receive and process webhook messages."""
            try:
                webhook_data = request.get_json()
                
                if not webhook_data:
                    return "Invalid data", 400
                
                self.logger.info(f"Received webhook: {json.dumps(webhook_data, indent=2)}")
                
                # Process the webhook data
                self._process_webhook_data(webhook_data)
                
                return "OK", 200
                
            except Exception as e:
                error_msg = f"Webhook processing error: {str(e)}"
                self.logger.error(error_msg)
                self.signals.webhook_error.emit("processing", error_msg)
                return "Internal error", 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'service': 'WhatsApp Webhook Handler',
                'running': self.is_running
            })
        
        @self.app.route('/status', methods=['GET'])
        def status_endpoint():
            """Status endpoint with detailed information."""
            return jsonify({
                'service': 'WhatsApp Webhook Handler',
                'running': self.is_running,
                'api_handler_configured': self.api_handler is not None,
                'virtual_assistant_configured': self.virtual_assistant is not None,
                'endpoints': WEBHOOK_ENDPOINTS
            })
    
    def _process_webhook_data(self, webhook_data: Dict[str, Any]):
        """Process incoming webhook data."""
        try:
            # Emit signal for raw webhook data
            self.signals.message_received.emit(webhook_data)
            
            # Process messages
            self._handle_messages(webhook_data)
            
            # Process status updates
            self._handle_status_updates(webhook_data)
            
        except Exception as e:
            self.logger.error(f"Error processing webhook data: {e}")
    
    def _handle_messages(self, webhook_data: Dict[str, Any]):
        """Handle incoming messages from webhook."""
        try:
            if not self.api_handler or not self.virtual_assistant:
                self.logger.warning("API handler or virtual assistant not configured")
                return
            
            # Process message using API handler
            message_data = self.api_handler.process_webhook_message(webhook_data)
            
            if not message_data:
                return
            
            user_id = message_data.get('from')
            message_text = message_data.get('text')
            message_type = message_data.get('type')
            
            if not user_id:
                return
            
            # Mark message as read
            if message_data.get('id'):
                self.api_handler.mark_message_read(message_data['id'])
            
            # Handle different message types
            if message_type == 'text' and message_text:
                self._handle_text_message(user_id, message_text, message_data)
            elif message_type == 'interactive':
                self._handle_interactive_message(user_id, message_data)
            elif message_type == 'button':
                self._handle_button_message(user_id, message_data)
            else:
                # Handle unsupported message types
                self._handle_unsupported_message(user_id, message_type, message_data)
                
        except Exception as e:
            self.logger.error(f"Error handling messages: {e}")
    
    def _handle_text_message(self, user_id: str, message_text: str, message_data: Dict[str, Any]):
        """Handle incoming text messages."""
        try:
            # Process message with virtual assistant
            response, metadata = self.virtual_assistant.process_message(
                user_id, message_text, message_data
            )
            
            # Send response back to user
            if response:
                success, result = self.api_handler.send_text_message(user_id, response)
                if not success:
                    self.logger.error(f"Failed to send response: {result}")
                else:
                    self.logger.info(f"Sent response to {user_id}: {response[:100]}...")
                    
                # Handle escalation if needed
                if metadata.get('escalated'):
                    self._handle_escalation(user_id, message_data, metadata)
                    
        except Exception as e:
            self.logger.error(f"Error handling text message: {e}")
            # Send fallback message
            self._send_fallback_message(user_id)
    
    def _handle_interactive_message(self, user_id: str, message_data: Dict[str, Any]):
        """Handle incoming interactive messages (button/list replies)."""
        try:
            interactive_data = message_data.get('interactive', {})
            interactive_type = interactive_data.get('type')
            
            if interactive_type == 'button_reply':
                button_id = interactive_data.get('button_reply', {}).get('id')
                button_title = interactive_data.get('button_reply', {}).get('title')
                
                # Process button selection
                response = self._process_button_selection(user_id, button_id, button_title)
                
            elif interactive_type == 'list_reply':
                list_id = interactive_data.get('list_reply', {}).get('id')
                list_title = interactive_data.get('list_reply', {}).get('title')
                
                # Process list selection
                response = self._process_list_selection(user_id, list_id, list_title)
                
            else:
                response = WEBHOOK_RESPONSES['SELECTION_DEFAULT']
            
            # Send response
            if response:
                self.api_handler.send_text_message(user_id, response)
                
        except Exception as e:
            self.logger.error(f"Error handling interactive message: {e}")
            self._send_fallback_message(user_id)
    
    def _handle_button_message(self, user_id: str, message_data: Dict[str, Any]):
        """Handle incoming button messages."""
        try:
            button_data = message_data.get('button', {})
            button_text = button_data.get('text', '')
            button_payload = button_data.get('payload', '')
            
            # Process button press as text message
            if button_text:
                self._handle_text_message(user_id, button_text, message_data)
            
        except Exception as e:
            self.logger.error(f"Error handling button message: {e}")
            self._send_fallback_message(user_id)
    
    def _handle_unsupported_message(self, user_id: str, message_type: str, message_data: Dict[str, Any]):
        """Handle unsupported message types."""
        try:
            response = WEBHOOK_RESPONSES['UNSUPPORTED_MEDIA'].format(message_type=message_type)
            self.api_handler.send_text_message(user_id, response)
            
        except Exception as e:
            self.logger.error(f"Error handling unsupported message: {e}")
    
    def _process_button_selection(self, user_id: str, button_id: str, button_title: str) -> str:
        """Process button selection and return appropriate response."""
        # Handle contact button separately since it needs dynamic content
        if button_id == 'contact' and self.virtual_assistant and hasattr(self.virtual_assistant, 'business_info'):
            try:
                business_info = self.virtual_assistant.business_info
                phone = business_info.get('contact', {}).get('phone', '')
                email = business_info.get('contact', {}).get('email', '')
                return f"You can reach us at {phone} or {email}. How else can I help?"
            except (KeyError, AttributeError):
                return "Please contact us for more information. How else can I help?"
        
        # Standard button responses
        button_responses = {
            'services': WEBHOOK_RESPONSES['SERVICES'],
            'pricing': WEBHOOK_RESPONSES['PRICING'], 
            'support': WEBHOOK_RESPONSES['SUPPORT'],
            'human': WEBHOOK_RESPONSES['HUMAN']
        }
        
        return button_responses.get(button_id, f"Thanks for selecting '{button_title}'. How can I help you with this?")
    
    def _process_list_selection(self, user_id: str, list_id: str, list_title: str) -> str:
        """Process list selection and return appropriate response."""
        # Similar to button processing but for list items
        return f"You selected '{list_title}'. Let me help you with that. What specific information do you need?"
    
    def _handle_escalation(self, user_id: str, message_data: Dict[str, Any], metadata: Dict[str, Any]):
        """Handle escalation to human agents."""
        try:
            # Here you would integrate with your ticketing system, CRM, or agent dashboard
            self.logger.info(f"Escalating conversation for user {user_id}: {metadata.get('escalation_reason')}")
            
            # Send escalation notification to internal systems
            # This could be via email, Slack, database, etc.
            
        except Exception as e:
            self.logger.error(f"Error handling escalation: {e}")
    
    def _handle_status_updates(self, webhook_data: Dict[str, Any]):
        """Handle status updates from webhook."""
        try:
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        statuses = value.get('statuses', [])
                        
                        for status in statuses:
                            self.signals.status_received.emit(status)
                            self.logger.debug(f"Message status update: {status}")
                            
        except Exception as e:
            self.logger.error(f"Error handling status updates: {e}")
    
    def _send_fallback_message(self, user_id: str):
        """Send a fallback message when processing fails."""
        try:
            self.api_handler.send_text_message(user_id, WEBHOOK_RESPONSES['FALLBACK'])
        except Exception as e:
            self.logger.error(f"Error sending fallback message: {e}")
    
    def start_server(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Start the webhook server."""
        try:
            if self.is_running:
                self.logger.warning("Webhook server is already running")
                return
            
            self.is_running = True
            
            def run_server():
                try:
                    self.app.run(host=host, port=port, debug=debug, use_reloader=False)
                except Exception as e:
                    self.logger.error(f"Webhook server error: {e}")
                    self.is_running = False
            
            self.server_thread = Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"WhatsApp webhook server started on {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Error starting webhook server: {e}")
            self.is_running = False
    
    def stop_server(self):
        """Stop the webhook server."""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            
            # Note: In production, you'd want a more graceful shutdown
            self.logger.info("WhatsApp webhook server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping webhook server: {e}")
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get webhook server status."""
        return {
            'running': self.is_running,
            'thread_active': self.server_thread and self.server_thread.is_alive() if self.server_thread else False,
            'endpoints_configured': True,
            'handlers_configured': {
                'api_handler': self.api_handler is not None,
                'virtual_assistant': self.virtual_assistant is not None
            }
        } 