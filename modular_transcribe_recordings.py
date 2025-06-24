#!/usr/bin/env python3
"""
Modular recording transcription system with configurable filters.

Usage:
    # Transcribe Eric Rawlins' June recordings > 60 seconds
    python modular_transcribe_recordings.py --name "Eric Rawlins" --month 6 --min-duration 60
    
    # Transcribe all recordings for a specific loan number
    python modular_transcribe_recordings.py --loan-number 1234567
    
    # Transcribe recordings from a specific date range
    python modular_transcribe_recordings.py --start-date 2025-06-01 --end-date 2025-06-30
"""

import os
import sys
import time
import json
import argparse
import paramiko
import pymysql
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

try:
    from faster_whisper import WhisperModel
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: pip install faster-whisper==1.1.1 tqdm")
    sys.exit(1)

# Configuration
class Config:
    SSH_USER = "estillmane"
    SSH_HOST = "s40vpsoxweb002"
    SSH_KEY_PATH = None  # Use default SSH key
    
    DB_HOST = "127.0.0.1"
    DB_PORT = 33306
    DB_USER = "root"
    DB_PASSWORD = "admin"
    DB_NAME = "oreka"
    
    REMOTE_BASE_PATH = "/var/log/orkaudio.prod.nfs/audio"
    LOCAL_TEMP_DIR = Path("temp_audio")
    OUTPUT_BASE_DIR = Path("transcriptions")
    MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
    
    # Processing options
    BATCH_SIZE = 5  # Process N recordings at a time
    MAX_RETRIES = 3
    CLEANUP_TEMP_FILES = True


class RecordingFilter:
    """Build SQL query based on filter criteria"""
    
    def __init__(self):
        self.conditions = []
        self.params = []
    
    def by_name(self, name: str):
        """Filter by participant name"""
        name_parts = name.lower().split()
        name_conditions = []
        
        for part in name_parts:
            name_conditions.append(
                f"(LOWER(r.localparty) LIKE '%{part}%' OR LOWER(r.remoteparty) LIKE '%{part}%')"
            )
        
        if name_conditions:
            self.conditions.append(f"({' AND '.join(name_conditions)})")
        return self
    
    def by_loan_number(self, loan_number: str):
        """Filter by loan number in filename"""
        self.conditions.append("r.filename LIKE %s")
        self.params.append(f"%{loan_number}%")
        return self
    
    def by_date_range(self, start_date: str, end_date: str):
        """Filter by date range"""
        self.conditions.append("r.timestamp >= %s AND r.timestamp < %s")
        self.params.extend([start_date, end_date])
        return self
    
    def by_month(self, year: int, month: int):
        """Filter by specific month"""
        start_date = f"{year}-{month:02d}-01 00:00:00"
        if month == 12:
            end_date = f"{year+1}-01-01 00:00:00"
        else:
            end_date = f"{year}-{month+1:02d}-01 00:00:00"
        
        return self.by_date_range(start_date, end_date)
    
    def by_min_duration(self, seconds: int):
        """Filter by minimum duration"""
        self.conditions.append(f"r.duration > {seconds}")
        return self
    
    def build_query(self) -> str:
        """Build the final SQL query"""
        base_query = """
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
            {conditions}
        ORDER BY 
            r.timestamp DESC
        """
        
        where_clause = " AND ".join(self.conditions) if self.conditions else "1=1"
        return base_query.format(conditions=where_clause)


class TranscriptionProcessor:
    """Handle the transcription process"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.ssh_client = None
        self.sftp_client = None
        
        # Ensure directories exist
        self.config.LOCAL_TEMP_DIR.mkdir(exist_ok=True)
    
    def load_model(self):
        """Load Whisper model"""
        if not Path(self.config.MODEL_PATH).exists():
            raise FileNotFoundError(f"Model not found at: {self.config.MODEL_PATH}")
        
        print(f"🚀 Loading Whisper model...")
        self.model = WhisperModel(
            self.config.MODEL_PATH,
            device="cuda",
            compute_type="int8_float16",
            num_workers=4
        )
        print("✅ Model loaded")
    
    def connect_ssh(self):
        """Establish SSH connection"""
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.config.SSH_KEY_PATH:
            self.ssh_client.connect(
                self.config.SSH_HOST, 
                username=self.config.SSH_USER, 
                key_filename=self.config.SSH_KEY_PATH
            )
        else:
            self.ssh_client.connect(
                self.config.SSH_HOST, 
                username=self.config.SSH_USER
            )
        
        self.sftp_client = self.ssh_client.open_sftp()
        print(f"✅ Connected to {self.config.SSH_HOST}")
    
    def query_recordings(self, filter_query: str, params: list = None) -> List[Dict]:
        """Query database for recordings"""
        recordings = []
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect SSH
            if self.config.SSH_KEY_PATH:
                ssh.connect(
                    self.config.SSH_HOST, 
                    username=self.config.SSH_USER, 
                    key_filename=self.config.SSH_KEY_PATH
                )
            else:
                ssh.connect(
                    self.config.SSH_HOST, 
                    username=self.config.SSH_USER
                )
            
            # Create tunnel
            transport = ssh.get_transport()
            dest_addr = ('127.0.0.1', 3306)
            local_addr = ('127.0.0.1', self.config.DB_PORT)
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
            
            # Connect to DB
            db = pymysql.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                charset='utf8mb4'
            )
            
            cursor = db.cursor()
            
            if params:
                cursor.execute(filter_query, params)
            else:
                cursor.execute(filter_query)
            
            results = cursor.fetchall()
            
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
            
        finally:
            ssh.close()
        
        return recordings
    
    def download_file(self, recording: Dict) -> Optional[Path]:
        """Download recording file"""
        timestamp = recording['timestamp']
        year = timestamp.strftime('%Y')
        month = timestamp.strftime('%m')
        day = timestamp.strftime('%d')
        hour = timestamp.strftime('%H')
        
        remote_path = f"{self.config.REMOTE_BASE_PATH}/{year}/{month}/{day}/{hour}/{recording['filename']}"
        local_path = self.config.LOCAL_TEMP_DIR / recording['filename']
        
        try:
            print(f"📥 Downloading: {recording['filename']}")
            self.sftp_client.get(remote_path, str(local_path))
            return local_path
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def transcribe_file(self, audio_path: Path) -> Optional[Dict]:
        """Transcribe audio file"""
        try:
            start_time = time.time()
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=1,
                best_of=1,
                temperature=0,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                ),
                language="en"
            )
            
            full_text = " ".join(segment.text for segment in segments)
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
    
    def extract_metadata(self, text: str) -> Dict:
        """Extract metadata from transcript"""
        import re
        
        # Extract loan number
        loan_pattern = r'\b\d{7,10}\b'
        loan_matches = re.findall(loan_pattern, text)
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_matches = re.findall(phone_pattern, text)
        
        return {
            'loan_numbers': list(set(loan_matches)),
            'phone_numbers': list(set(phone_matches)),
            'word_count': len(text.split())
        }
    
    def save_results(self, recording: Dict, transcription: Dict, output_dir: Path):
        """Save transcription results"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract metadata
        metadata = self.extract_metadata(transcription['text'])
        
        # Save JSON
        json_file = output_dir / f"{recording['filename']}.json"
        output_data = {
            'recording': recording,
            'transcription': transcription,
            'metadata': metadata,
            'processed_at': datetime.now().isoformat()
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        # Save text
        text_file = output_dir / f"{recording['filename']}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Recording: {recording['filename']}\n")
            f.write(f"Date: {recording['timestamp']}\n")
            f.write(f"Duration: {recording['duration']}s\n")
            f.write(f"Parties: {recording['localparty']} <-> {recording['remoteparty']}\n")
            f.write(f"Loan Numbers: {', '.join(metadata['loan_numbers']) or 'None found'}\n")
            f.write(f"Speed: {transcription['speed_factor']:.2f}x real-time\n")
            f.write(f"\n{'='*60}\n\n")
            f.write(transcription['text'])
        
        return json_file
    
    def process_recordings(self, recordings: List[Dict], output_name: str) -> Tuple[int, int]:
        """Process a list of recordings"""
        if not self.model:
            self.load_model()
        
        if not self.ssh_client:
            self.connect_ssh()
        
        output_dir = self.config.OUTPUT_BASE_DIR / output_name
        processed = 0
        failed = 0
        
        print(f"\n📋 Processing {len(recordings)} recordings...")
        
        for recording in tqdm(recordings, desc="Transcribing"):
            # Download
            local_path = self.download_file(recording)
            if not local_path:
                failed += 1
                continue
            
            # Transcribe
            result = self.transcribe_file(local_path)
            if not result:
                failed += 1
                if self.config.CLEANUP_TEMP_FILES:
                    local_path.unlink()
                continue
            
            # Save results
            self.save_results(recording, result, output_dir)
            processed += 1
            
            # Cleanup
            if self.config.CLEANUP_TEMP_FILES:
                local_path.unlink()
        
        return processed, failed
    
    def close(self):
        """Close connections"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Modular recording transcription system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Filter options
    parser.add_argument("--name", help="Filter by participant name")
    parser.add_argument("--loan-number", help="Filter by loan number")
    parser.add_argument("--month", type=int, help="Filter by month (1-12)")
    parser.add_argument("--year", type=int, default=2025, help="Year (default: 2025)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--min-duration", type=int, default=0, help="Minimum duration in seconds")
    
    # Processing options
    parser.add_argument("--output-name", help="Output directory name")
    parser.add_argument("--limit", type=int, help="Limit number of recordings to process")
    
    args = parser.parse_args()
    
    # Build filter
    filter_obj = RecordingFilter()
    
    if args.name:
        filter_obj.by_name(args.name)
    
    if args.loan_number:
        filter_obj.by_loan_number(args.loan_number)
    
    if args.month:
        filter_obj.by_month(args.year, args.month)
    elif args.start_date and args.end_date:
        filter_obj.by_date_range(args.start_date, args.end_date)
    
    if args.min_duration:
        filter_obj.by_min_duration(args.min_duration)
    
    # Generate output name if not provided
    if not args.output_name:
        parts = []
        if args.name:
            parts.append(args.name.lower().replace(" ", "_"))
        if args.month:
            parts.append(f"{args.year}_{args.month:02d}")
        if args.loan_number:
            parts.append(f"loan_{args.loan_number}")
        
        args.output_name = "_".join(parts) or "recordings"
    
    # Process
    config = Config()
    processor = TranscriptionProcessor(config)
    
    try:
        # Query recordings
        query = filter_obj.build_query()
        if args.limit:
            query += f" LIMIT {args.limit}"
        
        print("🔍 Querying database...")
        recordings = processor.query_recordings(query, filter_obj.params)
        
        if not recordings:
            print("❌ No recordings found matching criteria")
            return
        
        # Display summary
        total_duration = sum(r['duration'] for r in recordings)
        print(f"\n📊 Found {len(recordings)} recordings")
        print(f"   Total duration: {total_duration/60:.1f} minutes")
        print(f"   Output directory: {config.OUTPUT_BASE_DIR / args.output_name}")
        
        # Process
        processed, failed = processor.process_recordings(recordings, args.output_name)
        
        # Summary
        print(f"\n✅ Processed: {processed}")
        print(f"❌ Failed: {failed}")
        
    finally:
        processor.close()


if __name__ == "__main__":
    main()