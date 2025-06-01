import praw
import json
from datetime import datetime, timedelta
import os
import requests
import secrets
import base64
import hashlib
import webbrowser
from dotenv import load_dotenv, set_key, find_dotenv
from oauth_server import start_oauth_server

# Load environment variables
load_dotenv()

def get_linkedin_access_token():
    """Get LinkedIn access token using OAuth 2.0 with automatic browser flow"""
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        print("Error: Missing LinkedIn credentials in .env file")
        return None
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(16)
    
    # Step 1: Generate authorization URL
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=w_member_social&"
        f"state={state}"
    )
    
    auth_code = None
    
    # Handle different redirect URI types
    if redirect_uri.startswith("http://localhost:"):
        # Extract port from localhost redirect URI
        try:
            port = int(redirect_uri.split(':')[2].split('/')[0])
        except (IndexError, ValueError):
            port = 8080
        
        print(f"Starting OAuth callback server on port {port}...")
        print("Your browser will open automatically for LinkedIn authorization.")
        print("If it doesn't open automatically, please visit this URL:")
        print(f"{auth_url}\n")
        
        # Start the OAuth server in a separate thread and open browser
        import threading
        import time
        
        # Start server
        server_result = {'code': None}
        
        def server_worker():
            server_result['code'] = start_oauth_server(port=port, timeout=300)
        
        server_thread = threading.Thread(target=server_worker)
        server_thread.daemon = True
        server_thread.start()
        
        # Give server time to start
        time.sleep(1)
        
        # Open browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
        
        # Wait for server to complete
        server_thread.join(timeout=310)  # 5 minutes + buffer
        auth_code = server_result['code']
        
    elif redirect_uri == "urn:ietf:wg:oauth:2.0:oob":
        print("Using out-of-band flow:")
        print(f"Please visit this URL to authorize:\n{auth_url}")
        print("\nAfter authorization, LinkedIn will display an authorization code on the webpage.")
        print("Copy that code and paste it below.")
        auth_code = input("Enter the authorization code: ").strip()
        
    else:
        print(f"Please visit this URL to authorize:\n{auth_url}")
        print(f"\nAfter authorization, you'll be redirected to: {redirect_uri}")
        print("Copy the 'code' parameter from the redirect URL and paste it below.")
        print("Example: if redirected to 'http://example.com/callback?code=ABC123&state=xyz'")
        print("Then enter: ABC123")
        auth_code = input("Enter the authorization code: ").strip()
    
    if not auth_code:
        print("Error: No authorization code provided")
        return None
    
    # Step 2: Exchange code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    try:
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            print(f"Failed to get access token: {response.status_code} - {response.text}")
            return None
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token', '')
        
        if not access_token:
            print(f"Error: No access token in response: {token_data}")
            return None
        
        # Save tokens to .env
        env_path = find_dotenv()
        set_key(env_path, 'LINKEDIN_ACCESS_TOKEN', access_token)
        if refresh_token:
            set_key(env_path, 'LINKEDIN_REFRESH_TOKEN', refresh_token)
        
        print("Access token saved to .env")
        return access_token
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during token exchange: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during token exchange: {e}")
        return None

def post_to_linkedin(title, url, access_token):
    """Post to LinkedIn using the API"""
    api_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    payload = {
        "author": f"urn:li:person:{os.getenv('LINKEDIN_PERSON_URN')}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": f"{title}\n\nRead more: {url}"
                },
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Read the full article"
                        },
                        "originalUrl": url
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully posted to LinkedIn!")
    else:
        print(f"LinkedIn post failed: {response.status_code} - {response.text}")

def fetch_reddit_posts():
    try:
        # Initialize Reddit instance
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        # Calculate time 24 hours ago
        time_24h_ago = datetime.utcnow() - timedelta(hours=24)
        
        # Fetch posts from r/technews
        subreddit = reddit.subreddit('technews')
        posts = []
        
        for post in subreddit.new(limit=100):  # Limit to 100 posts max
            post_time = datetime.utcfromtimestamp(post.created_utc)
            if post_time > time_24h_ago:
                posts.append({
                    'title': post.title,
                    'author': str(post.author),
                    'score': post.score,
                    'url': post.url,
                    'created_utc': post.created_utc,
                    'id': post.id,
                    'num_comments': post.num_comments,
                    'content': post.selftext
                })
        
        # Save to JSON file
        with open('technews_posts.json', 'w') as f:
            json.dump(posts, f, indent=2)
        
        print(f"Successfully saved {len(posts)} posts to technews_posts.json")
        
        # Post first post to LinkedIn for testing
        if posts:
            access_token = os.getenv('LINKEDIN_ACCESS_TOKEN') or get_linkedin_access_token()
            if access_token:
                first_post = posts[0]
                print(f"Posting to LinkedIn: {first_post['title']}")
                post_to_linkedin(first_post['title'], first_post['url'], access_token)
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    fetch_reddit_posts()
