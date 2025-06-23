#!/usr/bin/env python3
"""
Extract complete database schema from MariaDB (Windows-compatible version)
Creates a visual representation of all tables and relationships
"""

import pymysql
import json
from datetime import datetime
from collections import defaultdict
import sys

# Set encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("DATABASE SCHEMA EXTRACTOR - First Principles")
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

print(f"\nConnecting to MariaDB...")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Database: {DB_CONFIG['database']}")

try:
    # Connect to database
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("Connected successfully!")
    
    # Get database version and info
    cursor.execute("SELECT VERSION() as version")
    version = cursor.fetchone()['version']
    print(f"\nDatabase Version: {version}")
    
    # Get all tables
    print("\nExtracting Schema Information...")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            TABLE_ROWS,
            DATA_LENGTH,
            INDEX_LENGTH,
            CREATE_TIME,
            TABLE_COMMENT
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
    """, (DB_CONFIG['database'],))
    
    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables in database '{DB_CONFIG['database']}'")
    
    # Store schema information
    schema = {
        'database': DB_CONFIG['database'],
        'version': version,
        'extracted_at': datetime.now().isoformat(),
        'tables': {}
    }
    
    # Focus on core tables first
    core_tables = ['orktape', 'orksegment', 'orkuser', 'call_transcripts', 'orkmetadata']
    
    print("\nCORE TABLES:")
    print("-" * 40)
    
    # Process core tables first
    for table in tables:
        table_name = table['TABLE_NAME']
        if table_name not in core_tables:
            continue
            
        print(f"\nTable: {table_name}")
        
        # Get columns
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                EXTRA,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'], table_name))
        
        columns = cursor.fetchall()
        
        # Get indexes
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        indexes = cursor.fetchall()
        
        # Get foreign keys
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (DB_CONFIG['database'], table_name))
        
        foreign_keys = cursor.fetchall()
        
        # Store table info
        schema['tables'][table_name] = {
            'info': {
                'rows': table['TABLE_ROWS'],
                'data_size': table['DATA_LENGTH'],
                'index_size': table['INDEX_LENGTH'],
                'created': str(table['CREATE_TIME']) if table['CREATE_TIME'] else None,
                'comment': table['TABLE_COMMENT']
            },
            'columns': columns,
            'indexes': indexes,
            'foreign_keys': foreign_keys
        }
        
        print(f"   - Columns: {len(columns)}")
        print(f"   - Indexes: {len(indexes)}")
        print(f"   - Foreign Keys: {len(foreign_keys)}")
        print(f"   - Rows: {table['TABLE_ROWS']:,}")
    
    # Generate schema documentation
    print("\n" + "=" * 80)
    print("CREATING SCHEMA DOCUMENTATION")
    print("=" * 80)
    
    # Create schema documentation
    doc_file = f"oreka_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write("OREKA DATABASE SCHEMA\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Database: {DB_CONFIG['database']}\n")
        f.write(f"Server: {DB_CONFIG['host']}\n")
        f.write(f"Version: {version}\n")
        f.write(f"Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Core tables section
        f.write("CORE TABLES FOR CALL RECORDINGS\n")
        f.write("-" * 80 + "\n\n")
        
        # Document each core table
        for table_name in core_tables:
            if table_name not in schema['tables']:
                continue
                
            table_data = schema['tables'][table_name]
            info = table_data['info']
            
            f.write(f"\n{table_name.upper()}\n")
            f.write("=" * len(table_name) + "\n")
            
            # Table description
            if table_name == 'orktape':
                f.write("Main recordings table (legacy name for 'recordings')\n")
            elif table_name == 'orksegment':
                f.write("Links recordings to users/parties\n")
            elif table_name == 'orkuser':
                f.write("User/underwriter information\n")
            elif table_name == 'call_transcripts':
                f.write("Stores transcriptions and summaries\n")
            elif table_name == 'orkmetadata':
                f.write("Additional metadata for recordings\n")
            
            # Stats
            f.write(f"\nStatistics:\n")
            f.write(f"  - Rows: {info['rows']:,}\n")
            f.write(f"  - Data Size: {info['data_size']:,} bytes\n")
            
            # Columns
            f.write(f"\nColumns:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Field':<25} {'Type':<20} {'Key':<5} {'Null':<5}\n")
            f.write("-" * 60 + "\n")
            
            for col in table_data['columns']:
                field = col['COLUMN_NAME'][:24]
                type_str = col['COLUMN_TYPE'][:19]
                key = ''
                if col['COLUMN_KEY'] == 'PRI':
                    key = 'PK'
                elif col['COLUMN_KEY'] == 'MUL':
                    key = 'FK'
                elif col['COLUMN_KEY'] == 'UNI':
                    key = 'UK'
                null = col['IS_NULLABLE']
                
                f.write(f"{field:<25} {type_str:<20} {key:<5} {null:<5}\n")
            
            # Foreign keys
            if table_data['foreign_keys']:
                f.write("\nForeign Keys:\n")
                for fk in table_data['foreign_keys']:
                    f.write(f"  - {fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}\n")
            
            f.write("\n" + "-" * 80 + "\n")
        
        # Relationships diagram
        f.write("\n\nKEY RELATIONSHIPS\n")
        f.write("=" * 80 + "\n")
        f.write("""
orktape (recordings)
    |
    +-- uid --------------+
                         |
orksegment              fktape
    |
    +-- fktape ----------+
    +-- fkuser ----------+
                         |
orkuser                 uid
    |
    +-- uid -------------+

call_transcripts
    |
    +-- orkuid -> references orktape.uid
""")
        
        # All tables summary
        f.write("\n\nALL TABLES IN DATABASE\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total tables: {len(tables)}\n\n")
        
        for table in sorted(tables, key=lambda x: x['TABLE_NAME']):
            f.write(f"- {table['TABLE_NAME']:<30} (Rows: {table['TABLE_ROWS']:>10,})\n")
    
    print(f"\nSchema documentation saved to: {doc_file}")
    
    # Save JSON version
    json_file = f"oreka_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, bytes):
                return obj.decode('utf-8', errors='ignore')
            return str(obj)
        
        json.dump(schema, f, indent=2, default=serialize, ensure_ascii=False)
    
    print(f"JSON schema saved to: {json_file}")
    
    cursor.close()
    connection.close()
    
except pymysql.Error as e:
    print(f"\nDatabase connection failed!")
    print(f"Error: {e}")
    
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)