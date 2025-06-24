#!/usr/bin/env python3
"""
Modular script to transcribe all Eric Rawlins recordings from June 2025
that are greater than 60 seconds in duration.

This script:
1. Connects to MariaDB via SSH tunnel
2. Queries for Eric Rawlins' June recordings > 60 seconds
3. Downloads audio files via SCP
4. Transcribes using Whisper large-v3-turbo
5. Saves transcriptions with metadata
"""

import os
import sys
import time
import json
import paramiko
import pymysql
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# Add faster_whisper import
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ faster_whisper not installed. Run: pip install faster-whisper==1.1.1")
    sys.exit(1)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
SSH_KEY_PATH = None  # Use default SSH key

DB_HOST = "127.0.0.1"
DB_PORT = 33306  # Local tunnel port
DB_USER = "root"
DB_PASSWORD = "admin"
DB_NAME = "oreka"

REMOTE_BASE_PATH = "/var/log/orkaudio.prod.nfs/audio"
LOCAL_TEMP_DIR = Path("temp_audio")
OUTPUT_DIR = Path("transcriptions/eric_rawlins_june")
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"

# Ensure directories exist
LOCAL_TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class SSHConnection:
    """Manage SSH connection and file transfers"""
    
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
    
    def connect(self):
        """Establish SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if SSH_KEY_PATH:
                self.ssh_client.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)
            else:
                self.ssh_client.connect(SSH_HOST, username=SSH_USER)
            
            self.sftp_client = self.ssh_client.open_sftp()
            print(f"✅ Connected to {SSH_HOST}")
            return True
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            return False
    
    def download_file(self, remote_path, local_path):
        """Download file via SCP"""
        try:
            print(f"📥 Downloading: {os.path.basename(remote_path)}")
            self.sftp_client.get(remote_path, str(local_path))
            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def close(self):
        """Close SSH connection"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()


@contextmanager
def ssh_tunnel():
    """Create SSH tunnel for database connection"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if SSH_KEY_PATH:
            ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)
        else:
            ssh.connect(SSH_HOST, username=SSH_USER)
        
        # Create tunnel
        transport = ssh.get_transport()
        local_bind_port = DB_PORT
        remote_bind_address = ('localhost', 3306)
        channel = transport.open_channel(
            "direct-tcpip",
            remote_bind_address,
            ('localhost', local_bind_port)
        )
        
        print(f"✅ SSH tunnel established on port {local_bind_port}")
        yield channel
        
    finally:
        ssh.close()


def query_eric_rawlins_june_recordings():
    """Query database for Eric Rawlins' June recordings > 60 seconds"""
    recordings = []
    
    try:
        # Connect via tunnel
        print("🔌 Connecting to database via SSH tunnel...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if SSH_KEY_PATH:
            ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)
        else:
            ssh.connect(SSH_HOST, username=SSH_USER)
        
        # Port forwarding
        transport = ssh.get_transport()
        dest_addr = ('127.0.0.1', 3306)
        local_addr = ('127.0.0.1', DB_PORT)
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
        
        # Connect to DB through tunnel
        db = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = db.cursor()
        
        # Query for Eric Rawlins' June 2025 recordings > 60 seconds
        query = """
        SELECT 
            r.filename,
            r.timestamp,
            r.duration,
            r.localparty,
            r.remoteparty,
            r.direction,
            r.id as recording_id
        FROM 
            orkrec r
        WHERE 
            (LOWER(r.localparty) LIKE '%eric%rawlins%' 
             OR LOWER(r.remoteparty) LIKE '%eric%rawlins%'
             OR LOWER(r.localparty) LIKE '%rawlins%eric%'
             OR LOWER(r.remoteparty) LIKE '%rawlins%eric%')
            AND r.timestamp >= '2025-06-01 00:00:00'
            AND r.timestamp < '2025-07-01 00:00:00'
            AND r.duration > 60
        ORDER BY 
            r.timestamp DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"\n📊 Found {len(results)} recordings for Eric Rawlins in June > 60 seconds")
        
        for row in results:
            recordings.append({
                'filename': row[0],
                'timestamp': row[1],
                'duration': row[2],
                'localparty': row[3],
                'remoteparty': row[4],
                'direction': row[5],
                'recording_id': row[6]
            })
        
        cursor.close()
        db.close()
        ssh.close()
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
    
    return recordings


def transcribe_audio(audio_path, model):
    """Transcribe audio file using Whisper"""
    try:
        print(f"🎙️ Transcribing: {audio_path.name}")
        
        start_time = time.time()
        segments, info = model.transcribe(
            str(audio_path),
            beam_size=1,      # Turbo setting
            best_of=1,        # Turbo setting  
            temperature=0,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            ),
            language="en"
        )
        
        # Collect full transcript
        full_text = ""
        for segment in segments:
            full_text += segment.text + " "
        
        transcribe_time = time.time() - start_time
        
        return {
            'text': full_text.strip(),
            'duration': info.duration,
            'language': info.language,
            'transcribe_time': transcribe_time,
            'speed_factor': transcribe_time / info.duration if info.duration > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None


def extract_loan_number(text):
    """Extract loan number from transcript"""
    import re
    
    # Pattern for loan numbers (7-10 digits)
    loan_pattern = r'\b\d{7,10}\b'
    
    matches = re.findall(loan_pattern, text)
    return matches[0] if matches else None


def main():
    """Main processing function"""
    print("=" * 60)
    print("Eric Rawlins June 2025 Recordings Transcription")
    print("=" * 60)
    
    # Step 1: Query database
    print("\n📊 Querying database for recordings...")
    recordings = query_eric_rawlins_june_recordings()
    
    if not recordings:
        print("❌ No recordings found")
        return
    
    # Display summary
    print(f"\n📋 Recording Summary:")
    total_duration = sum(r['duration'] for r in recordings)
    print(f"   - Total recordings: {len(recordings)}")
    print(f"   - Total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    print(f"   - Average duration: {total_duration/len(recordings):.1f} seconds")
    
    # Step 2: Load Whisper model
    print(f"\n🚀 Loading Whisper model...")
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found at: {MODEL_PATH}")
        print("Please ensure the Whisper model is downloaded")
        return
    
    model = WhisperModel(
        MODEL_PATH,
        device="cuda",
        compute_type="int8_float16",
        num_workers=4
    )
    print("✅ Model loaded")
    
    # Step 3: Process recordings
    ssh_conn = SSHConnection()
    if not ssh_conn.connect():
        return
    
    processed = 0
    failed = 0
    
    try:
        for i, recording in enumerate(recordings, 1):
            print(f"\n{'='*60}")
            print(f"Processing {i}/{len(recordings)}: {recording['filename']}")
            print(f"Duration: {recording['duration']}s, Time: {recording['timestamp']}")
            
            # Construct remote path
            timestamp = recording['timestamp']
            year = timestamp.strftime('%Y')
            month = timestamp.strftime('%m')
            day = timestamp.strftime('%d')
            hour = timestamp.strftime('%H')
            
            remote_path = f"{REMOTE_BASE_PATH}/{year}/{month}/{day}/{hour}/{recording['filename']}"
            local_path = LOCAL_TEMP_DIR / recording['filename']
            
            # Download file
            if ssh_conn.download_file(remote_path, local_path):
                # Transcribe
                result = transcribe_audio(local_path, model)
                
                if result:
                    # Extract loan number
                    loan_number = extract_loan_number(result['text'])
                    
                    # Save transcription
                    output_file = OUTPUT_DIR / f"{recording['filename']}.json"
                    output_data = {
                        'recording': recording,
                        'transcription': result,
                        'loan_number': loan_number,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, default=str)
                    
                    # Also save text version
                    text_file = OUTPUT_DIR / f"{recording['filename']}.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(f"Recording: {recording['filename']}\n")
                        f.write(f"Date: {recording['timestamp']}\n")
                        f.write(f"Duration: {recording['duration']}s\n")
                        f.write(f"Parties: {recording['localparty']} <-> {recording['remoteparty']}\n")
                        f.write(f"Loan Number: {loan_number or 'Not found'}\n")
                        f.write(f"Transcription Speed: {result['speed_factor']:.2f}x real-time\n")
                        f.write(f"\n{'='*60}\n\n")
                        f.write(result['text'])
                    
                    print(f"✅ Transcribed successfully")
                    print(f"   - Speed: {result['speed_factor']:.2f}x real-time")
                    print(f"   - Loan: {loan_number or 'Not found'}")
                    processed += 1
                    
                    # Clean up temp file
                    local_path.unlink()
                else:
                    failed += 1
            else:
                failed += 1
                
    finally:
        ssh_conn.close()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()