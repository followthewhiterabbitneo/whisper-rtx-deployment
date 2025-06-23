#!/usr/bin/env python3
"""
Fast loan extractor - Whisper transcription + loan extraction only
No Gemma summaries for maximum speed
"""

import os
import sys
import json
import re
import time
import pymysql
import paramiko
from faster_whisper import WhisperModel
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

class FastLoanExtractor:
    def __init__(self):
        print("Initializing Fast Loan Extractor...")
        
        # Initialize Whisper model
        self.model_path = "models/faster-whisper-large-v3-turbo-ct2"
        print(f"Loading Whisper model from {self.model_path}...")
        
        self.whisper_model = WhisperModel(
            self.model_path,
            device="cuda",
            compute_type="int8_float16"  # Optimal for turbo
        )
        print("✓ Whisper model loaded")
        
        # Initialize database
        self.db_conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.db_conn.cursor(pymysql.cursors.DictCursor)
        print("✓ Database connected")
        
        # SSH for file download
        self.ssh_client = None
        self.sftp_client = None
        self.init_ssh()
        
        # Transcript directory
        self.transcript_dir = "C:/transcripts" if sys.platform == "win32" else "transcripts"
        os.makedirs(self.transcript_dir, exist_ok=True)
        
        # Loan number patterns
        self.loan_patterns = [
            r'\b\d{8}\b',           # 8 digits
            r'\b\d{9}\b',           # 9 digits  
            r'\b\d{10}\b',          # 10 digits
            r'\b\d{7}\b',           # 7 digits
            r'loan\s*#?\s*(\d{7,10})', # "loan #12345678"
            r'number\s*#?\s*(\d{7,10})', # "number 12345678"
        ]
    
    def init_ssh(self):
        """Initialize SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect('s40vpsoxweb002', username='estillmane')
            self.sftp_client = self.ssh_client.open_sftp()
            print("✓ SSH connected")
        except Exception as e:
            print(f"⚠️  SSH connection failed: {e}")
    
    def download_audio(self, filename, orkuid):
        """Download audio file via SFTP"""
        try:
            remote_path = f"/var/log/orkaudio.prod.nfs/audio/{filename}"
            local_path = f"temp_audio/{orkuid}.wav"
            
            os.makedirs("temp_audio", exist_ok=True)
            self.sftp_client.get(remote_path, local_path)
            
            return local_path
        except Exception as e:
            print(f"   ⚠️  Download failed: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio with Whisper - turbo speed"""
        try:
            start_time = time.time()
            
            # Transcribe with turbo model
            segments, info = self.whisper_model.transcribe(
                audio_path,
                language="en",
                task="transcribe",
                beam_size=1,  # Faster with beam_size=1
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=100
                )
            )
            
            # Combine segments
            full_text = " ".join([seg.text.strip() for seg in segments])
            
            transcribe_time = time.time() - start_time
            audio_duration = info.duration
            speed_factor = audio_duration / transcribe_time if transcribe_time > 0 else 0
            
            return {
                'text': full_text,
                'duration': audio_duration,
                'transcribe_time': transcribe_time,
                'speed_factor': speed_factor
            }
            
        except Exception as e:
            print(f"   ⚠️  Transcription failed: {e}")
            return None
    
    def extract_loan_numbers(self, text):
        """Extract loan numbers from transcript"""
        loan_numbers = set()
        
        for pattern in self.loan_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract just the number if it's a group match
                if isinstance(match, tuple):
                    match = match[0]
                if isinstance(match, str) and match.isdigit() and 7 <= len(match) <= 10:
                    loan_numbers.add(match)
        
        return list(loan_numbers)
    
    def save_transcript(self, orkuid, transcript_text, timestamp):
        """Save transcript to filesystem"""
        try:
            # Create directory structure: YYYY/MM/DD
            date_path = timestamp.strftime("%Y/%m/%d")
            full_path = os.path.join(self.transcript_dir, date_path)
            os.makedirs(full_path, exist_ok=True)
            
            # Save transcript
            transcript_file = os.path.join(full_path, f"{orkuid}.txt")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            return transcript_file
        except Exception as e:
            print(f"   ⚠️  Failed to save transcript: {e}")
            return None
    
    def save_to_database(self, orkuid, loan_numbers, transcript_path, processing_time_ms):
        """Save minimal info to database - no summary"""
        try:
            # Save to call_transcripts_v2
            self.cursor.execute("""
                INSERT INTO call_transcripts_v2 
                (orkuid, summary, transcript_path, loan_numbers, sentiment, 
                 processing_time_ms, whisper_model, summary_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    transcript_path = VALUES(transcript_path),
                    loan_numbers = VALUES(loan_numbers),
                    processing_time_ms = VALUES(processing_time_ms),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                orkuid,
                '[No summary - fast mode]',  # Placeholder summary
                transcript_path,
                json.dumps(loan_numbers),
                'neutral',  # Default sentiment
                processing_time_ms,
                'large-v3-turbo',
                'none'  # No summary model
            ))
            
            self.db_conn.commit()
            return True
            
        except Exception as e:
            print(f"   ⚠️  Database save failed: {e}")
            self.db_conn.rollback()
            return False
    
    def update_loan_index(self, orkuid, loan_numbers, call_info):
        """Update loan number search index"""
        if not loan_numbers:
            return
        
        try:
            # Extract user info
            user_name = f"{call_info.get('user_firstname', '')} {call_info.get('user_lastname', '')}".strip()
            
            for loan_number in loan_numbers:
                self.cursor.execute("""
                    INSERT IGNORE INTO loan_number_index
                    (loan_number, orkuid, user_name, user_firstname, user_lastname,
                     call_date, call_timestamp, duration)
                    VALUES (%s, %s, %s, %s, %s, DATE(%s), %s, %s)
                """, (
                    loan_number,
                    orkuid,
                    user_name if user_name else None,
                    call_info.get('user_firstname'),
                    call_info.get('user_lastname'),
                    call_info.get('timestamp'),
                    call_info.get('timestamp'),
                    call_info.get('duration', 0)
                ))
            
            self.db_conn.commit()
            
        except Exception as e:
            print(f"   ⚠️  Failed to update loan index: {e}")
    
    def process_recording(self, recording_info):
        """Process a single recording - fast mode"""
        orkuid = recording_info['orkUid']
        filename = recording_info['filename']
        
        try:
            # Download audio
            audio_path = self.download_audio(filename, orkuid)
            if not audio_path:
                return False
            
            # Transcribe
            result = self.transcribe_audio(audio_path)
            if not result:
                return False
            
            print(f"   ✓ Transcribed in {result['transcribe_time']:.1f}s (speed: {result['speed_factor']:.1f}x)")
            
            # Extract loan numbers
            loan_numbers = self.extract_loan_numbers(result['text'])
            if loan_numbers:
                print(f"   ✓ Found loan numbers: {loan_numbers}")
            else:
                print(f"   ⚠️  No loan numbers found")
            
            # Save transcript
            transcript_path = self.save_transcript(orkuid, result['text'], recording_info['timestamp'])
            
            # Save to database (minimal)
            processing_time_ms = int(result['transcribe_time'] * 1000)
            if self.save_to_database(orkuid, loan_numbers, transcript_path, processing_time_ms):
                print(f"   ✓ Saved to database")
            
            # Update loan index
            self.update_loan_index(orkuid, loan_numbers, recording_info)
            
            # Clean up
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return True
            
        except Exception as e:
            print(f"   ✗ Processing failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.cursor:
            self.cursor.close()
        if self.db_conn:
            self.db_conn.close()
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()

def main():
    """Main function for standalone testing"""
    if len(sys.argv) < 3:
        print("Usage: python fast_loan_extractor.py <orkuid> <filename>")
        print("Example: python fast_loan_extractor.py 20250620_145645_LOLW 2025/06/20/14/20250620_145645_LOLW.wav")
        return
    
    orkuid = sys.argv[1]
    filename = sys.argv[2]
    
    extractor = FastLoanExtractor()
    
    try:
        recording_info = {
            'orkUid': orkuid,
            'filename': filename,
            'timestamp': datetime.now(),
            'duration': 0,
            'user_firstname': 'Test',
            'user_lastname': 'User'
        }
        
        print(f"\nProcessing {orkuid}...")
        success = extractor.process_recording(recording_info)
        
        if success:
            print("\n✓ Processing complete!")
        else:
            print("\n✗ Processing failed!")
            
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    main()