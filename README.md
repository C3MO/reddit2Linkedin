# Reddit to LinkedIn Bot

This bot fetches posts from r/technews and automatically posts them to your LinkedIn profile every hour, with duplicate detection and automatic refetching.

## 🚀 Features

- ✅ Fetches posts from r/technews
- ✅ Posts to LinkedIn every hour automatically
- ✅ Duplicate post detection
- ✅ Automatically fetches new posts when current list is finished
- ✅ Tracks posting history
- ✅ Prioritizes posts by score (popularity)
- ✅ Simple management interface

## 📋 Setup Instructions

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test Authentication

Run the test script to verify your setup:
```bash
python test_linkedin_auth.py
```

## 🎯 Usage

### Basic Commands

**Fetch new posts from Reddit:**
```bash
python reddit_fetcher.py fetch
```

**Post a single post immediately:**
```bash
python reddit_fetcher.py post
```

**Start automated posting (every hour):**
```bash
python reddit_fetcher.py schedule
```

**Manage bot status and history:**
```bash
python bot_manager.py
```

### Automated Posting

The bot will:
1. Check for unposted content
2. Select the highest-scoring unposted article
3. Post it to LinkedIn
4. Mark it as posted to prevent duplicates
5. Wait 1 hour and repeat
6. Automatically fetch new posts when current list is exhausted

To start automated posting:
```bash
python reddit_fetcher.py schedule
```

You'll be asked to choose between:
1. **Advanced scheduler** (requires `pip install schedule`) - More precise timing
2. **Simple time loop** (no dependencies) - Basic 1-hour intervals

## 📊 Bot Management

Use the bot manager for easy status tracking:

```bash
python bot_manager.py
```

This provides:
- ✅ Current status overview
- 📝 Next posts to be shared
- 🔄 Reset posting history
- 📈 Statistics

## 📁 Files Overview

- `reddit_fetcher.py` - Main application
- `oauth_server.py` - Local OAuth callback server
- `test_linkedin_auth.py` - Authentication test script
- `bot_manager.py` - Bot status and management
- `technews_posts.json` - Fetched Reddit posts
- `posted_history.json` - Tracking of posted content
- `.env` - Environment variables (keep this file private!)

## 🔄 How Duplicate Detection Works

The bot maintains a `posted_history.json` file that tracks:
- ✅ Post IDs that have been shared
- 🕐 Timestamp of last posting
- 📊 Posting statistics

Each post has a unique Reddit ID, so the same article will never be posted twice.

## ⚙️ Posting Logic

1. **Priority**: Posts are sorted by Reddit score (upvotes - downvotes)
2. **Filtering**: Only posts from the last 24 hours are considered
3. **Deduplication**: Already posted content is skipped
4. **Scheduling**: Posts every hour automatically
5. **Auto-refresh**: Fetches new posts when current list is finished

## 🛠️ Troubleshooting

### Redirect URI Issues

**Problem**: "redirect_uri_mismatch" error

**Solution**: 
1. Make sure the redirect URI in your `.env` file exactly matches what's configured in your LinkedIn app
2. Check for extra spaces or typos
3. Use `http://localhost:8080/callback` (recommended) or `urn:ietf:wg:oauth:2.0:oob`

### No Posts to Share

**Problem**: "No new posts to share"

**Solution**: 
1. Run `python reddit_fetcher.py fetch` to get new posts
2. Check `python bot_manager.py` for status
3. Consider resetting history if needed

### LinkedIn API Errors

**Problem**: 422 error or posting failures

**Solution**: 
1. Check your LinkedIn Person URN format
2. Verify your access token is valid
3. Run `python test_linkedin_auth.py` to refresh tokens

## 🔒 Security Notes

- Keep your `.env` file private and never commit it to version control
- Your access tokens are stored in the `.env` file
- The OAuth server only runs temporarily during authentication
- Posted history is stored locally in JSON format

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.