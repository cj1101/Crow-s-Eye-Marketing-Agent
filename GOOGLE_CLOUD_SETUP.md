# Google Cloud Storage Setup Guide

## Prerequisites
1. Google Cloud Account with billing enabled
2. Google Cloud SDK installed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select an existing project
3. Note your **Project ID** (e.g., `my-social-media-tool-12345`)

## Step 2: Enable Required APIs

1. Go to **APIs & Services > Library**
2. Enable these APIs:
   - **Cloud Storage API**
   - **Cloud Resource Manager API**

## Step 3: Create Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click **"Create Service Account"**
3. Fill in details:
   - **Name**: `crow-eye-storage`
   - **Description**: `Service account for Crow Eye media storage`
4. Click **"Create and Continue"**
5. Grant these roles:
   - **Storage Admin** (for full bucket access)
   - **Storage Object Admin** (for file operations)
6. Click **"Done"**

## Step 4: Generate Service Account Key

1. Find your service account in the list
2. Click the **three dots (⋮) > Manage keys**
3. Click **"Add Key" > "Create new key"**
4. Choose **JSON** format
5. Download the JSON file
6. **IMPORTANT**: Keep this file secure and never commit it to version control

## Step 5: Create Storage Bucket

1. Go to **Cloud Storage > Buckets**
2. Click **"Create Bucket"**
3. Configure:
   - **Name**: Choose a globally unique name (e.g., `crow-eye-media-storage-12345`)
   - **Location**: Choose region closest to your users
   - **Storage class**: Standard
   - **Access control**: Uniform (recommended)
4. Click **"Create"**

## Step 6: Configure Environment

1. **Set environment variable for credentials:**
   ```bash
   # Windows PowerShell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"
   
   # Windows Command Prompt
   set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
   
   # Linux/Mac
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

2. **Update your .env file:**
   ```env
   # Google Cloud Configuration
   GOOGLE_CLOUD_PROJECT=your-project-id-here
   GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name-here
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
   ```

## Step 7: Install Dependencies

```bash
pip install google-cloud-storage
```

## Step 8: Test Configuration

Create a test script to verify everything works:

```python
from google.cloud import storage
import os

def test_gcs_connection():
    try:
        # Initialize client
        client = storage.Client()
        
        # List buckets to test connection
        buckets = list(client.list_buckets())
        print(f"✅ Connected! Found {len(buckets)} buckets:")
        for bucket in buckets:
            print(f"  - {bucket.name}")
            
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_gcs_connection()
```

## Security Best Practices

1. **Never commit credentials to version control**
2. **Use environment variables for sensitive data**
3. **Set up proper IAM permissions (principle of least privilege)**
4. **Enable bucket versioning for data protection**
5. **Consider using signed URLs for secure file access**

## Troubleshooting

### Common Issues:

1. **"Billing account disabled"**: Enable billing in Google Cloud Console
2. **"Permission denied"**: Check IAM roles and service account permissions
3. **"Bucket not found"**: Verify bucket name and project ID
4. **"Credentials not found"**: Check GOOGLE_APPLICATION_CREDENTIALS path

### Debug Commands:

```bash
# Check if credentials file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test gcloud authentication
gcloud auth list

# Test storage access
gsutil ls gs://your-bucket-name
``` 