#!/usr/bin/env python3
"""
FIRST PRINCIPLES: Debug why same orkuid shows different durations
Raw SQL investigation
"""

import pymysql

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def debug_loan():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    loan_number = "1225237672"
    
    print("="*80)
    print(f"SQL DEBUGGING: LOAN {loan_number}")
    print("="*80)
    
    # 1. Raw query on call_transcripts_v2
    print("\n1. RAW DATA FROM call_transcripts_v2:")
    print("-"*60)
    cursor.execute("""
        SELECT 
            orkuid,
            loan_numbers,
            created_at
        FROM call_transcripts_v2
        WHERE loan_numbers LIKE %s
    """, (f'%{loan_number}%',))
    
    print("ORKUID                   | LOAN_NUMBERS    | CREATED_AT")
    print("-"*60)
    for row in cursor.fetchall():
        print(f"{row['orkuid']:24} | {row['loan_numbers']:15} | {row['created_at']}")
    
    # 2. Raw query on orktape
    print("\n\n2. RAW DATA FROM orktape:")
    print("-"*60)
    cursor.execute("""
        SELECT 
            orkUid,
            duration,
            timestamp,
            localParty,
            remoteParty
        FROM orktape
        WHERE orkUid IN (
            SELECT orkuid FROM call_transcripts_v2 
            WHERE loan_numbers LIKE %s
        )
        ORDER BY orkUid
    """, (f'%{loan_number}%',))
    
    print("ORKUID                   | DURATION | TIMESTAMP           | PARTIES")
    print("-"*80)
    for row in cursor.fetchall():
        print(f"{row['orkUid']:24} | {row['duration']:8} | {row['timestamp']} | {row['localParty']} <-> {row['remoteParty']}")
    
    # 3. Check for duplicates in orktape
    print("\n\n3. CHECKING FOR DUPLICATE ORKUIDs IN orktape:")
    print("-"*60)
    cursor.execute("""
        SELECT 
            orkUid,
            COUNT(*) as count,
            GROUP_CONCAT(duration) as durations,
            GROUP_CONCAT(id) as tape_ids
        FROM orktape
        WHERE orkUid IN (
            SELECT orkuid FROM call_transcripts_v2 
            WHERE loan_numbers LIKE %s
        )
        GROUP BY orkUid
        HAVING count > 1
    """, (f'%{loan_number}%',))
    
    duplicates = cursor.fetchall()
    if duplicates:
        print("FOUND DUPLICATES!")
        for dup in duplicates:
            print(f"\nORKUID: {dup['orkUid']}")
            print(f"  Count: {dup['count']} records")
            print(f"  Durations: {dup['durations']}")
            print(f"  Tape IDs: {dup['tape_ids']}")
    else:
        print("No duplicate orkUIDs found")
    
    # 4. Join query to see what happens
    print("\n\n4. JOIN QUERY (what the scripts use):")
    print("-"*60)
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.orkUid,
            t.duration,
            t.id as tape_id
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        ORDER BY ct.orkuid
    """, (f'%{loan_number}%',))
    
    print("CT.ORKUID                | T.ORKUID                 | DURATION | TAPE_ID")
    print("-"*80)
    for row in cursor.fetchall():
        print(f"{row['orkuid']:24} | {row['orkUid']:24} | {row['duration']:8} | {row['tape_id']}")
    
    # 5. Count total records
    print("\n\n5. RECORD COUNTS:")
    print("-"*60)
    
    cursor.execute("""
        SELECT COUNT(DISTINCT orkuid) as unique_calls
        FROM call_transcripts_v2
        WHERE loan_numbers LIKE %s
    """, (f'%{loan_number}%',))
    unique = cursor.fetchone()['unique_calls']
    
    cursor.execute("""
        SELECT COUNT(*) as total_join_records
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
    """, (f'%{loan_number}%',))
    total = cursor.fetchone()['total_join_records']
    
    print(f"Unique calls in call_transcripts_v2: {unique}")
    print(f"Total records after JOIN: {total}")
    
    if total > unique:
        print(f"\n⚠️  JOIN is creating duplicates! {total - unique} extra records")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    debug_loan()