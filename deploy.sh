#!/bin/bash

# Crow's Eye API - Google Cloud Run Deployment Script
# This script deploys the Crow's Eye API to Google Cloud Run

set -e

echo "🚀 Starting Crow's Eye API deployment to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project is set
PROJECT_ID=$(gcloud config get-value project)
if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ No Google Cloud project set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy
echo "🏗️  Building and deploying container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/crow-eye-api

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy crow-eye-api \
  --image gcr.io/$PROJECT_ID/crow-eye-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300

# Get the service URL
SERVICE_URL=$(gcloud run services describe crow-eye-api --platform managed --region us-central1 --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 API URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Update your web app's API_URL to: $SERVICE_URL"
echo "2. Test the API: curl $SERVICE_URL/health"
echo "3. Deploy your web app to Firebase"
echo ""
echo "💡 The API will scale to zero when not in use (free tier friendly)"
echo "   and automatically scale up when requests come in." 