# Service Account Setup Guide

## Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
./scripts/setup-service-account.sh
```

This script will:
- ✅ Create the service account
- ✅ Assign all required roles
- ✅ Download the key file
- ✅ Verify the key file
- ✅ Provide security warnings

### Option 2: Manual Setup

If you prefer to do it manually:

```bash
# 1. Set the project
gcloud config set project THE_PROJECT_ID

# 2. Create service account
gcloud iam service-accounts create whisperx-service \
  --display-name="WhisperX Microservice Service Account"

# 3. Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:WhisperX Microservice" --format="value(email)")

# 4. Assign roles
gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/datastore.admin"

gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding THE_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/monitoring.admin"

# 5. Download the key file
gcloud iam service-accounts keys create whisperx-service-key.json \
  --iam-account=$SA_EMAIL
```

## Prerequisites

Before running the setup:

1. **Install Google Cloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from:
   # https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with Google Cloud**
   ```bash
   gcloud auth login
   ```

3. **Set the project**
   ```bash
   gcloud config set project THE_PROJECT_ID
   ```

## What You'll Get

After running the setup, you'll have:

- **Service Account**: `whisperx-service@THE_PROJECT_ID.iam.gserviceaccount.com`
- **Key File**: `whisperx-service-key.json` (in the project directory)
- **Permissions**: All necessary roles for Cloud Run, Storage, Pub/Sub, etc.

## Security Best Practices

### ⚠️ Important Security Notes

1. **Never commit the key file to version control**
   ```bash
   # Add to .gitignore
   echo "whisperx-service-key.json" >> .gitignore
   ```

2. **Store the key securely**
   - Use a password manager
   - Limit access to the key file
   - Rotate keys regularly

3. **For production, consider Workload Identity**
   - More secure than service account keys
   - No key files to manage
   - Automatic credential rotation

## Using the Key File

### In Docker Container

```dockerfile
# Copy the key file to the container
COPY whisperx-service-key.json /app/service-account.json

# Set environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
```

### In Cloud Run Deployment

```bash
# Deploy with the key file
gcloud run deploy whisperx-microservice \
  --image gcr.io/THE_PROJECT_ID/whisperx-microservice:v1 \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json"
```

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**
   ```bash
   # Check if you have the necessary permissions
   gcloud projects get-iam-policy THE_PROJECT_ID
   ```

2. **"Service account not found"**
   ```bash
   # List all service accounts
   gcloud iam service-accounts list
   ```

3. **"Invalid key file"**
   ```bash
   # Verify the key file
   python3 -c "import json; json.load(open('whisperx-service-key.json'))"
   ```

### Verification Commands

```bash
# Check if service account exists
gcloud iam service-accounts list --filter="displayName:WhisperX Microservice"

# Check assigned roles
gcloud projects get-iam-policy THE_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:whisperx-service@THE_PROJECT_ID.iam.gserviceaccount.com"

# Verify key file
ls -la whisperx-service-key.json
```

## Next Steps

After getting the service account key:

1. **Test locally**: `./scripts/test-production.sh`
2. **Deploy to Cloud Run**: Follow the [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
3. **Monitor**: Check Cloud Run logs and metrics

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/setup-service-account.sh` | Automated setup |
| `gcloud iam service-accounts list` | List service accounts |
| `gcloud projects get-iam-policy PROJECT_ID` | Check permissions |
| `ls -la whisperx-service-key.json` | Verify key file |

**Key File Location**: `./whisperx-service-key.json`
**Environment Variable**: `GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json` 