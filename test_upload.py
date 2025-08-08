#!/usr/bin/env python3
"""
Test script for file upload functionality
"""

import os
import tempfile
import requests
from pathlib import Path

def create_test_audio():
    """Create a simple test audio file"""
    # Create a simple WAV file header (this is just for testing)
    wav_header = (
        b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' +
        b'fmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little') +
        (1).to_bytes(2, 'little') + (44100).to_bytes(4, 'little') +
        (88200).to_bytes(4, 'little') + (2).to_bytes(2, 'little') +
        (16).to_bytes(2, 'little') + b'data' + (0).to_bytes(4, 'little')
    )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(wav_header)
        return f.name

def test_upload():
    """Test file upload functionality"""
    print("🧪 Testing file upload functionality...")
    
    # Create test audio file
    test_file = create_test_audio()
    print(f"📁 Created test file: {test_file}")
    
    try:
        # Test upload
        url = "http://localhost:8000/api/v1/jobs/upload"
        params = {
            "model_size": "large-v2",
            "enable_diarization": "true",
            "enable_alignment": "true"
        }
        headers = {
            "X-API-Key": "jamp"
        }
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            response = requests.post(url, params=params, headers=headers, files=files)
        
        print(f"📤 Upload response status: {response.status_code}")
        print(f"📤 Upload response: {response.text}")
        
        if response.status_code == 200:
            print("✅ File upload test PASSED!")
        else:
            print("❌ File upload test FAILED!")
            
    except Exception as e:
        print(f"❌ Error during upload test: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"🧹 Cleaned up test file: {test_file}")

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"📊 Health status: {response.status_code}")
        print(f"📊 Health response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check PASSED!")
        else:
            print("❌ Health check FAILED!")
            
    except Exception as e:
        print(f"❌ Error during health check: {e}")

if __name__ == "__main__":
    print("🚀 Starting WhisperX upload tests...")
    print("=" * 50)
    
    test_health()
    print()
    test_upload()
    print()
    print("�� Tests completed!") 