#!/bin/bash

# Production Testing Script for WhisperX Cloud Run Microservice
# This script helps test the production setup locally before deployment

set -e

echo "🚀 WhisperX Production Testing Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Environment Setup
print_status "Step 1: Setting up production environment..."

# Create production .env file
cat > .env.prod << EOF
# Production Environment Settings
DEBUG=false
ENVIRONMENT=production

# Server settings
HOST=0.0.0.0
PORT=8000

# Google Cloud settings (will be set during deployment)
GOOGLE_CLOUD_PROJECT=the-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
CLOUD_STORAGE_BUCKET=the-audio-bucket

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
API_KEYS=["test-api-key-123"]

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis settings
REDIS_URL=redis://localhost:6379

# File upload settings
MAX_FILE_SIZE=104857600
ALLOWED_AUDIO_FORMATS=["mp3","wav","m4a","flac","ogg"]

# Directory settings
TEMP_DIR=/app/temp
UPLOADS_DIR=/app/uploads
MODELS_DIR=/app/models

# CORS settings
ALLOWED_HOSTS=["*"]
EOF

print_success "Production .env file created"

# Step 2: Install Production Dependencies
print_status "Step 2: Installing production dependencies..."

# Create production virtual environment
python3.11 -m venv venv-prod 2>/dev/null || print_warning "Python 3.11 not found, using current Python"
source venv-prod/bin/activate

# Install production requirements
pip install --upgrade pip
pip install -r requirements-prod.txt

print_success "Production dependencies installed"

# Step 3: Test Production Build
print_status "Step 3: Testing production Docker build..."

# Build Docker image
docker build -t whisperx-microservice:test .

print_success "Docker image built successfully"

# Step 4: Run Production Tests
print_status "Step 4: Running production tests..."

# Start the production server
print_status "Starting production server..."
export $(cat .env.prod | xargs)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test endpoints
print_status "Testing API endpoints..."

# Health check
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_success "Health check passed"
else
    print_error "Health check failed"
    exit 1
fi

# API documentation
if curl -s http://localhost:8000/openapi.json | grep -q "openapi"; then
    print_success "OpenAPI spec accessible"
else
    print_error "OpenAPI spec not accessible"
    exit 1
fi

# Test job creation
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{"audio_file": "test.mp3", "model_size": "large-v2"}')

if echo "$JOB_RESPONSE" | grep -q "job_id"; then
    print_success "Job creation endpoint working"
else
    print_warning "Job creation endpoint returned: $JOB_RESPONSE"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null || true

print_success "Production testing completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Set up Google Cloud Project"
echo "2. Create service account and download credentials"
echo "3. Create Cloud Storage bucket"
echo "4. Deploy to Cloud Run"
echo ""
echo "Run: ./scripts/deploy.sh for deployment instructions" 