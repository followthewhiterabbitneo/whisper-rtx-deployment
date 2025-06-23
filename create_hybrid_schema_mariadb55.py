#!/usr/bin/env python3
"""
Create database schema for hybrid storage approach - MariaDB 5.5 compatible
Stores summaries in DB, transcripts on filesystem
Uses TEXT fields instead of JSON for compatibility
"""

import pymysql
import sys
import json

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
    loan_numbers TEXT COMMENT 'JSON array of loan numbers as text',
    key_facts TEXT COMMENT 'JSON structured key facts as text',
    sentiment VARCHAR(20) COMMENT 'Call sentiment: positive/negative/neutral',
    processing_time_ms INT COMMENT 'Time to process in milliseconds',
    whisper_model VARCHAR(50) DEFAULT 'large-v3-turbo',
    summary_model VARCHAR(50) DEFAULT 'gemma-3-12b',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_created (created_at),
    INDEX idx_sentiment (sentiment),
    FULLTEXT idx_summary (summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Hybrid storage for call transcriptions';
"""

# Helper function to search loan numbers in TEXT field
LOAN_SEARCH_FUNCTION = """
CREATE FUNCTION IF NOT EXISTS search_loan_number(json_text TEXT, loan_number VARCHAR(50))
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    RETURN json_text LIKE CONCAT('%"', loan_number, '"%');
END;
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
    
    # Try to create helper function
    try:
        cursor.execute("DROP FUNCTION IF EXISTS search_loan_number")
        cursor.execute(LOAN_SEARCH_FUNCTION)
        print("✓ Created loan search helper function")
    except Exception as e:
        print("⚠️  Could not create helper function")
        print("   Will use LIKE queries for loan searches")
    
    # Create sample entry
    print("\nInserting sample entry...")
    
    # Prepare JSON data as strings
    loan_numbers = json.dumps(["123456789"])
    key_facts = json.dumps({
        "caller": "Eric Rawlins",
        "topic": "Payment deferral",
        "resolution": "Approved",
        "follow_up": "Send confirmation letter"
    })
    
    sample_sql = """
    INSERT INTO call_transcripts_v2 
    (orkuid, summary, transcript_path, loan_numbers, key_facts, sentiment, processing_time_ms)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(sample_sql, (
        '20250620_145645_LOLW',
        'Eric Rawlins called regarding loan #123456789. Discussed payment schedule adjustment due to recent employment change. Agreed to defer one payment and extend term by one month. Customer expressed satisfaction with resolution.',
        '/transcripts/2025/06/20/14/20250620_145645_LOLW.txt',
        loan_numbers,
        key_facts,
        'positive',
        15234
    ))
    
    connection.commit()
    print("✓ Sample entry inserted")
    
    # Test queries
    print("\nTesting queries...")
    
    # Test 1: Full-text search
    cursor.execute("""
        SELECT orkuid, summary 
        FROM call_transcripts_v2 
        WHERE MATCH(summary) AGAINST('payment' IN BOOLEAN MODE)
    """)
    results = cursor.fetchall()
    print(f"✓ Full-text search found {len(results)} results")
    
    # Test 2: Loan number search using LIKE
    cursor.execute("""
        SELECT orkuid, loan_numbers 
        FROM call_transcripts_v2 
        WHERE loan_numbers LIKE %s
    """, ('%"123456789"%',))
    results = cursor.fetchall()
    print(f"✓ Loan number search found {len(results)} results")
    
    # Test 3: Show how to extract data from JSON text
    print("\nDemonstrating JSON text extraction:")
    cursor.execute("""
        SELECT orkuid, key_facts 
        FROM call_transcripts_v2 
        WHERE orkuid = '20250620_145645_LOLW'
    """)
    
    for orkuid, key_facts_text in cursor.fetchall():
        key_facts_dict = json.loads(key_facts_text)
        print(f"  Caller: {key_facts_dict.get('caller')}")
        print(f"  Topic: {key_facts_dict.get('topic')}")
        print(f"  Resolution: {key_facts_dict.get('resolution')}")
    
    # Show table structure
    print("\nTable structure created:")
    print("-" * 60)
    cursor.execute("DESCRIBE call_transcripts_v2")
    
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<30} {row[3]:<5}")
    
    # Provide Python helper functions
    print("\n" + "=" * 80)
    print("PYTHON HELPER FUNCTIONS")
    print("=" * 80)
    print("""
# To insert JSON data:
import json

loan_numbers = json.dumps(["123456", "789012"])
key_facts = json.dumps({"caller": "John Doe", "topic": "Payment"})

cursor.execute(
    "INSERT INTO call_transcripts_v2 (orkuid, loan_numbers, key_facts, ...) VALUES (%s, %s, %s, ...)",
    (orkuid, loan_numbers, key_facts, ...)
)

# To search loan numbers:
cursor.execute(
    "SELECT * FROM call_transcripts_v2 WHERE loan_numbers LIKE %s",
    ('%"' + loan_number + '"%',)
)

# To extract JSON data:
cursor.execute("SELECT key_facts FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
key_facts_text = cursor.fetchone()[0]
key_facts_dict = json.loads(key_facts_text) if key_facts_text else {}
""")
    
    # Close connection
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 80)
    print("✅ HYBRID SCHEMA SETUP COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Create /transcripts directory structure on filesystem")
    print("2. Update SCREAM pipeline to use this schema")
    print("3. Process recordings with hybrid storage")
    print("\nNote: Using TEXT fields for JSON data due to MariaDB 5.5 limitations")
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nMake sure you're running this from the RTX 4090")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()