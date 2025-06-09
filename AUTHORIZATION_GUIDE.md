# 🔐 Authorization Guide for Swagger UI

## ❌ **What You're Seeing (The Confusing Form):**
You're seeing a complex OAuth2 form with username, password, client_id, client_secret, etc.

## ✅ **What You Actually Need to Do:**

### **Step 1: Get Your Token**
1. Go to `POST /api/v1/users/` - Create user first
2. Go to `POST /api/v1/login/access-token` - Login
3. **Copy the `access_token` from the response**

### **Step 2: Authorize in Swagger UI**
1. Click the **"Authorize"** button at the top of Swagger UI
2. **IGNORE** the complex OAuth2 form
3. **Look for a simple text field** (might need to scroll down)
4. **Enter exactly:** `Bearer YOUR_ACCESS_TOKEN`
   - Replace `YOUR_ACCESS_TOKEN` with the actual token from Step 1
   - **Important:** Include the word "Bearer" followed by a space
5. Click **"Authorize"**
6. Click **"Close"**

### **Step 3: Test Upload First**
1. Go to `POST /api/v1/media/upload`
2. Click "Try it out"
3. **Choose a file** (image or video)
4. Add optional caption
5. Click "Execute"
6. **Copy the `id` number from the response** - this is your media ID!

### **Step 4: Use Media ID**
Now you can use that ID in endpoints like:
- `GET /api/v1/media/{media_id}` - Enter the ID you got from upload
- `POST /api/v1/ai/media/{media_id}/tags` - Enter the same ID
- `GET /api/v1/media/{media_id}/download` - Enter the same ID

## 🎯 **Example:**

If your access token is: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

Then enter in the authorization field: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

If your uploaded file returns: `{"id": 123, "filename": "..."}`

Then use `123` as your media_id in other endpoints.

## 🚨 **Common Mistakes:**
- ❌ Don't fill out the OAuth2 form with username/password
- ❌ Don't forget the word "Bearer" before your token
- ❌ Don't try to use media endpoints without uploading a file first
- ❌ Don't use quotes around the Bearer token

## ✅ **Correct Format:**
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzM4NTM2MjIzfQ.example_signature
``` 