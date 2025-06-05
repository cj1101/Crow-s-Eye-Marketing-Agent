"""
WhatsApp Business API handler for virtual help desk functionality.
Supports automated messaging, conversation management, and customer service.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class WhatsAppAPISignals(QObject):
    """Signals for WhatsApp API operations."""
    message_sent = Signal(str, dict)  # recipient, message_data
    message_received = Signal(str, str, dict)  # sender, message, metadata
    media_sent = Signal(str, dict)  # recipient, media_data
    media_received = Signal(str, dict)  # sender, media_data
    media_uploaded = Signal(str, str)  # file_path, media_id
    media_downloaded = Signal(str, str)  # media_id, file_path
    webhook_received = Signal(dict)  # webhook_data
    error_occurred = Signal(str, str)  # operation, error_message
    status_update = Signal(str)

class WhatsAppAPIHandler:
    """Handler for WhatsApp Business API operations."""
    
    def __init__(self):
        """Initialize the WhatsApp API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = WhatsAppAPISignals()
        self.credentials = {}
        self.base_url = "https://graph.facebook.com"
        self.api_version = "v18.0"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load WhatsApp Business API credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'whatsapp_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                # Try environment variables
                access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
                phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
                verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN')
                
                if access_token and phone_number_id:
                    self.credentials = {
                        'access_token': access_token,
                        'phone_number_id': phone_number_id,
                        'verify_token': verify_token or 'default_verify_token'
                    }
                    return True
                    
                self.logger.warning("WhatsApp credentials not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading WhatsApp credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save WhatsApp Business API credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'whatsapp_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("WhatsApp credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving WhatsApp credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the WhatsApp Business API connection."""
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                return False, "Access token or phone number ID not found"
            
            # Test with phone number info endpoint
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                display_name = data.get('display_phone_number', 'Unknown')
                return True, f"Connected to WhatsApp Business: {display_name}"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                return False, f"WhatsApp API error: {error_msg}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def send_text_message(self, recipient: str, message: str) -> Tuple[bool, str]:
        """
        Send a text message to a WhatsApp user.
        
        Args:
            recipient: Phone number in international format (e.g., 1234567890)
            message: Text message to send
            
        Returns:
            Tuple of (success, message_id or error)
        """
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("send_message", error_msg)
                return False, error_msg
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                
                self.signals.message_sent.emit(recipient, {
                    'message_id': message_id,
                    'message': message,
                    'type': 'text'
                })
                
                return True, message_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown send error')
                self.signals.error_occurred.emit("send_message", error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error sending WhatsApp message: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("send_message", error_msg)
            return False, error_msg
    
    def send_template_message(self, recipient: str, template_name: str, language_code: str = "en_US", 
                            components: Optional[List[Dict]] = None) -> Tuple[bool, str]:
        """
        Send a template message to a WhatsApp user.
        
        Args:
            recipient: Phone number in international format
            template_name: Name of the approved template
            language_code: Language code for the template
            components: Template components (header, body, buttons)
            
        Returns:
            Tuple of (success, message_id or error)
        """
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("send_template", error_msg)
                return False, error_msg
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual", 
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                
                self.signals.message_sent.emit(recipient, {
                    'message_id': message_id,
                    'template': template_name,
                    'type': 'template'
                })
                
                return True, message_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown template error')
                self.signals.error_occurred.emit("send_template", error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error sending WhatsApp template: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("send_template", error_msg)
            return False, error_msg
    
    def send_interactive_message(self, recipient: str, message_type: str, 
                               header_text: str, body_text: str, footer_text: str,
                               action_data: Dict) -> Tuple[bool, str]:
        """
        Send an interactive message (buttons, list, etc.) to a WhatsApp user.
        
        Args:
            recipient: Phone number in international format
            message_type: 'button' or 'list'
            header_text: Header text
            body_text: Main message body
            footer_text: Footer text
            action_data: Button or list action data
            
        Returns:
            Tuple of (success, message_id or error)
        """
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("send_interactive", error_msg)
                return False, error_msg
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "interactive",
                "interactive": {
                    "type": message_type,
                    "header": {
                        "type": "text",
                        "text": header_text
                    },
                    "body": {
                        "text": body_text
                    },
                    "footer": {
                        "text": footer_text
                    },
                    "action": action_data
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                
                self.signals.message_sent.emit(recipient, {
                    'message_id': message_id,
                    'type': 'interactive',
                    'interactive_type': message_type
                })
                
                return True, message_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown interactive error')
                self.signals.error_occurred.emit("send_interactive", error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error sending WhatsApp interactive message: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("send_interactive", error_msg)
            return False, error_msg
    
    def send_media_message(self, recipient: str, media_type: str, media_url: str = None, 
                          media_id: str = None, caption: str = None, filename: str = None) -> Tuple[bool, str]:
        """
        Send a media message (image, document, audio, video) to a WhatsApp user.
        
        Args:
            recipient: Phone number in international format
            media_type: Type of media ('image', 'document', 'audio', 'video')
            media_url: URL of the media file (if using URL)
            media_id: Media ID from uploaded media (if using uploaded media)
            caption: Optional caption for the media
            filename: Optional filename for documents
            
        Returns:
            Tuple of (success, message_id or error)
        """
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("send_media", error_msg)
                return False, error_msg
            
            if not media_url and not media_id:
                error_msg = "Either media_url or media_id must be provided"
                self.signals.error_occurred.emit("send_media", error_msg)
                return False, error_msg
            
            if media_type not in ['image', 'document', 'audio', 'video']:
                error_msg = f"Unsupported media type: {media_type}"
                self.signals.error_occurred.emit("send_media", error_msg)
                return False, error_msg
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            # Build media object
            media_obj = {}
            if media_id:
                media_obj['id'] = media_id
            elif media_url:
                media_obj['link'] = media_url
            
            # Add caption for supported media types
            if caption and media_type in ['image', 'document', 'video']:
                media_obj['caption'] = caption
            
            # Add filename for documents
            if filename and media_type == 'document':
                media_obj['filename'] = filename
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": media_type,
                media_type: media_obj
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                
                media_data = {
                    'message_id': message_id,
                    'type': media_type,
                    'media_url': media_url,
                    'media_id': media_id,
                    'caption': caption,
                    'filename': filename
                }
                
                self.signals.message_sent.emit(recipient, media_data)
                self.signals.media_sent.emit(recipient, media_data)
                
                return True, message_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown media error')
                self.signals.error_occurred.emit("send_media", error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error sending WhatsApp media message: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("send_media", error_msg)
            return False, error_msg
    
    def upload_media(self, file_path: str, media_type: str) -> Tuple[bool, str]:
        """
        Upload media file to WhatsApp and get media ID.
        
        Args:
            file_path: Path to the media file
            media_type: MIME type of the media file
            
        Returns:
            Tuple of (success, media_id or error)
        """
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("upload_media", error_msg)
                return False, error_msg
            
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                self.signals.error_occurred.emit("upload_media", error_msg)
                return False, error_msg
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/media"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}"
            }
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, media_type),
                    'messaging_product': (None, 'whatsapp'),
                    'type': (None, media_type)
                }
                
                response = requests.post(url, headers=headers, files=files, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                media_id = result.get('id')
                if media_id:
                    self.logger.info(f"Media uploaded successfully: {media_id}")
                    self.signals.media_uploaded.emit(file_path, media_id)
                    return True, media_id
                else:
                    error_msg = "No media ID returned from upload"
                    self.signals.error_occurred.emit("upload_media", error_msg)
                    return False, error_msg
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown upload error')
                self.signals.error_occurred.emit("upload_media", error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error uploading media: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("upload_media", error_msg)
            return False, error_msg
    
    def download_media(self, media_id: str, save_path: str = None) -> Tuple[bool, str]:
        """
        Download media from WhatsApp using media ID.
        
        Args:
            media_id: Media ID from received message
            save_path: Optional path to save the file
            
        Returns:
            Tuple of (success, file_path or error)
        """
        try:
            if not self.credentials.get('access_token'):
                error_msg = "WhatsApp not configured. Please set up credentials first."
                self.signals.error_occurred.emit("download_media", error_msg)
                return False, error_msg
            
            # First get media URL
            url = f"{self.base_url}/{self.api_version}/{media_id}"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Error getting media URL')
                self.signals.error_occurred.emit("download_media", error_msg)
                return False, error_msg
            
            media_info = response.json()
            media_url = media_info.get('url')
            mime_type = media_info.get('mime_type', 'application/octet-stream')
            
            if not media_url:
                error_msg = "No media URL found"
                self.signals.error_occurred.emit("download_media", error_msg)
                return False, error_msg
            
            # Download the actual media file
            media_response = requests.get(media_url, headers=headers, timeout=60)
            
            if media_response.status_code != 200:
                error_msg = "Failed to download media file"
                self.signals.error_occurred.emit("download_media", error_msg)
                return False, error_msg
            
            # Determine file path
            if not save_path:
                # Create downloads directory if it doesn't exist
                downloads_dir = os.path.join(const.ROOT_DIR, 'downloads', 'whatsapp')
                os.makedirs(downloads_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = self._get_extension_from_mime_type(mime_type)
                filename = f"whatsapp_media_{timestamp}_{media_id[:8]}{extension}"
                save_path = os.path.join(downloads_dir, filename)
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the file
            with open(save_path, 'wb') as f:
                f.write(media_response.content)
            
            self.logger.info(f"Media downloaded: {save_path}")
            self.signals.media_downloaded.emit(media_id, save_path)
            return True, save_path
            
        except Exception as e:
            error_msg = f"Error downloading media: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.error_occurred.emit("download_media", error_msg)
            return False, error_msg
    
    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Get file extension from MIME type."""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
            'audio/amr': '.amr',
            'audio/ogg': '.ogg',
            'video/mp4': '.mp4',
            'video/3gpp': '.3gp',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'text/plain': '.txt'
        }
        return mime_to_ext.get(mime_type, '.bin')
    
    def mark_message_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            if not self.credentials.get('access_token') or not self.credentials.get('phone_number_id'):
                return False
            
            url = f"{self.base_url}/{self.api_version}/{self.credentials['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error marking message as read: {e}")
            return False
    
    def process_webhook_message(self, webhook_data: Dict) -> Optional[Dict]:
        """
        Process incoming webhook message data.
        
        Args:
            webhook_data: Webhook payload from WhatsApp
            
        Returns:
            Processed message data or None
        """
        try:
            if 'entry' not in webhook_data:
                return None
            
            for entry in webhook_data['entry']:
                if 'changes' not in entry:
                    continue
                    
                for change in entry['changes']:
                    if change.get('field') != 'messages':
                        continue
                    
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    for message in messages:
                        message_type = message.get('type', '')
                        
                        # Extract message content based on type
                        text_content = ''
                        media_info = {}
                        
                        if message_type == 'text':
                            text_content = message.get('text', {}).get('body', '')
                        elif message_type in ['image', 'document', 'audio', 'video']:
                            media_data = message.get(message_type, {})
                            media_info = {
                                'media_id': media_data.get('id'),
                                'mime_type': media_data.get('mime_type'),
                                'sha256': media_data.get('sha256'),
                                'caption': media_data.get('caption', ''),
                                'filename': media_data.get('filename', '') if message_type == 'document' else ''
                            }
                            text_content = media_info.get('caption', f"[{message_type.upper()} MESSAGE]")
                        elif message_type == 'interactive':
                            interactive_data = message.get('interactive', {})
                            if interactive_data.get('type') == 'button_reply':
                                text_content = interactive_data.get('button_reply', {}).get('title', '')
                            elif interactive_data.get('type') == 'list_reply':
                                text_content = interactive_data.get('list_reply', {}).get('title', '')
                        
                        message_data = {
                            'id': message.get('id'),
                            'from': message.get('from'),
                            'timestamp': message.get('timestamp'),
                            'type': message_type,
                            'text': text_content,
                            'media': media_info,
                            'interactive': message.get('interactive', {}),
                            'button': message.get('button', {}),
                            'list_reply': message.get('list_reply', {}),
                            'context': message.get('context', {}),
                            'contacts': value.get('contacts', []),
                            'metadata': value.get('metadata', {})
                        }
                        
                        # Emit signal for message received
                        self.signals.message_received.emit(
                            message_data['from'], 
                            message_data['text'], 
                            message_data
                        )
                        
                        # Emit media signal if it's a media message
                        if message_type in ['image', 'document', 'audio', 'video'] and media_info:
                            self.signals.media_received.emit(message_data['from'], media_info)
                        
                        return message_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing webhook message: {e}")
            return None
    
    def verify_webhook(self, verify_token: str, mode: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription.
        
        Args:
            verify_token: Token from webhook verification
            mode: Verification mode
            challenge: Challenge string from Facebook
            
        Returns:
            Challenge string if verification successful, None otherwise
        """
        try:
            expected_token = self.credentials.get('verify_token', 'default_verify_token')
            
            if mode == 'subscribe' and verify_token == expected_token:
                self.logger.info("Webhook verified successfully")
                return challenge
            else:
                self.logger.warning(f"Webhook verification failed: mode={mode}, token={verify_token}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error verifying webhook: {e}")
            return None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the current configuration status."""
        return {
            'configured': bool(self.credentials.get('access_token') and self.credentials.get('phone_number_id')),
            'has_access_token': bool(self.credentials.get('access_token')),
            'has_phone_number_id': bool(self.credentials.get('phone_number_id')),
            'has_verify_token': bool(self.credentials.get('verify_token')),
            'api_version': self.api_version,
            'base_url': self.base_url
        }
    
    def logout(self) -> None:
        """Clear WhatsApp API credentials."""
        self.credentials = {}
        self.logger.info("WhatsApp API credentials cleared")
        self.signals.status_update.emit("Logged out from WhatsApp Business API") 