#!/usr/bin/env python3
"""
Test script for database functionality
"""

import requests
import time
import tempfile
import os

def create_test_audio():
    """Create a simple test audio file"""
    # Create a simple WAV file header
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

def test_database_functionality():
    """Test complete database functionality"""
    print("🧪 Testing Database Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1/jobs"
    headers = {"X-API-Key": "jamp"}
    
    # Step 1: Test job listing (should be empty initially)
    print("\n📋 Step 1: Testing job listing...")
    response = requests.get(f"{base_url}/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Step 2: Upload a test file
    print("\n📤 Step 2: Uploading test file...")
    test_file = create_test_audio()
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            params = {
                'model_size': 'large-v2',
                'enable_diarization': 'true',
                'enable_alignment': 'true'
            }
            response = requests.post(f"{base_url}/upload", headers=headers, files=files, params=params)
        
        print(f"Upload Status: {response.status_code}")
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Job created: {job_id}")
        else:
            print(f"❌ Upload failed: {response.text}")
            return
            
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    # Step 3: Wait a moment for processing
    print("\n⏳ Step 3: Waiting for processing...")
    time.sleep(2)
    
    # Step 4: Check job status
    print("\n📊 Step 4: Checking job status...")
    response = requests.get(f"{base_url}/{job_id}", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        job_status = response.json()
        print(f"Job Status: {job_status['status']}")
        print(f"Progress: {job_status['progress']}")
    else:
        print(f"❌ Failed to get job: {response.text}")
    
    # Step 5: List jobs again (should show the new job)
    print("\n📋 Step 5: Listing jobs again...")
    response = requests.get(f"{base_url}/", headers=headers)
    print(f"Status: {response.status_code}")
    jobs_data = response.json()
    print(f"Total jobs: {jobs_data['total']}")
    print(f"Jobs in response: {len(jobs_data['jobs'])}")
    
    # Step 6: Test job cancellation
    print("\n❌ Step 6: Testing job cancellation...")
    response = requests.delete(f"{base_url}/{job_id}", headers=headers)
    print(f"Cancel Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Job cancelled successfully")
    else:
        print(f"❌ Cancel failed: {response.text}")
    
    print("\n🏁 Database functionality test completed!")

if __name__ == "__main__":
    test_database_functionality() 