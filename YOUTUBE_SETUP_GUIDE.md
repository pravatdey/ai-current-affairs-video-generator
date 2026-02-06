# YouTube Auto-Upload Setup Guide

Follow these steps to enable automatic YouTube uploads for your UPSC Current Affairs videos.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `UPSC-Video-Uploader`
4. Click **Create**

## Step 2: Enable YouTube Data API v3

1. In your project, go to **APIs & Services** → **Library**
2. Search for **"YouTube Data API v3"**
3. Click on it and click **"Enable"**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **"External"** user type → Click **Create**
3. Fill in the form:
   - **App name**: `UPSC Video Uploader`
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **Save and Continue**
5. On **Scopes** page, click **Add or Remove Scopes**
6. Add these scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
7. Click **Save and Continue**
8. On **Test users** page, click **Add Users**
9. Add your Gmail address (the one linked to your YouTube channel)
10. Click **Save and Continue** → **Back to Dashboard**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Select **Application type**: **"Desktop app"**
4. Name: `UPSC Video Uploader Desktop`
5. Click **Create**
6. Click **"Download JSON"** button
7. **Save the file as**: `config/client_secrets.json` in your project folder

## Step 5: First-Time Authentication

Run this command to authenticate (only needed once):

```bash
python -m src.youtube.auth --auth
```

This will:
1. Open your browser
2. Ask you to sign in to your Google/YouTube account
3. Grant permissions to upload videos
4. Save the token for future use (no login needed again)

## Step 6: Test the Setup

Test that everything works:

```bash
python -m src.youtube.auth --info
```

You should see your channel name and subscriber count.

## Step 7: Start Automatic Uploads

Run the scheduler:

```bash
# Generate at 10 AM, Upload at 11 AM (IST)
python scheduler_auto.py --generate-time 10:00 --upload-time 11:00

# Or run once immediately to test
python scheduler_auto.py --run-now
```

---

## Troubleshooting

### "Access Denied" Error
- Make sure you added your email as a test user in OAuth consent screen
- Try revoking and re-authenticating: `python -m src.youtube.auth --revoke`

### "Quota Exceeded" Error
- YouTube API has daily limits (10,000 units)
- Each upload uses ~1,600 units
- You can upload ~6 videos per day with free quota

### "Channel not verified" for Thumbnails
- Custom thumbnails require channel verification
- Go to: https://www.youtube.com/verify
- Verify your phone number

### Token Expired
- Tokens auto-refresh, but if issues occur:
- Delete `config/youtube_token.json`
- Run `python -m src.youtube.auth --auth` again

---

## File Structure After Setup

```
config/
├── client_secrets.json    ← Downloaded from Google Cloud
├── youtube_token.json     ← Auto-created after first auth
├── settings.yaml          ← Your app settings
└── youtube_config.yaml    ← YouTube upload settings
```

---

## Security Notes

- **NEVER share** `client_secrets.json` or `youtube_token.json`
- Add these to `.gitignore`:
  ```
  config/client_secrets.json
  config/youtube_token.json
  ```
- These files give full access to your YouTube channel!
