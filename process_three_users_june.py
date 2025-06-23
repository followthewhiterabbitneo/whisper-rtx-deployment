#!/usr/bin/env python3
"""
Process all recordings for:
- Eric Rawlins
- Celina Fischer  
- Negin Rahimifar

For the period: June 1-20, 2025 (entire month up to June 20)
Today is June 23, 2025
"""

import pymysql
import subprocess
import sys
import os
from datetime import datetime

print("=" * 80)
print("PROCESSING THREE USERS - JUNE 2025")
print("=" * 80)

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Users to process
TARGET_USERS = [
    ('Eric', 'Rawlins'),
    ('Celina', 'Fischer'),
    ('Negin', 'Rahimifar')
]

# Date range
START_DATE = '2025-06-01'
END_DATE = '2025-06-20 23:59:59'

def find_recordings_for_users():
    """Find all recordings for the target users in June 2025"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        print("✓ Connected to database\n")
        
        all_recordings = []
        
        # First, let's check if these users exist in orkuser table
        print("1. CHECKING ORKUSER TABLE:")
        print("-" * 40)
        
        for firstname, lastname in TARGET_USERS:
            cursor.execute("""
                SELECT id, firstname, lastname 
                FROM orkuser 
                WHERE firstname LIKE %s AND lastname LIKE %s
            """, (f'%{firstname}%', f'%{lastname}%'))
            
            users = cursor.fetchall()
            if users:
                print(f"\n✓ Found {firstname} {lastname} in orkuser:")
                for user in users:
                    print(f"  ID: {user['id']} - {user['firstname']} {user['lastname']}")
            else:
                print(f"\n✗ {firstname} {lastname} not found in orkuser table")
        
        # Now search in orktape by party names
        print("\n\n2. SEARCHING ORKTAPE BY PARTY NAMES:")
        print("-" * 40)
        
        for firstname, lastname in TARGET_USERS:
            print(f"\nSearching for {firstname} {lastname}...")
            
            # Search in localParty and remoteParty fields
            query = """
            SELECT 
                t.orkUid,
                t.filename,
                t.duration,
                t.timestamp,
                t.localParty,
                t.remoteParty
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE 
                ct.orkuid IS NULL  -- Not yet processed
                AND t.timestamp >= %s 
                AND t.timestamp <= %s
                AND t.duration >= 60  -- At least 1 minute
                AND (
                    t.localParty LIKE %s OR t.localParty LIKE %s
                    OR t.remoteParty LIKE %s OR t.remoteParty LIKE %s
                    OR t.localParty LIKE %s OR t.remoteParty LIKE %s
                )
            ORDER BY t.timestamp DESC
            """
            
            # Search patterns
            firstname_pattern = f'%{firstname}%'
            lastname_pattern = f'%{lastname}%'
            fullname_pattern = f'%{firstname}%{lastname}%'
            
            cursor.execute(query, (
                START_DATE, END_DATE,
                firstname_pattern, lastname_pattern,
                firstname_pattern, lastname_pattern,
                fullname_pattern, fullname_pattern
            ))
            
            recordings = cursor.fetchall()
            
            if recordings:
                print(f"  Found {len(recordings)} recordings")
                for rec in recordings:
                    rec['user'] = f"{firstname} {lastname}"
                    all_recordings.append(rec)
                    
                # Show first few
                for rec in recordings[:3]:
                    print(f"\n  orkUid: {rec['orkUid']}")
                    print(f"  Time: {rec['timestamp']}")
                    print(f"  Duration: {rec['duration']}s")
                    print(f"  Parties: {rec['localParty']} <-> {rec['remoteParty']}")
                    
                if len(recordings) > 3:
                    print(f"\n  ... and {len(recordings) - 3} more recordings")
            else:
                print(f"  No recordings found")
        
        # Also check by joining with orkuser (in case users are properly linked)
        print("\n\n3. SEARCHING VIA ORKUSER LINKAGE:")
        print("-" * 40)
        
        query = """
        SELECT 
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            u.firstname,
            u.lastname
        FROM orktape t
        JOIN orksegment s ON t.orkUid = s.tape_id
        JOIN orkuser u ON s.user_id = u.id
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        WHERE 
            ct.orkuid IS NULL
            AND t.timestamp >= %s 
            AND t.timestamp <= %s
            AND t.duration >= 60
            AND (
                (u.firstname = 'Eric' AND u.lastname = 'Rawlins')
                OR (u.firstname = 'Celina' AND u.lastname = 'Fischer')
                OR (u.firstname = 'Negin' AND u.lastname = 'Rahimifar')
            )
        ORDER BY t.timestamp DESC
        """
        
        cursor.execute(query, (START_DATE, END_DATE))
        linked_recordings = cursor.fetchall()
        
        if linked_recordings:
            print(f"\nFound {len(linked_recordings)} recordings via user linkage")
            for rec in linked_recordings:
                rec['user'] = f"{rec['firstname']} {rec['lastname']}"
                # Check if not already in list
                if not any(r['orkUid'] == rec['orkUid'] for r in all_recordings):
                    all_recordings.append(rec)
        
        cursor.close()
        connection.close()
        
        return all_recordings
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_recordings(recordings):
    """Process all found recordings"""
    if not recordings:
        print("\n\nNo recordings to process!")
        return
    
    print("\n\n" + "=" * 80)
    print(f"PROCESSING {len(recordings)} RECORDINGS")
    print("=" * 80)
    
    # Group by user
    by_user = {}
    for rec in recordings:
        user = rec.get('user', 'Unknown')
        if user not in by_user:
            by_user[user] = []
        by_user[user].append(rec)
    
    # Show summary
    print("\nSummary by user:")
    for user, recs in by_user.items():
        total_duration = sum(r['duration'] for r in recs)
        print(f"  {user}: {len(recs)} recordings ({total_duration//60} minutes total)")
    
    # Ask for confirmation
    print(f"\nThis will process {len(recordings)} recordings.")
    response = input("Continue? (y/n): ").lower().strip()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Process each recording
    success_count = 0
    error_count = 0
    
    for idx, rec in enumerate(recordings, 1):
        orkuid = rec['orkUid']
        user = rec.get('user', 'Unknown')
        
        print(f"\n[{idx}/{len(recordings)}] Processing {orkuid}")
        print(f"  User: {user}")
        print(f"  Duration: {rec['duration']}s")
        print(f"  Time: {rec['timestamp']}")
        
        # Run the processing script
        cmd = [sys.executable, "process_any_recording.py", orkuid]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Success")
            success_count += 1
        else:
            print(f"  ✗ Failed: {result.stderr[:200]}")
            error_count += 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total: {len(recordings)} recordings")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

# Main execution
if __name__ == "__main__":
    print(f"\nSearching for recordings from {START_DATE} to {END_DATE}")
    print(f"Today is: {datetime.now().strftime('%Y-%m-%d')}")
    
    recordings = find_recordings_for_users()
    
    if recordings:
        print(f"\n\nTotal recordings found: {len(recordings)}")
        process_recordings(recordings)
    else:
        print("\n\nNo recordings found for the specified users and date range.")