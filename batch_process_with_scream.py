#!/usr/bin/env python3
"""
Batch processor that uses existing scream_hybrid_pipeline.py
"""

import os
import sys
import subprocess
import time
import pymysql
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

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def download_audio_file(orkuid, filename):
    """Download audio file via SCP"""
    try:
        # Parse the filename to get the path
        # Format: 2025/06/20/14/20250620_145645_LOLW.wav
        remote_path = f"/var/log/orkaudio.prod.nfs/audio/{filename}"
        local_path = f"temp_audio/{orkuid}.wav"
        
        # Create temp directory
        os.makedirs("temp_audio", exist_ok=True)
        
        # Download file
        scp_command = [
            "scp",
            f"estillmane@s40vpsoxweb002:{remote_path}",
            local_path
        ]
        
        result = subprocess.run(scp_command, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(local_path):
            return local_path
        else:
            print(f"   ⚠️  Failed to download: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"   ⚠️  Download error: {e}")
        return None

def process_recordings(recordings):
    """Process recordings using scream_hybrid_pipeline.py"""
    
    processed = 0
    failed = 0
    start_time = time.time()
    total = len(recordings)
    
    for i, rec in enumerate(recordings, 1):
        print(f"\n[{i}/{total}] Processing: {rec['target_user']} - {rec['orkUid']}")
        print(f"  Timestamp: {rec['timestamp']}")
        print(f"  Duration: {rec['duration']}s ({rec['duration']/60:.1f}m)")
        
        try:
            # Download the audio file
            audio_path = download_audio_file(rec['orkUid'], rec['filename'])
            
            if not audio_path:
                failed += 1
                print(f"  ✗ Failed to download audio file")
                continue
            
            # Run scream_hybrid_pipeline.py
            cmd = [
                sys.executable,
                "scream_hybrid_pipeline.py",
                rec['orkUid'],
                audio_path
            ]
            
            # Add user info as environment variables for the pipeline
            env = os.environ.copy()
            env['USER_FIRSTNAME'] = rec.get('user_firstname', '')
            env['USER_LASTNAME'] = rec.get('user_lastname', '')
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                processed += 1
                print(f"  ✓ Processed successfully")
            else:
                failed += 1
                print(f"  ✗ Pipeline failed: {result.stderr}")
            
            # Clean up temp file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Show progress
            elapsed = time.time() - start_time
            rate = processed / (elapsed / 3600) if elapsed > 0 else 0
            remaining = (total - i) / rate if rate > 0 else 0
            
            print(f"  Progress: {i}/{total} ({i/total*100:.1f}%)")
            print(f"  Processed: {processed}, Failed: {failed}")
            print(f"  Rate: {rate:.1f} recordings/hour")
            print(f"  Est. time remaining: {remaining:.1f} hours")
            
        except Exception as e:
            failed += 1
            print(f"  ✗ Error: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE!")
    print(f"- Processed: {processed}")
    print(f"- Failed: {failed}")
    print(f"- Total time: {(time.time() - start_time)/60:.1f} minutes")
    print("=" * 80)

def main():
    """Main function - accepts recordings data from stdin or file"""
    
    # Check if scream_hybrid_pipeline.py exists
    if not os.path.exists("scream_hybrid_pipeline.py"):
        print("ERROR: scream_hybrid_pipeline.py not found in current directory")
        print("Please ensure you're running from the correct directory")
        return
    
    # For testing with a small batch
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("TEST MODE: Processing first 3 recordings only")
        
        # Get a few test recordings
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                t.orkUid,
                t.filename,
                t.duration,
                t.timestamp,
                t.localParty,
                t.remoteParty,
                'Test User' as target_user,
                'Test' as user_firstname,
                'User' as user_lastname
            FROM orktape t
            WHERE t.timestamp >= '2025-06-01'
            AND t.timestamp <= '2025-06-20'
            AND t.duration >= 90
            LIMIT 3
        """)
        
        recordings = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if recordings:
            process_recordings(recordings)
        else:
            print("No test recordings found")
    else:
        print("This script should be called from process_users_fresh_start.py")
        print("Or run with --test flag to test with 3 recordings")

if __name__ == "__main__":
    main()