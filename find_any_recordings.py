#!/usr/bin/env python3
"""
Find ANY recent recordings to understand the data structure
"""

import pymysql
from datetime import datetime, timedelta

print("=" * 80)
print("FIND ANY RECENT RECORDINGS")
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
    
    # 1. Check orktape table structure
    print("1. ORKTAPE TABLE STRUCTURE:")
    print("-" * 40)
    cursor.execute("DESCRIBE orktape")
    columns = cursor.fetchall()
    key_columns = ['uid', 'filename', 'localparty', 'remoteparty', 'duration', 'timestamp']
    for col in columns:
        if col['Field'] in key_columns:
            print(f"   {col['Field']:<15} {col['Type']}")
    
    # 2. Find recent recordings
    print("\n2. RECENT RECORDINGS (last 24 hours):")
    print("-" * 40)
    cursor.execute("""
        SELECT uid, filename, localparty, remoteparty, duration, timestamp
        FROM orktape
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        AND duration >= 120
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    recordings = cursor.fetchall()
    if recordings:
        for rec in recordings[:5]:
            print(f"\nUID: {rec['uid']}")
            print(f"File: {rec['filename']}")
            print(f"Local: {rec['localparty']}")
            print(f"Remote: {rec['remoteparty']}")
            print(f"Duration: {rec['duration']}s")
            print(f"Time: {rec['timestamp']}")
    else:
        print("No recordings found in last 24 hours")
        
        # Try last 7 days
        print("\nTrying last 7 days...")
        cursor.execute("""
            SELECT COUNT(*) as count FROM orktape
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        count = cursor.fetchone()['count']
        print(f"Found {count} recordings in last 7 days")
    
    # 3. Check orkuser table
    print("\n3. ORKUSER TABLE:")
    print("-" * 40)
    cursor.execute("""
        SELECT COUNT(*) as count FROM orkuser
    """)
    user_count = cursor.fetchone()['count']
    print(f"Total users: {user_count}")
    
    # Sample users
    cursor.execute("""
        SELECT uid, firstname, lastname, loginstring
        FROM orkuser
        WHERE firstname IS NOT NULL AND lastname IS NOT NULL
        LIMIT 10
    """)
    users = cursor.fetchall()
    if users:
        print("\nSample users:")
        for user in users[:5]:
            print(f"  - {user['firstname']} {user['lastname']} (login: {user['loginstring']})")
    
    # 4. Check how recordings link to users
    print("\n4. ORKSEGMENT LINKAGE:")
    print("-" * 40)
    cursor.execute("""
        SELECT COUNT(*) as count FROM orksegment
    """)
    segment_count = cursor.fetchone()['count']
    print(f"Total segments: {segment_count}")
    
    # Sample linked data
    cursor.execute("""
        SELECT 
            t.uid,
            t.localparty,
            t.remoteparty,
            u.firstname,
            u.lastname
        FROM orktape t
        JOIN orksegment s ON t.uid = s.fktape
        JOIN orkuser u ON s.fkuser = u.uid
        WHERE t.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        LIMIT 10
    """)
    
    linked = cursor.fetchall()
    if linked:
        print("\nSample linked recordings:")
        for link in linked[:3]:
            print(f"\n  Recording: {link['uid']}")
            print(f"  Parties: {link['localparty']} <-> {link['remoteparty']}")
            print(f"  User: {link['firstname']} {link['lastname']}")
    
    # 5. Search for names in party fields
    print("\n5. SEARCHING FOR 'ERIC' OR 'RAWLINS' IN PARTIES:")
    print("-" * 40)
    cursor.execute("""
        SELECT uid, localparty, remoteparty, duration, timestamp
        FROM orktape
        WHERE (localparty LIKE '%Eric%' OR localparty LIKE '%Rawlins%'
           OR remoteparty LIKE '%Eric%' OR remoteparty LIKE '%Rawlins%')
        AND duration >= 120
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    eric_recordings = cursor.fetchall()
    if eric_recordings:
        print(f"Found {len(eric_recordings)} recordings with 'Eric' or 'Rawlins':")
        for rec in eric_recordings:
            print(f"\n  UID: {rec['uid']}")
            print(f"  Parties: {rec['localparty']} <-> {rec['remoteparty']}")
            print(f"  Duration: {rec['duration']}s")
    else:
        print("No recordings found with 'Eric' or 'Rawlins' in party names")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)