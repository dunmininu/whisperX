# WhisperX Service Documentation

## Overview
The WhisperX service provides audio transcription with speaker diarization capabilities, optimized for both development (M1 Mac) and production (GCP) environments. This document explains the service architecture, optimizations, and key features.

## Architecture

### Core Components
1. **WhisperX Transcription**: Handles speech-to-text conversion with timestamps
2. **PyAnnotate Diarization**: Manages speaker identification and segmentation
3. **Chunked Processing**: Enables memory-efficient handling of long audio files

## Configuration

### Development Environment (M1 Mac)
```python
WHISPERX_MODEL_SIZE: str = "base"  # Lighter model for development
WHISPERX_DEVICE: str = "mps"       # Metal Performance Shaders
WHISPERX_COMPUTE_TYPE: str = "float32"
BATCH_SIZE: int = 8
MAX_WORKERS: int = 2
MAX_AUDIO_DURATION: int = 600      # 10 minutes max
```

### Production Environment (GCP)
```python
WHISPERX_MODEL_SIZE: str = "large-v2"
WHISPERX_DEVICE: str = "cuda"      # GPU support
WHISPERX_COMPUTE_TYPE: str = "float16"
BATCH_SIZE: int = 32
MAX_WORKERS: int = 8
MAX_AUDIO_DURATION: int = 7200     # 2 hours max
```

## Memory-Efficient Processing

### Chunked Audio Processing
The service implements a chunking strategy to handle long audio files efficiently:

1. **Chunk Size**: Default 30-second chunks
2. **Processing Flow**:
   - Audio file is loaded and split into chunks
   - Each chunk is processed independently
   - Results are merged with adjusted timestamps
   - Final alignment and diarization are performed

```python
# Example chunk processing
chunk_size = 30  # seconds
samples_per_chunk = chunk_size * 16000  # 16kHz sample rate
audio_chunks = [audio[i:i + samples_per_chunk] for i in range(0, len(audio), samples_per_chunk)]
```

### Timestamp Adjustment
For each chunk, timestamps are adjusted to maintain continuity:
```python
chunk_offset = chunk_index * chunk_size
for segment in chunk_result["segments"]:
    segment["start"] += chunk_offset
    segment["end"] += chunk_offset
```

## Speaker Diarization

### PyAnnotate Integration
The service uses PyAnnotate's Pipeline directly for speaker diarization:
```python
from pyannote.audio import Pipeline
diarize_model = Pipeline.from_pretrained("pyannote/speaker-diarization")
```

### Diarization Features
- Minimum 1 speaker
- Maximum 10 speakers
- Speaker labels assigned to both segments and words

## Error Handling and Logging

### Key Error Scenarios
1. Model initialization failures
2. Audio loading issues
3. Processing errors
4. Memory constraints

### Logging Strategy
- Detailed progress logging for each chunk
- Error tracking with stack traces
- Performance metrics logging

## Performance Considerations

### Memory Usage
- Chunk size affects memory footprint
- Smaller chunks = lower memory usage
- Trade-off between memory and processing time

### Processing Speed
- GPU acceleration when available
- Parallel processing limitations
- Chunk size impact on overall speed

### Hardware-Specific Optimizations
1. **M1 Mac**:
   - MPS backend utilization
   - Reduced batch size
   - Conservative worker count

2. **GPU Server**:
   - CUDA acceleration
   - Larger batch sizes
   - Increased parallelism

## Best Practices

### Development
1. Use smaller models during development
2. Test with short audio files first
3. Monitor memory usage
4. Use appropriate chunk sizes

### Production
1. Implement proper error handling
2. Monitor system resources
3. Use appropriate hardware for load
4. Regular performance monitoring

## Troubleshooting

### Common Issues
1. **Memory Errors**:
   - Reduce chunk size
   - Lower batch size
   - Use smaller model

2. **Processing Errors**:
   - Check audio format
   - Verify model compatibility
   - Monitor GPU memory

3. **Performance Issues**:
   - Adjust worker count
   - Optimize chunk size
   - Check hardware utilization

## Future Improvements

### Planned Enhancements
1. Adaptive chunk sizing
2. Better error recovery
3. Enhanced parallel processing
4. Improved memory management
5. Real-time processing capabilities

## API Reference

### Main Methods
```python
async def transcribe_audio(
    self,
    audio_path: str,
    language: str = "en",
    chunk_size: int = 30
) -> Dict
```

### Parameters
- `audio_path`: Path to audio file
- `language`: Language code (default: "en")
- `chunk_size`: Size of audio chunks in seconds (default: 30)

### Return Value
Dictionary containing:
- Transcribed text
- Speaker segments
- Word-level timing
- Confidence scores
- Processing metadata
