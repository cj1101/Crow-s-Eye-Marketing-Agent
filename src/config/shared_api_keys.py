"""
Shared API Keys Configuration
Provides default API keys for users who don't have their own.
"""

# Shared Gemini API Key for all users
# This allows users to use the application without setting up their own API keys
# Users can still override this by setting their own GEMINI_API_KEY environment variable
SHARED_GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Replace with your actual API key

# Shared Google API Key for Veo video generation
# Users can override by setting GOOGLE_API_KEY environment variable
SHARED_GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"  # Replace with your actual API key

def get_gemini_api_key():
    """
    Get the Gemini API key, preferring user's own key over shared key.
    
    Returns:
        str: The API key to use
    """
    import os
    
    # First check if user has their own key
    user_key = os.getenv("GEMINI_API_KEY")
    if user_key and user_key != "your_gemini_api_key_here":
        return user_key
    
    # Fall back to shared key
    return SHARED_GEMINI_API_KEY

def get_google_api_key():
    """
    Get the Google API key for Veo, preferring user's own key over shared key.
    
    Returns:
        str: The API key to use
    """
    import os
    
    # First check if user has their own key
    user_key = os.getenv("GOOGLE_API_KEY")
    if user_key and user_key != "your_google_api_key_here":
        return user_key
    
    # Fall back to shared key
    return SHARED_GOOGLE_API_KEY

def is_using_shared_key(service="gemini"):
    """
    Check if the application is using a shared key vs user's own key.
    
    Args:
        service: Either "gemini" or "google"
        
    Returns:
        bool: True if using shared key, False if using user's own key
    """
    import os
    
    if service == "gemini":
        user_key = os.getenv("GEMINI_API_KEY")
        return not (user_key and user_key != "your_gemini_api_key_here")
    elif service == "google":
        user_key = os.getenv("GOOGLE_API_KEY")
        return not (user_key and user_key != "your_google_api_key_here")
    
    return True 