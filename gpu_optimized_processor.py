#!/usr/bin/env python3
"""
GPU-optimized processor - maximize RTX 4090 usage
- Pre-download files to minimize I/O wait
- Batch processing on GPU
- Multiple models if needed
"""

import os
import sys
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from faster_whisper import WhisperModel, BatchedInferencePipeline
import queue
import threading
from datetime import datetime
import pymysql
import re

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

class GPUOptimizedProcessor:
    def __init__(self, num_models=2):
        """Initialize with multiple models to use more VRAM"""
        print(f"Initializing {num_models} Whisper models for better GPU usage...")
        
        self.models = []
        for i in range(num_models):
            model = WhisperModel(
                "models/faster-whisper-large-v3-turbo-ct2",
                device="cuda",
                compute_type="int8_float16",
                num_workers=2,  # Multiple workers per model
                device_index=0
            )
            self.models.append(model)
            print(f"  Model {i+1} loaded")
        
        # Pre-download queue
        self.download_queue = queue.Queue(maxsize=100)
        self.process_queue = queue.Queue(maxsize=50)
        
        # Database pool
        self.db_lock = threading.Lock()
        
        # Loan patterns
        self.loan_patterns = [
            re.compile(r'\b\d{8}\b'),
            re.compile(r'\b\d{9}\b'),
            re.compile(r'\b\d{10}\b'),
            re.compile(r'\b\d{7}\b'),
        ]
        
        print(f"✓ Ready with {num_models} models (~{num_models*2}GB VRAM)")
    
    def downloader_thread(self, recordings):
        """Pre-download files in background"""
        print("Starting background downloader...")
        
        for rec in recordings:
            # Download file
            remote_path = f"/var/log/orkaudio.prod.nfs/audio/{rec['filename']}"
            local_path = f"temp_audio/pre_{rec['orkuid']}.wav"
            
            os.makedirs("temp_audio", exist_ok=True)
            
            scp_cmd = ["scp", "-q", f"estillmane@s40vpsoxweb002:{remote_path}", local_path]
            result = subprocess.run(scp_cmd, capture_output=True)
            
            if result.returncode == 0 and os.path.exists(local_path):
                self.download_queue.put((rec, local_path))
            else:
                print(f"Download failed: {rec['orkuid']}")
    
    def gpu_worker(self, worker_id, model):
        """GPU worker - processes files continuously"""
        print(f"GPU Worker {worker_id} started")
        
        while True:
            try:
                # Get pre-downloaded file
                rec, audio_path = self.download_queue.get(timeout=5)
                
                # Process on GPU
                start = time.time()
                segments, info = model.transcribe(
                    audio_path,
                    language="en",
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    vad_filter=True,
                    without_timestamps=True  # Faster
                )
                
                # Combine text
                text = " ".join([s.text.strip() for s in segments])
                gpu_time = time.time() - start
                
                # Extract loans
                loans = []
                for pattern in self.loan_patterns:
                    for match in pattern.findall(text):
                        if match.isdigit() and 7 <= len(match) <= 10:
                            loans.append(match)
                
                # Save results
                self.save_results(rec, text, loans, gpu_time)
                
                # Cleanup
                os.remove(audio_path)
                
                # Report
                speed = info.duration / gpu_time if gpu_time > 0 else 0
                status = f"Loans: {loans}" if loans else "No loans"
                print(f"[Worker {worker_id}] {rec['orkuid']} - {speed:.1f}x - {status}")
                
                self.download_queue.task_done()
                
            except queue.Empty:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    def save_results(self, rec, text, loans, gpu_time):
        """Save to database and filesystem"""
        with self.db_lock:
            try:
                conn = pymysql.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Save transcript
                date_path = rec['timestamp'].strftime("%Y/%m/%d")
                os.makedirs(f"C:/transcripts/{date_path}", exist_ok=True)
                transcript_path = f"C:/transcripts/{date_path}/{rec['orkuid']}.txt"
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                # Update database
                cursor.execute("""
                    INSERT INTO call_transcripts_v2 
                    (orkuid, summary, transcript_path, loan_numbers, sentiment, 
                     processing_time_ms, whisper_model, summary_model)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        transcript_path = VALUES(transcript_path),
                        loan_numbers = VALUES(loan_numbers)
                """, (
                    rec['orkuid'], '[GPU batch]', transcript_path,
                    json.dumps(loans), 'neutral', int(gpu_time * 1000),
                    'large-v3-turbo', 'none'
                ))
                
                # Update loan index
                if loans:
                    for loan in loans:
                        cursor.execute("""
                            INSERT IGNORE INTO loan_number_index
                            (loan_number, orkuid, user_name, call_date, call_timestamp, duration)
                            VALUES (%s, %s, %s, DATE(%s), %s, %s)
                        """, (
                            loan, rec['orkuid'], rec.get('target_user'),
                            rec['timestamp'], rec['timestamp'], rec['duration']
                        ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Save error: {e}")
    
    def process_batch(self, recordings):
        """Process with optimized GPU usage"""
        total = len(recordings)
        print(f"\nProcessing {total} recordings with GPU optimization...")
        
        # Start downloader thread
        dl_thread = threading.Thread(target=self.downloader_thread, args=(recordings,))
        dl_thread.start()
        
        # Start GPU workers
        gpu_threads = []
        for i, model in enumerate(self.models):
            for j in range(2):  # 2 threads per model
                worker_id = i * 2 + j
                t = threading.Thread(target=self.gpu_worker, args=(worker_id, model))
                gpu_threads.append(t)
                t.start()
        
        # Monitor progress
        start_time = time.time()
        processed = 0
        
        while dl_thread.is_alive() or not self.download_queue.empty():
            time.sleep(5)
            processed = total - self.download_queue.qsize()
            elapsed = time.time() - start_time
            rate = processed / (elapsed / 3600) if elapsed > 0 else 0
            
            print(f"\rProgress: {processed}/{total} ({processed/total*100:.1f}%) - "
                  f"Rate: {rate:.1f}/hour - Queue: {self.download_queue.qsize()}", end='')
        
        # Wait for completion
        dl_thread.join()
        self.download_queue.join()
        
        for t in gpu_threads:
            t.join()
        
        print(f"\n\nComplete! Processed {total} recordings in {(time.time()-start_time)/60:.1f} minutes")

def main():
    # Load recordings
    if not os.path.exists('recordings_to_transcribe.json'):
        print("Run smart_loan_network_finder.py first!")
        return
    
    with open('recordings_to_transcribe.json', 'r') as f:
        recordings = json.load(f)
    
    # Convert timestamps
    for rec in recordings:
        rec['orkuid'] = rec.get('orkuid', rec.get('orkUid'))
        rec['target_user'] = f"{rec.get('user_firstname', '')} {rec.get('user_lastname', '')}".strip()
        if isinstance(rec['timestamp'], str):
            rec['timestamp'] = datetime.fromisoformat(rec['timestamp'])
    
    print(f"Loaded {len(recordings)} recordings")
    
    # Check GPU
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu', 
                               '--format=csv,noheader'], capture_output=True, text=True)
        if result.returncode == 0:
            used, total, util = result.stdout.strip().split(', ')
            print(f"\nGPU Status: {used}/{total} ({util} utilization)")
    except:
        pass
    
    print("\nGPU Optimization Settings:")
    print("- 2 Whisper models (use more VRAM)")
    print("- 4 GPU workers total")
    print("- Pre-download queue")
    print("- Batch processing")
    
    if input("\nProcess with GPU optimization? (yes/no): ").lower() == 'yes':
        processor = GPUOptimizedProcessor(num_models=2)
        processor.process_batch(recordings)

if __name__ == "__main__":
    main()