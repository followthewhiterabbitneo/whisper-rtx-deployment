#!/usr/bin/env python3
"""
Process recordings for all specified users in June 2025
Minimum duration: 90 seconds
"""

import os
import sys
import pymysql
from datetime import datetime
import time

# List of all users to process
USERS_TO_PROCESS = [
    "Hunter Gollehur",
    "Alexa Bidigare", 
    "Andrew Smith",
    "Audrey Sawmiller",
    "Dana Williams",
    "Eric Rawlins",
    "Jun Lee",
    "Louisa Fennell",
    "Nicholas Shields",
    "Nina Cousins",
    "Nolan Vander Wall",
    "Rykaia Garrett",
    "Chris Hoerle",
    "Amanda Herzberg",
    "Brandon Sorge",
    "Christian Hatchett",
    "Daniel Roger",
    "Eric Neil",
    "Gia Carroll",
    "Jonathon Abraham",
    "Kay Hicks",
    "Nayaisha Alexander Edmond",
    "Stefan Stajic",
    "Stephen Shields",
    "Stephen Twigg",
    "Zach Mladenoski"
]

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

def find_user_recordings(user_name, min_duration=90):
    """Find all recordings for a user in June 2025 with minimum duration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Split name for more flexible matching
        name_parts = user_name.split()
        firstname = name_parts[0] if name_parts else ''
        lastname = name_parts[-1] if len(name_parts) > 1 else ''
        
        # Query to find recordings - check multiple fields
        query = """
        SELECT DISTINCT
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            CASE 
                WHEN u1.firstname IS NOT NULL THEN CONCAT(u1.firstname, ' ', u1.lastname)
                WHEN u2.firstname IS NOT NULL THEN CONCAT(u2.firstname, ' ', u2.lastname)
                WHEN t.localParty LIKE %s THEN t.localParty
                WHEN t.remoteParty LIKE %s THEN t.remoteParty
                ELSE 'Unknown'
            END as user_name
        FROM orktape t
        LEFT JOIN orkuser u1 ON t.localParty = u1.id
        LEFT JOIN orkuser u2 ON t.remoteParty = u2.id
        WHERE t.timestamp >= '2025-06-01 00:00:00'
        AND t.timestamp <= '2025-06-20 23:59:59'
        AND t.duration >= %s
        AND (
            -- Check orkuser table
            (u1.firstname = %s AND u1.lastname = %s) OR
            (u2.firstname = %s AND u2.lastname = %s) OR
            -- Check full name in party fields
            t.localParty LIKE %s OR
            t.remoteParty LIKE %s OR
            -- Check individual name parts
            (t.localParty LIKE %s AND t.localParty LIKE %s) OR
            (t.remoteParty LIKE %s AND t.remoteParty LIKE %s)
        )
        ORDER BY t.timestamp ASC
        """
        
        cursor.execute(query, (
            f'%{user_name}%',  # For CASE statement
            f'%{user_name}%',  # For CASE statement
            min_duration,
            firstname, lastname,  # u1 check
            firstname, lastname,  # u2 check
            f'%{user_name}%',    # Full name in localParty
            f'%{user_name}%',    # Full name in remoteParty
            f'%{firstname}%', f'%{lastname}%',  # Parts in localParty
            f'%{firstname}%', f'%{lastname}%'   # Parts in remoteParty
        ))
        
        recordings = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return recordings
        
    except Exception as e:
        print(f"Database error: {e}")
        return []

def check_already_processed(orkuid):
    """Check if recording has already been processed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT orkuid FROM call_transcripts_v2 
            WHERE orkuid = %s
        """, (orkuid,))
        
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        print(f"Error checking processed status: {e}")
        return False

def main():
    print("=" * 80)
    print(f"Processing recordings for {len(USERS_TO_PROCESS)} users (June 1-20, 2025)")
    print("Minimum duration: 90 seconds")
    print("=" * 80)
    
    # Track statistics
    total_recordings = 0
    users_with_recordings = 0
    users_without_recordings = []
    all_recordings = []
    
    # Find recordings for each user
    for user_name in USERS_TO_PROCESS:
        recordings = find_user_recordings(user_name, min_duration=90)
        
        if recordings:
            users_with_recordings += 1
            total_recordings += len(recordings)
            
            print(f"\n✓ {user_name}: Found {len(recordings)} recordings")
            
            # Add user info to each recording
            for rec in recordings:
                rec['target_user'] = user_name
                all_recordings.append(rec)
        else:
            users_without_recordings.append(user_name)
            print(f"\n✗ {user_name}: No recordings found")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"- Users with recordings: {users_with_recordings}/{len(USERS_TO_PROCESS)}")
    print(f"- Total recordings found: {total_recordings}")
    print(f"- Average per user: {total_recordings/users_with_recordings:.1f}" if users_with_recordings > 0 else "0")
    
    if users_without_recordings:
        print(f"\nUsers without recordings ({len(users_without_recordings)}):")
        for user in users_without_recordings:
            print(f"  - {user}")
    
    # Check how many need processing
    need_processing = 0
    for rec in all_recordings:
        if not check_already_processed(rec['orkUid']):
            need_processing += 1
    
    print(f"\nRecordings needing processing: {need_processing}/{total_recordings}")
    
    if need_processing == 0:
        print("\nAll recordings have already been processed!")
        return
    
    # Ask to proceed
    print("\n" + "=" * 80)
    response = input(f"Process {need_processing} recordings? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Import and run the pipeline
    try:
        from scream_hybrid_pipeline import WhisperGemmaPipeline
        
        print("\nStarting SCREAM pipeline...")
        pipeline = WhisperGemmaPipeline()
        
        # Process recordings
        processed = 0
        skipped = 0
        failed = 0
        
        start_time = time.time()
        
        for i, rec in enumerate(all_recordings, 1):
            if check_already_processed(rec['orkUid']):
                skipped += 1
                print(f"\n[{i}/{total_recordings}] Skipping {rec['orkUid']} (already processed)")
                continue
            
            print(f"\n[{i}/{total_recordings}] Processing: {rec['target_user']} - {rec['orkUid']}")
            print(f"  Timestamp: {rec['timestamp']}")
            print(f"  Duration: {rec['duration']}s ({rec['duration']/60:.1f}m)")
            
            try:
                # Process the recording
                pipeline.process_recording({
                    'orkuid': rec['orkUid'],
                    'filename': rec['filename'],
                    'timestamp': rec['timestamp'],
                    'duration': rec['duration'],
                    'localParty': rec['localParty'],
                    'remoteParty': rec['remoteParty']
                })
                
                processed += 1
                
                # Show progress
                elapsed = time.time() - start_time
                rate = processed / (elapsed / 3600) if elapsed > 0 else 0
                remaining = (need_processing - processed) / rate if rate > 0 else 0
                
                print(f"  ✓ Processed successfully")
                print(f"  Progress: {processed}/{need_processing} ({processed/need_processing*100:.1f}%)")
                print(f"  Rate: {rate:.1f} recordings/hour")
                print(f"  Est. time remaining: {remaining:.1f} hours")
                
            except Exception as e:
                failed += 1
                print(f"  ✗ Failed: {e}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE!")
        print(f"- Processed: {processed}")
        print(f"- Skipped: {skipped}")
        print(f"- Failed: {failed}")
        print(f"- Total time: {(time.time() - start_time)/60:.1f} minutes")
        print("=" * 80)
        
    except ImportError:
        print("\nERROR: Could not import scream_hybrid_pipeline.py")
        print("Make sure you're running this from the correct directory")
        print("\nTo process manually, run for each recording:")
        print("python scream_hybrid_pipeline.py")

if __name__ == "__main__":
    main()