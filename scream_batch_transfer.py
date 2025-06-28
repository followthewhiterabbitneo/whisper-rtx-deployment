#!/usr/bin/env python3
"""
SCREAM BATCH TRANSFER & TRANSCRIBE
Transfer audio files from remote server and transcribe them
This runs on your local coding machine and sends files to RTX 4090
"""

import os
import sys
import subprocess
import tempfile
import time
import json
from datetime import datetime
import pymysql

# SSH Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

# Database Configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka'
}

def get_loan_calls(loan_number):
    """Get all calls for a specific loan from database"""
    print(f"\n🔍 Finding calls for loan {loan_number}...")
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Query for calls mentioning this loan
    query = """
    SELECT 
        ct.orkuid,
        t.timestamp,
        t.duration,
        t.filename,
        t.localParty,
        t.remoteParty,
        ct.transcript_path,
        YEAR(t.timestamp) as year,
        MONTH(t.timestamp) as month,
        DAY(t.timestamp) as day,
        HOUR(t.timestamp) as hour
    FROM call_transcripts_v2 ct
    JOIN orktape t ON ct.orkuid = t.orkUid
    WHERE ct.loan_numbers LIKE %s
    AND ct.transcript_path IS NULL  -- Only untranscribed
    ORDER BY t.timestamp
    """
    
    cursor.execute(query, (f'%{loan_number}%',))
    calls = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print(f"✅ Found {len(calls)} untranscribed calls")
    return calls

def transfer_files(calls):
    """Transfer WAV files from remote server"""
    print(f"\n📥 Transferring {len(calls)} files...")
    
    # Create transfer directory
    transfer_dir = f"transfer_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(transfer_dir, exist_ok=True)
    
    transferred = []
    
    for i, call in enumerate(calls, 1):
        # Build remote path
        ts = call['timestamp']
        remote_path = f"{REMOTE_BASE}/audio/{call['year']:04d}/{call['month']:02d}/{call['day']:02d}/{call['hour']:02d}/{call['filename']}"
        
        # Local path
        local_path = os.path.join(transfer_dir, call['filename'])
        
        print(f"\n[{i}/{len(calls)}] {call['filename']}")
        print(f"  Remote: {remote_path}")
        
        # SCP the file
        scp_cmd = ['scp', '-q', f'{SSH_USER}@{SSH_HOST}:{remote_path}', local_path]
        
        start = time.time()
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(local_path):
            transfer_time = time.time() - start
            size = os.path.getsize(local_path)
            print(f"  ✅ Transferred in {transfer_time:.1f}s ({size/1024/1024:.1f} MB)")
            
            transferred.append({
                'orkuid': call['orkuid'],
                'filename': call['filename'],
                'local_path': local_path,
                'remote_path': remote_path,
                'duration': call['duration'],
                'timestamp': str(call['timestamp'])
            })
        else:
            print(f"  ❌ Transfer failed: {result.stderr}")
    
    print(f"\n✅ Successfully transferred {len(transferred)}/{len(calls)} files")
    print(f"📁 Files saved to: {transfer_dir}/")
    
    # Save manifest
    manifest_file = os.path.join(transfer_dir, "manifest.json")
    with open(manifest_file, 'w') as f:
        json.dump({
            'transfer_time': datetime.now().isoformat(),
            'total_files': len(transferred),
            'files': transferred
        }, f, indent=2)
    
    print(f"📄 Manifest saved: {manifest_file}")
    
    return transfer_dir, transferred

def create_rtx_script(transfer_dir, files):
    """Create script to run on RTX 4090"""
    script_name = os.path.join(transfer_dir, "transcribe_all.py")
    
    script_content = '''#!/usr/bin/env python3
"""
Auto-generated script to transcribe transferred files
Run this on RTX 4090
"""

import os
import json
from faster_whisper import WhisperModel

# Load manifest
with open("manifest.json", 'r') as f:
    manifest = json.load(f)

print(f"🎤 Transcribing {manifest['total_files']} files...")

# Load model
model = WhisperModel(
    "models/faster-whisper-large-v3-turbo-ct2",
    device="cuda",
    compute_type="int8_float16"
)

# Process each file
for file_info in manifest['files']:
    print(f"\\n📁 {file_info['filename']}")
    
    # Transcribe
    segments, info = model.transcribe(
        file_info['filename'],
        beam_size=5,
        language="en"
    )
    
    # Collect text
    text = " ".join([seg.text.strip() for seg in segments])
    
    # Save transcript
    output_file = file_info['filename'].replace('.wav', '_transcript.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"orkUid: {file_info['orkuid']}\\n")
        f.write(f"Duration: {file_info['duration']}s\\n")
        f.write(f"Timestamp: {file_info['timestamp']}\\n")
        f.write(f"\\nTRANSCRIPT:\\n{text}")
    
    print(f"  ✅ Saved: {output_file}")

print("\\n✅ All files transcribed!")
'''
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    print(f"\n📝 Created RTX script: {script_name}")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print(f"1. Copy folder '{transfer_dir}' to your RTX 4090")
    print(f"2. Navigate to the folder")
    print(f"3. Run: python transcribe_all.py")
    print("="*60)

def main():
    if len(sys.argv) < 2:
        print("SCREAM BATCH TRANSFER")
        print("="*30)
        print("Usage: python scream_batch_transfer.py <loan_number>")
        print("\nExample: python scream_batch_transfer.py 1225237672")
        sys.exit(1)
    
    loan_number = sys.argv[1]
    
    print(f"🚀 SCREAM BATCH TRANSFER FOR LOAN {loan_number}")
    print("="*60)
    
    # Get calls from database
    calls = get_loan_calls(loan_number)
    
    if not calls:
        print("❌ No untranscribed calls found")
        sys.exit(0)
    
    # Transfer files
    transfer_dir, transferred = transfer_files(calls)
    
    if transferred:
        # Create script for RTX
        create_rtx_script(transfer_dir, transferred)
    
    print("\n✅ Transfer complete!")

if __name__ == "__main__":
    main()