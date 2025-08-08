# WhisperX Cloud Run Microservice - Architecture Documentation

## Overview

The WhisperX Cloud Run Microservice is a high-performance, scalable audio processing service that provides advanced transcription and speaker diarization capabilities. It's designed to work as part of a larger audio processing pipeline, receiving audio files from a primary transcription service and enhancing them with WhisperX's advanced features.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Microservice 1 │───▶│  Microservice 2 │
│                 │    │ (Initial Trans) │    │ (WhisperX +     │
│                 │    │                 │    │  Diarization)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Cloud Storage  │    │   Cloud Run     │
                       │   (Audio Files) │    │  (WhisperX API) │
                       └─────────────────┘    └─────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WhisperX Cloud Run Service                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   FastAPI   │  │   WhisperX  │  │   Google    │          │
│  │   Web App   │  │   Service   │  │   Cloud     │          │
│  │             │  │             │  │   Services  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   API       │  │   Audio     │  │   Storage   │          │
│  │   Endpoints │  │   Processing │  │   & Pub/Sub │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs with automatic documentation
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management

### Audio Processing
- **WhisperX**: Advanced speech recognition with word-level timestamps and speaker diarization
- **PyTorch**: Deep learning framework for WhisperX models
- **Librosa**: Audio processing and analysis
- **Pydub**: Audio file manipulation and conversion

### Cloud Platform
- **Google Cloud Run**: Serverless container platform for deployment
- **Google Cloud Storage**: File storage for audio files
- **Google Cloud Firestore**: NoSQL database for job tracking
- **Google Cloud Pub/Sub**: Asynchronous messaging for job processing
- **Google Cloud Logging**: Centralized logging
- **Google Cloud Monitoring**: Performance monitoring and metrics

### Containerization
- **Docker**: Containerization for consistent deployment
- **Multi-stage builds**: Optimized container images

### Security & Authentication
- **API Key Authentication**: Simple but effective API security
- **IAM Integration**: Google Cloud service account permissions
- **CORS Configuration**: Cross-origin resource sharing

## Data Flow

### 1. Job Submission
```
Client → FastAPI → Job Queue → Background Processing
```

### 2. Audio Processing
```
Audio File → Validation → WhisperX → Transcription → Diarization → Results
```

### 3. Response Handling
```
Results → Database → API Response → Client
```

## API Design

### RESTful Endpoints

#### Jobs API
- `POST /api/v1/jobs/upload` - Upload and process audio file
- `GET /api/v1/jobs/{job_id}` - Get job status and results
- `GET /api/v1/jobs/` - List all jobs with pagination
- `DELETE /api/v1/jobs/{job_id}` - Cancel a running job

#### Health & Monitoring
- `GET /health` - Service health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /health/detailed` - Detailed health information

#### Metrics
- `GET /api/v1/metrics/` - Service performance metrics
- `GET /api/v1/metrics/performance` - Detailed performance metrics
- `GET /api/v1/metrics/jobs` - Job-specific metrics
- `GET /api/v1/metrics/system` - System resource metrics

### Request/Response Models

#### Job Request
```json
{
  "audio_file": "audio.mp3",
  "model_size": "large-v2",
  "enable_diarization": true,
  "enable_alignment": true,
  "language": "en"
}
```

#### Job Response
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 0.75,
  "current_stage": "diarization",
  "result": {
    "text": "Transcribed text...",
    "speaker_segments": [...],
    "word_segments": [...],
    "confidence": 0.95
  }
}
```

## Security Architecture

### Authentication
- API Key-based authentication
- Configurable API keys via environment variables
- Header-based key validation

### Authorization
- Google Cloud IAM integration
- Service account permissions
- Resource-level access control

### Data Protection
- Input validation and sanitization
- File type and size restrictions
- Secure file handling
- Temporary file cleanup

## Performance Optimization

### Model Loading
- Lazy loading of WhisperX models
- Model caching and reuse
- Memory-efficient model loading

### Processing Optimization
- Batch processing capabilities
- Parallel processing where possible
- Resource-aware processing

### Scalability
- Auto-scaling on Cloud Run
- Horizontal scaling support
- Load balancing ready

## Monitoring & Observability

### Logging
- Structured logging with structlog
- JSON-formatted logs
- Log levels and filtering
- Request/response logging

### Metrics
- Service performance metrics
- Job processing statistics
- System resource monitoring
- Custom business metrics

### Health Checks
- Liveness probes
- Readiness probes
- Detailed health information
- Dependency health checks

## Deployment Architecture

### Cloud Run Configuration
```yaml
service:
  name: whisperx-service
  region: us-central1
  memory: 4Gi
  cpu: 2
  max_instances: 10
  min_instances: 0
  timeout: 900s
  concurrency: 80
```

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT=the-project-id
MODEL_SIZE=large-v2
MAX_AUDIO_DURATION=300
ENABLE_GPU=false
LOG_LEVEL=INFO
```

## Error Handling

### Error Categories
1. **Validation Errors**: Invalid input, file format, size limits
2. **Processing Errors**: Audio processing failures, model errors
3. **Infrastructure Errors**: Cloud service failures, network issues
4. **Authentication Errors**: Invalid API keys, permission issues

### Error Response Format
```json
{
  "error": "Error message",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "audio_file",
    "reason": "File too large"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Cost Optimization

### Resource Management
- Efficient memory usage
- CPU optimization
- Model size selection
- Batch processing

### Cloud Run Optimization
- Auto-scaling policies
- Instance configuration
- Request timeout settings
- Concurrency limits

## Future Enhancements

### Planned Features
1. **GPU Support**: CUDA-enabled processing
2. **Batch Processing**: Multiple file processing
3. **Real-time Processing**: WebSocket support
4. **Advanced Analytics**: Processing insights
5. **Multi-language Support**: Enhanced language detection

### Scalability Improvements
1. **Microservice Split**: Separate services for different functions
2. **Caching Layer**: Redis for result caching
3. **Queue Management**: Advanced job queuing
4. **CDN Integration**: Global content delivery

## Security Considerations

### Data Privacy
- No persistent storage of audio files
- Temporary file cleanup
- Secure transmission protocols
- Data encryption at rest

### Access Control
- API key rotation
- Rate limiting
- IP whitelisting (if needed)
- Audit logging

### Compliance
- GDPR compliance considerations
- Data retention policies
- Privacy by design
- Security best practices 