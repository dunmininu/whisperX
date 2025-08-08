# Production Deployment Guide

## Overview

This guide walks you through deploying the WhisperX Cloud Run Microservice to Google Cloud Platform for production use.

## Prerequisites

- Google Cloud Platform account
- Google Cloud CLI (`gcloud`) installed and configured
- Docker installed
- Python 3.11 (for local testing)

## Step 1: Google Cloud Project Setup

### 1.1 Create or Select Project

```bash
# List existing projects
gcloud projects list

# Create new project (if needed)
gcloud projects create whisperx-microservice-123 --name="WhisperX Microservice"

# Set the project
gcloud config set project whisperx-microservice-123
```

### 1.2 Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

## Step 2: Service Account Setup

### 2.1 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create whisperx-service \
  --display-name="WhisperX Microservice Service Account"

# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:WhisperX Microservice" --format="value(email)")
echo "Service Account Email: $SA_EMAIL"
```

### 2.2 Assign Required Roles

```bash
# Assign Cloud Run Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

# Assign Storage Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin"

# Assign Pub/Sub Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/pubsub.admin"

# Assign Firestore Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/datastore.admin"

# Assign Logging Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/logging.admin"

# Assign Monitoring Admin role
gcloud projects add-iam-policy-binding whisperx-microservice-123 \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/monitoring.admin"
```

### 2.3 Download Service Account Key

```bash
# Create and download service account key
gcloud iam service-accounts keys create whisperx-service-key.json \
  --iam-account=$SA_EMAIL

# Verify the key was created
ls -la whisperx-service-key.json
```

**⚠️ Security Note:** Keep this key secure and never commit it to version control!

## Step 3: Cloud Storage Setup

### 3.1 Create Storage Bucket

```bash
# Create bucket for audio files
gsutil mb -l us-central1 gs://whisperx-audio-files-123

# Create bucket for temporary files
gsutil mb -l us-central1 gs://whisperx-temp-files-123

# List buckets to verify
gsutil ls
```

### 3.2 Set Bucket Permissions

```bash
# Make buckets publicly readable (for audio files)
gsutil iam ch allUsers:objectViewer gs://whisperx-audio-files-123

# Set lifecycle policy for temp files (delete after 7 days)
gsutil lifecycle set lifecycle.json gs://whisperx-temp-files-123
```

Create `lifecycle.json`:
```json
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "age": 7,
        "isLive": true
      }
    }
  ]
}
```

## Step 4: Environment Configuration

### 4.1 Create Production Environment File

Create `.env.production`:

```bash
# Application settings
DEBUG=false
ENVIRONMENT=production

# Server settings
HOST=0.0.0.0
PORT=8000

# Google Cloud settings
GOOGLE_CLOUD_PROJECT=whisperx-microservice-123
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
CLOUD_STORAGE_BUCKET=whisperx-audio-files-123

# WhisperX settings
MODEL_SIZE=large-v2
WHISPERX_MODEL_SIZE=large-v2
WHISPERX_DEVICE=cpu
WHISPERX_COMPUTE_TYPE=float16
MAX_AUDIO_DURATION=300
ENABLE_GPU=false
COMPUTE_TYPE=float16

# Processing settings
BATCH_SIZE=16
MAX_WORKERS=4

# Security settings
API_KEY_HEADER=X-API-Key
API_KEYS=["the-production-api-key-here"]

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis settings (if using Cloud Memorystore)
REDIS_URL=redis://10.0.0.3:6379

# File upload settings
MAX_FILE_SIZE=104857600
ALLOWED_AUDIO_FORMATS=["mp3","wav","m4a","flac","ogg"]

# Directory settings
TEMP_DIR=/app/temp
UPLOADS_DIR=/app/uploads
MODELS_DIR=/app/models

# CORS settings
ALLOWED_HOSTS=["*"]
```

## Step 5: Local Production Testing

### 5.1 Run Production Tests

```bash
# Make script executable
chmod +x scripts/test-production.sh

# Run production testing
./scripts/test-production.sh
```

### 5.2 Test Docker Build

```bash
# Build production Docker image
docker build -t whisperx-microservice:prod .

# Test the image locally
docker run -p 8000:8000 \
  -e DEBUG=false \
  -e ENVIRONMENT=production \
  whisperx-microservice:prod
```

## Step 6: Deploy to Cloud Run

### 6.1 Build and Push Docker Image

```bash
# Configure Docker for Google Cloud
gcloud auth configure-docker

# Build and push to Google Container Registry
docker build -t gcr.io/whisperx-microservice-123/whisperx-microservice:v1 .

docker push gcr.io/whisperx-microservice-123/whisperx-microservice:v1
```

### 6.2 Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy whisperx-microservice \
  --image gcr.io/whisperx-microservice-123/whisperx-microservice:v1 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars="DEBUG=false,ENVIRONMENT=production" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=whisperx-microservice-123" \
  --set-env-vars="CLOUD_STORAGE_BUCKET=whisperx-audio-files-123" \
  --set-env-vars="API_KEYS=[\"the-production-api-key-here\"]"
```

### 6.3 Get Service URL

```bash
# Get the service URL
gcloud run services describe whisperx-microservice \
  --platform managed \
  --region us-central1 \
  --format="value(status.url)"
```

## Step 7: Post-Deployment Testing

### 7.1 Health Check

```bash
# Test health endpoint
curl https://the-service-url/health
```

### 7.2 API Testing

```bash
# Test job creation
curl -X POST "https://the-service-url/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: the-production-api-key-here" \
  -d '{"audio_file": "gs://whisperx-audio-files-123/test.mp3", "model_size": "large-v2"}'
```

### 7.3 Upload Test Audio

```bash
# Upload test audio file
gsutil cp test-audio.mp3 gs://whisperx-audio-files-123/

# Test transcription
curl -X POST "https://the-service-url/api/v1/jobs/upload" \
  -H "X-API-Key: the-production-api-key-here" \
  -F "file=@test-audio.mp3" \
  -F "model_size=large-v2" \
  -F "enable_diarization=true"
```

## Step 8: Monitoring and Logging

### 8.1 View Logs

```bash
# View service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=whisperx-microservice" \
  --limit 50 \
  --format "value(timestamp,severity,textPayload)"
```

### 8.2 Monitor Performance

```bash
# Open Cloud Monitoring
gcloud monitoring dashboards list

# View service metrics
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com"
```

## Step 9: Security Hardening

### 9.1 API Key Management

```bash
# Generate secure API key
openssl rand -hex 32

# Update environment with new key
gcloud run services update whisperx-microservice \
  --region us-central1 \
  --set-env-vars="API_KEYS=[\"the-new-secure-api-key\"]"
```

### 9.2 Network Security

```bash
# Restrict to specific IPs (if needed)
gcloud run services update whisperx-microservice \
  --region us-central1 \
  --set-env-vars="ALLOWED_HOSTS=[\"the-domain.com\"]"
```

## Troubleshooting

### Common Issues

1. **Service won't start**: Check logs with `gcloud logging read`
2. **Permission denied**: Verify service account roles
3. **Out of memory**: Increase memory allocation
4. **Timeout errors**: Increase timeout settings

### Debug Commands

```bash
# Check service status
gcloud run services describe whisperx-microservice --region us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit 10

# Check IAM permissions
gcloud projects get-iam-policy whisperx-microservice-123
```

## Cost Optimization

### 8.1 Resource Optimization

```bash
# Scale down during low usage
gcloud run services update whisperx-microservice \
  --region us-central1 \
  --max-instances 5 \
  --min-instances 0
```

### 8.2 Monitoring Costs

```bash
# View cost breakdown
gcloud billing accounts list
gcloud billing projects describe whisperx-microservice-123
```

## Next Steps

1. Set up CI/CD pipeline
2. Configure custom domain
3. Set up monitoring alerts
4. Implement backup strategies
5. Plan for scaling

---

**📋 Quick Reference:**

- **Service URL**: `https://whisperx-microservice-xxxxx-uc.a.run.app`
- **API Key**: `the-production-api-key-here`
- **Storage Bucket**: `gs://whisperx-audio-files-123`
- **Project ID**: `whisperx-microservice-123`
- **Region**: `us-central1` 