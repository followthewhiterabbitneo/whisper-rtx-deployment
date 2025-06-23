#!/usr/bin/env python3
"""
Debug loan extraction - check why no loans are being found
"""

import os
import sys
import re
from faster_whisper import WhisperModel
import subprocess

def test_loan_patterns():
    """Test loan number patterns"""
    print("Testing loan number patterns...")
    
    # Test texts with loan numbers
    test_texts = [
        "The loan number is 12345678",
        "Loan #87654321",
        "Your loan 1234567 is approved",
        "Reference number: 9876543210",
        "Account 123456789",
        "I need help with loan number 98765432",
        "calling about 12345678",
        "my number is 5551234567",  # Phone number - should not match
        "loan# 87654321",
        "LOAN NUMBER 12345678",
    ]
    
    # Patterns to test
    patterns = [
        r'\b\d{8}\b',           # 8 digits
        r'\b\d{9}\b',           # 9 digits  
        r'\b\d{10}\b',          # 10 digits
        r'\b\d{7}\b',           # 7 digits
        r'loan\s*#?\s*(\d{7,10})', # "loan #12345678"
        r'number\s*#?\s*(\d{7,10})', # "number 12345678"
    ]
    
    print("\nPattern matching results:")
    for text in test_texts:
        print(f"\nText: '{text}'")
        found_loans = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if isinstance(match, str) and match.isdigit() and 7 <= len(match) <= 10:
                    # Exclude phone numbers (starting with 555, 1, etc)
                    if not match.startswith('555') and not match.startswith('1'):
                        found_loans.add(match)
        
        print(f"  Found: {list(found_loans)}")

def check_specific_recording(orkuid, filename):
    """Download and check a specific recording"""
    print(f"\nChecking recording: {orkuid}")
    print(f"Filename: {filename}")
    
    # Download file
    remote_path = f"/var/log/orkaudio.prod.nfs/audio/{filename}"
    local_path = f"debug_{orkuid}.wav"
    
    print("Downloading...")
    scp_cmd = ["scp", f"estillmane@s40vpsoxweb002:{remote_path}", local_path]
    result = subprocess.run(scp_cmd, capture_output=True)
    
    if result.returncode != 0 or not os.path.exists(local_path):
        print("Failed to download!")
        return
    
    # Get file info
    file_size = os.path.getsize(local_path)
    print(f"File size: {file_size:,} bytes")
    
    # Transcribe
    print("\nTranscribing...")
    model = WhisperModel(
        "models/faster-whisper-large-v3-turbo-ct2",
        device="cuda",
        compute_type="int8_float16"
    )
    
    segments, info = model.transcribe(
        local_path,
        language="en",
        beam_size=1,
        vad_filter=True
    )
    
    # Get full transcript
    full_text = ""
    for segment in segments:
        full_text += segment.text + " "
    
    print(f"\nAudio duration: {info.duration:.1f} seconds")
    print(f"Transcript length: {len(full_text)} characters")
    print(f"\nFirst 500 characters:")
    print(full_text[:500])
    
    # Look for numbers
    print("\n\nSearching for numbers in transcript...")
    all_numbers = re.findall(r'\b\d{5,12}\b', full_text)
    print(f"All numbers found: {all_numbers}")
    
    # Look for loan keywords
    loan_keywords = ['loan', 'account', 'number', 'reference', 'mortgage', 'application']
    print("\nLoan-related context:")
    for keyword in loan_keywords:
        pattern = rf'.{{0,50}}{keyword}.{{0,50}}'
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            print(f"\n'{keyword}' contexts:")
            for match in matches[:3]:  # First 3 matches
                print(f"  ...{match}...")
    
    # Save full transcript for inspection
    debug_file = f"debug_transcript_{orkuid}.txt"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(f"Recording: {orkuid}\n")
        f.write(f"Duration: {info.duration} seconds\n")
        f.write(f"Filename: {filename}\n")
        f.write("-" * 80 + "\n")
        f.write(full_text)
    
    print(f"\nFull transcript saved to: {debug_file}")
    
    # Cleanup
    if os.path.exists(local_path):
        os.remove(local_path)

def main():
    print("=" * 80)
    print("LOAN EXTRACTION DEBUGGER")
    print("=" * 80)
    
    # Test patterns first
    test_loan_patterns()
    
    # Check a specific recording
    print("\n" + "=" * 80)
    print("Let's check one of the Hunter Gollehur recordings that showed 'No loans'")
    
    # You can modify these to test different recordings
    test_cases = [
        ("20250602_160503_KUMZ", "2025/06/02/16/20250602_160503_KUMZ.wav"),
        ("20250602_154526_KPQG", "2025/06/02/15/20250602_154526_KPQG.wav"),
    ]
    
    for orkuid, filename in test_cases[:1]:  # Test first one
        check_specific_recording(orkuid, filename)
        break

if __name__ == "__main__":
    main()