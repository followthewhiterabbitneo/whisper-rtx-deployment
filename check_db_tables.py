#!/usr/bin/env python3
"""
Quick check: What tables exist on s40vpsoxweb002?
"""

import pymysql

print("=" * 80)
print("DATABASE TABLE CHECK - s40vpsoxweb002")
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
    print(f"\nConnecting to {DB_CONFIG['host']}...")
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    print("✓ Connected")
    
    # Check version
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"✓ MariaDB version: {version}")
    
    # List all tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} tables:")
    print("-" * 40)
    
    # Key tables to look for
    key_tables = ['orktape', 'orksegment', 'orkuser', 'call_transcripts', 'call_transcripts_v2']
    
    all_table_names = [table[0] for table in tables]
    
    # Show first 20 tables
    for table in tables[:20]:
        table_name = table[0]
        marker = "⭐" if table_name in key_tables else "  "
        print(f"{marker} {table_name}")
    
    if len(tables) > 20:
        print(f"   ... and {len(tables) - 20} more tables")
    
    # Check for our specific tables
    print("\n" + "=" * 40)
    print("KEY TABLES CHECK:")
    print("-" * 40)
    
    for table_name in key_tables:
        if table_name in all_table_names:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"✓ {table_name:<20} - {count:,} rows")
        else:
            print(f"✗ {table_name:<20} - NOT FOUND")
    
    # Check if call_transcripts_v2 exists (our new table)
    if 'call_transcripts_v2' in all_table_names:
        print("\n✓ call_transcripts_v2 table exists!")
        cursor.execute("DESCRIBE call_transcripts_v2")
        columns = cursor.fetchall()
        print(f"  Columns: {len(columns)}")
    else:
        print("\n⚠️  call_transcripts_v2 table does not exist")
        print("   Run: python create_hybrid_schema_mariadb55.py")
    
    cursor.close()
    connection.close()
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nPossible issues:")
    print("1. Can't reach s40vpsoxweb002 from your location")
    print("2. Database 'oreka' doesn't exist")
    print("3. Credentials incorrect")

print("\n" + "=" * 80)