#!/usr/bin/env python3
"""
Find recordings by any means necessary - check all possible name formats
"""

import pymysql

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

def find_recordings_for_user(user_name):
    """Try every possible way to find recordings for a user"""
    print(f"\n{'='*60}")
    print(f"Searching for: {user_name}")
    print(f"{'='*60}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Split name
    parts = user_name.split()
    firstname = parts[0] if parts else ''
    lastname = parts[-1] if len(parts) > 1 else ''
    
    # 1. Check if user exists in orkuser table
    print("\n1. Checking orkuser table...")
    cursor.execute("""
        SELECT id, firstname, lastname, email
        FROM orkuser
        WHERE (firstname = %s AND lastname = %s)
        OR (firstname LIKE %s AND lastname LIKE %s)
    """, (firstname, lastname, f'%{firstname}%', f'%{lastname}%'))
    
    orkusers = cursor.fetchall()
    if orkusers:
        print(f"   Found in orkuser table:")
        for u in orkusers:
            print(f"   - ID: {u['id']}, Name: {u['firstname']} {u['lastname']}")
    else:
        print(f"   NOT found in orkuser table")
    
    # 2. Search in localParty/remoteParty - multiple patterns
    print("\n2. Searching in party fields...")
    
    # Pattern A: Full name exact
    cursor.execute("""
        SELECT COUNT(*) as count, 
               MIN(timestamp) as first_call,
               MAX(timestamp) as last_call
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND (localParty = %s OR remoteParty = %s)
    """, (user_name, user_name))
    result = cursor.fetchone()
    print(f"   A. Exact full name match: {result['count']} recordings")
    
    # Pattern B: Full name with wildcards
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND (localParty LIKE %s OR remoteParty LIKE %s)
    """, (f'%{user_name}%', f'%{user_name}%'))
    result = cursor.fetchone()
    print(f"   B. Full name LIKE match: {result['count']} recordings")
    
    # Pattern C: First name only
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND (localParty LIKE %s OR remoteParty LIKE %s)
    """, (f'%{firstname}%', f'%{firstname}%'))
    result = cursor.fetchone()
    print(f"   C. First name only: {result['count']} recordings")
    
    # Pattern D: Last name only
    if lastname:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM orktape
            WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
            AND duration >= 90
            AND (localParty LIKE %s OR remoteParty LIKE %s)
        """, (f'%{lastname}%', f'%{lastname}%'))
        result = cursor.fetchone()
        print(f"   D. Last name only: {result['count']} recordings")
    
    # 3. Show actual party values that contain the name
    print(f"\n3. Sample party fields containing '{firstname}':")
    cursor.execute("""
        SELECT DISTINCT localParty, remoteParty, duration
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND (localParty LIKE %s OR remoteParty LIKE %s)
        ORDER BY duration DESC
        LIMIT 5
    """, (f'%{firstname}%', f'%{firstname}%'))
    
    samples = cursor.fetchall()
    if samples:
        for i, s in enumerate(samples, 1):
            print(f"   {i}. Local: '{s['localParty']}' | Remote: '{s['remoteParty']}' | Duration: {s['duration']}s")
    else:
        print("   No matches found")
    
    # 4. Try alternative spellings or formats
    print(f"\n4. Checking variations...")
    
    # Check with comma (Last, First)
    comma_format = f"{lastname}, {firstname}" if lastname else firstname
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND (localParty LIKE %s OR remoteParty LIKE %s)
    """, (f'%{comma_format}%', f'%{comma_format}%'))
    result = cursor.fetchone()
    print(f"   Comma format (Last, First): {result['count']} recordings")
    
    cursor.close()
    conn.close()

def check_all_party_values():
    """Show all unique party values in June to understand the format"""
    print("\n" + "="*80)
    print("ALL UNIQUE PARTY VALUES IN JUNE 2025")
    print("="*80)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get unique localParty values
    cursor.execute("""
        SELECT DISTINCT localParty, COUNT(*) as count
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND localParty NOT LIKE '+%'  -- Exclude phone numbers
        GROUP BY localParty
        ORDER BY count DESC
        LIMIT 20
    """)
    
    print("\nTop 20 localParty values (excluding phone numbers):")
    locals = cursor.fetchall()
    for i, party in enumerate(locals, 1):
        print(f"{i:2d}. '{party['localParty']}' ({party['count']} calls)")
    
    # Get unique remoteParty values
    cursor.execute("""
        SELECT DISTINCT remoteParty, COUNT(*) as count
        FROM orktape
        WHERE timestamp >= '2025-06-01' AND timestamp <= '2025-06-20'
        AND duration >= 90
        AND remoteParty NOT LIKE '+%'  -- Exclude phone numbers
        GROUP BY remoteParty
        ORDER BY count DESC
        LIMIT 20
    """)
    
    print("\nTop 20 remoteParty values (excluding phone numbers):")
    remotes = cursor.fetchall()
    for i, party in enumerate(remotes, 1):
        print(f"{i:2d}. '{party['remoteParty']}' ({party['count']} calls)")
    
    cursor.close()
    conn.close()

def main():
    # First, understand the data format
    check_all_party_values()
    
    # Then search for specific users
    test_users = [
        "Hunter Gollehur",
        "Eric Rawlins",
        "Dana Williams",
        "Alexa Bidigare",
        "Chris Hoerle"
    ]
    
    for user in test_users:
        find_recordings_for_user(user)
    
    print("\n" + "="*80)
    print("SEARCH COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()