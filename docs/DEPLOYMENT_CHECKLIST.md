# Deployment Checklist

## Pre-Deployment Checklist

### ✅ Google Cloud Setup
- [ ] Google Cloud account created
- [ ] `gcloud` CLI installed and authenticated
- [ ] Project created or selected
- [ ] Required APIs enabled:
  - [ ] Cloud Build API
  - [ ] Cloud Run API
  - [ ] Cloud Storage API
  - [ ] Pub/Sub API
  - [ ] Firestore API
  - [ ] Logging API
  - [ ] Monitoring API

### ✅ Service Account Setup
- [ ] Service account created: `whisperx-service`
- [ ] Roles assigned:
  - [ ] Cloud Run Admin
  - [ ] Storage Admin
  - [ ] Pub/Sub Admin
  - [ ] Firestore Admin
  - [ ] Logging Admin
  - [ ] Monitoring Admin
- [ ] Service account key downloaded: `whisperx-service-key.json`

### ✅ Cloud Storage Setup
- [ ] Audio files bucket created: `gs://whisperx-audio-files-123`
- [ ] Temp files bucket created: `gs://whisperx-temp-files-123`
- [ ] Bucket permissions configured
- [ ] Lifecycle policies set

### ✅ Local Testing
- [ ] Production dependencies installed
- [ ] Docker build successful
- [ ] Local production tests passed
- [ ] API endpoints working

## Deployment Steps

### 1. Environment Setup
```bash
# Set project
gcloud config set project THE_PROJECT_ID

# Verify authentication
gcloud auth list
```

### 2. Build and Push Image
```bash
# Build Docker image
docker build -t gcr.io/THE_PROJECT_ID/whisperx-microservice:v1 .

# Push to Google Container Registry
docker push gcr.io/THE_PROJECT_ID/whisperx-microservice:v1
```

### 3. Deploy to Cloud Run
```bash
gcloud run deploy whisperx-microservice \
  --image gcr.io/THE_PROJECT_ID/whisperx-microservice:v1 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars="DEBUG=false,ENVIRONMENT=production" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=THE_PROJECT_ID" \
  --set-env-vars="CLOUD_STORAGE_BUCKET=THE_BUCKET_NAME" \
  --set-env-vars="API_KEYS=[\"THE_API_KEY\"]"
```

### 4. Post-Deployment Verification
- [ ] Service URL obtained
- [ ] Health check passed: `curl https://THE_SERVICE_URL/health`
- [ ] API documentation accessible: `curl https://THE_SERVICE_URL/openapi.json`
- [ ] Test job creation endpoint
- [ ] Test file upload endpoint

## Configuration Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_CLOUD_PROJECT` | `the-project-id` | The GCP project ID |
| `CLOUD_STORAGE_BUCKET` | `gs://the-bucket-name` | Audio files bucket |
| `API_KEYS` | `["the-api-key"]` | API keys for authentication |
| `DEBUG` | `false` | Disable debug mode |
| `ENVIRONMENT` | `production` | Production environment |

## Security Checklist

### ✅ API Security
- [ ] Secure API key generated
- [ ] API key stored securely
- [ ] Rate limiting configured
- [ ] CORS settings appropriate

### ✅ Network Security
- [ ] Service account permissions minimal
- [ ] Bucket permissions appropriate
- [ ] No sensitive data in logs
- [ ] HTTPS enforced

### ✅ Monitoring
- [ ] Logging enabled
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Error tracking enabled

## Testing Checklist

### ✅ Functional Testing
- [ ] Health endpoint responds
- [ ] Job creation works
- [ ] File upload works
- [ ] Transcription processing works
- [ ] Error handling works

### ✅ Performance Testing
- [ ] Response times acceptable
- [ ] Memory usage within limits
- [ ] CPU usage reasonable
- [ ] Concurrent requests handled

### ✅ Security Testing
- [ ] API key authentication works
- [ ] Invalid requests rejected
- [ ] Rate limiting enforced
- [ ] CORS headers correct

## Troubleshooting Commands

```bash
# Check service status
gcloud run services describe whisperx-microservice --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=whisperx-microservice" --limit 20

# Check IAM permissions
gcloud projects get-iam-policy THE_PROJECT_ID

# Test health endpoint
curl https://THE_SERVICE_URL/health

# Test API endpoint
curl -X POST "https://THE_SERVICE_URL/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: THE_API_KEY" \
  -d '{"audio_file": "test.mp3", "model_size": "large-v2"}'
```

## Cost Monitoring

### ✅ Resource Optimization
- [ ] Memory allocation appropriate
- [ ] CPU allocation reasonable
- [ ] Max instances set correctly
- [ ] Min instances optimized

### ✅ Cost Tracking
- [ ] Billing alerts configured
- [ ] Cost breakdown monitored
- [ ] Resource usage tracked
- [ ] Optimization opportunities identified

## Quick Reference

**Service URL**: `https://whisperx-microservice-xxxxx-uc.a.run.app`
**API Key**: `the-production-api-key`
**Storage Bucket**: `gs://the-audio-bucket`
**Project ID**: `the-project-id`
**Region**: `us-central1`

## Emergency Procedures

### Service Down
1. Check Cloud Run service status
2. Review recent logs
3. Check resource usage
4. Restart service if needed

### Performance Issues
1. Scale up resources
2. Check for memory leaks
3. Optimize code
4. Add caching if needed

### Security Issues
1. Rotate API keys
2. Review access logs
3. Update permissions
4. Notify stakeholders 