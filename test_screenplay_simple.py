#!/usr/bin/env python3
"""
SIMPLE SCREENPLAY TEST
Test the screenplay format without WhisperX
Just uses channel separation with existing Whisper setup
"""

import subprocess
import sys

def test_simple():
    """Test with a simple approach first"""
    print("🎬 Testing Screenplay Transcription")
    print("=" * 50)
    print("This version uses your existing Whisper setup")
    print("No new dependencies needed!")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage: python test_screenplay_simple.py <audio_file.wav>")
        print("\nExample:")
        print("  python test_screenplay_simple.py test_recording.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Run the screenplay transcription
    cmd = ["python3", "transcribe_screenplay_stereo.py", audio_file]
    subprocess.run(cmd)

if __name__ == "__main__":
    test_simple()