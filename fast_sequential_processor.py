#!/usr/bin/env python3
"""
Optimized sequential processor - single model, maximum efficiency
Processes recordings one by one but with optimizations
"""

import os
import sys
import json
import re
import time
import pymysql
import subprocess
from faster_whisper import WhisperModel
from datetime import datetime

# Copy user finding code
exec(open('process_users_fresh_start.py').read().split('def main():')[0])

class OptimizedProcessor:
    def __init__(self):
        print("Initializing Optimized Sequential Processor...")
        
        # Load model ONCE
        self.model = WhisperModel(
            "models/faster-whisper-large-v3-turbo-ct2",
            device="cuda",
            compute_type="int8_float16"
        )
        print("✓ Whisper model loaded")
        
        # Pre-compile regex patterns
        self.loan_patterns = [
            re.compile(r'\b\d{8}\b'),
            re.compile(r'\b\d{9}\b'),
            re.compile(r'\b\d{10}\b'),
            re.compile(r'\b\d{7}\b'),
            re.compile(r'loan\s*#?\s*(\d{7,10})', re.IGNORECASE),
            re.compile(r'number\s*#?\s*(\d{7,10})', re.IGNORECASE),
        ]
        
        # Database connection (reuse)
        self.db_conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.db_conn.cursor()
        
        # Directories
        self.transcript_dir = "C:/transcripts" if sys.platform == "win32" else "transcripts"
        os.makedirs(self.transcript_dir, exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
    
    def process_recording(self, rec):
        """Process single recording efficiently"""
        orkuid = rec['orkUid']
        
        try:
            # 1. Download
            remote_path = f"/var/log/orkaudio.prod.nfs/audio/{rec['filename']}"
            local_path = f"temp_audio/{orkuid}.wav"
            
            scp_cmd = ["scp", "-q", f"estillmane@s40vpsoxweb002:{remote_path}", local_path]
            if subprocess.run(scp_cmd, capture_output=True).returncode != 0:
                return False, []
            
            # 2. Transcribe (optimized settings)
            start = time.time()
            segments, info = self.model.transcribe(
                local_path,
                language="en",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text = " ".join([s.text.strip() for s in segments])
            speed = info.duration / (time.time() - start)
            
            # 3. Extract loans
            loans = set()
            for pattern in self.loan_patterns:
                for match in pattern.findall(text):
                    if isinstance(match, tuple):
                        match = match[0]
                    if match.isdigit() and 7 <= len(match) <= 10:
                        loans.add(match)
            loans = list(loans)
            
            # 4. Save transcript
            date_path = rec['timestamp'].strftime("%Y/%m/%d")
            os.makedirs(os.path.join(self.transcript_dir, date_path), exist_ok=True)
            transcript_path = os.path.join(self.transcript_dir, date_path, f"{orkuid}.txt")
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # 5. Database operations (batch for efficiency)
            self.cursor.execute("""
                INSERT INTO call_transcripts_v2 
                (orkuid, summary, transcript_path, loan_numbers, sentiment, 
                 processing_time_ms, whisper_model, summary_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    transcript_path = VALUES(transcript_path),
                    loan_numbers = VALUES(loan_numbers)
            """, (
                orkuid, '[No summary]', transcript_path, json.dumps(loans),
                'neutral', int((time.time() - start) * 1000), 'large-v3-turbo', 'none'
            ))
            
            # Update loan index
            if loans:
                user_name = f"{rec.get('user_firstname', '')} {rec.get('user_lastname', '')}".strip()
                for loan in loans:
                    self.cursor.execute("""
                        INSERT IGNORE INTO loan_number_index
                        (loan_number, orkuid, user_name, user_firstname, user_lastname,
                         call_date, call_timestamp, duration)
                        VALUES (%s, %s, %s, %s, %s, DATE(%s), %s, %s)
                    """, (
                        loan, orkuid, user_name, rec.get('user_firstname'),
                        rec.get('user_lastname'), rec['timestamp'], 
                        rec['timestamp'], rec['duration']
                    ))
            
            # Cleanup
            os.remove(local_path)
            
            return True, loans
            
        except Exception as e:
            print(f"Error processing {orkuid}: {e}")
            return False, []
    
    def process_batch(self, recordings):
        """Process recordings efficiently"""
        total = len(recordings)
        processed = 0
        failed = 0
        loans_found = 0
        start_time = time.time()
        
        print(f"\nProcessing {total} recordings sequentially...")
        
        for i, rec in enumerate(recordings, 1):
            success, loans = self.process_recording(rec)
            
            if success:
                processed += 1
                if loans:
                    loans_found += 1
                    print(f"[{i}/{total}] ✓ {rec['target_user']} - Loans: {loans}")
                else:
                    print(f"[{i}/{total}] ✓ {rec['target_user']} - No loans")
            else:
                failed += 1
                print(f"[{i}/{total}] ✗ {rec['target_user']} - Failed")
            
            # Commit every 10 recordings
            if i % 10 == 0:
                self.db_conn.commit()
                
                # Progress
                elapsed = time.time() - start_time
                rate = i / (elapsed / 3600)
                remaining = (total - i) / rate if rate > 0 else 0
                
                print(f"\nProgress: {i}/{total} ({i/total*100:.1f}%)")
                print(f"Rate: {rate:.1f}/hour | ETA: {remaining:.1f} hours\n")
        
        # Final commit
        self.db_conn.commit()
        
        total_time = time.time() - start_time
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE!")
        print(f"- Processed: {processed}")
        print(f"- Failed: {failed}")
        print(f"- With loans: {loans_found}")
        print(f"- Time: {total_time/60:.1f} minutes")
        print(f"- Speed: {total / (total_time / 3600):.1f} recordings/hour")
        print("=" * 80)
    
    def cleanup(self):
        """Cleanup resources"""
        self.cursor.close()
        self.db_conn.close()

def main():
    print("=" * 80)
    print("OPTIMIZED SEQUENTIAL PROCESSOR")
    print("Single model instance, maximum efficiency")
    print("=" * 80)
    
    # Create tables
    if not create_tables_if_needed():
        return
    
    # Find all recordings (same as before)
    all_recordings = []
    # ... (same user finding code as other scripts)
    
    # Get recording count
    print(f"\nReady to process {len(all_recordings)} recordings")
    print("Expected speed: 20-30 recordings/hour")
    print(f"Estimated time: {len(all_recordings) / 25:.1f} hours")
    
    if input("\nProceed? (yes/no): ").lower() != 'yes':
        return
    
    # Process
    processor = OptimizedProcessor()
    try:
        processor.process_batch(all_recordings)
    finally:
        processor.cleanup()

if __name__ == "__main__":
    # If running standalone, just show info
    print("Optimized Sequential Processor")
    print("\nThis processor:")
    print("- Loads Whisper model ONCE")
    print("- Reuses database connection")
    print("- Batches commits every 10 records")
    print("- Pre-compiles regex patterns")
    print("- Minimal overhead between recordings")
    print("\nExpected: 20-30 recordings/hour on RTX 4090")