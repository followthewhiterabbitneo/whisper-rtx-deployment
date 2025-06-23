#!/usr/bin/env python3
"""
Create database schema for hybrid storage - MariaDB 5.5 Compatible Version
Uses TEXT fields for JSON data since MariaDB 5.5 doesn't support JSON type
"""

import pymysql
import json
import sys

print("=" * 80)
print("HYBRID STORAGE SCHEMA SETUP - MariaDB 5.5 Compatible")
print("=" * 80)

# Database configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Schema creation SQL - MariaDB 5.5 compatible
CREATE_TABLE_SQL = """
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Hybrid storage for call transcriptions';
"""

print(f"\nConnecting to database...")
print(f"Server: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")

try:
    # Connect to database
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    print("✓ Connected successfully")
    
    # Check MariaDB version
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"✓ MariaDB version: {version}")
    
    # Check if table already exists
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'call_transcripts_v2'
    """, (DB_CONFIG['database'],))
    
    exists = cursor.fetchone()[0] > 0
    
    if exists:
        print("\n⚠️  Table 'call_transcripts_v2' already exists")
        response = input("Drop and recreate? (y/n): ").lower().strip()
        
        if response == 'y':
            print("Dropping existing table...")
            cursor.execute("DROP TABLE call_transcripts_v2")
            print("✓ Table dropped")
    
    # Create table
    print("\nCreating hybrid storage table...")
    cursor.execute(CREATE_TABLE_SQL)
    print("✓ Table created successfully")
    
    # Create sample entry with JSON as TEXT
    print("\nInserting sample entry...")
    
    # Prepare JSON data
    loan_numbers = ["123456789", "987654321"]
    key_facts = {
        "caller": "Eric Rawlins",
        "topic": "Payment deferral",
        "resolution": "Approved",
        "follow_up": "Send confirmation letter"
    }
    
    sample_sql = """
    INSERT INTO call_transcripts_v2 
    (orkuid, summary, transcript_path, loan_numbers, key_facts, sentiment, processing_time_ms)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(sample_sql, (
        '20250620_145645_LOLW',
        'Eric Rawlins called regarding loan #123456789. Discussed payment schedule adjustment due to recent employment change. Agreed to defer one payment and extend term by one month. Customer expressed satisfaction with resolution.',
        '/transcripts/2025/06/20/14/20250620_145645_LOLW.txt',
        json.dumps(loan_numbers),  # Convert to JSON string
        json.dumps(key_facts),     # Convert to JSON string
        'positive',
        15234
    ))
    
    connection.commit()
    print("✓ Sample entry inserted")
    
    # Test queries
    print("\nTesting queries...")
    
    # Test 1: Summary search (using LIKE for MariaDB 5.5 InnoDB)
    cursor.execute("""
        SELECT orkuid, summary 
        FROM call_transcripts_v2 
        WHERE summary LIKE '%payment%'
    """)
    results = cursor.fetchall()
    print(f"✓ Summary search found {len(results)} results")
    
    # Test 2: JSON search (using LIKE for MariaDB 5.5)
    cursor.execute("""
        SELECT orkuid, loan_numbers 
        FROM call_transcripts_v2 
        WHERE loan_numbers LIKE '%"123456789"%'
    """)
    results = cursor.fetchall()
    print(f"✓ Loan number search found {len(results)} results")
    
    # Show how to retrieve and parse JSON
    print("\nRetrieving and parsing JSON data...")
    cursor.execute("""
        SELECT orkuid, loan_numbers, key_facts 
        FROM call_transcripts_v2 
        WHERE orkuid = '20250620_145645_LOLW'
    """)
    
    row = cursor.fetchone()
    if row:
        orkuid, loan_numbers_json, key_facts_json = row
        
        # Parse JSON from TEXT fields
        loan_numbers = json.loads(loan_numbers_json)
        key_facts = json.loads(key_facts_json)
        
        print(f"✓ Retrieved orkuid: {orkuid}")
        print(f"  Loan numbers: {loan_numbers}")
        print(f"  Key facts: {key_facts}")
    
    # Show table structure
    print("\nTable structure created:")
    print("-" * 60)
    cursor.execute("DESCRIBE call_transcripts_v2")
    
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<30} {row[3]:<5}")
    
    # Close connection
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 80)
    print("✅ HYBRID SCHEMA SETUP COMPLETE")
    print("=" * 80)
    print("\nIMPORTANT: MariaDB 5.5 Compatibility Notes:")
    print("- JSON data is stored as TEXT")
    print("- Use json.dumps() when inserting JSON data")
    print("- Use json.loads() when retrieving JSON data")
    print("- Search JSON with LIKE queries (e.g., WHERE loan_numbers LIKE '%\"123456789\"%')")
    print("\nNext steps:")
    print("1. Create C:\\transcripts directory on Windows")
    print("2. Update pipeline scripts to handle JSON as TEXT")
    print("3. Process recordings with hybrid storage")
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nMake sure you're running this from the RTX 4090")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()