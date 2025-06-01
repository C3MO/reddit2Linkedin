import praw
import json
from datetime import datetime, timedelta
import os
import requests
import secrets
import base64
import hashlib
import webbrowser
import time
from dotenv import load_dotenv, set_key, find_dotenv
from oauth_server import start_oauth_server

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

def get_linkedin_profile(access_token):
    """Get LinkedIn profile information to verify Person URN"""
    api_url = "https://api.linkedin.com/v2/people/~"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            profile_data = response.json()
            person_id = profile_data.get('id')
            if person_id:
                print(f"Your LinkedIn Person ID: {person_id}")
                print(f"Correct Person URN: urn:li:person:{person_id}")
                
                # Save the correct URN to .env
                env_path = find_dotenv()
                set_key(env_path, 'LINKEDIN_PERSON_URN', f"urn:li:person:{person_id}")
                
                return f"urn:li:person:{person_id}"
            else:
                print("Could not get person ID from profile")
                return None
        else:
            print(f"Failed to get profile: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting LinkedIn profile: {e}")
        return None

def post_to_linkedin(title, url, access_token):
    """Post to LinkedIn using the API"""
    # First, get the correct Person URN
    correct_urn = get_linkedin_profile(access_token)
    if not correct_urn:
        # Fall back to the URN from .env, but fix the format
        person_urn = os.getenv('LINKEDIN_PERSON_URN')
        if person_urn and person_urn.startswith('urn:li:person:'):
            correct_urn = person_urn
        else:
            correct_urn = f"urn:li:person:{person_urn}" if person_urn else None
    
    if not correct_urn:
        print("Error: Could not determine LinkedIn Person URN")
        return
    
    print(f"Using Person URN: {correct_urn}")
    
    api_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    payload = {
        "author": correct_urn,
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
        },        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    print(f"Payload author field: {payload['author']}")
    
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully posted to LinkedIn!")
        return True
    else:
        print(f"LinkedIn post failed: {response.status_code} - {response.text}")
        return False

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
          # Show summary
        history = load_posted_history()
        remaining_posts = len([p for p in posts if not is_post_already_posted(p['id'], history)])
        print(f"Total posts: {len(posts)} | New posts: {remaining_posts}")
        
        if remaining_posts > 0:
            print("\nTo start automated posting, run:")
            print("   python reddit_fetcher.py schedule")
            print("\nTo post a single post now, run:")
            print("   python reddit_fetcher.py post")
    
    except Exception as e:
        print(f"Error: {str(e)}")

def load_posted_history():
    """Load the history of already posted content"""
    try:
        with open('posted_history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"posted_ids": [], "last_posted": None}
    except Exception as e:
        print(f"Error loading posted history: {e}")
        return {"posted_ids": [], "last_posted": None}

def save_posted_history(history):
    """Save the history of posted content"""
    try:
        with open('posted_history.json', 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving posted history: {e}")

def is_post_already_posted(post_id, history):
    """Check if a post has already been posted"""
    return post_id in history.get("posted_ids", [])

def mark_post_as_posted(post_id, history):
    """Mark a post as posted"""
    if "posted_ids" not in history:
        history["posted_ids"] = []
    if post_id not in history["posted_ids"]:
        history["posted_ids"].append(post_id)
        history["last_posted"] = datetime.utcnow().isoformat()

def get_next_post_to_share():
    """Get the next post to share from the stored posts"""
    try:
        # Load the posts
        with open('technews_posts.json', 'r') as f:
            posts = json.load(f)
        
        # Load posted history
        history = load_posted_history()
        
        # Filter posts that haven't been posted yet
        unposted_posts = [post for post in posts if not is_post_already_posted(post['id'], history)]
        
        if not unposted_posts:
            print("No new posts to share. All posts have been posted.")
            return None, history
        
        # Sort by score (most popular first) or by date (newest first)
        unposted_posts.sort(key=lambda x: x['score'], reverse=True)
        
        return unposted_posts[0], history
        
    except FileNotFoundError:
        print("No posts found. Run fetch_reddit_posts() first.")
        return None, load_posted_history()
    except Exception as e:
        print(f"Error getting next post: {e}")
        return None, load_posted_history()

def scheduled_post():
    """Post a single post to LinkedIn (called by scheduler)"""
    print(f"\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Checking for posts to share...")
    
    # Get next post to share
    post, history = get_next_post_to_share()
    
    if not post:
        return
    
    # Get access token
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        print("No LinkedIn access token found. Please run authentication first.")
        return
    
    # Post to LinkedIn
    print(f"Posting to LinkedIn: {post['title']}")
    success = post_to_linkedin(post['title'], post['url'], access_token)
    
    if success:
        # Mark as posted
        mark_post_as_posted(post['id'], history)
        save_posted_history(history)
        print(f"Successfully posted: {post['title']}")
        print(f"Post score: {post['score']} | Comments: {post['num_comments']}")
    else:
        print(f"Failed to post: {post['title']}")

def run_scheduler():
    """Run the posting scheduler"""
    try:
        import schedule
    except ImportError:
        print("Schedule library not found. Please install it with: pip install schedule")
        print("Alternatively, you can run manual_posting_loop() for a simple time-based loop")
        return
    
    print("Starting LinkedIn posting scheduler...")
    print("Posts will be shared every 3 hours")
    print("Press Ctrl+C to stop the scheduler\n")
    
    # Schedule the job every 3 hours
    schedule.every(3).hours.do(scheduled_post)
    
    # Also post immediately if there are unposted posts
    print("Checking for immediate post...")
    scheduled_post()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")

def manual_posting_loop():
    """Simple manual posting loop without external dependencies"""
    print("Starting simple posting loop...")
    print("Posts will be shared every 3 hours")
    print("Press Ctrl+C to stop\n")
    
    # Post immediately if there are unposted posts
    print("Checking for immediate post...")
    scheduled_post()
    
    try:
        while True:
            print(f"Sleeping for 3 hours... (next post at {(datetime.utcnow() + timedelta(hours=3)).strftime('%H:%M:%S')})")
            time.sleep(3 * 60 * 60)  # Sleep for 3 hours
            scheduled_post()
    except KeyboardInterrupt:
        print("\nPosting loop stopped by user")

def start_posting_bot():
    """Main function to start the posting bot"""
    print("LinkedIn Auto-Poster Bot")
    print("=" * 50)
    
    # Check if we have posts to work with
    try:
        with open('technews_posts.json', 'r') as f:
            posts = json.load(f)
        print(f"Found {len(posts)} posts in storage")
    except FileNotFoundError:
        print("No posts found. Fetching posts first...")
        fetch_reddit_posts()
        return
    
    # Check posted history
    history = load_posted_history()
    posted_count = len(history.get("posted_ids", []))
    remaining_posts = len([p for p in posts if not is_post_already_posted(p['id'], history)])
    
    print(f"Already posted: {posted_count}")
    print(f"Remaining to post: {remaining_posts}")
    
    if remaining_posts == 0:
        print("\nAll posts have been shared! Fetch new posts with fetch_reddit_posts()")
        return
    
    # Ask user which method to use
    print("\nChoose posting method:")
    print("1. Advanced scheduler (requires 'pip install schedule')")
    print("2. Simple time-based loop (no extra dependencies)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            run_scheduler()
        else:
            manual_posting_loop()
    except KeyboardInterrupt:
        print("\nGoodbye!")

def post_single():
    """Post a single post immediately"""
    print("Posting single post...")
    scheduled_post()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "schedule":
            start_posting_bot()
        elif command == "post":
            post_single()
        elif command == "fetch":
            fetch_reddit_posts()
        else:
            print("Available commands:")
            print("  python reddit_fetcher.py fetch    - Fetch new Reddit posts")
            print("  python reddit_fetcher.py post     - Post single post immediately")
            print("  python reddit_fetcher.py schedule - Start automated posting")
    else:
        # Default behavior - just fetch posts
        fetch_reddit_posts()
