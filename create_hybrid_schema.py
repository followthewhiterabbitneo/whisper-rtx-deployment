#!/usr/bin/env python3
"""
Create database schema for hybrid storage approach
Stores summaries in DB, transcripts on filesystem
"""

import pymysql
import sys

print("=" * 80)
print("HYBRID STORAGE SCHEMA SETUP")
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

# Schema creation SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS call_transcripts_v2 (
    orkuid VARCHAR(50) PRIMARY KEY,
    summary TEXT COMMENT 'Legal brief summary of the call',
    transcript_path VARCHAR(500) COMMENT 'Path to full transcript file',
    loan_numbers JSON COMMENT 'Array of loan numbers found',
    key_facts JSON COMMENT 'Structured key facts extracted',
    sentiment VARCHAR(20) COMMENT 'Call sentiment: positive/negative/neutral',
    processing_time_ms INT COMMENT 'Time to process in milliseconds',
    whisper_model VARCHAR(50) DEFAULT 'large-v3-turbo',
    summary_model VARCHAR(50) DEFAULT 'gemma-3-12b',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_created (created_at),
    INDEX idx_sentiment (sentiment),
    FULLTEXT idx_summary (summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Hybrid storage for call transcriptions';
"""

# Add JSON search capability for MariaDB 10.2+
ALTER_TABLE_SQL = """
ALTER TABLE call_transcripts_v2
ADD COLUMN IF NOT EXISTS loan_numbers_text VARCHAR(1000) 
GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(loan_numbers, '$[*]'))) VIRTUAL,
ADD INDEX idx_loan_search (loan_numbers_text);
"""

print(f"\nConnecting to database...")
print(f"Server: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")

try:
    # Connect to database
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    print("✓ Connected successfully")
    
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
    
    # Try to add virtual column (may fail on older MariaDB)
    try:
        cursor.execute(ALTER_TABLE_SQL)
        print("✓ Added virtual column for loan number search")
    except Exception as e:
        print("⚠️  Could not add virtual column (requires MariaDB 10.2+)")
        print("   Loan number search will use JSON functions")
    
    # Create sample entry
    print("\nInserting sample entry...")
    
    sample_sql = """
    INSERT INTO call_transcripts_v2 
    (orkuid, summary, transcript_path, loan_numbers, key_facts, sentiment, processing_time_ms)
    VALUES (
        '20250620_145645_LOLW',
        'Eric Rawlins called regarding loan #123456789. Discussed payment schedule adjustment due to recent employment change. Agreed to defer one payment and extend term by one month. Customer expressed satisfaction with resolution.',
        '/transcripts/2025/06/20/14/20250620_145645_LOLW.txt',
        '["123456789"]',
        '{"caller": "Eric Rawlins", "topic": "Payment deferral", "resolution": "Approved", "follow_up": "Send confirmation letter"}',
        'positive',
        15234
    )
    """
    
    cursor.execute(sample_sql)
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
    
    # Test 2: JSON search
    cursor.execute("""
        SELECT orkuid, loan_numbers 
        FROM call_transcripts_v2 
        WHERE JSON_CONTAINS(loan_numbers, '"123456789"')
    """)
    results = cursor.fetchall()
    print(f"✓ JSON search found {len(results)} results")
    
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
    print("\nNext steps:")
    print("1. Create /transcripts directory structure on filesystem")
    print("2. Update SCREAM pipeline to use this schema")
    print("3. Process recordings with hybrid storage")
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nMake sure you're running this from the RTX 4090")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()