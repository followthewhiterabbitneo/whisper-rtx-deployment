#!/usr/bin/env python3
"""
Ultra-fast parallel processing - 4 workers, Whisper only
Expected speed: 60-80 recordings per hour
"""

import os
import sys
import pymysql
from datetime import datetime
import time
from fast_parallel_loan_extractor import process_batch_parallel

# Copy all the user finding code from process_users_fresh_start.py
exec(open('process_users_fresh_start.py').read().split('def main():')[0])

def main():
    print("=" * 80)
    print("ULTRA-FAST PARALLEL LOAN EXTRACTION")
    print("4 Workers | Whisper Only | No Summaries")
    print(f"Processing recordings for {len(USERS_TO_PROCESS)} users (June 1-20, 2025)")
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
    
    # Find user IDs and recordings
    for full_name in USERS_TO_PROCESS:
        parts = full_name.split()
        firstname = parts[0] if parts else ''
        lastname = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        if full_name == "Nayaisha Alexander Edmond":
            firstname = "Nayaisha"
            lastname = "Alexander Edmond"
        
        print(f"\nChecking: {full_name}")
        
        user = find_user_id(firstname, lastname)
        
        if not user:
            users_not_found.append(full_name)
            print(f"✗ User not found")
            continue
        
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
            print(f"✗ No recordings")
    
    # Process additional last names
    print("\n" + "-" * 40)
    print("Checking last names: Krall, Rahimifar")
    print("-" * 40)
    
    for lastname in LAST_NAME_SEARCHES:
        print(f"\nSearching: {lastname}")
        
        users = find_users_by_lastname(lastname)
        
        if not users:
            print(f"✗ No users found")
            continue
        
        print(f"✓ Found {len(users)} users")
        
        for user in users:
            full_name = f"{user['firstname']} {user['lastname']}"
            
            recordings = find_user_recordings_by_segment(user['id'], min_duration=90)
            
            if recordings:
                users_with_recordings += 1
                total_recordings += len(recordings)
                print(f"  {full_name}: {len(recordings)} recordings")
                
                for rec in recordings:
                    rec['target_user'] = full_name
                    rec['user_firstname'] = user['firstname']
                    rec['user_lastname'] = user['lastname']
                    all_recordings.append(rec)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"- Total recordings found: {total_recordings}")
    print(f"- Users with recordings: {users_with_recordings}")
    
    if total_recordings == 0:
        print("\nNo recordings found to process!")
        return
    
    # Time estimate for parallel processing
    print("\n" + "=" * 80)
    print("PARALLEL PROCESSING ESTIMATE:")
    print(f"- Recordings: {total_recordings}")
    print(f"- Workers: 4 parallel")
    print(f"- Expected speed: 60-80 recordings/hour total")
    print(f"- Estimated time: {total_recordings / 70:.1f} hours ({total_recordings / 70 * 60:.0f} minutes)")
    print("=" * 80)
    
    response = input(f"\nProcess {total_recordings} recordings with 4 PARALLEL WORKERS? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Process in parallel!
    process_batch_parallel(all_recordings, num_workers=4)
    
    print("\nYou can now search for loan numbers using the loan search API!")
    print("Run: python loan_search_api.py")

if __name__ == "__main__":
    main()