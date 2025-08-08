#!/bin/bash

# Service Account Setup Script for WhisperX Cloud Run Microservice
# This script creates a service account and downloads the key file

set -e

echo "🔐 Setting up Google Cloud Service Account"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "You are not authenticated with gcloud. Please run:"
    echo "gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No project is set. Please set a project first:"
    echo "gcloud config set project THE_PROJECT_ID"
    exit 1
fi

print_status "Using project: $PROJECT_ID"

# Step 1: Create Service Account
print_status "Step 1: Creating service account..."

# Check if service account already exists
if gcloud iam service-accounts list --filter="displayName:WhisperX Microservice" --format="value(email)" | grep -q .; then
    print_warning "Service account already exists"
    SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:WhisperX Microservice" --format="value(email)")
    print_status "Using existing service account: $SA_EMAIL"
else
    # Create new service account
    gcloud iam service-accounts create whisperx-service \
        --display-name="WhisperX Microservice Service Account" \
        --description="Service account for WhisperX Cloud Run Microservice"
    
    SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:WhisperX Microservice" --format="value(email)")
    print_success "Created service account: $SA_EMAIL"
fi

# Step 2: Assign Required Roles
print_status "Step 2: Assigning required roles..."

ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/pubsub.admin"
    "roles/datastore.admin"
    "roles/logging.admin"
    "roles/monitoring.admin"
)

for ROLE in "${ROLES[@]}"; do
    print_status "Assigning $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" \
        --quiet
done

print_success "All roles assigned successfully"

# Step 3: Download Service Account Key
print_status "Step 3: Downloading service account key..."

# Check if key file already exists
if [ -f "whisperx-service-key.json" ]; then
    print_warning "Key file already exists. Backing up..."
    mv whisperx-service-key.json whisperx-service-key.json.backup
fi

# Create new key file
gcloud iam service-accounts keys create whisperx-service-key.json \
    --iam-account=$SA_EMAIL

# Verify the key file
if [ -f "whisperx-service-key.json" ]; then
    print_success "Service account key downloaded successfully"
    
    # Verify JSON format
    if python3 -c "import json; json.load(open('whisperx-service-key.json'))" 2>/dev/null; then
        print_success "Key file is valid JSON"
    else
        print_error "Key file is not valid JSON"
        exit 1
    fi
    
    # Show key file info
    echo ""
    print_status "Key file details:"
    ls -la whisperx-service-key.json
    echo ""
    print_status "Key file location: $(pwd)/whisperx-service-key.json"
else
    print_error "Failed to download service account key"
    exit 1
fi

# Step 4: Security Warning
echo ""
print_warning "⚠️  SECURITY WARNING ⚠️"
echo "=================================="
echo "The service account key file contains sensitive credentials."
echo "Keep this file secure and never commit it to version control."
echo ""
echo "Recommended actions:"
echo "1. Add 'whisperx-service-key.json' to the .gitignore file"
echo "2. Store the key securely (e.g., in a password manager)"
echo "3. For production, consider using Workload Identity instead"
echo ""

# Step 5: Next Steps
print_success "Service account setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Use this key file in the Docker container"
echo "2. Set GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json"
echo "3. Deploy to Cloud Run using the deployment guide"
echo ""
echo "Run: ./scripts/deploy.sh for deployment instructions" 