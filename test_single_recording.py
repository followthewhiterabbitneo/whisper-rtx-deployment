#!/usr/bin/env python3
"""
Test Single Recording - First Principles
Process ONE call recording from start to finish
"""

import os
import sys
import json
from datetime import datetime

# First, let's check what we need
print("=" * 60)
print("SCREAM Single Recording Test")
print("=" * 60)

# Step 1: Database Connection
print("\n1. DATABASE CONNECTION")
print("-" * 30)

try:
    import pymysql
    print("✓ PyMySQL available")
except ImportError:
    print("✗ PyMySQL not installed")
    print("  Run: pip install pymysql")
    sys.exit(1)

# Database configuration
# If using SSH tunnel, connect to localhost:33306
# If direct connection, use s40vpsoxweb002:3306
DB_CONFIG = {
    'host': 'localhost',  # Using SSH tunnel
    'port': 33306,        # Local tunneled port
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Alternative: Direct connection (if on same network)
# DB_CONFIG = {
#     'host': 's40vpsoxweb002',
#     'port': 3306,
#     'user': 'root',
#     'password': 'admin',
#     'database': 'oreka',
#     'charset': 'utf8mb4'
# }

print(f"  Host: {DB_CONFIG['host']}")
print(f"  Database: {DB_CONFIG['database']}")
print(f"  User: {DB_CONFIG['user']}")

# Step 2: Connect and Find ONE Recording
print("\n2. FINDING A TEST RECORDING")
print("-" * 30)

try:
    # Connect to database
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("✓ Connected to database")
    
    # Query for ONE recent call >= 2 minutes
    query = """
    SELECT 
        s.orkuid,
        s.timestamp,
        s.duration,
        s.localparty,
        s.remoteparty,
        s.orkuser_id,
        t.filename
    FROM orksegment s
    INNER JOIN orktape t ON s.orkuid = t.orkuid
    WHERE s.duration >= 120
        AND t.filename IS NOT NULL
        AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ORDER BY s.timestamp DESC
    LIMIT 1
    """
    
    cursor.execute(query)
    recording = cursor.fetchone()
    
    if recording:
        print("✓ Found recording:")
        print(f"  ID: {recording['orkuid']}")
        print(f"  Date: {recording['timestamp']}")
        print(f"  Duration: {recording['duration']} seconds")
        print(f"  Local: {recording['localparty']}")
        print(f"  Remote: {recording['remoteparty']}")
        print(f"  File: {recording['filename']}")
    else:
        print("✗ No recordings found matching criteria")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)
finally:
    if 'connection' in locals():
        connection.close()

# Step 3: Check File Access
print("\n3. FILE ACCESS CHECK")
print("-" * 30)

# Construct NFS path
nfs_mount = "/var/log/orkaudio.prod.nfs"
if recording['filename'].startswith('/'):
    file_path = nfs_mount + recording['filename']
else:
    file_path = os.path.join(nfs_mount, recording['filename'])

print(f"  Full path: {file_path}")

# Check if we can access the file
if os.path.exists(file_path):
    file_size = os.path.getsize(file_path)
    print(f"✓ File accessible: {file_size:,} bytes")
else:
    print("✗ File not found at expected path")
    print("  Please verify NFS mount is accessible")
    sys.exit(1)

# Step 4: Test Whisper
print("\n4. WHISPER ENGINE CHECK")
print("-" * 30)

try:
    from faster_whisper import WhisperModel
    print("✓ faster-whisper available")
except ImportError:
    print("✗ faster-whisper not installed")
    print("  Run: pip install faster-whisper")
    sys.exit(1)

model_path = "models/faster-whisper-large-v3-turbo-ct2"
if os.path.exists(model_path):
    print(f"✓ Model found: {model_path}")
else:
    print(f"✗ Model not found at: {model_path}")
    print("  Run bootstrap script to download model")
    sys.exit(1)

# Step 5: Process Recording
print("\n5. PROCESSING RECORDING")
print("-" * 30)

print("Loading model...")
model = WhisperModel(model_path, device="cuda", compute_type="int8_float16")
print("✓ Model loaded")

print(f"Transcribing {recording['duration']} second recording...")
start_time = datetime.now()

segments, info = model.transcribe(file_path, beam_size=5)

# Collect transcript
transcript_lines = []
for segment in segments:
    line = f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text.strip()}"
    transcript_lines.append(line)

end_time = datetime.now()
processing_time = (end_time - start_time).total_seconds()

print(f"✓ Transcription complete in {processing_time:.1f} seconds")
print(f"  Language: {info.language}")
print(f"  Speed: {info.duration / processing_time:.1f}x realtime")

# Step 6: Extract Key Information
print("\n6. EXTRACTING KEY INFORMATION")
print("-" * 30)

# Join transcript for analysis
full_transcript = "\n".join([seg.text.strip() for seg in segments])

# Look for loan number
import re
loan_patterns = [
    r'loan\s*(?:number|#)?\s*[:\s]*(\d{8,12})',
    r'application\s*(?:number|#)?\s*[:\s]*(\d{8,12})',
    r'(?:loan|app|application)\s*(\d{8,12})'
]

loan_number = None
for pattern in loan_patterns:
    match = re.search(pattern, full_transcript, re.IGNORECASE)
    if match:
        loan_number = match.group(1)
        print(f"✓ Loan number found: {loan_number}")
        break

if not loan_number:
    print("✗ No loan number found in transcript")

# Look for dollar amounts
dollar_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*dollars?\b'
amounts = re.findall(dollar_pattern, full_transcript, re.IGNORECASE)
if amounts:
    print(f"✓ Found {len(amounts)} dollar amounts: {', '.join(amounts[:3])}...")

# Step 7: Generate Summary
print("\n7. GENERATING SUMMARY")
print("-" * 30)

summary = {
    'recording_id': recording['orkuid'],
    'timestamp': str(recording['timestamp']),
    'duration': recording['duration'],
    'underwriter_phone': recording['localparty'],
    'broker_phone': recording['remoteparty'],
    'loan_number': loan_number,
    'language': info.language,
    'processing_time': processing_time,
    'key_amounts': amounts[:5] if amounts else [],
    'transcript_preview': transcript_lines[:5],
    'total_segments': len(transcript_lines)
}

# Save outputs
output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)

# Save transcript
transcript_file = os.path.join(output_dir, f"{recording['orkuid']}_transcript.txt")
with open(transcript_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(transcript_lines))
print(f"✓ Transcript saved: {transcript_file}")

# Save summary
summary_file = os.path.join(output_dir, f"{recording['orkuid']}_summary.json")
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"✓ Summary saved: {summary_file}")

# Display preview
print("\n8. SUMMARY PREVIEW")
print("-" * 30)
print(f"Recording: {recording['orkuid']}")
print(f"Duration: {recording['duration']} seconds")
print(f"Loan Number: {loan_number or 'Not found'}")
print(f"Amounts Found: {len(amounts)}")
print(f"\nFirst few lines:")
for line in transcript_lines[:3]:
    print(f"  {line}")

print("\n✅ TEST COMPLETE!")
print(f"   Check {output_dir}/ for full results")