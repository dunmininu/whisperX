"""
Configuration settings for WhisperX Cloud Run Microservice
"""

import os
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application settings
    APP_NAME: str = "WhisperX Cloud Run Microservice"
    DEBUG: bool = Field(default=False, env="DEBUG")
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # CORS settings
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_HOSTS from comma-separated string"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # Cloud Storage settings
    CLOUD_STORAGE_BUCKET: str = Field(..., env="CLOUD_STORAGE_BUCKET")

    # WhisperX settings
    MODEL_SIZE: str = Field(default="large-v2", env="MODEL_SIZE")
    WHISPERX_MODEL_SIZE: str = Field(default="large-v2", env="WHISPERX_MODEL_SIZE")
    WHISPERX_DEVICE: str = Field(default="cpu", env="WHISPERX_DEVICE")
    WHISPERX_COMPUTE_TYPE: str = Field(default="float32", env="WHISPERX_COMPUTE_TYPE")
    MAX_AUDIO_DURATION: int = Field(default=300, env="MAX_AUDIO_DURATION")
    ENABLE_GPU: bool = Field(default=False, env="ENABLE_GPU")
    COMPUTE_TYPE: str = Field(default="float32", env="COMPUTE_TYPE")

    # Processing settings
    BATCH_SIZE: int = Field(default=16, env="BATCH_SIZE")
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")

    # Security settings
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    API_KEYS: List[str] = Field(default=[], env="API_KEYS")
    HF_TOKEN: str = Field(default="", env="HF_TOKEN")  # Hugging Face API token for PyAnnotate

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")

    # Redis settings (for caching and job queue)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # File upload settings
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=["mp3", "wav", "m4a", "flac", "ogg"], env="ALLOWED_AUDIO_FORMATS"
    )

    # Temporary directory
    TEMP_DIR: str = Field(default="/tmp", env="TEMP_DIR")
    UPLOADS_DIR: str = Field(default="/tmp/whisperx-uploads", env="UPLOADS_DIR")
    MODELS_DIR: str = Field(default="/tmp/whisperx-models", env="MODELS_DIR")

    @validator("MODEL_SIZE")
    def validate_model_size(cls, v):
        """Validate WhisperX model size"""
        valid_sizes = ["tiny", "base", "small", "medium", "large", "large-v2"]
        if v not in valid_sizes:
            raise ValueError(f"Model size must be one of {valid_sizes}")
        return v

    @validator("COMPUTE_TYPE")
    def validate_compute_type(cls, v):
        """Validate compute type"""
        valid_types = ["float16", "float32", "int8"]
        if v not in valid_types:
            raise ValueError(f"Compute type must be one of {valid_types}")
        return v

    @validator("API_KEYS", pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from comma-separated string"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Development directories (use local paths)
    TEMP_DIR: str = "./temp"
    UPLOADS_DIR: str = "./uploads"
    MODELS_DIR: str = "./models"
    
    # Optimized settings for M1 Mac
    WHISPERX_MODEL_SIZE: str = "base"  # Use smaller model for development
    WHISPERX_DEVICE: str = "mps"  # Use Metal Performance Shaders for M1
    WHISPERX_COMPUTE_TYPE: str = "float32"  # More stable on M1
    BATCH_SIZE: int = 8  # Smaller batch size for M1
    MAX_WORKERS: int = 2  # Limit concurrent processing
    MAX_AUDIO_DURATION: int = 600  # 10 minutes max for development


class ProductionSettings(Settings):
    """Production environment settings"""

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: List[str] = ["*"]  # Configure appropriately for production
    
    # Production directories (use /tmp for Cloud Run)
    TEMP_DIR: str = "/tmp"
    UPLOADS_DIR: str = "/tmp/whisperx-uploads"
    MODELS_DIR: str = "/tmp/whisperx-models"
    
    # Optimized settings for GCP
    WHISPERX_MODEL_SIZE: str = "large-v2"
    WHISPERX_DEVICE: str = "cuda"
    WHISPERX_COMPUTE_TYPE: str = "float16"
    BATCH_SIZE: int = 32
    MAX_WORKERS: int = 8
    MAX_AUDIO_DURATION: int = 7200  # 2 hours max for production


class TestSettings(Settings):
    """Test environment settings"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    GOOGLE_CLOUD_PROJECT: str = "test-project"
    CLOUD_STORAGE_BUCKET: str = "test-bucket"


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()
