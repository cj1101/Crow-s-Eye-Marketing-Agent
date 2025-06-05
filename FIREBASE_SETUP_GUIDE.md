# 🔥 Firebase Authentication Setup Guide

## 🚨 **Current Issue**
Your Firebase configuration is using placeholder values instead of actual credentials, preventing user authentication.

## 📋 **Required Steps**

### 1. **Get Firebase Configuration**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `crows-eye-website`
3. Click the gear icon ⚙️ → **Project Settings**
4. Scroll down to **Your apps** section
5. If no web app exists, click **Add app** → **Web** 🌐
6. Register your app with name: "Crow's Eye Website"
7. Copy the configuration object

### 2. **Update Environment Variables**

Replace the placeholder values in `C:\Users\charl\CodingProjets\Crow's Eye Website\.env.local`:

```env
# Firebase Configuration for Crow's Eye Website
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=crows-eye-website.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=crows-eye-website
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=crows-eye-website.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789 # Your actual sender ID
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123 # Your actual app ID
```

### 3. **Enable Authentication Methods**

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Enable these providers:
   - ✅ **Email/Password**
   - ✅ **Google** (recommended)
   - ✅ **Anonymous** (for guest users)

### 4. **Configure Firestore Database**

1. Go to **Firestore Database** → **Create database**
2. Choose **Start in test mode** (for development)
3. Select your preferred location (us-central1 recommended)

### 5. **Set Up Security Rules**

Update Firestore security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Subscription data
    match /subscriptions/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Usage statistics
    match /usage/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 🔧 **Integration with Current Project**

### **User Authentication Flow**

The current project expects Firebase authentication. Here's how to integrate:

1. **Update Firebase Config** in the marketing tool:

```python
# src/config/firebase_config.py
FIREBASE_CONFIG = {
    "apiKey": "your-api-key-here",
    "authDomain": "crows-eye-website.firebaseapp.com", 
    "projectId": "crows-eye-website",
    "storageBucket": "crows-eye-website.appspot.com",
    "messagingSenderId": "your-sender-id",
    "appId": "your-app-id"
}
```

2. **Test Authentication**:

```bash
cd "C:\Users\charl\CodingProjets\breadsmith_marketing\social_media_tool_v5_noMeta_final"
python test_subscription_system.py
```

## 🧪 **Testing Steps**

1. **Update Firebase credentials** in the Crow's Eye Website
2. **Deploy the website** to test authentication
3. **Run the marketing tool** and try logging in
4. **Verify subscription features** work correctly

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **"Firebase app not initialized"**
   - Check that all environment variables are set correctly
   - Restart the development server

2. **"Auth domain not authorized"**
   - Add your domain to authorized domains in Firebase Console
   - Go to Authentication → Settings → Authorized domains

3. **"Permission denied"**
   - Check Firestore security rules
   - Ensure user is properly authenticated

### **Debug Commands:**

```bash
# Check Firebase project status
firebase projects:list

# Test Firebase connection
firebase auth:export users.json --project crows-eye-website

# Check environment variables
echo $NEXT_PUBLIC_FIREBASE_API_KEY
```

## 📞 **Next Steps**

1. **Get your actual Firebase configuration** from the console
2. **Update the .env.local file** with real values
3. **Test the authentication** in the Crow's Eye Website
4. **Run the marketing tool** to verify login works
5. **Contact me** if you need help with any step

## 🔐 **Security Notes**

- Never commit real Firebase keys to version control
- Use environment variables for all sensitive data
- Enable App Check for production
- Set up proper Firestore security rules
- Monitor authentication logs for suspicious activity

---

**Need Help?** The Firebase configuration is the key to fixing your login issue. Once you update the credentials, the subscription system should work perfectly! 