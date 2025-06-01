#!/usr/bin/env python3
"""
Simple OAuth callback server for LinkedIn authentication
This runs a temporary local server to handle the OAuth redirect
"""

import http.server
import socketserver
import urllib.parse as urlparse
import threading
import time
import webbrowser
from typing import Optional

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, auth_code_container=None, **kwargs):
        self.auth_code_container = auth_code_container
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Parse the query parameters
        parsed_path = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_path.query)
        
        # Extract the authorization code
        auth_code = query_params.get('code', [None])[0]
        error = query_params.get('error', [None])[0]
        
        if error:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
            <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>You can close this window.</p>
                </body>
            </html>
            """.encode())
            if self.auth_code_container is not None:
                self.auth_code_container['error'] = error
        elif auth_code:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
            </html>
            """.encode())
            if self.auth_code_container is not None:
                self.auth_code_container['code'] = auth_code
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
                <body>
                    <h1>No Authorization Code</h1>
                    <p>No authorization code was found in the callback.</p>
                    <p>You can close this window.</p>
                </body>
            </html>
            """.encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_oauth_server(port: int = 8080, timeout: int = 300) -> Optional[str]:
    """
    Start a temporary OAuth callback server
    
    Args:
        port: Port to listen on (default 8080)
        timeout: Timeout in seconds (default 5 minutes)
    
    Returns:
        Authorization code if successful, None if failed or timeout
    """
    auth_code_container = {}
    
    # Create handler with shared container
    def handler(*args, **kwargs):
        return OAuthCallbackHandler(*args, auth_code_container=auth_code_container, **kwargs)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"OAuth callback server started on http://localhost:{port}/callback")
            print(f"Waiting for authorization callback (timeout: {timeout} seconds)...")
            
            # Set timeout for the server
            httpd.timeout = 1  # Check every second
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                httpd.handle_request()
                
                # Check if we got a response
                if 'code' in auth_code_container:
                    print("Authorization code received!")
                    return auth_code_container['code']
                elif 'error' in auth_code_container:
                    print(f"Authorization failed: {auth_code_container['error']}")
                    return None
            
            print("Timeout waiting for authorization callback")
            return None
            
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Error: Port {port} is already in use. Try a different port.")
        else:
            print(f"Error starting server: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Test the server
    code = start_oauth_server()
    if code:
        print(f"Received authorization code: {code}")
    else:
        print("Failed to receive authorization code")
