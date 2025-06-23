#!/usr/bin/env python3
"""
Explore CORE Oreka tables for call recordings
Focus on the main tables needed for the SCREAM pipeline
"""

import pymysql
from datetime import datetime, timedelta

print("=" * 80)
print("OREKA CORE TABLES EXPLORER")
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

def format_number(num):
    """Format large numbers with commas"""
    return f"{num:,}" if num else "0"

print(f"\nConnecting to MariaDB...")
print(f"Host: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")

try:
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("Connected successfully!\n")
    
    # Define core tables we care about
    core_tables = {
        'orktape': 'Main recordings table (legacy name)',
        'orksegment': 'Call segments linking recordings to users',
        'orkuser': 'Users/underwriters table',
        'call_transcripts': 'Transcriptions and summaries',
        'orkmetadata': 'Additional call metadata'
    }
    
    print("CORE TABLES FOR CALL RECORDINGS")
    print("=" * 80)
    
    for table_name, description in core_tables.items():
        print(f"\n### {table_name.upper()}")
        print(f"Description: {description}")
        
        # Check if table exists and get row count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        row_count = cursor.fetchone()['count']
        print(f"Total Records: {format_number(row_count)}")
        
        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        print("\nColumns:")
        print("-" * 60)
        print(f"{'Field':<25} {'Type':<20} {'Key':<5} {'Null':<5}")
        print("-" * 60)
        
        for col in columns:
            field = col['Field'][:24]
            type_str = col['Type'][:19]
            key = col['Key'] or ''
            null = col['Null']
            print(f"{field:<25} {type_str:<20} {key:<5} {null:<5}")
        
        # Show sample data for key tables
        if table_name == 'orktape' and row_count > 0:
            print("\nRecent Recordings (last 5):")
            cursor.execute("""
                SELECT orkUid as orkuid, filename, duration, timestamp, localParty, remoteParty
                FROM orktape
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            for rec in cursor.fetchall():
                print(f"  - {rec['uid']} | {rec['timestamp']} | {rec['duration']}s | {rec['localParty']}")
        
        elif table_name == 'orkuser' and row_count > 0:
            print("\nSample Users:")
            cursor.execute("""
                SELECT orkUid as orkuid, firstname, lastname, loginstring
                FROM orkuser
                WHERE firstname IS NOT NULL AND lastname IS NOT NULL
                LIMIT 5
            """)
            for user in cursor.fetchall():
                print(f"  - {user['firstname']} {user['lastname']} (ID: {user['uid']})")
    
    # Show relationships
    print("\n" + "=" * 80)
    print("KEY RELATIONSHIPS")
    print("=" * 80)
    
    print("""
    orktape (recordings)
        |
        └── uid ──────────┐
                         ↓
    orksegment          fktape
        |
        ├── fktape ──────┘
        └── fkuser ──────┐
                         ↓
    orkuser             uid
        |
        └── uid ─────────┘
    
    call_transcripts
        |
        └── orkuid → references orktape.orkUid
    """)
    
    # Check for the recordings table (might be aliased)
    print("\n" + "=" * 80)
    print("CHECKING FOR 'recordings' TABLE/VIEW")
    print("=" * 80)
    
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME LIKE '%recording%'
    """, (DB_CONFIG['database'],))
    
    recording_tables = cursor.fetchall()
    if recording_tables:
        print("\nFound recording-related tables/views:")
        for tbl in recording_tables:
            print(f"  - {tbl['TABLE_NAME']} ({tbl['TABLE_TYPE']})")
    else:
        print("\nNo 'recordings' table found.")
        print("Note: 'orktape' is the main recordings table in Oreka")
    
    # Quick stats
    print("\n" + "=" * 80)
    print("QUICK STATS")
    print("=" * 80)
    
    # Total recordings today
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM orktape 
        WHERE DATE(timestamp) = CURDATE()
    """)
    today_count = cursor.fetchone()['count']
    print(f"Recordings today: {format_number(today_count)}")
    
    # Total recordings this week
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM orktape 
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    week_count = cursor.fetchone()['count']
    print(f"Recordings this week: {format_number(week_count)}")
    
    # Average call duration
    cursor.execute("""
        SELECT AVG(duration) as avg_duration 
        FROM orktape 
        WHERE duration > 0 AND duration < 3600
    """)
    avg_duration = cursor.fetchone()['avg_duration']
    if avg_duration:
        print(f"Average call duration: {avg_duration:.1f} seconds")
    
    cursor.close()
    connection.close()
    
except pymysql.Error as e:
    print(f"\nDatabase connection failed!")
    print(f"Error: {e}")
    
except Exception as e:
    print(f"\nUnexpected error: {e}")

print("\n" + "=" * 80)
print("Note: 'orktape' is the legacy name for the recordings table")
print("Use 'orktape' instead of 'recordings' in your queries")
print("=" * 80)