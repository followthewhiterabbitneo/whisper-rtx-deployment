#!/usr/bin/env python3
"""
Ultra-fast loan scanner - transcribe only first 30 seconds
If no loan number in first 30 seconds, skip the rest
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
import wave
import numpy as np

# Database config
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

class UltraFastLoanScanner:
    def __init__(self):
        print("Initializing Ultra-Fast Loan Scanner...")
        
        # Load Whisper model
        self.model = WhisperModel(
            "models/faster-whisper-large-v3-turbo-ct2",
            device="cuda",
            compute_type="int8_float16"
        )
        
        # Loan patterns
        self.loan_patterns = [
            re.compile(r'\b\d{8}\b'),
            re.compile(r'\b\d{9}\b'),
            re.compile(r'\b\d{10}\b'),
            re.compile(r'\b\d{7}\b'),
            re.compile(r'loan\s*#?\s*(\d{7,10})', re.IGNORECASE),
            re.compile(r'number\s*#?\s*(\d{7,10})', re.IGNORECASE),
            re.compile(r'account\s*#?\s*(\d{7,10})', re.IGNORECASE),
            re.compile(r'mortgage\s*#?\s*(\d{7,10})', re.IGNORECASE),
        ]
        
        # Quick scan keywords that suggest loan discussion
        self.loan_keywords = ['loan', 'mortgage', 'account', 'number', 'payment', 'balance']
        
        # Database
        self.db_conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.db_conn.cursor()
        
        os.makedirs("temp_audio", exist_ok=True)
        os.makedirs("quick_transcripts", exist_ok=True)
    
    def quick_scan(self, audio_path, max_seconds=30):
        """Quick scan first 30 seconds for loan numbers"""
        try:
            # Transcribe only first 30 seconds
            segments, info = self.model.transcribe(
                audio_path,
                language="en",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                max_new_tokens=128,  # Limit output length
                prefix="loan number account"  # Hint for better recognition
            )
            
            # Get text from first 30 seconds only
            text_30s = ""
            for segment in segments:
                if segment.start > max_seconds:
                    break
                text_30s += segment.text + " "
            
            # Quick check for loan keywords
            text_lower = text_30s.lower()
            has_loan_context = any(keyword in text_lower for keyword in self.loan_keywords)
            
            # Extract loan numbers
            loans = set()
            for pattern in self.loan_patterns:
                for match in pattern.findall(text_30s):
                    if isinstance(match, tuple):
                        match = match[0]
                    if match.isdigit() and 7 <= len(match) <= 10:
                        # Basic validation - not a phone number
                        if not match.startswith('1') and not match.startswith('555'):
                            loans.add(match)
            
            return {
                'has_loan_context': has_loan_context,
                'loan_numbers': list(loans),
                'text_preview': text_30s[:200],
                'should_full_scan': has_loan_context or len(loans) > 0
            }
            
        except Exception as e:
            print(f"Quick scan error: {e}")
            return None
    
    def full_transcribe(self, audio_path):
        """Full transcription if loan context found"""
        segments, info = self.model.transcribe(
            audio_path,
            language="en",
            beam_size=1,
            best_of=1,
            vad_filter=True
        )
        
        full_text = " ".join([s.text.strip() for s in segments])
        
        # Extract all loan numbers
        loans = set()
        for pattern in self.loan_patterns:
            for match in pattern.findall(full_text):
                if isinstance(match, tuple):
                    match = match[0]
                if match.isdigit() and 7 <= len(match) <= 10:
                    if not match.startswith('1') and not match.startswith('555'):
                        loans.add(match)
        
        return full_text, list(loans)
    
    def process_recording(self, rec):
        """Process with quick scan first"""
        orkuid = rec['orkUid']
        
        try:
            # Download
            remote_path = f"/var/log/orkaudio.prod.nfs/audio/{rec['filename']}"
            local_path = f"temp_audio/{orkuid}.wav"
            
            scp_cmd = ["scp", "-q", f"estillmane@s40vpsoxweb002:{remote_path}", local_path]
            if subprocess.run(scp_cmd, capture_output=True).returncode != 0:
                return 'failed', []
            
            # Quick scan first 30 seconds
            quick_result = self.quick_scan(local_path)
            
            if not quick_result:
                os.remove(local_path)
                return 'failed', []
            
            # If no loan context and no numbers, skip
            if not quick_result['should_full_scan']:
                os.remove(local_path)
                return 'skipped', []
            
            # Found potential loans - do full transcription
            full_text, all_loans = self.full_transcribe(local_path)
            
            # Save results
            if all_loans:
                # Save transcript
                with open(f"quick_transcripts/{orkuid}.txt", 'w') as f:
                    f.write(full_text)
                
                # Update database
                self.cursor.execute("""
                    INSERT INTO call_transcripts_v2 
                    (orkuid, summary, transcript_path, loan_numbers, sentiment, 
                     processing_time_ms, whisper_model, summary_model)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE loan_numbers = VALUES(loan_numbers)
                """, (
                    orkuid, '[Quick scan]', f"quick_transcripts/{orkuid}.txt",
                    json.dumps(all_loans), 'neutral', 0, 'large-v3-turbo', 'none'
                ))
                
                # Update loan index
                for loan in all_loans:
                    self.cursor.execute("""
                        INSERT IGNORE INTO loan_number_index
                        (loan_number, orkuid, user_name, call_date, call_timestamp, duration)
                        VALUES (%s, %s, %s, DATE(%s), %s, %s)
                    """, (
                        loan, orkuid, rec.get('target_user'),
                        rec['timestamp'], rec['timestamp'], rec['duration']
                    ))
                
                self.db_conn.commit()
            
            os.remove(local_path)
            return 'found' if all_loans else 'no_loans', all_loans
            
        except Exception as e:
            print(f"Error: {e}")
            return 'failed', []
    
    def cleanup(self):
        self.cursor.close()
        self.db_conn.close()

def scan_recordings(recordings):
    """Scan recordings with ultra-fast method"""
    scanner = UltraFastLoanScanner()
    
    stats = {
        'found': 0,
        'no_loans': 0, 
        'skipped': 0,
        'failed': 0,
        'total_loans': 0
    }
    
    start_time = time.time()
    
    try:
        for i, rec in enumerate(recordings, 1):
            print(f"\n[{i}/{len(recordings)}] {rec['target_user']} - {rec['orkUid']}")
            
            status, loans = scanner.process_recording(rec)
            stats[status] = stats.get(status, 0) + 1
            
            if loans:
                stats['total_loans'] += len(loans)
                print(f"  ✓ FOUND LOANS: {loans}")
            elif status == 'skipped':
                print(f"  ⚡ Skipped (no loan context in first 30s)")
            elif status == 'no_loans':
                print(f"  ✓ Processed (no loans found)")
            else:
                print(f"  ✗ Failed")
            
            # Progress
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / (elapsed / 3600)
                print(f"\nProgress: Found loans in {stats['found']}/{i} recordings")
                print(f"Skipped {stats['skipped']} recordings (no loan context)")
                print(f"Rate: {rate:.1f} recordings/hour")
    
    finally:
        scanner.cleanup()
    
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"Found loans: {stats['found']} recordings")
    print(f"No loans: {stats['no_loans']} recordings")  
    print(f"Skipped: {stats['skipped']} recordings")
    print(f"Failed: {stats['failed']} recordings")
    print(f"Total loans found: {stats['total_loans']}")
    print(f"Time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    print("Ultra-Fast Loan Scanner")
    print("Scans first 30 seconds, skips if no loan context")
    print("\nThis is a module - import and use scan_recordings()")