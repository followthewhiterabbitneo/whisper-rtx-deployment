#!/usr/bin/env python3
"""
Direct MariaDB connection to s40vpsoxweb002
For use on RTX 4090 or any machine that can reach the database
"""

import pymysql
import sys
from datetime import datetime, timedelta

print("=" * 60)
print("MARIADB DIRECT CONNECTION")
print("=" * 60)

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

print(f"\nConnecting to MariaDB 5.5.68")
print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"Database: {DB_CONFIG['database']}")

try:
    # Establish connection
    connection = pymysql.connect(**DB_CONFIG)
    print("✓ Connected successfully!")
    
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Test query - get database version
    cursor.execute("SELECT VERSION() as version")
    result = cursor.fetchone()
    print(f"\nDatabase version: {result['version']}")
    
    # Show available tables
    print("\nAvailable tables:")
    print("-" * 30)
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        table_name = list(table.values())[0]
        print(f"  - {table_name}")
    
    # Query for Eric Rawlins recordings
    print("\nSearching for Eric Rawlins recordings...")
    print("-" * 60)
    
    query = """
    SELECT 
        r.orkuid,
        r.filename,
        r.duration,
        r.timestamp,
        u.firstname,
        u.lastname,
        r.localparty,
        r.remoteparty
    FROM recordings r
    JOIN orksegments s ON r.orkuid = s.fkrecordings
    JOIN orkusers u ON s.fkorkusers = u.uid
    WHERE 
        u.firstname = 'Eric' 
        AND u.lastname = 'Rawlins'
        AND r.duration >= 120
        AND r.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ORDER BY r.timestamp DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    recordings = cursor.fetchall()
    
    if recordings:
        print(f"\nFound {len(recordings)} Eric Rawlins recordings:\n")
        
        for idx, rec in enumerate(recordings, 1):
            print(f"{idx}. Orkuid: {rec['orkuid']}")
            print(f"   Timestamp: {rec['timestamp']}")
            print(f"   Duration: {rec['duration']} seconds")
            print(f"   Filename: {rec['filename']}")
            print(f"   Local Party: {rec['localparty']}")
            print(f"   Remote Party: {rec['remoteparty']}")
            
            # Build file path
            orkuid = rec['orkuid']
            if len(orkuid) >= 15:
                year = orkuid[:4]
                month = orkuid[4:6] 
                day = orkuid[6:8]
                hour = orkuid[9:11]
                path = f"/var/log/orkaudio.prod.nfs/audio/{year}/{month}/{day}/{hour}/{rec['filename']}"
                print(f"   Path: {path}")
            print()
    else:
        print("No Eric Rawlins recordings found in the last 7 days.")
        
        # Try without date filter
        print("\nTrying without date filter...")
        query_all = """
        SELECT COUNT(*) as count
        FROM recordings r
        JOIN orksegments s ON r.orkuid = s.fkrecordings
        JOIN orkusers u ON s.fkorkusers = u.uid
        WHERE 
            u.firstname = 'Eric' 
            AND u.lastname = 'Rawlins'
        """
        cursor.execute(query_all)
        result = cursor.fetchone()
        print(f"Total Eric Rawlins recordings in database: {result['count']}")
    
    # Interactive mode
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    print("Enter SQL queries (or 'quit' to exit):")
    
    while True:
        query = input("\nSQL> ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
            
        try:
            cursor.execute(query)
            if query.upper().startswith('SELECT'):
                results = cursor.fetchall()
                if results:
                    # Print column headers
                    if results:
                        headers = list(results[0].keys())
                        print("\n" + " | ".join(headers))
                        print("-" * (len(" | ".join(headers))))
                        
                        # Print rows
                        for row in results[:20]:  # Limit to 20 rows
                            values = [str(row[h])[:50] for h in headers]  # Truncate long values
                            print(" | ".join(values))
                        
                        if len(results) > 20:
                            print(f"\n... and {len(results) - 20} more rows")
                else:
                    print("No results found.")
            else:
                connection.commit()
                print(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    cursor.close()
    connection.close()
    print("\n✓ Connection closed")
    
except pymysql.Error as e:
    print(f"\n✗ Database connection failed!")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check if you can reach s40vpsoxweb002 from your machine")
    print("2. Verify firewall allows port 3306")
    print("3. Confirm credentials are correct")
    print("4. You may need to run this from the RTX 4090 workstation")
    
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")

print("\n" + "=" * 60)