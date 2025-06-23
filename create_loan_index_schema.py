#!/usr/bin/env python3
"""
Create optimized loan number index for efficient searching
Designed for React/Vite/TypeScript frontend on s01vpsromuls001
"""

import pymysql
import json

print("=" * 80)
print("LOAN NUMBER INDEX SCHEMA - OPTIMIZED FOR SEARCH")
print("=" * 80)

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Create loan index table for fast searching
CREATE_LOAN_INDEX = """
CREATE TABLE IF NOT EXISTS loan_number_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_number VARCHAR(20) NOT NULL,
    orkuid VARCHAR(50) NOT NULL,
    user_name VARCHAR(100),
    user_firstname VARCHAR(50),
    user_lastname VARCHAR(50),
    call_date DATE,
    call_timestamp TIMESTAMP,
    duration INT,
    confidence DECIMAL(3,2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_loan_number (loan_number),
    INDEX idx_user_name (user_name),
    INDEX idx_call_date (call_date),
    INDEX idx_orkuid (orkuid),
    UNIQUE KEY unique_loan_orkuid (loan_number, orkuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Loan number search index';
"""

# Create user loan mapping for "one loan per user"
CREATE_USER_LOANS = """
CREATE TABLE IF NOT EXISTS user_loan_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL UNIQUE,
    user_firstname VARCHAR(50),
    user_lastname VARCHAR(50),
    primary_loan_number VARCHAR(20),
    all_loan_numbers TEXT COMMENT 'JSON array of all loan numbers found',
    total_calls INT DEFAULT 0,
    first_call_date DATE,
    last_call_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_primary_loan (primary_loan_number),
    INDEX idx_user (user_firstname, user_lastname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User to loan number mapping';
"""

# Create API cache table for frontend
CREATE_API_CACHE = """
CREATE TABLE IF NOT EXISTS loan_search_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    result_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API response cache';
"""

def create_tables():
    """Create all necessary tables"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("\n✓ Connected to database")
        
        # Create tables
        tables = [
            ("loan_number_index", CREATE_LOAN_INDEX),
            ("user_loan_mapping", CREATE_USER_LOANS),
            ("loan_search_cache", CREATE_API_CACHE)
        ]
        
        for table_name, create_sql in tables:
            print(f"\nCreating {table_name}...")
            cursor.execute(create_sql)
            print(f"✓ {table_name} created")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✅ All tables created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def populate_loan_index():
    """Populate loan index from existing call_transcripts_v2"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        print("\n\nPOPULATING LOAN INDEX FROM EXISTING DATA...")
        print("-" * 60)
        
        # Get all transcripts with loan numbers
        cursor.execute("""
            SELECT 
                ct.orkuid,
                ct.loan_numbers,
                ct.created_at,
                t.localParty,
                t.remoteParty,
                t.duration,
                t.timestamp
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            WHERE ct.loan_numbers IS NOT NULL 
            AND ct.loan_numbers != '[]'
        """)
        
        transcripts = cursor.fetchall()
        print(f"Found {len(transcripts)} transcripts with loan numbers")
        
        inserted = 0
        for transcript in transcripts:
            try:
                # Parse loan numbers
                loan_numbers = json.loads(transcript['loan_numbers'])
                
                if loan_numbers:
                    # Extract user name from parties
                    user_name = extract_user_name(
                        transcript['localParty'], 
                        transcript['remoteParty']
                    )
                    
                    # Insert each loan number
                    for loan_num in loan_numbers:
                        cursor.execute("""
                            INSERT IGNORE INTO loan_number_index
                            (loan_number, orkuid, user_name, call_date, 
                             call_timestamp, duration)
                            VALUES (%s, %s, %s, DATE(%s), %s, %s)
                        """, (
                            loan_num,
                            transcript['orkuid'],
                            user_name,
                            transcript['timestamp'],
                            transcript['timestamp'],
                            transcript['duration']
                        ))
                        inserted += cursor.rowcount
                        
            except json.JSONDecodeError:
                print(f"  ⚠️  Invalid JSON in {transcript['orkuid']}")
                continue
        
        connection.commit()
        print(f"\n✓ Inserted {inserted} loan number entries")
        
        # Build user loan mapping
        print("\nBuilding user loan mapping...")
        cursor.execute("""
            INSERT INTO user_loan_mapping (user_name, primary_loan_number, total_calls)
            SELECT 
                user_name,
                loan_number,
                COUNT(*) as total_calls
            FROM loan_number_index
            WHERE user_name IS NOT NULL
            GROUP BY user_name
            ON DUPLICATE KEY UPDATE
                total_calls = VALUES(total_calls),
                updated_at = CURRENT_TIMESTAMP
        """)
        
        connection.commit()
        print(f"✓ User loan mapping updated")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"\n❌ Error populating index: {e}")

def extract_user_name(local_party, remote_party):
    """Extract user name from party fields"""
    # This is simplified - you may need more sophisticated logic
    for party in [local_party, remote_party]:
        if party and not party.startswith('+'):
            # Might be a name
            return party
    return None

if __name__ == "__main__":
    create_tables()
    
    # Ask if user wants to populate from existing data
    response = input("\nPopulate index from existing data? (y/n): ").lower().strip()
    if response == 'y':
        populate_loan_index()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Run API server: python loan_search_api.py")
    print("2. Update pipeline to insert into loan_number_index")
    print("3. Connect React frontend to API endpoints")
    print("=" * 80)