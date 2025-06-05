"""
Simple OAuth callback server for handling authentication redirects.
This server runs locally to capture OAuth callback URLs from Meta platforms.
"""
import os
import json
import logging
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks."""
    
    def do_GET(self):
        """Handle GET requests (OAuth callbacks)."""
        try:
            # Parse the URL and query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Determine which platform this callback is for
            if '/auth/callback' in self.path:
                self._handle_meta_callback(query_params)
            else:
                self._send_error_response("Unknown callback path")
                
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            self._send_error_response(f"Error: {str(e)}")
    
    def _handle_meta_callback(self, query_params):
        """Handle Meta OAuth callback."""
        try:
            from .oauth_handler import oauth_handler
            
            # Reconstruct the full callback URL
            callback_url = f"https://localhost:8080{self.path}"
            
            # Handle the callback
            success = oauth_handler.handle_callback(callback_url)
            
            if success:
                self._send_success_response("Meta", "Successfully connected to Meta! You can close this window.")
            else:
                self._send_error_response("Failed to connect to Meta. Please try again.")
                
        except Exception as e:
            logger.error(f"Error handling Meta callback: {e}")
            self._send_error_response(f"Meta connection error: {str(e)}")
    
    def _send_success_response(self, platform: str, message: str):
        """Send a success response page."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{platform} Connection Successful</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #8B5A9F 0%, #6D28D9 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                .success-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    margin: 0 0 20px 0;
                    font-size: 28px;
                }}
                p {{
                    margin: 0;
                    font-size: 18px;
                    opacity: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>{platform} Connected!</h1>
                <p>{message}</p>
            </div>
            <script>
                // Auto-close after 3 seconds
                setTimeout(() => {{
                    window.close();
                }}, 3000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _send_error_response(self, error_message: str):
        """Send an error response page."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                .error-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    margin: 0 0 20px 0;
                    font-size: 28px;
                }}
                p {{
                    margin: 0;
                    font-size: 18px;
                    opacity: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">❌</div>
                <h1>Connection Error</h1>
                <p>{error_message}</p>
            </div>
            <script>
                // Auto-close after 5 seconds
                setTimeout(() => {{
                    window.close();
                }}, 5000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass

class OAuthCallbackServer:
    """Simple OAuth callback server."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the callback server."""
        if self.server is not None:
            logger.warning("OAuth callback server is already running")
            return
            
        try:
            self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"OAuth callback server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start OAuth callback server: {e}")
            
    def stop(self):
        """Stop the callback server."""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            if self.server_thread:
                self.server_thread.join(timeout=1)
                self.server_thread = None
            logger.info("OAuth callback server stopped")

# Global instance
oauth_callback_server = OAuthCallbackServer() 