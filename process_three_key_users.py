#!/usr/bin/env python3
"""
Process only 3 key users: Eric Rawlins, Krall, and Rahimifar
Fast loan extraction - focused approach
"""

import os
import sys
import pymysql
from datetime import datetime
import time
from fast_parallel_loan_extractor import process_batch_parallel

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

def create_tables_if_needed():
    """Create the necessary tables if they don't exist"""
    print("\nCreating/checking database tables...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create call_transcripts_v2 table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_transcripts_v2 (
            orkuid VARCHAR(50) PRIMARY KEY,
            summary TEXT COMMENT 'Legal brief summary of the call',
            transcript_path VARCHAR(500) COMMENT 'Path to full transcript file',
            loan_numbers TEXT COMMENT 'JSON array of loan numbers found',
            key_facts TEXT COMMENT 'JSON structured key facts extracted',
            sentiment VARCHAR(20) COMMENT 'Call sentiment: positive/negative/neutral',
            processing_time_ms INT COMMENT 'Time to process in milliseconds',
            whisper_model VARCHAR(50) DEFAULT 'large-v3-turbo',
            summary_model VARCHAR(50) DEFAULT 'gemma-3-12b',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            
            INDEX idx_created (created_at),
            INDEX idx_sentiment (sentiment)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Create loan index table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_number_index (
            id INT AUTO_INCREMENT PRIMARY KEY,
            loan_number VARCHAR(20) NOT NULL,
            orkuid VARCHAR(50) NOT NULL,
            user_name VARCHAR(100),
            user_firstname VARCHAR(50),
            user_lastname VARCHAR(50),
            call_date DATE,
            call_timestamp TIMESTAMP NULL,
            duration INT,
            confidence DECIMAL(3,2) DEFAULT 1.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX idx_loan_number (loan_number),
            INDEX idx_user_name (user_name),
            INDEX idx_call_date (call_date),
            INDEX idx_orkuid (orkuid),
            UNIQUE KEY unique_loan_orkuid (loan_number, orkuid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Tables created/verified successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def find_recordings_for_three_users():
    """Find recordings for Eric Rawlins, Krall, and Rahimifar"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    all_recordings = []
    
    print("\n" + "="*60)
    print("FINDING RECORDINGS FOR 3 KEY USERS")
    print("="*60)
    
    # 1. Eric Rawlins - by name
    print("\n1. Eric Rawlins")
    cursor.execute("""
        SELECT DISTINCT
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            'Eric Rawlins' as target_user,
            'Eric' as user_firstname,
            'Rawlins' as user_lastname
        FROM orktape t
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE t.timestamp >= '2025-06-01' 
        AND t.timestamp <= '2025-06-20'
        AND t.duration >= 90
        AND (
            (u.firstname = 'Eric' AND u.lastname = 'Rawlins') OR
            t.localParty LIKE '%Eric%Rawlins%' OR
            t.remoteParty LIKE '%Eric%Rawlins%'
        )
        ORDER BY t.timestamp
    """)
    
    eric_recordings = cursor.fetchall()
    print(f"   Found: {len(eric_recordings)} recordings")
    all_recordings.extend(eric_recordings)
    
    # 2. All Krall recordings
    print("\n2. All Krall users")
    cursor.execute("""
        SELECT DISTINCT
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            CONCAT(u.firstname, ' ', u.lastname) as target_user,
            u.firstname as user_firstname,
            u.lastname as user_lastname
        FROM orkuser u
        JOIN orksegment s ON u.id = s.user_id
        JOIN orktape t ON s.tape_id = t.id
        WHERE u.lastname = 'Krall'
        AND t.timestamp >= '2025-06-01' 
        AND t.timestamp <= '2025-06-20'
        AND t.duration >= 90
        ORDER BY t.timestamp
    """)
    
    krall_recordings = cursor.fetchall()
    print(f"   Found: {len(krall_recordings)} recordings")
    all_recordings.extend(krall_recordings)
    
    # 3. All Rahimifar recordings
    print("\n3. All Rahimifar users")
    cursor.execute("""
        SELECT DISTINCT
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            CONCAT(u.firstname, ' ', u.lastname) as target_user,
            u.firstname as user_firstname,
            u.lastname as user_lastname
        FROM orkuser u
        JOIN orksegment s ON u.id = s.user_id
        JOIN orktape t ON s.tape_id = t.id
        WHERE u.lastname = 'Rahimifar'
        AND t.timestamp >= '2025-06-01' 
        AND t.timestamp <= '2025-06-20'
        AND t.duration >= 90
        ORDER BY t.timestamp
    """)
    
    rahimifar_recordings = cursor.fetchall()
    print(f"   Found: {len(rahimifar_recordings)} recordings")
    all_recordings.extend(rahimifar_recordings)
    
    cursor.close()
    conn.close()
    
    # Summary by user
    print("\n" + "-"*60)
    print("SUMMARY BY USER:")
    user_counts = {}
    for rec in all_recordings:
        user = rec['target_user']
        user_counts[user] = user_counts.get(user, 0) + 1
    
    for user, count in sorted(user_counts.items()):
        print(f"  {user}: {count} recordings")
    
    print(f"\nTOTAL: {len(all_recordings)} recordings")
    print("-"*60)
    
    return all_recordings

def main():
    print("="*80)
    print("PROCESS 3 KEY USERS ONLY")
    print("Eric Rawlins, Krall, Rahimifar")
    print("="*80)
    
    # Create tables
    if not create_tables_if_needed():
        return
    
    # Find recordings
    recordings = find_recordings_for_three_users()
    
    if not recordings:
        print("\nNo recordings found!")
        return
    
    # Time estimate
    print(f"\nProcessing estimate:")
    print(f"- Recordings: {len(recordings)}")
    print(f"- With 4 workers: {len(recordings)/70:.1f} hours")
    print(f"- Sequential: {len(recordings)/25:.1f} hours")
    
    # Choose processing method
    print("\nProcessing options:")
    print("1. Parallel (4 workers) - Faster but may have issues")
    print("2. Sequential - Slower but more reliable")
    print("3. Cancel")
    
    choice = input("\nChoice (1/2/3): ")
    
    if choice == '1':
        # Process in parallel
        print("\nStarting PARALLEL processing...")
        process_batch_parallel(recordings, num_workers=4)
        
    elif choice == '2':
        # Process sequentially
        print("\nStarting SEQUENTIAL processing...")
        from fast_loan_extractor import FastLoanExtractor
        
        extractor = FastLoanExtractor()
        processed = 0
        failed = 0
        loans_found = 0
        start_time = time.time()
        
        try:
            for i, rec in enumerate(recordings, 1):
                print(f"\n[{i}/{len(recordings)}] {rec['target_user']} - {rec['orkUid']}")
                
                success = extractor.process_recording(rec)
                
                if success:
                    processed += 1
                    # Check if loans found
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
                
                # Progress
                elapsed = time.time() - start_time
                rate = i / (elapsed / 3600) if elapsed > 0 else 0
                remaining = (len(recordings) - i) / rate if rate > 0 else 0
                
                if i % 5 == 0:
                    print(f"\nProgress: {i}/{len(recordings)} ({i/len(recordings)*100:.1f}%)")
                    print(f"Success: {processed}, Failed: {failed}, Loans: {loans_found}")
                    print(f"Rate: {rate:.1f}/hour, ETA: {remaining:.1f} hours")
        
        finally:
            extractor.cleanup()
        
        print(f"\nComplete! Processed: {processed}, Failed: {failed}, With loans: {loans_found}")
    
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main()