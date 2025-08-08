# WhisperX Cloud Run Microservice

Advanced audio transcription and speaker diarization service built with FastAPI and deployed on Google Cloud Run.

## 🚀 Current Status

✅ **Development Environment**: Fully functional with mock services
✅ **API Documentation**: Available at `/docs` (when DEBUG=true)
✅ **Health Checks**: All endpoints working
✅ **Production Ready**: Docker configuration and deployment scripts ready

## 📋 Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd whisperX

# Set up development environment
chmod +x scripts/dev.sh
./scripts/dev.sh

# Start the development server
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🏗️ Architecture

### System Components

- **FastAPI Application**: RESTful API with async processing
- **WhisperX Service**: Audio transcription and speaker diarization
- **Mock Service**: Development-friendly alternative to heavy ML dependencies
- **Google Cloud Integration**: Storage, Pub/Sub, Firestore, Logging
- **Docker Containerization**: Production-ready containerization

### Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Audio Processing**: WhisperX, PyTorch, torchaudio
- **Cloud Platform**: Google Cloud Run, Cloud Storage, Pub/Sub
- **Monitoring**: Cloud Logging, Cloud Monitoring
- **Security**: API Key authentication, CORS, TrustedHostMiddleware

## 📁 Project Structure

```
whisperX/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Configuration and logging
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── docs/                 # Documentation
├── scripts/              # Deployment and utility scripts
├── tests/                # Test suite
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── Dockerfile           # Production container
└── docker-compose.yml   # Local development
```

## 🔧 API Endpoints

### Health & Monitoring
- `GET /health` - Health check
- `GET /api/v1/health/` - Detailed health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Job Management
- `POST /api/v1/jobs/` - Create transcription job
- `GET /api/v1/jobs/` - List jobs
- `GET /api/v1/jobs/{job_id}` - Get job status
- `DELETE /api/v1/jobs/{job_id}` - Cancel job
- `POST /api/v1/jobs/upload` - Upload and process audio

### Metrics
- `GET /api/v1/metrics/` - Service metrics
- `GET /api/v1/metrics/performance` - Performance metrics
- `GET /api/v1/metrics/jobs` - Job metrics
- `GET /api/v1/metrics/system` - System metrics

## 🚀 Production Deployment

### Prerequisites

1. **Google Cloud Platform Account**
2. **Google Cloud CLI** (`gcloud`)
3. **Docker** installed
4. **Python 3.11** (for local testing)

### Quick Deployment

```bash
# 1. Set up Google Cloud Project
gcloud config set project PROJECT_ID

# 2. Run production tests locally
./scripts/test-production.sh

# 3. Deploy to Cloud Run
./scripts/deploy.sh
```

### Detailed Deployment Guide

See [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) for step-by-step instructions.

## 🔐 Security

### Authentication
- API Key-based authentication
- Configurable API keys via environment variables
- Rate limiting support

### Network Security
- CORS configuration
- TrustedHostMiddleware
- HTTPS enforcement in production

### Data Security
- Secure file handling
- Temporary file cleanup
- No sensitive data in logs

## 📊 Monitoring & Logging

### Structured Logging
- JSON-formatted logs
- Request/response logging
- Error tracking with context

### Metrics
- Service performance metrics
- Job processing statistics
- System resource usage

### Cloud Integration
- Google Cloud Logging
- Google Cloud Monitoring
- Custom dashboards

## 🧪 Testing

### Local Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

### Production Testing
```bash
# Test production setup
./scripts/test-production.sh
```

## 🔄 Development Workflow

### Environment Setup
1. **Development**: Uses `requirements-dev.txt` (lightweight)
2. **Production**: Uses `requirements-prod.txt` (full ML dependencies)

### Code Quality
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Production Tests**: Full deployment testing

## 📈 Performance

### Resource Requirements
- **Memory**: 4GB (recommended)
- **CPU**: 2 cores (recommended)
- **Storage**: 10GB (for models and temp files)

### Optimization Features
- Async processing
- Background task handling
- Resource cleanup
- Memory-efficient model loading

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**: Check Python version compatibility
2. **Memory Issues**: Increase Cloud Run memory allocation
3. **Timeout Errors**: Increase timeout settings
4. **Permission Errors**: Verify service account roles

### Debug Commands

```bash
# Check service status
gcloud run services describe whisperx-microservice --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20

# Test health endpoint
curl https://SERVICE_URL/health
```

## 📚 Documentation

- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)
- [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)
- [API Documentation](http://localhost:8000/docs) (when running locally)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the deployment guide
3. Check Cloud Run logs
4. Open an issue on GitHub

---

**🎯 Ready for Production Deployment!**

Your WhisperX Cloud Run Microservice is fully configured and ready for production deployment. Follow the [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) to get started. 