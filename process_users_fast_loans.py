#!/usr/bin/env python3
"""
Fast processing for loan extraction only - no summaries
Uses fast_loan_extractor for maximum speed
"""

import os
import sys
import pymysql
from datetime import datetime
import time
from fast_loan_extractor import FastLoanExtractor

# Copy all the user finding code from process_users_fresh_start.py
exec(open('process_users_fresh_start.py').read().split('def main():')[0])

def main():
    print("=" * 80)
    print("FAST LOAN EXTRACTION - NO SUMMARIES")
    print(f"Processing recordings for {len(USERS_TO_PROCESS)} users (June 1-20, 2025)")
    print("Using Whisper transcription + loan extraction only")
    print("Minimum duration: 90 seconds")
    print("=" * 80)
    
    # Create tables first
    if not create_tables_if_needed():
        print("\nFailed to create tables. Exiting.")
        return
    
    # Track statistics
    total_recordings = 0
    users_with_recordings = 0
    users_not_found = []
    users_without_recordings = []
    all_recordings = []
    
    # Find user IDs and recordings (same as before)
    for full_name in USERS_TO_PROCESS:
        parts = full_name.split()
        firstname = parts[0] if parts else ''
        lastname = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        if full_name == "Nayaisha Alexander Edmond":
            firstname = "Nayaisha"
            lastname = "Alexander Edmond"
        
        print(f"\n{'='*60}")
        print(f"Processing: {full_name}")
        
        user = find_user_id(firstname, lastname)
        
        if not user:
            users_not_found.append(full_name)
            print(f"✗ User not found in orkuser table")
            continue
        
        print(f"✓ Found user: ID={user['id']}, {user['firstname']} {user['lastname']}")
        
        recordings = find_user_recordings_by_segment(user['id'], min_duration=90)
        
        if recordings:
            users_with_recordings += 1
            total_recordings += len(recordings)
            
            print(f"✓ Found {len(recordings)} recordings")
            
            for rec in recordings:
                rec['target_user'] = full_name
                rec['user_firstname'] = user['firstname']
                rec['user_lastname'] = user['lastname']
                all_recordings.append(rec)
        else:
            users_without_recordings.append(full_name)
            print(f"✗ No recordings found for user ID {user['id']}")
    
    # Process additional last names
    print("\n" + "=" * 80)
    print("SEARCHING BY LAST NAME ONLY")
    print("=" * 80)
    
    for lastname in LAST_NAME_SEARCHES:
        print(f"\n{'='*60}")
        print(f"Searching for all users with last name: {lastname}")
        
        users = find_users_by_lastname(lastname)
        
        if not users:
            print(f"✗ No users found with last name '{lastname}'")
            continue
        
        print(f"✓ Found {len(users)} users with last name '{lastname}':")
        
        for user in users:
            full_name = f"{user['firstname']} {user['lastname']}"
            print(f"\nProcessing: {full_name} (ID: {user['id']})")
            
            recordings = find_user_recordings_by_segment(user['id'], min_duration=90)
            
            if recordings:
                users_with_recordings += 1
                total_recordings += len(recordings)
                
                print(f"✓ Found {len(recordings)} recordings")
                
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
    
    if total_recordings == 0:
        print("\nNo recordings found to process!")
        return
    
    # Estimate time
    print("\n" + "=" * 80)
    print("TIME ESTIMATE:")
    print(f"- Recordings to process: {total_recordings}")
    print(f"- Estimated speed: 15-20x real-time (Whisper only)")
    print(f"- Average duration: ~3 minutes per recording")
    print(f"- Processing time per recording: ~10-15 seconds")
    print(f"- Total estimated time: {total_recordings * 12 / 3600:.1f} hours")
    print("=" * 80)
    
    response = input(f"\nProcess all {total_recordings} recordings in FAST MODE? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Initialize fast extractor
    print("\nInitializing Fast Loan Extractor...")
    extractor = FastLoanExtractor()
    
    # Process recordings
    processed = 0
    failed = 0
    loans_found = 0
    
    start_time = time.time()
    
    try:
        for i, rec in enumerate(all_recordings, 1):
            print(f"\n[{i}/{total_recordings}] {rec['target_user']} - {rec['orkUid']}")
            print(f"  Duration: {rec['duration']}s ({rec['duration']/60:.1f}m)")
            
            success = extractor.process_recording(rec)
            
            if success:
                processed += 1
                # Count if loans were found
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT loan_numbers FROM call_transcripts_v2 
                    WHERE orkuid = %s
                """, (rec['orkUid'],))
                result = cursor.fetchone()
                if result and result['loan_numbers'] != '[]':
                    loans_found += 1
                cursor.close()
                conn.close()
            else:
                failed += 1
            
            # Progress update
            elapsed = time.time() - start_time
            rate = processed / (elapsed / 3600) if elapsed > 0 else 0
            remaining = (total_recordings - i) / rate if rate > 0 else 0
            
            print(f"  Progress: {i}/{total_recordings} ({i/total_recordings*100:.1f}%)")
            print(f"  Success rate: {processed}/{i} ({processed/i*100:.1f}%)")
            print(f"  Loans found: {loans_found}/{processed} recordings")
            print(f"  Rate: {rate:.1f} recordings/hour")
            print(f"  Est. remaining: {remaining:.1f} hours")
    
    finally:
        extractor.cleanup()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FAST PROCESSING COMPLETE!")
    print(f"- Processed: {processed}")
    print(f"- Failed: {failed}")
    print(f"- Recordings with loans: {loans_found}")
    print(f"- Total time: {(time.time() - start_time)/60:.1f} minutes")
    print(f"- Average speed: {processed / ((time.time() - start_time) / 3600):.1f} recordings/hour")
    print("=" * 80)
    
    print("\nYou can now search for loan numbers using the loan search API!")

if __name__ == "__main__":
    main()