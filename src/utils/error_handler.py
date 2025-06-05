"""
Error handler utility for API related errors.
"""
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def handle_api_error(response: Any, context: str = "API") -> Tuple[bool, str]:
    """
    Handle API error responses.
    
    Args:
        response: The response object from the API call
        context: Context string for the error message
        
    Returns:
        Tuple of (success_flag, error_message)
    """
    try:
        # Check if it's a requests Response object
        if hasattr(response, 'status_code') and hasattr(response, 'json'):
            if 200 <= response.status_code < 300:
                return True, ""
                
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', f"{context} error: HTTP {response.status_code}")
            except Exception:
                error_message = f"{context} error: HTTP {response.status_code}"
                
            logger.error(f"{context} error: {error_message}")
            return False, error_message
            
        # Default case for non-response objects
        return False, f"Invalid response object for {context}"
        
    except Exception as e:
        error_message = f"Error handling {context} response: {str(e)}"
        logger.exception(error_message)
        return False, error_message
        
def format_api_error(error: Exception, context: str = "API") -> str:
    """
    Format an exception into a user-friendly error message.
    
    Args:
        error: The exception
        context: Context string for the error message
        
    Returns:
        Formatted error message
    """
    if hasattr(error, 'response') and hasattr(error.response, 'json'):
        try:
            error_data = error.response.json()
            error_message = error_data.get('error', {}).get('message', str(error))
            return f"{context} error: {error_message}"
        except Exception:
            pass
    
    return f"{context} error: {str(error)}" 