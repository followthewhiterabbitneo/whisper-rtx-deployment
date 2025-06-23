#!/usr/bin/env python3
"""
Parallel fast loan extraction - 4 workers for maximum speed
No paramiko dependency - uses subprocess for scp
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import queue

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Global lock for database operations
db_lock = Lock()

class FastWorker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        print(f"[Worker {worker_id}] Initializing...")
        
        # Initialize Whisper model
        self.model_path = "models/faster-whisper-large-v3-turbo-ct2"
        self.whisper_model = WhisperModel(
            self.model_path,
            device="cuda",
            compute_type="int8_float16",
            device_index=0  # All workers share GPU
        )
        print(f"[Worker {worker_id}] ✓ Whisper model loaded")
        
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
    
    def download_audio(self, filename, orkuid):
        """Download audio file via scp subprocess"""
        try:
            remote_path = f"/var/log/orkaudio.prod.nfs/audio/{filename}"
            local_path = f"temp_audio/worker{self.worker_id}_{orkuid}.wav"
            
            os.makedirs("temp_audio", exist_ok=True)
            
            # Use scp command
            cmd = [
                "scp",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                f"estillmane@s40vpsoxweb002:{remote_path}",
                local_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(local_path):
                return local_path
            else:
                print(f"[Worker {self.worker_id}] Download failed for {orkuid}")
                return None
                
        except Exception as e:
            print(f"[Worker {self.worker_id}] Download error: {e}")
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
                beam_size=1,  # Faster
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
            print(f"[Worker {self.worker_id}] Transcription failed: {e}")
            return None
    
    def extract_loan_numbers(self, text):
        """Extract loan numbers from transcript"""
        loan_numbers = set()
        
        for pattern in self.loan_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if isinstance(match, str) and match.isdigit() and 7 <= len(match) <= 10:
                    loan_numbers.add(match)
        
        return list(loan_numbers)
    
    def save_transcript(self, orkuid, transcript_text, timestamp):
        """Save transcript to filesystem"""
        try:
            date_path = timestamp.strftime("%Y/%m/%d")
            full_path = os.path.join(self.transcript_dir, date_path)
            os.makedirs(full_path, exist_ok=True)
            
            transcript_file = os.path.join(full_path, f"{orkuid}.txt")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            return transcript_file
        except Exception as e:
            print(f"[Worker {self.worker_id}] Failed to save transcript: {e}")
            return None
    
    def save_to_database(self, orkuid, loan_numbers, transcript_path, processing_time_ms):
        """Save to database with thread safety"""
        with db_lock:
            try:
                conn = pymysql.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                cursor.execute("""
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
                    '[No summary - fast mode]',
                    transcript_path,
                    json.dumps(loan_numbers),
                    'neutral',
                    processing_time_ms,
                    'large-v3-turbo',
                    'none'
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                print(f"[Worker {self.worker_id}] Database save failed: {e}")
                return False
    
    def update_loan_index(self, orkuid, loan_numbers, call_info):
        """Update loan index with thread safety"""
        if not loan_numbers:
            return
        
        with db_lock:
            try:
                conn = pymysql.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                user_name = f"{call_info.get('user_firstname', '')} {call_info.get('user_lastname', '')}".strip()
                
                for loan_number in loan_numbers:
                    cursor.execute("""
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
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"[Worker {self.worker_id}] Failed to update loan index: {e}")
    
    def process_recording(self, recording_info):
        """Process a single recording"""
        orkuid = recording_info['orkUid']
        
        try:
            # Download audio
            audio_path = self.download_audio(recording_info['filename'], orkuid)
            if not audio_path:
                return False, orkuid, []
            
            # Transcribe
            result = self.transcribe_audio(audio_path)
            if not result:
                return False, orkuid, []
            
            # Extract loan numbers
            loan_numbers = self.extract_loan_numbers(result['text'])
            
            # Save transcript
            transcript_path = self.save_transcript(orkuid, result['text'], recording_info['timestamp'])
            
            # Save to database
            processing_time_ms = int(result['transcribe_time'] * 1000)
            self.save_to_database(orkuid, loan_numbers, transcript_path, processing_time_ms)
            
            # Update loan index
            self.update_loan_index(orkuid, loan_numbers, recording_info)
            
            # Clean up
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return True, orkuid, loan_numbers
            
        except Exception as e:
            print(f"[Worker {self.worker_id}] Processing failed for {orkuid}: {e}")
            return False, orkuid, []

def process_batch_parallel(recordings, num_workers=4):
    """Process recordings in parallel with multiple workers"""
    
    print(f"\nStarting parallel processing with {num_workers} workers...")
    
    # Stats
    total = len(recordings)
    processed = 0
    failed = 0
    loans_found = 0
    start_time = time.time()
    
    # Create work queue
    work_queue = queue.Queue()
    for rec in recordings:
        work_queue.put(rec)
    
    # Process with thread pool
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Create workers
        workers = [FastWorker(i) for i in range(num_workers)]
        
        # Submit initial batch
        futures = {}
        for i in range(min(num_workers * 2, total)):  # Start with 2x workers
            if not work_queue.empty():
                rec = work_queue.get()
                future = executor.submit(workers[i % num_workers].process_recording, rec)
                futures[future] = rec
        
        # Process results and submit new work
        while futures:
            # Wait for any future to complete
            done, pending = as_completed(futures), []
            
            for future in done:
                rec = futures[future]
                try:
                    success, orkuid, loan_numbers = future.result()
                    
                    if success:
                        processed += 1
                        if loan_numbers:
                            loans_found += 1
                            print(f"[{processed}/{total}] ✓ {rec['target_user']} - {orkuid} - Loans: {loan_numbers}")
                        else:
                            print(f"[{processed}/{total}] ✓ {rec['target_user']} - {orkuid} - No loans")
                    else:
                        failed += 1
                        print(f"[{processed + failed}/{total}] ✗ {rec['target_user']} - {orkuid} - Failed")
                    
                    # Progress stats
                    completed = processed + failed
                    elapsed = time.time() - start_time
                    rate = completed / (elapsed / 3600) if elapsed > 0 else 0
                    remaining = (total - completed) / rate if rate > 0 else 0
                    
                    if completed % 10 == 0:  # Every 10 recordings
                        print(f"\n--- Progress: {completed}/{total} ({completed/total*100:.1f}%) ---")
                        print(f"Success rate: {processed}/{completed} ({processed/completed*100:.1f}%)")
                        print(f"Loans found: {loans_found}/{processed} recordings")
                        print(f"Rate: {rate:.1f} recordings/hour")
                        print(f"Est. remaining: {remaining:.1f} hours\n")
                    
                except Exception as e:
                    failed += 1
                    print(f"Future failed: {e}")
                
                # Remove completed future
                del futures[future]
                
                # Submit new work
                if not work_queue.empty():
                    rec = work_queue.get()
                    worker_id = (processed + failed) % num_workers
                    future = executor.submit(workers[worker_id].process_recording, rec)
                    futures[future] = rec
    
    # Final stats
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("PARALLEL PROCESSING COMPLETE!")
    print(f"- Workers: {num_workers}")
    print(f"- Processed: {processed}")
    print(f"- Failed: {failed}")
    print(f"- Recordings with loans: {loans_found}")
    print(f"- Total time: {total_time/60:.1f} minutes")
    print(f"- Average speed: {(processed + failed) / (total_time / 3600):.1f} recordings/hour")
    print(f"- Per worker: {(processed + failed) / num_workers / (total_time / 3600):.1f} recordings/hour")
    print("=" * 80)

# For testing
if __name__ == "__main__":
    print("This module should be imported by process_users_fast_parallel.py")
    print("Testing single worker...")
    
    worker = FastWorker(0)
    test_rec = {
        'orkUid': 'TEST001',
        'filename': '2025/06/01/00/TEST001.wav',
        'timestamp': datetime.now(),
        'duration': 180,
        'target_user': 'Test User',
        'user_firstname': 'Test',
        'user_lastname': 'User'
    }
    
    success, orkuid, loans = worker.process_recording(test_rec)
    print(f"Test result: {success}, Loans: {loans}")