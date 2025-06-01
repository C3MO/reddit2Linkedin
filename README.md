# Reddit to LinkedIn Bot

This bot fetches posts from r/technews and posts them to your LinkedIn profile.

## Setup Instructions

### 1. LinkedIn App Configuration

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app or use your existing app
3. In your app settings, go to the "Auth" tab
4. Set the redirect URI to one of these options:

   **Option A: Localhost (Recommended)**
   ```
   http://localhost:8080/callback
   ```
   
   **Option B: Out-of-band flow (Fallback)**
   ```
   urn:ietf:wg:oauth:2.0:oob
   ```

5. Make sure your app has the `w_member_social` permission

### 2. Environment Configuration

Update your `.env` file with the correct redirect URI:

For localhost redirect (recommended):
```env
LINKEDIN_REDIRECT_URI=http://localhost:8080/callback
```

For out-of-band flow:
```env
LINKEDIN_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
```

### 3. Test Authentication

Run the test script to verify your setup:
```bash
python test_linkedin_auth.py
```

This will:
- Check your environment variables
- Test the OAuth flow
- Verify you can get an access token

### 4. Run the Main Application

Once authentication is working:
```bash
python reddit_fetcher.py
```

## Troubleshooting

### Redirect URI Issues

**Problem**: "redirect_uri_mismatch" error

**Solution**: 
1. Make sure the redirect URI in your `.env` file exactly matches what's configured in your LinkedIn app
2. Check for extra spaces or typos
3. Use `http://localhost:8080/callback` (recommended) or `urn:ietf:wg:oauth:2.0:oob`

### Port Already in Use

**Problem**: "Port 8080 is already in use"

**Solution**: 
1. Change the port in your redirect URI (e.g., `http://localhost:8081/callback`)
2. Update both your `.env` file and LinkedIn app settings

### Browser Doesn't Open

**Problem**: Browser doesn't open automatically

**Solution**: 
1. Copy and paste the URL manually
2. The OAuth server will still capture the callback

### Out-of-Band Flow Not Working

**Problem**: OOB flow shows errors

**Solution**: 
1. Switch to localhost redirect URI method
2. Update your LinkedIn app redirect URI to `http://localhost:8080/callback`
3. Update your `.env` file accordingly

## Files Overview

- `reddit_fetcher.py` - Main application
- `oauth_server.py` - Local OAuth callback server
- `test_linkedin_auth.py` - Authentication test script
- `.env` - Environment variables (keep this file private!)

## Security Notes

- Keep your `.env` file private and never commit it to version control
- Your access tokens are stored in the `.env` file
- The OAuth server only runs temporarily during authentication
