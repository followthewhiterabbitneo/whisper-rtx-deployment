#!/usr/bin/env python3
"""
Quick check: What recordings exist in June 2025?
"""

import pymysql
from datetime import datetime

print("=" * 80)
print("JUNE 2025 RECORDINGS CHECK")
print("=" * 80)

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

try:
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("✓ Connected to database\n")
    
    # 1. Total recordings in June 2025
    print("1. JUNE 2025 STATISTICS:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(duration) as total_duration,
            MIN(timestamp) as first_recording,
            MAX(timestamp) as last_recording
        FROM orktape
        WHERE timestamp >= '2025-06-01' 
        AND timestamp <= '2025-06-20 23:59:59'
    """)
    
    stats = cursor.fetchone()
    print(f"Total recordings: {stats['total_count']:,}")
    print(f"Total duration: {stats['total_duration']//3600:,} hours")
    print(f"First recording: {stats['first_recording']}")
    print(f"Last recording: {stats['last_recording']}")
    
    # 2. Search for specific names in party fields
    print("\n2. SEARCHING FOR TARGET USERS:")
    print("-" * 40)
    
    names_to_search = [
        ('Eric', 'Rawlins'),
        ('Celina', 'Fischer'),
        ('Negin', 'Rahimifar')
    ]
    
    for firstname, lastname in names_to_search:
        print(f"\nSearching for {firstname} {lastname}...")
        
        # Count recordings
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM orktape
            WHERE timestamp >= '2025-06-01' 
            AND timestamp <= '2025-06-20 23:59:59'
            AND (
                localParty LIKE %s OR localParty LIKE %s
                OR remoteParty LIKE %s OR remoteParty LIKE %s
                OR localParty LIKE %s OR remoteParty LIKE %s
            )
        """, (f'%{firstname}%', f'%{lastname}%', 
              f'%{firstname}%', f'%{lastname}%',
              f'%{firstname}%{lastname}%', f'%{firstname}%{lastname}%'))
        
        count = cursor.fetchone()['count']
        print(f"  Found: {count} recordings")
        
        if count > 0 and count <= 5:
            # Show them if few
            cursor.execute("""
                SELECT orkUid, timestamp, duration, localParty, remoteParty
                FROM orktape
                WHERE timestamp >= '2025-06-01' 
                AND timestamp <= '2025-06-20 23:59:59'
                AND (
                    localParty LIKE %s OR localParty LIKE %s
                    OR remoteParty LIKE %s OR remoteParty LIKE %s
                    OR localParty LIKE %s OR remoteParty LIKE %s
                )
                ORDER BY timestamp DESC
            """, (f'%{firstname}%', f'%{lastname}%', 
                  f'%{firstname}%', f'%{lastname}%',
                  f'%{firstname}%{lastname}%', f'%{firstname}%{lastname}%'))
            
            recordings = cursor.fetchall()
            for rec in recordings:
                print(f"    - {rec['orkUid']} | {rec['timestamp']} | {rec['duration']}s")
    
    # 3. Sample of party names to understand format
    print("\n3. SAMPLE PARTY NAMES (to understand format):")
    print("-" * 40)
    
    cursor.execute("""
        SELECT DISTINCT localParty, remoteParty
        FROM orktape
        WHERE timestamp >= '2025-06-01' 
        AND timestamp <= '2025-06-20 23:59:59'
        AND localParty NOT LIKE '+%'  -- Look for non-phone number parties
        LIMIT 20
    """)
    
    samples = cursor.fetchall()
    if samples:
        print("\nNon-phone number parties found:")
        for sample in samples[:10]:
            print(f"  Local: {sample['localParty']} | Remote: {sample['remoteParty']}")
    
    # 4. Check call_transcripts_v2 status
    print("\n4. PROCESSING STATUS:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM call_transcripts_v2
        WHERE created_at >= '2025-06-01'
    """)
    
    processed = cursor.fetchone()['count']
    print(f"Already processed in June: {processed} recordings")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)