# Crow's Eye API - Deployment Guide

This guide helps you deploy the Crow's Eye API to Google Cloud Run for free hosting.

## Prerequisites

1. **Google Cloud Account**: Create a free account at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install from [docker.com](https://www.docker.com/get-started)

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### Option 2: Manual Deployment

```bash
# 1. Set your project ID
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/crow-eye-api
gcloud run deploy crow-eye-api \
  --image gcr.io/YOUR_PROJECT_ID/crow-eye-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000
```

## Free Tier Limits

Google Cloud Run offers generous free tier:
- **2 million requests/month**
- **360,000 GB-seconds/month**
- **180,000 vCPU-seconds/month**
- **1 GB network egress/month**

The API is configured to scale to zero when not in use, so you only pay for actual usage.

## Configuration

After deployment, you'll get a URL like:
`https://crow-eye-api-xxxxx-uc.a.run.app`

Update your web app's environment variables:
```bash
# In your web app's .env.local or .env.production
NEXT_PUBLIC_API_URL=https://crow-eye-api-xxxxx-uc.a.run.app
```

## Alternative Free Hosting Options

If you prefer not to use Google Cloud:

### Railway (Recommended Alternative)
- Visit [railway.app](https://railway.app)
- Connect your GitHub repository
- Deploy with one click
- 500 hours/month free tier

### Render
- Visit [render.com](https://render.com)
- Connect your GitHub repository
- Free tier: 750 hours/month

### Fly.io
- Visit [fly.io](https://fly.io)
- Install flyctl CLI
- Run `fly deploy`
- Free tier: 160GB-hours/month

## Monitoring

After deployment, monitor your API:
```bash
# View logs
gcloud run services logs read crow-eye-api --region us-central1

# Check status
gcloud run services describe crow-eye-api --region us-central1
```

## Troubleshooting

### Common Issues

1. **Build fails**: Check Docker is running and you have sufficient permissions
2. **Deploy fails**: Ensure APIs are enabled and billing is set up (free tier)
3. **API not responding**: Check Cloud Run logs for errors

### Support

For issues, check:
- [Google Cloud Run documentation](https://cloud.google.com/run/docs)
- [FastAPI deployment guide](https://fastapi.tiangolo.com/deployment/) 