#!/usr/bin/env python3
"""
Explore Oreka Database Structure - First Principles
Target: s01vdsoxweb047:3306/oreka (MariaDB 5.5.68)
"""

import sys

# MySQL connector options for Python 3.6
try:
    import pymysql as mysql_connector
    print("Using PyMySQL")
except ImportError:
    try:
        import mysql.connector as mysql_connector
        print("Using mysql-connector-python")
    except ImportError:
        print("ERROR: No MySQL driver found!")
        print("Install with: pip install pymysql")
        sys.exit(1)

# Database configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka'
}

def explore_database():
    """Explore the Oreka database structure"""
    
    try:
        # Connect to database
        print(f"Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}...")
        conn = mysql_connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # 1. List all tables
        print("1. TABLES IN OREKA DATABASE:")
        print("-" * 40)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        print()
        
        # 2. Explore key tables
        key_tables = ['orktape', 'orksegment', 'orkuser', 'scream_processing']
        
        for table_name in key_tables:
            if any(table_name in t for t in tables):
                print(f"2. STRUCTURE OF {table_name.upper()}:")
                print("-" * 40)
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[0]:20} {col[1]:15} {col[2]:5} {col[3] or ''}")
                print()
        
        # 3. Find Eric Rawlins recording
        print("3. SEARCHING FOR ERIC RAWLINS RECORDING:")
        print("-" * 40)
        
        # Search by filename pattern
        filename = '20250620_145645_LOLW'
        print(f"Searching for: {filename}")
        
        # Try orktape first
        cursor.execute("""
            SELECT * FROM orktape 
            WHERE filename LIKE %s 
            OR localparty LIKE %s 
            OR remoteparty LIKE %s
            LIMIT 5
        """, (f'%{filename}%', '%rawlins%', '%rawlins%'))
        
        results = cursor.fetchall()
        if results:
            # Get column names
            cursor.execute("DESCRIBE orktape")
            columns = [col[0] for col in cursor.fetchall()]
            
            print(f"\nFound in orktape:")
            for row in results:
                print("\n  Record:")
                for i, col in enumerate(columns):
                    if row[i]:
                        print(f"    {col}: {row[i]}")
        
        # 4. Sample query to understand data flow
        print("\n4. SAMPLE DATA FLOW:")
        print("-" * 40)
        
        # Get recent recordings
        cursor.execute("""
            SELECT filename, timestamp, duration, localparty, remoteparty 
            FROM orktape 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        recent = cursor.fetchall()
        if recent:
            print("Recent recordings:")
            for rec in recent:
                print(f"  File: {rec[0]}")
                print(f"    Time: {rec[1]}, Duration: {rec[2]}s")
                print(f"    Parties: {rec[3]} <-> {rec[4]}\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check network connectivity to s01vdsoxweb047")
        print("2. Verify credentials (root/admin)")
        print("3. Install MySQL driver: pip install pymysql")

if __name__ == "__main__":
    explore_database()