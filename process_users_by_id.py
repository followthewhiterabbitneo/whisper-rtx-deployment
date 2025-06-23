#!/usr/bin/env python3
"""
Process recordings by finding user IDs in orkuser table first
Then finding their recordings via orksegment.user_id
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

def find_user_id(firstname, lastname):
    """Find user ID from orkuser table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute("""
            SELECT id, firstname, lastname, email
            FROM orkuser
            WHERE firstname = %s AND lastname = %s
            AND deleted = 0
        """, (firstname, lastname))
        
        user = cursor.fetchone()
        
        if not user:
            # Try case-insensitive match
            cursor.execute("""
                SELECT id, firstname, lastname, email
                FROM orkuser
                WHERE LOWER(firstname) = LOWER(%s) 
                AND LOWER(lastname) = LOWER(%s)
                AND deleted = 0
            """, (firstname, lastname))
            user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return user
        
    except Exception as e:
        print(f"Error finding user: {e}")
        return None

def find_user_recordings_by_segment(user_id, min_duration=90):
    """Find recordings via orksegment table using user_id"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query orksegment to find tapes for this user
        query = """
        SELECT DISTINCT
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            s.user_id
        FROM orksegment s
        JOIN orktape t ON s.tape_id = t.id
        WHERE s.user_id = %s
        AND t.timestamp >= '2025-06-01 00:00:00'
        AND t.timestamp <= '2025-06-20 23:59:59'
        AND t.duration >= %s
        ORDER BY t.timestamp ASC
        """
        
        cursor.execute(query, (user_id, min_duration))
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
    print("Using orkuser IDs and orksegment table")
    print("Minimum duration: 90 seconds")
    print("=" * 80)
    
    # Track statistics
    total_recordings = 0
    users_with_recordings = 0
    users_not_found = []
    users_without_recordings = []
    all_recordings = []
    
    # Find user IDs and recordings
    for full_name in USERS_TO_PROCESS:
        parts = full_name.split()
        firstname = parts[0] if parts else ''
        lastname = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        # Handle special case for compound last names
        if full_name == "Nayaisha Alexander Edmond":
            firstname = "Nayaisha"
            lastname = "Alexander Edmond"
        
        print(f"\n{'='*60}")
        print(f"Processing: {full_name}")
        
        # Step 1: Find user ID
        user = find_user_id(firstname, lastname)
        
        if not user:
            users_not_found.append(full_name)
            print(f"✗ User not found in orkuser table")
            continue
        
        print(f"✓ Found user: ID={user['id']}, {user['firstname']} {user['lastname']}")
        
        # Step 2: Find recordings
        recordings = find_user_recordings_by_segment(user['id'], min_duration=90)
        
        if recordings:
            users_with_recordings += 1
            total_recordings += len(recordings)
            
            print(f"✓ Found {len(recordings)} recordings")
            
            # Add user info to each recording
            for rec in recordings:
                rec['target_user'] = full_name
                rec['user_firstname'] = user['firstname']
                rec['user_lastname'] = user['lastname']
                all_recordings.append(rec)
        else:
            users_without_recordings.append(full_name)
            print(f"✗ No recordings found for user ID {user['id']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"- Users found in DB: {len(USERS_TO_PROCESS) - len(users_not_found)}/{len(USERS_TO_PROCESS)}")
    print(f"- Users with recordings: {users_with_recordings}")
    print(f"- Total recordings found: {total_recordings}")
    print(f"- Average per user: {total_recordings/users_with_recordings:.1f}" if users_with_recordings > 0 else "0")
    
    if users_not_found:
        print(f"\nUsers NOT in orkuser table ({len(users_not_found)}):")
        for user in users_not_found:
            print(f"  - {user}")
    
    if users_without_recordings:
        print(f"\nUsers with no recordings ({len(users_without_recordings)}):")
        for user in users_without_recordings:
            print(f"  - {user}")
    
    # Check how many need processing
    need_processing = 0
    for rec in all_recordings:
        if not check_already_processed(rec['orkUid']):
            need_processing += 1
    
    print(f"\nRecordings needing processing: {need_processing}/{total_recordings}")
    
    if need_processing == 0 and total_recordings > 0:
        print("\nAll recordings have already been processed!")
        return
    
    if total_recordings == 0:
        print("\nNo recordings found to process!")
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
                    'remoteParty': rec['remoteParty'],
                    'user_firstname': rec['user_firstname'],
                    'user_lastname': rec['user_lastname']
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

if __name__ == "__main__":
    main()