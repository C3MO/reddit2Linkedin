#!/usr/bin/env python3
"""
Usage examples and utilities for the Reddit to LinkedIn bot
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def show_status():
    """Show current bot status"""
    print("Reddit to LinkedIn Bot - Status")
    print("=" * 40)
    
    # Check posts
    try:
        with open('technews_posts.json', 'r') as f:
            posts = json.load(f)
        print(f"Available posts: {len(posts)}")
    except FileNotFoundError:
        print("Available posts: 0 (run fetch first)")
        posts = []
    
    # Check posted history
    try:
        with open('posted_history.json', 'r') as f:
            history = json.load(f)
        posted_count = len(history.get("posted_ids", []))
        last_posted = history.get("last_posted", "Never")
        if last_posted != "Never":
            last_posted = datetime.fromisoformat(last_posted).strftime("%Y-%m-%d %H:%M:%S")
    except FileNotFoundError:
        posted_count = 0
        last_posted = "Never"
    
    print(f"Posted count: {posted_count}")
    print(f"Last posted: {last_posted}")
    
    # Calculate remaining
    if posts:
        remaining = len([p for p in posts if p['id'] not in history.get("posted_ids", [])])
        print(f"Remaining to post: {remaining}")
    
    # Check LinkedIn credentials
    has_token = bool(os.getenv('LINKEDIN_ACCESS_TOKEN'))
    print(f"LinkedIn token: {'Available' if has_token else 'Missing'}")
    
    print("\n" + "=" * 40)

def show_next_posts(count=5):
    """Show the next posts that would be posted"""
    try:
        with open('technews_posts.json', 'r') as f:
            posts = json.load(f)
    except FileNotFoundError:
        print("No posts found. Run fetch first.")
        return
    
    try:
        with open('posted_history.json', 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"posted_ids": []}
    
    # Filter unposted posts
    unposted = [p for p in posts if p['id'] not in history.get("posted_ids", [])]
    
    if not unposted:
        print("No unposted content available.")
        return
    
    # Sort by score
    unposted.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Next {min(count, len(unposted))} posts to be shared:")
    print("-" * 60)
    
    for i, post in enumerate(unposted[:count], 1):
        print(f"{i}. {post['title'][:80]}...")
        print(f"   Score: {post['score']} | Comments: {post['num_comments']}")
        print(f"   URL: {post['url']}")
        print()

def reset_posted_history():
    """Reset the posted history (use with caution)"""
    confirm = input("This will reset all posting history. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        try:
            os.remove('posted_history.json')
            print("Posted history reset successfully.")
        except FileNotFoundError:
            print("No history file found.")
    else:
        print("Operation cancelled.")

def main():
    """Main interactive menu"""
    while True:
        print("\nReddit to LinkedIn Bot Manager")
        print("=" * 40)
        print("1. Show status")
        print("2. Show next posts to be shared")
        print("3. Reset posted history")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            show_status()
        elif choice == "2":
            count = input("How many posts to show? (default 5): ").strip()
            try:
                count = int(count) if count else 5
            except ValueError:
                count = 5
            show_next_posts(count)
        elif choice == "3":
            reset_posted_history()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
