#!/usr/bin/env python3
"""
Process loan networks with 4 parallel workers - NO PARAMIKO
Uses subprocess for SCP like the working parallel processor
"""

import json
import os
import sys
import time
from datetime import datetime
from fast_parallel_loan_extractor import process_batch_parallel, FastWorker
from smart_loan_network_finder import find_loan_officer_networks

def main():
    print("="*80)
    print("LOAN NETWORK PARALLEL PROCESSOR")
    print("4 Workers | No Paramiko | Process ALL loan officer calls")
    print("="*80)
    
    # Find loan officer networks
    print("\nAnalyzing loan officer networks...")
    officers, recordings = find_loan_officer_networks()
    
    if not recordings:
        print("\nNo recordings to process!")
        return
    
    print(f"\n{'='*80}")
    print(f"Ready to process {len(recordings)} recordings from loan officer networks")
    print(f"{'='*80}")
    
    # Duration breakdown
    short = len([r for r in recordings if r['duration'] < 90])
    medium = len([r for r in recordings if 90 <= r['duration'] < 300])
    long = len([r for r in recordings if r['duration'] >= 300])
    
    print(f"\nDuration breakdown:")
    print(f"  < 90 seconds: {short} calls (previously skipped!)")
    print(f"  90-300 seconds: {medium} calls")
    print(f"  > 300 seconds: {long} calls")
    
    # Prepare recordings for parallel processor
    for rec in recordings:
        # Add required fields
        rec['orkUid'] = rec['orkuid']
        rec['target_user'] = f"{rec.get('user_firstname', '')} {rec.get('user_lastname', '')}".strip() or 'Unknown'
        # Convert timestamp if needed
        if hasattr(rec['timestamp'], 'isoformat'):
            rec['timestamp'] = rec['timestamp']
        else:
            rec['timestamp'] = datetime.fromisoformat(rec['timestamp'])
    
    # Time estimate
    print(f"\nTime estimate with 4 workers:")
    print(f"  Expected speed: 60-80 recordings/hour")
    print(f"  Estimated time: {len(recordings)/70:.1f} hours")
    
    response = input(f"\nProcess {len(recordings)} recordings with 4 PARALLEL WORKERS? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Process with 4 workers!
    print("\nStarting parallel processing...")
    process_batch_parallel(recordings, num_workers=4)
    
    # Show results
    print("\n" + "="*60)
    print("NETWORK PROCESSING COMPLETE!")
    print("="*60)
    
    # Check what loans we found
    try:
        import pymysql
        conn = pymysql.connect(
            host='s40vpsoxweb002',
            port=3306,
            user='root',
            password='admin',
            database='oreka'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT loan_number, COUNT(*) as count
            FROM loan_number_index
            GROUP BY loan_number
            ORDER BY count DESC
        """)
        
        loans = cursor.fetchall()
        
        print("\nLOAN NUMBERS FOUND:")
        for loan in loans:
            print(f"  Loan #{loan[0]}: {loan[1]} calls")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Could not fetch loan summary: {e}")
    
    print("\n✓ Loan officer networks fully processed!")
    print("✓ Run loan_search_api.py to start searching!")

if __name__ == "__main__":
    # First check if we have the JSON file
    if os.path.exists('recordings_to_transcribe.json'):
        print("Loading recordings from recordings_to_transcribe.json...")
        with open('recordings_to_transcribe.json', 'r') as f:
            recordings = json.load(f)
        
        # Convert timestamps
        for rec in recordings:
            rec['orkUid'] = rec['orkuid']
            rec['target_user'] = f"{rec.get('user_firstname', '')} {rec.get('user_lastname', '')}".strip() or 'Unknown'
            if isinstance(rec['timestamp'], str):
                rec['timestamp'] = datetime.fromisoformat(rec['timestamp'])
        
        print(f"Loaded {len(recordings)} recordings")
        
        response = input(f"\nProcess these {len(recordings)} recordings with 4 workers? (yes/no): ")
        if response.lower() == 'yes':
            process_batch_parallel(recordings, num_workers=4)
    else:
        # Run full analysis
        main()