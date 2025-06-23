#!/usr/bin/env python3
"""
SCREAM Batch Processor
Process multiple recordings from database queue
"""

import os
import sys
import time
import subprocess
import tempfile
import pymysql
from datetime import datetime, timedelta
from scream_hybrid_pipeline import ScreamPipeline

print("=" * 80)
print("SCREAM BATCH PROCESSOR")
print("=" * 80)

# Configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

class BatchProcessor:
    def __init__(self, limit=10):
        self.limit = limit
        self.pipeline = ScreamPipeline()
        self.processed_count = 0
        self.error_count = 0
        
    def find_unprocessed_recordings(self):
        """Find recordings that need processing"""
        print("\nSearching for unprocessed recordings...")
        
        # Query for recordings not yet processed
        # Join with orksegment and orkuser to get underwriter info
        query = """
        SELECT 
            t.uid as orkuid,
            t.filename,
            t.duration,
            t.timestamp,
            u.firstname,
            u.lastname
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.uid = ct.orkuid
        LEFT JOIN orksegment s ON t.uid = s.fktape
        LEFT JOIN orkuser u ON s.fkuser = u.uid
        WHERE 
            ct.orkuid IS NULL  -- Not yet processed
            AND t.duration >= 120  -- At least 2 minutes
            AND t.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)  -- Last 7 days
        GROUP BY t.uid
        ORDER BY t.timestamp DESC
        LIMIT %s
        """
        
        cursor = self.pipeline.cursor
        cursor.execute(query, (self.limit,))
        recordings = cursor.fetchall()
        
        print(f"Found {len(recordings)} unprocessed recordings")
        return recordings
    
    def download_recording(self, orkuid, filename):
        """Download recording from remote server via SCP"""
        # Parse orkuid to build path
        year = orkuid[:4]
        month = orkuid[4:6]
        day = orkuid[6:8]
        hour = orkuid[9:11]
        
        remote_path = f"{REMOTE_BASE}/audio/{year}/{month}/{day}/{hour}/{filename}"
        
        # Create temp file
        temp_dir = tempfile.mkdtemp(prefix="scream_")
        local_path = os.path.join(temp_dir, filename)
        
        # SCP the file
        print(f"   Downloading {filename}...")
        scp_cmd = ['scp', '-q', f'{SSH_USER}@{SSH_HOST}:{remote_path}', local_path]
        
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            print(f"   ✓ Downloaded {file_size/1024/1024:.1f} MB")
            return local_path, temp_dir
        else:
            print(f"   ❌ Download failed: {result.stderr}")
            return None, temp_dir
    
    def process_batch(self):
        """Process a batch of recordings"""
        recordings = self.find_unprocessed_recordings()
        
        if not recordings:
            print("\nNo unprocessed recordings found")
            return
        
        print(f"\nProcessing {len(recordings)} recordings...")
        print("-" * 60)
        
        start_time = time.time()
        
        for idx, rec in enumerate(recordings, 1):
            orkuid = rec['orkuid']
            filename = rec['filename']
            duration = rec['duration']
            firstname = rec.get('firstname', 'Unknown')
            lastname = rec.get('lastname', 'User')
            
            print(f"\n[{idx}/{len(recordings)}] {orkuid}")
            print(f"   Underwriter: {firstname} {lastname}")
            print(f"   Duration: {duration}s")
            
            # Download file
            local_path, temp_dir = self.download_recording(orkuid, filename)
            
            if local_path:
                try:
                    # Process through pipeline
                    success = self.pipeline.process_recording(orkuid, local_path)
                    
                    if success:
                        self.processed_count += 1
                    else:
                        self.error_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Pipeline error: {e}")
                    self.error_count += 1
                finally:
                    # Clean up temp files
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
            else:
                self.error_count += 1
                # Clean up temp dir
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
        
        # Summary
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Processed: {self.processed_count}")
        print(f"Errors: {self.error_count}")
        print(f"Total time: {elapsed_time:.1f}s")
        print(f"Average: {elapsed_time/len(recordings):.1f}s per recording")
    
    def process_specific_user(self, firstname, lastname):
        """Process recordings for a specific user"""
        print(f"\nSearching for {firstname} {lastname} recordings...")
        
        try:
            # First check if the user exists
            check_user_query = """
            SELECT DISTINCT u.uid, u.firstname, u.lastname 
            FROM orkuser u
            WHERE u.firstname LIKE %s OR u.lastname LIKE %s
            LIMIT 10
            """
            
            cursor = self.pipeline.cursor
            cursor.execute(check_user_query, (f'%{firstname}%', f'%{lastname}%'))
            users = cursor.fetchall()
            
            if users:
                print(f"\nFound users matching '{firstname}' or '{lastname}':")
                for user in users:
                    print(f"  - {user['firstname']} {user['lastname']} (uid: {user['uid']})")
            else:
                print(f"\nNo users found matching '{firstname}' or '{lastname}'")
                
                # Let's check the orktape table directly for parties
                print("\nChecking recordings with party names...")
                party_query = """
                SELECT DISTINCT localparty, remoteparty 
                FROM orktape 
                WHERE localparty LIKE %s OR localparty LIKE %s 
                   OR remoteparty LIKE %s OR remoteparty LIKE %s
                LIMIT 10
                """
                cursor.execute(party_query, (f'%{firstname}%', f'%{lastname}%', f'%{firstname}%', f'%{lastname}%'))
                parties = cursor.fetchall()
                
                if parties:
                    print("\nFound party names:")
                    for party in parties:
                        print(f"  Local: {party['localparty']} | Remote: {party['remoteparty']}")
            
            query = """
            SELECT 
                t.uid as orkuid,
                t.filename,
                t.duration,
                t.timestamp,
                t.localparty,
                t.remoteparty
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.uid = ct.orkuid
            LEFT JOIN orksegment s ON t.uid = s.fktape
            LEFT JOIN orkuser u ON s.fkuser = u.uid
            WHERE 
                ct.orkuid IS NULL
                AND (
                    (u.firstname = %s AND u.lastname = %s)
                    OR t.localparty LIKE %s 
                    OR t.localparty LIKE %s
                    OR t.remoteparty LIKE %s
                    OR t.remoteparty LIKE %s
                )
                AND t.duration >= 120
            ORDER BY t.timestamp DESC
            LIMIT %s
            """
            
            cursor = self.pipeline.cursor
            full_name_pattern = f'%{firstname}%{lastname}%'
            cursor.execute(query, (
                firstname, lastname, 
                f'%{firstname}%', f'%{lastname}%',
                f'%{firstname}%', f'%{lastname}%',
                self.limit
            ))
            recordings = cursor.fetchall()
            
        except Exception as e:
            print(f"\n❌ Error searching for user: {e}")
            import traceback
            traceback.print_exc()
            recordings = []
        
        if recordings:
            print(f"Found {len(recordings)} unprocessed recordings for {firstname} {lastname}")
            # Process them
            for rec in recordings:
                rec['firstname'] = firstname
                rec['lastname'] = lastname
            
            # Temporarily store and process
            self.recordings = recordings
            self.process_batch()
        else:
            print(f"No unprocessed recordings found for {firstname} {lastname}")


# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--user" and len(sys.argv) >= 4:
            # Process specific user
            firstname = sys.argv[2]
            lastname = sys.argv[3]
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 5
            
            processor = BatchProcessor(limit=limit)
            try:
                processor.process_specific_user(firstname, lastname)
            finally:
                processor.pipeline.close()
        else:
            print("Usage:")
            print("  python scream_batch_processor.py")
            print("  python scream_batch_processor.py --user Eric Rawlins [limit]")
    else:
        # Process general batch
        processor = BatchProcessor(limit=10)
        try:
            processor.process_batch()
        finally:
            processor.pipeline.close()