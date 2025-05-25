# LinkedIn and X (Twitter) Integration Setup

This guide explains how to set up LinkedIn and X (Twitter) integration for the Breadsmith Marketing Tool.

## LinkedIn Setup

### 1. Create a LinkedIn Developer App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click "Create App"
3. Fill in the required information:
   - App name: "Breadsmith Marketing Tool"
   - LinkedIn Page: Your company page
   - App logo: Upload your logo
   - Legal agreement: Accept terms

### 2. Configure App Products

1. In your app dashboard, go to the "Products" tab
2. Add these products:
   - **Sign In with LinkedIn** (for authentication)
   - **Share on LinkedIn** (for posting content)

### 3. Set OAuth Redirect URLs

1. Go to the "Auth" tab
2. Add redirect URLs (for local development):
   - `http://localhost:8080/auth/linkedin/callback`
   - `http://127.0.0.1:8080/auth/linkedin/callback`

### 4. Get Your Credentials

1. Note down your **Client ID** and **Client Secret** from the "Auth" tab
2. You'll need to implement OAuth flow to get:
   - **Access Token** (with `r_liteprofile` and `w_member_social` scopes)
   - **Person ID** (from `/v2/people/~` endpoint)

### 5. Configure Credentials

1. Copy `linkedin_credentials_template.json` to `linkedin_credentials.json`
2. Fill in your actual credentials:

```json
{
  "access_token": "YOUR_ACTUAL_ACCESS_TOKEN",
  "person_id": "YOUR_ACTUAL_PERSON_ID"
}
```

## X (Twitter) Setup

### 1. Create a Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Apply for a developer account
3. Create a new project/app

### 2. Generate API Keys

1. In your app dashboard, go to "Keys and tokens"
2. Generate:
   - **API Key** (Consumer Key)
   - **API Secret** (Consumer Secret)
   - **Bearer Token**
   - **Access Token**
   - **Access Token Secret**

### 3. Set App Permissions

1. Go to "App permissions"
2. Set to **Read and Write** (required for posting)

### 4. Install Required Dependencies

The X integration requires OAuth 1.0a for media uploads:

```bash
pip install requests-oauthlib
```

### 5. Configure Credentials

1. Copy `x_credentials_template.json` to `x_credentials.json`
2. Fill in your actual credentials:

```json
{
  "bearer_token": "YOUR_ACTUAL_BEARER_TOKEN",
  "api_key": "YOUR_ACTUAL_API_KEY",
  "api_secret": "YOUR_ACTUAL_API_SECRET",
  "access_token": "YOUR_ACTUAL_ACCESS_TOKEN",
  "access_token_secret": "YOUR_ACTUAL_ACCESS_TOKEN_SECRET"
}
```

## Environment Variables (Alternative)

Instead of JSON files, you can set environment variables:

### LinkedIn
```bash
export LINKEDIN_ACCESS_TOKEN="your_access_token"
export LINKEDIN_PERSON_ID="your_person_id"
```

### X (Twitter)
```bash
export X_BEARER_TOKEN="your_bearer_token"
export X_API_KEY="your_api_key"
export X_API_SECRET="your_api_secret"
export X_ACCESS_TOKEN="your_access_token"
export X_ACCESS_TOKEN_SECRET="your_access_token_secret"
```

## Platform-Specific Features

### LinkedIn
- **Text-only posts**: Supported
- **Image posts**: Supported (max 20MB)
- **Video posts**: Supported (max 5GB)
- **Caption limit**: 3,000 characters
- **Media requirements**: Optional

### X (Twitter)
- **Text-only posts**: Supported
- **Image posts**: Supported (max 5MB)
- **Video posts**: Supported (max 512MB)
- **Caption limit**: 280 characters (auto-truncated)
- **Media requirements**: Optional

## Usage

Once configured, you can:

1. **Generate content** with AI (works without media for LinkedIn/X)
2. **Select platforms** in the posting dialog
3. **Post to multiple platforms** simultaneously
4. **Text-only posting** for LinkedIn and X (Instagram still requires media)

## Troubleshooting

### LinkedIn Issues
- Ensure your access token has the correct scopes
- Check that your app has "Share on LinkedIn" product enabled
- Verify your person ID is correct

### X Issues
- Make sure your app has Read and Write permissions
- Verify all 5 credentials are correct
- Check that requests-oauthlib is installed for media uploads

### General Issues
- Check the application logs for detailed error messages
- Verify your internet connection
- Ensure credentials files are in the root directory
- Check that JSON files are valid (no syntax errors)

## Security Notes

- Never commit credential files to version control
- Add `*_credentials.json` to your `.gitignore`
- Use environment variables in production
- Regularly rotate your API keys
- Monitor your API usage to avoid rate limits 