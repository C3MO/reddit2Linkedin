#!/usr/bin/env python3
"""
Test script for LinkedIn OAuth authentication
Run this to test your LinkedIn OAuth setup before running the main application
"""

import os
from dotenv import load_dotenv
from reddit_fetcher import get_linkedin_access_token

def test_linkedin_auth():
    """Test LinkedIn authentication"""
    print("LinkedIn OAuth Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET', 'LINKEDIN_REDIRECT_URI']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease add these to your .env file")
        return False
    
    # Display current configuration
    print("Current LinkedIn configuration:")
    print(f"Client ID: {os.getenv('LINKEDIN_CLIENT_ID')}")
    print(f"Redirect URI: {os.getenv('LINKEDIN_REDIRECT_URI')}")
    print()
    
    # Test authentication
    print("Starting LinkedIn authentication test...")
    access_token = get_linkedin_access_token()
    
    if access_token:
        print("✅ LinkedIn authentication successful!")
        print(f"Access token received: {access_token[:20]}...")
        return True
    else:
        print("❌ LinkedIn authentication failed!")
        return False

if __name__ == "__main__":
    success = test_linkedin_auth()
    if success:
        print("\n🎉 Your LinkedIn OAuth setup is working correctly!")
        print("You can now run the main reddit_fetcher.py script")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your LinkedIn app is properly configured")
        print("2. Verify your redirect URI matches exactly in your LinkedIn app settings")
        print("3. Ensure your client ID and secret are correct")
        print("4. Check that your LinkedIn app has the 'w_member_social' permission")
