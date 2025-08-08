#!/bin/bash

# WhisperX Cloud Run Deployment Script
# This script deploys the WhisperX microservice to Google Cloud Run

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"the-project-id"}
SERVICE_NAME="whisperx-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
SERVICE_ACCOUNT="whisperx-service@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying WhisperX Cloud Run Microservice${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Authenticate with Google Cloud
echo -e "${YELLOW}🔐 Authenticating with Google Cloud...${NC}"
gcloud auth login --no-launch-browser

# Set project
echo -e "${YELLOW}📁 Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create service account if it doesn't exist
echo -e "${YELLOW}👤 Creating service account...${NC}"
gcloud iam service-accounts create whisperx-service \
    --display-name="WhisperX Service Account" \
    --description="Service account for WhisperX Cloud Run service" \
    || echo "Service account already exists"

# Grant necessary permissions
echo -e "${YELLOW}🔑 Granting permissions...${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/monitoring.metricWriter"

# Build and push Docker image
echo -e "${YELLOW}🐳 Building and pushing Docker image...${NC}"
docker build -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --service-account=${SERVICE_ACCOUNT} \
    --memory=4Gi \
    --cpu=2 \
    --max-instances=10 \
    --min-instances=0 \
    --timeout=900 \
    --concurrency=80 \
    --port=8000 \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="MODEL_SIZE=large-v2" \
    --set-env-vars="MAX_AUDIO_DURATION=300" \
    --set-env-vars="ENABLE_GPU=false" \
    --set-env-vars="LOG_LEVEL=INFO"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📚 API Documentation: ${SERVICE_URL}/docs${NC}"
echo -e "${GREEN}❤️  Health Check: ${SERVICE_URL}/health${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
curl -f ${SERVICE_URL}/health || echo -e "${RED}❌ Health check failed${NC}"

echo -e "${GREEN}🎉 WhisperX Cloud Run Microservice is now live!${NC}" 