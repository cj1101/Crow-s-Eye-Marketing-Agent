# Setting Up a Business Account for Meta Integration

This document provides step-by-step instructions for setting up a Meta Business Account and connecting it to the Breadsmith Marketing Tool. Following these steps will ensure your business can properly use all features of the tool including Instagram and Facebook integration.

## Prerequisites

Before you begin, make sure you have:

- A personal Facebook account (required to create and manage a Business account)
- Admin access to your business's Facebook Page (or ability to create one)
- Access to your business's Instagram account credentials
- The Breadsmith Marketing Tool installed and running

## Step 1: Create a Meta Business Account

1. **Visit Facebook Business Suite**
   - Go to [business.facebook.com](https://business.facebook.com/)
   - Click "Create Account" if you don't have a Business account

2. **Enter Business Information**
   - Enter your business name
   - Enter your name and work email address
   - Click "Submit"

3. **Verify Your Business Email**
   - Check your email for a verification message
   - Click the verification link
   - Complete the setup process

## Step 2: Connect Your Facebook Page

1. **Add Your Facebook Page**
   - In Business Manager, go to "Business Settings"
   - Select "Accounts" > "Pages"
   - Click "Add" > "Add a Page"
   - Search for your business's Facebook Page
   - Select it and click "Add Page"

2. **If You Don't Have a Facebook Page Yet**
   - Click "Create a Page" instead
   - Choose a business category
   - Enter your business details
   - Upload a profile picture and cover photo
   - Click "Create Page"

3. **Assign Admin Permissions**
   - Still in "Pages" settings, click on your page
   - Click "Assign People"
   - Add yourself as an Admin
   - Click "Save Changes"

## Step 3: Set Up Instagram Business Account

1. **Convert Personal Instagram to Business Account**
   - Open the Instagram app on your mobile device
   - Go to your profile and tap the hamburger menu (☰)
   - Tap "Settings and Privacy"
   - Tap "Account"
   - Scroll down and tap "Switch to Professional Account"
   - Select "Business" (not Creator)
   - Follow the prompts to complete setup

2. **Connect Instagram to Facebook Page**
   - During the Instagram Business setup, you'll be prompted to connect to a Facebook Page
   - Select the Facebook Page you added to Business Manager
   - Complete the connection process

3. **Verify Connection**
   - In Facebook Business Settings, go to "Accounts" > "Instagram Accounts"
   - You should see your Instagram account listed
   - If not, click "Add" > "Add Instagram Account" and follow the prompts

## Step 4: Create a Meta Developer Account

1. **Visit Meta for Developers**
   - Go to [developers.facebook.com](https://developers.facebook.com/)
   - Log in with your Facebook account

2. **Register as a Developer**
   - Click "Get Started" or "Register"
   - Follow the prompts to register your developer account
   - Verify your account if required

## Step 5: Create a Meta App

1. **Create a New App**
   - From the Meta for Developers dashboard, click "Create App"
   - Select "Business" as the app type
   - Enter your app name (e.g., "Breadsmith Marketing App")
   - Enter your contact email
   - Select your Business account
   - Click "Create App"

2. **Set Up the App**
   - On your new app's dashboard, navigate to "App Settings" > "Basic"
   - Fill in the required fields:
     - App Icon
     - Privacy Policy URL (point to your privacy policy)
     - Terms of Service URL (if available)
   - Click "Save Changes"

3. **Add Products to Your App**
   - From the left sidebar, click "Add Products"
   - Add the following products:
     - Instagram Basic Display
     - Instagram Graph API
     - Facebook Login
     - Pages API

## Step 6: Configure App Settings

1. **Set Up Facebook Login**
   - Navigate to "Products" > "Facebook Login" > "Settings"
   - Add the following to "Valid OAuth Redirect URIs":
     ```
     https://localhost:8000/auth/facebook/callback
     https://yourdomain.com/auth/facebook/callback
     ```
   - Click "Save Changes"

2. **Configure Instagram Graph API**
   - Navigate to "Products" > "Instagram Graph API"
   - Click "Getting Started"
   - Follow the instructions to connect your Instagram Business account

3. **Set App Permissions**
   - Navigate to "App Review" > "Permissions and Features"
   - Request the following permissions:
     - `instagram_basic`
     - `instagram_content_publish`
     - `instagram_manage_comments`
     - `instagram_manage_insights`
     - `pages_read_engagement`
   - For each permission, provide detailed explanation and screencast demos

## Step 7: Generate Access Tokens

1. **Generate a Page Access Token**
   - Navigate to "Tools" > "Graph API Explorer"
   - Select your app from the dropdown
   - Select your Facebook Page from the "User or Page" dropdown
   - In the Permissions field, add all the required permissions
   - Click "Generate Access Token"
   - Copy and save this token securely

2. **Get Your Instagram Business Account ID**
   - Still in Graph API Explorer
   - Enter the following query:
     ```
     GET /{your-page-id}?fields=instagram_business_account
     ```
   - Replace `{your-page-id}` with your Facebook Page ID
   - Click "Submit"
   - Copy the Instagram Business Account ID from the response

## Step 8: Configure Breadsmith Marketing Tool

1. **Open the Application**
   - Launch the Breadsmith Marketing Tool on your computer

2. **Navigate to Settings**
   - Click on "Settings" in the main menu
   - Select "API Configuration"

3. **Enter Meta API Credentials**
   - Enter the following information:
     - Facebook Page ID
     - Page Access Token
     - Instagram Business Account ID
   - Click "Save Credentials"

4. **Test the Connection**
   - Click "Test Connection"
   - If successful, you'll see a confirmation message
   - If unsuccessful, verify your credentials and try again

## Troubleshooting

### Common Issues and Solutions

1. **"Invalid OAuth Redirect URI" Error**
   - Ensure the redirect URIs in your app settings exactly match those used by the application
   - Check for trailing slashes or http vs https differences

2. **"Insufficient Permissions" Error**
   - Verify that all required permissions have been approved in App Review
   - Check that your access token includes all necessary permissions

3. **"Instagram Business Account Not Found" Error**
   - Verify that your Instagram account is properly converted to a Business account
   - Ensure it's connected to the correct Facebook Page

4. **Access Token Expired**
   - Generate a new long-lived access token
   - Update the token in your application settings

### Getting Help

If you encounter issues not covered here, please contact support:

- Email: support@breadsmithbakery.com
- Phone: (555) 123-4567
- In-app support: Click "Help" > "Contact Support"

## Next Steps

After successfully setting up your Meta Business Account and connecting it to the Breadsmith Marketing Tool, you can:

1. **Import Existing Content**
   - Pull in past posts and engagement data

2. **Set Up Content Calendar**
   - Create a posting schedule
   - Plan your content in advance

3. **Generate AI Captions**
   - Use the tool to create engaging captions for your posts

4. **Monitor Analytics**
   - Track performance of your social media content
   - Optimize based on engagement metrics 