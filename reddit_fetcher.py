import praw
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    except Exception as e:
        print(f"Error fetching posts: {str(e)}")

if __name__ == "__main__":
    fetch_reddit_posts()
