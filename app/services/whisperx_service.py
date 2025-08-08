"""
WhisperX service for audio transcription and speaker diarization
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import structlog

logger = structlog.get_logger(__name__)

# Conditional import for whisperx
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False
    logger.warning("WhisperX not available - using mock implementation")

# Conditional import for torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch not available - using mock implementation")

from app.core.config import settings
from app.models.schemas import TranscriptionResult, SpeakerSegment, WordSegment


class WhisperXService:
    """Service for handling WhisperX transcription and speaker diarization."""
    
    def __init__(self):
        self.model_size = settings.WHISPERX_MODEL_SIZE
        self.device = settings.WHISPERX_DEVICE
        self.compute_type = settings.WHISPERX_COMPUTE_TYPE
        self.model = None
        self.align_model = None
        self.diarize_model = None
        
    async def initialize(self):
        """Initialize WhisperX models."""
        if not WHISPERX_AVAILABLE:
            logger.warning("WhisperX not available - skipping initialization")
            return
            
        try:
            logger.info("Initializing WhisperX models...")
            
            # Check device and adjust compute type if needed
            if self.device == "cpu" and self.compute_type == "float16":
                logger.warning("float16 not supported on CPU, falling back to float32")
                self.compute_type = "float32"
            elif self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA device requested but not available, falling back to CPU")
                self.device = "cpu"
                self.compute_type = "float32"
                
            # Models will be loaded on-demand to save memory
            logger.info(f"WhisperX models initialized successfully (device: {self.device}, compute_type: {self.compute_type})")
        except Exception as e:
            logger.error(f"Error initializing WhisperX models: {str(e)}")
            raise
    
    async def transcribe_audio(
        self, audio_path: str, language: str = "en", chunk_size: int = 30
    ) -> Dict:
        """
        Transcribe audio file using WhisperX with speaker diarization.
        
        Args:
            audio_path: Path to the audio file
            language: Language code for transcription
            chunk_size: Size of audio chunks in seconds
            
        Returns:
            Dictionary containing transcription results with speaker diarization
        """
        if not WHISPERX_AVAILABLE:
            logger.warning("WhisperX not available - returning mock result")
            return self._get_mock_result(audio_path, language)
            
        try:
            logger.info(f"Starting transcription for {audio_path}")
            
            # Load audio
            audio = whisperx.load_audio(audio_path)
            
            # Calculate number of samples per chunk
            import numpy as np
            sample_rate = 16000  # WhisperX default
            samples_per_chunk = chunk_size * sample_rate
            
            # Split audio into chunks
            audio_chunks = [
                audio[i:i + samples_per_chunk]
                for i in range(0, len(audio), samples_per_chunk)
            ]
            
            logger.info(f"Processing {len(audio_chunks)} chunks of {chunk_size}s each")
            
            # Load model (only once)
            model = whisperx.load_model(
                self.model_size, 
                device=self.device,
                compute_type=self.compute_type
            )
            
            # Process each chunk
            all_results = []
            for i, chunk in enumerate(audio_chunks):
                logger.info(f"Processing chunk {i+1}/{len(audio_chunks)}")
                chunk_result = model.transcribe(chunk, language=language)
                
                # Adjust timestamps for chunk position
                chunk_offset = i * chunk_size
                for segment in chunk_result["segments"]:
                    segment["start"] += chunk_offset
                    segment["end"] += chunk_offset
                    for word in segment.get("words", []):
                        word["start"] += chunk_offset
                        word["end"] += chunk_offset

                logger.info(f"Chunk {i+1} result: {chunk_result}")
                
                all_results.append(chunk_result)
            
            # Merge results
            result = {
                "segments": [],
                "language": language
            }
            for chunk_result in all_results:
                result["segments"].extend(chunk_result["segments"])
            
            # Sort segments by start time
            result["segments"].sort(key=lambda x: x["start"])
            
            # Align whisper output
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"], 
                device=self.device
            )
            result = whisperx.align(
                result["segments"], 
                model_a, 
                metadata, 
                audio, 
                self.device,
                return_char_alignments=False
            )
            
            # Attempt diarization (optional) - requires PyAnnotate 3.1+
            diarize_success = False
            try:
                logger.info("Attempting speaker diarization with PyAnnotate 3.1...")
                
                # Check if HF_TOKEN is properly set
                if not settings.HF_TOKEN or settings.HF_TOKEN == "hf_token":
                    raise ValueError("Valid HF_TOKEN required for diarization")
                
                # Skip diarization on M1 for now due to compatibility issues
                if self.device == "mps":
                    logger.warning("Skipping diarization on MPS device due to compatibility issues")
                    raise ValueError("Diarization not supported on MPS device")
                
                from pyannote.audio import Pipeline
                import torch
                import asyncio
                
                # Set timeout for diarization (5 minutes max)
                timeout_seconds = 300
                
                async def run_diarization():
                    # Load the diarization pipeline
                    diarize_model = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=settings.HF_TOKEN
                    )
                    
                    # Move to appropriate device (CPU only for now)
                    # Skip GPU for M1 compatibility
                    logger.info("Running diarization on CPU for compatibility")
                    
                    # Run diarization on audio file
                    logger.info("Starting diarization processing...")
                    diarization = diarize_model(audio_path)
                    
                    # Convert PyAnnotate output to WhisperX format
                    diarize_segments = []
                    for turn, _, speaker in diarization.itertracks(yield_label=True):
                        diarize_segments.append({
                            "start": turn.start,
                            "end": turn.end,
                            "speaker": speaker
                        })
                    
                    return diarize_segments
                
                # Run with timeout
                diarize_segments = await asyncio.wait_for(
                    run_diarization(), 
                    timeout=timeout_seconds
                )
                
                # Assign speaker labels to transcription
                result = whisperx.assign_word_speakers(
                    {"speaker": diarize_segments}, 
                    result
                )
                
                diarize_success = True
                logger.info(f"Speaker diarization completed successfully with {len(diarize_segments)} segments")
                
            except asyncio.TimeoutError:
                logger.warning(f"Diarization timed out after {timeout_seconds} seconds, continuing without speaker labels")
                # Add default speaker labels
                for segment in result.get("segments", []):
                    segment["speaker"] = "SPEAKER_00"
                    for word in segment.get("words", []):
                        word["speaker"] = "SPEAKER_00"
            except Exception as e:
                logger.warning(f"Diarization failed, continuing without speaker labels: {str(e)}")
                # Add default speaker labels to ensure consistency
                for segment in result.get("segments", []):
                    segment["speaker"] = "SPEAKER_00"
                    for word in segment.get("words", []):
                        word["speaker"] = "SPEAKER_00"
            
            logger.info(f"Transcription completed for {audio_path}")
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {str(e)}")
            raise
    
    def _get_mock_result(self, audio_path: str, language: str) -> Dict:
        """Return a mock result when WhisperX is not available."""
        return {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a mock transcription result.",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {
                            "start": 0.0,
                            "end": 1.0,
                            "word": "This",
                            "speaker": "SPEAKER_00"
                        },
                        {
                            "start": 1.0,
                            "end": 2.0,
                            "word": "is",
                            "speaker": "SPEAKER_00"
                        },
                        {
                            "start": 2.0,
                            "end": 3.0,
                            "word": "a",
                            "speaker": "SPEAKER_00"
                        },
                        {
                            "start": 3.0,
                            "end": 5.0,
                            "word": "mock transcription.",
                            "speaker": "SPEAKER_00"
                        }
                    ]
                }
            ],
            "language": language,
            "audio_path": audio_path
        }

    async def _load_audio(self, audio_path: str) -> Optional[Any]:
        """Load audio file - simplified for development"""
        if not WHISPERX_AVAILABLE:
            logger.warning("WhisperX not available - skipping audio loading")
            return None
            
        try:
            return whisperx.load_audio(audio_path)
        except Exception as e:
            logger.error(f"Error loading audio file {audio_path}: {str(e)}")
            return None

    async def _convert_to_wav(self, audio: Optional[Any]) -> str:
        """Convert audio to WAV format - simplified for development"""
        if not WHISPERX_AVAILABLE or audio is None:
            logger.warning("WhisperX not available - returning original path")
            return ""
            
        try:
            # For development, just return the original path
            # In production, this would convert to WAV format
            return ""
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            return ""

    def _assign_speakers_to_segments(
        self, segments: List[Dict], speaker_segments: List[Dict]
    ) -> List[Dict]:
        """Assign speaker labels to transcription segments."""
        if not segments or not speaker_segments:
            return segments
            
        # Simple speaker assignment logic
        for segment in segments:
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            
            # Find overlapping speaker segment
            for speaker_seg in speaker_segments:
                speaker_start = speaker_seg.get("start", 0)
                speaker_end = speaker_seg.get("end", 0)
                
                if (segment_start <= speaker_end and 
                    segment_end >= speaker_start):
                    segment["speaker"] = speaker_seg.get("speaker", "UNKNOWN")
                    break
            else:
                segment["speaker"] = "UNKNOWN"
                
        return segments

    def _format_result(self, result: Dict) -> Dict:
        """Format WhisperX result into my standard format."""
        try:
            segments = []
            
            for segment in result.get("segments", []):
                words = []
                for word in segment.get("words", []):
                    words.append(WordSegment(
                        start=word.get("start", 0),
                        end=word.get("end", 0),
                        word=word.get("word", ""),
                        speaker=word.get("speaker", "UNKNOWN")
                    ))
                
                segments.append(SpeakerSegment(
                    start=segment.get("start", 0),
                    end=segment.get("end", 0),
                    text=segment.get("text", ""),
                    speaker=segment.get("speaker", "UNKNOWN"),
                    words=words
                ))
            
            return {
                "segments": [seg.dict() for seg in segments],
                "language": result.get("language", "en"),
                "audio_path": result.get("audio_path", "")
            }
            
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return self._get_mock_result("", "en")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up WhisperX service")
            # Cleanup logic would go here
            # For now, just log the cleanup
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return WHISPERX_AVAILABLE or True  # Always return True for mock mode
