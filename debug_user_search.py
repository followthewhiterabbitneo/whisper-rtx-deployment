#!/usr/bin/env python3
"""
Debug user search - understand how names are stored in the database
"""

import pymysql
from datetime import datetime

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

def analyze_orkuser_table():
    """Look at how users are stored in orkuser table"""
    print("\n=== ORKUSER TABLE ANALYSIS ===")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get sample of users
        cursor.execute("""
            SELECT id, firstname, lastname, email
            FROM orkuser
            WHERE firstname IS NOT NULL
            LIMIT 20
        """)
        
        users = cursor.fetchall()
        print(f"\nSample users in orkuser table:")
        for user in users:
            print(f"  ID: {user['id']}, Name: {user['firstname']} {user['lastname']}, Email: {user['email']}")
        
        # Check for specific users
        test_users = ['Hunter', 'Alexa', 'Eric', 'Dana']
        for name in test_users:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orkuser
                WHERE firstname LIKE %s OR lastname LIKE %s
            """, (f'%{name}%', f'%{name}%'))
            result = cursor.fetchone()
            print(f"\nUsers matching '{name}': {result['count']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def analyze_party_fields():
    """Look at how party fields are stored in orktape"""
    print("\n=== ORKTAPE PARTY FIELDS ANALYSIS ===")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get sample of party fields from June 2025
        cursor.execute("""
            SELECT DISTINCT localParty, remoteParty
            FROM orktape
            WHERE timestamp >= '2025-06-01'
            AND timestamp <= '2025-06-20'
            AND duration >= 90
            LIMIT 30
        """)
        
        parties = cursor.fetchall()
        print(f"\nSample party fields from June 2025:")
        for i, party in enumerate(parties, 1):
            print(f"{i}. Local: {party['localParty']}, Remote: {party['remoteParty']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def search_by_name_patterns():
    """Try different search patterns"""
    print("\n=== SEARCH PATTERN ANALYSIS ===")
    
    test_names = ['Hunter Gollehur', 'Eric Rawlins', 'Dana Williams']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for full_name in test_names:
            print(f"\nSearching for: {full_name}")
            name_parts = full_name.split()
            firstname = name_parts[0]
            lastname = name_parts[-1]
            
            # Method 1: Direct party match
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orktape
                WHERE timestamp >= '2025-06-01'
                AND timestamp <= '2025-06-20'
                AND duration >= 90
                AND (localParty = %s OR remoteParty = %s)
            """, (full_name, full_name))
            result = cursor.fetchone()
            print(f"  Method 1 (exact party match): {result['count']} recordings")
            
            # Method 2: LIKE party match
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orktape
                WHERE timestamp >= '2025-06-01'
                AND timestamp <= '2025-06-20'
                AND duration >= 90
                AND (localParty LIKE %s OR remoteParty LIKE %s)
            """, (f'%{full_name}%', f'%{full_name}%'))
            result = cursor.fetchone()
            print(f"  Method 2 (LIKE full name): {result['count']} recordings")
            
            # Method 3: First/Last name in parties
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orktape
                WHERE timestamp >= '2025-06-01'
                AND timestamp <= '2025-06-20'
                AND duration >= 90
                AND (
                    (localParty LIKE %s AND localParty LIKE %s) OR
                    (remoteParty LIKE %s AND remoteParty LIKE %s)
                )
            """, (f'%{firstname}%', f'%{lastname}%', f'%{firstname}%', f'%{lastname}%'))
            result = cursor.fetchone()
            print(f"  Method 3 (first AND last name): {result['count']} recordings")
            
            # Method 4: Just first name
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orktape
                WHERE timestamp >= '2025-06-01'
                AND timestamp <= '2025-06-20'
                AND duration >= 90
                AND (localParty LIKE %s OR remoteParty LIKE %s)
            """, (f'%{firstname}%', f'%{firstname}%'))
            result = cursor.fetchone()
            print(f"  Method 4 (just first name): {result['count']} recordings")
            
            # Show sample matches for first name
            if result['count'] > 0:
                cursor.execute("""
                    SELECT localParty, remoteParty, duration, timestamp
                    FROM orktape
                    WHERE timestamp >= '2025-06-01'
                    AND timestamp <= '2025-06-20'
                    AND duration >= 90
                    AND (localParty LIKE %s OR remoteParty LIKE %s)
                    LIMIT 3
                """, (f'%{firstname}%', f'%{firstname}%'))
                samples = cursor.fetchall()
                print(f"    Sample matches:")
                for s in samples:
                    print(f"      Local: {s['localParty']}, Remote: {s['remoteParty']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def check_total_june_recordings():
    """Check total recordings in June 2025"""
    print("\n=== JUNE 2025 RECORDINGS SUMMARY ===")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total recordings
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN duration >= 90 THEN 1 END) as over_90s,
                   AVG(duration) as avg_duration,
                   MIN(timestamp) as first_call,
                   MAX(timestamp) as last_call
            FROM orktape
            WHERE timestamp >= '2025-06-01'
            AND timestamp <= '2025-06-20'
        """)
        
        stats = cursor.fetchone()
        print(f"\nJune 2025 Statistics:")
        print(f"  Total recordings: {stats['total']}")
        print(f"  Recordings ≥90s: {stats['over_90s']}")
        print(f"  Average duration: {stats['avg_duration']:.1f}s")
        print(f"  Date range: {stats['first_call']} to {stats['last_call']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=" * 80)
    print("USER SEARCH DEBUGGING")
    print("=" * 80)
    
    # Run all analyses
    check_total_june_recordings()
    analyze_orkuser_table()
    analyze_party_fields()
    search_by_name_patterns()
    
    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()