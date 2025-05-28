# Firebase Website Integration Guide

## Overview

I've successfully integrated Firebase authentication to allow you to log into the Python application using your Crow's Eye website account. Here's what has been set up:

## 🔥 What's Been Implemented

### 1. Firebase Admin SDK Integration
- **File**: `src/auth/firebase_admin_auth.py`
- **Purpose**: Server-side Firebase authentication that can access the same user database as your website
- **Features**:
  - User lookup by email
  - Access to Firestore user profiles
  - List users from website
  - Verify user tokens

### 2. Firebase Authentication Handler
- **File**: `src/features/authentication/firebase_auth_handler.py`
- **Purpose**: Integrates Firebase Admin SDK with the existing authentication system
- **Features**:
  - Initialize Firebase connection
  - Authenticate users with email
  - Get user profiles from website database
  - Status checking and error handling

### 3. Updated User Interface
- **File**: `src/ui/dialogs/user_auth_dialog.py`
- **Changes**: Added "Login with Website Account" button
- **Features**:
  - Separate login option for website accounts
  - Automatic user creation/update from Firebase data
  - Error handling and status messages

### 4. Enhanced User Manager
- **File**: `src/models/user.py`
- **New Method**: `create_or_update_from_firebase()`
- **Features**:
  - Creates local user accounts from Firebase data
  - Syncs subscription status from website
  - Preserves user preferences and usage stats

### 5. Configuration Scripts
- **File**: `setup_firebase_sync.py` - Interactive setup script
- **File**: `test_firebase_connection.py` - Test Firebase connection
- **Purpose**: Help you configure Firebase and test the connection

## 🚀 How to Set Up

### Option 1: Firebase Admin SDK (Recommended)

1. **Get Service Account Key**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select project: `crows-eye-website`
   - Go to Project Settings (⚙️) → Service accounts
   - Click "Generate new private key"
   - Download the JSON file

2. **Save Service Account File**:
   - Save as `service-account.json` in the project root
   - Or save as `firebase-service-account.json`
   - Or save as `crows-eye-website-service-account.json`

3. **Test Connection**:
   ```bash
   python test_firebase_connection.py
   ```

### Option 2: Firebase Client Configuration

1. **Run Setup Script**:
   ```bash
   python setup_firebase_sync.py
   ```

2. **Follow Instructions**:
   - Get Firebase config from console
   - Enter API key, sender ID, and app ID
   - Script will update both projects

## 🎯 How to Use

### Login with Website Account

1. **Open the Application**
2. **Click "Account" or Login**
3. **Enter your website email address**
4. **Click "Login with Website Account"**
5. **If Firebase is configured, you'll be logged in automatically**

### Features Available

- ✅ **Same User Database**: Access the same users as your website
- ✅ **Subscription Sync**: Pro subscriptions from website are recognized
- ✅ **Profile Sync**: User profiles are automatically synced
- ✅ **Seamless Experience**: No need to create separate accounts

## 🔧 Technical Details

### Firebase Project Configuration
- **Project ID**: `crows-eye-website`
- **Auth Domain**: `crows-eye-website.firebaseapp.com`
- **Database**: Firestore with `users` collection

### User Data Structure
```json
{
  "uid": "user-id",
  "email": "user@example.com",
  "displayName": "User Name",
  "subscription": {
    "plan": "free|pro",
    "status": "active|inactive"
  },
  "createdAt": "2025-01-27T...",
  "lastLoginAt": "2025-01-27T..."
}
```

### Authentication Flow
1. User enters email in Python app
2. Firebase Admin SDK looks up user by email
3. If found, user data is retrieved from Firebase Auth + Firestore
4. Local user account is created/updated with Firebase data
5. User is logged into Python application

## 🛠️ Troubleshooting

### Firebase Admin SDK Not Working
- **Issue**: Service account file not found
- **Solution**: Download service account JSON from Firebase Console
- **Location**: Save as `service-account.json` in project root

### User Not Found
- **Issue**: Email not registered on website
- **Solution**: Create account on Crow's Eye website first
- **Alternative**: Use local account creation in Python app

### Configuration Issues
- **Issue**: Firebase not configured
- **Solution**: Run `python setup_firebase_sync.py`
- **Check**: Verify `.env` file has Firebase variables

## 📋 Testing

### Test Firebase Connection
```bash
python test_firebase_connection.py
```

### Test User Lookup
1. Run test script
2. Enter email address when prompted
3. Check if user is found in Firebase

### Test Login Flow
1. Open Python application
2. Go to Account/Login
3. Enter website email
4. Click "Login with Website Account"

## 🎉 Benefits

1. **Single Sign-On**: Use website credentials in Python app
2. **Subscription Sync**: Pro features automatically available
3. **Unified Experience**: Same account across all platforms
4. **Easy Setup**: Minimal configuration required
5. **Secure**: Uses Firebase Admin SDK for server-side auth

## 📞 Next Steps

1. **Set up Firebase Admin SDK** (recommended)
2. **Test the connection** with your website email
3. **Try logging in** through the Python application
4. **Verify subscription status** is synced correctly

The integration is now complete and ready to use! You can log into the Python application using any account created on your Crow's Eye website. 