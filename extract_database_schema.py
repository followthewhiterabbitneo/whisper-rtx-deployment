#!/usr/bin/env python3
"""
Extract complete database schema from MariaDB
Creates a visual representation of all tables and relationships
"""

import pymysql
import json
from datetime import datetime
from collections import defaultdict

print("=" * 80)
print("DATABASE SCHEMA EXTRACTOR - First Principles")
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

print(f"\n📊 Connecting to MariaDB...")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Database: {DB_CONFIG['database']}")

try:
    # Connect to database
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("✓ Connected successfully!")
    
    # Get database version and info
    cursor.execute("SELECT VERSION() as version")
    version = cursor.fetchone()['version']
    print(f"\n📌 Database Version: {version}")
    
    # Get all tables
    print("\n🔍 Extracting Schema Information...")
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
    print(f"\n📋 Found {len(tables)} tables in database '{DB_CONFIG['database']}'")
    
    # Store schema information
    schema = {
        'database': DB_CONFIG['database'],
        'version': version,
        'extracted_at': datetime.now().isoformat(),
        'tables': {}
    }
    
    # For each table, get detailed information
    for table in tables:
        table_name = table['TABLE_NAME']
        print(f"\n🔸 Table: {table_name}")
        
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
        cursor.execute("""
            SHOW INDEX FROM `%s`
        """ % table_name)
        
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
        
        print(f"   ├─ Columns: {len(columns)}")
        print(f"   ├─ Indexes: {len(indexes)}")
        print(f"   └─ Foreign Keys: {len(foreign_keys)}")
    
    # Generate visual schema documentation
    print("\n" + "=" * 80)
    print("📊 DATABASE SCHEMA VISUALIZATION")
    print("=" * 80)
    
    # Create schema documentation
    doc_file = f"oreka_database_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(doc_file, 'w') as f:
        f.write(f"# Oreka Database Schema\n\n")
        f.write(f"**Database:** {DB_CONFIG['database']}\n")
        f.write(f"**Server:** {DB_CONFIG['host']}\n")
        f.write(f"**Version:** {version}\n")
        f.write(f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Table of contents
        f.write("## Table of Contents\n\n")
        for table_name in sorted(schema['tables'].keys()):
            f.write(f"- [{table_name}](#{table_name.lower()})\n")
        
        # Relationship diagram
        f.write("\n## Entity Relationships\n\n")
        f.write("```mermaid\nerDiagram\n")
        
        # Add tables and relationships to diagram
        relationships = []
        for table_name, table_data in schema['tables'].items():
            # Add table to diagram
            f.write(f"    {table_name} {{\n")
            for col in table_data['columns'][:5]:  # Show first 5 columns
                col_type = col['COLUMN_TYPE'].split('(')[0]
                key_marker = 'PK' if col['COLUMN_KEY'] == 'PRI' else 'FK' if col['COLUMN_KEY'] == 'MUL' else ''
                f.write(f"        {col_type} {col['COLUMN_NAME']} {key_marker}\n")
            if len(table_data['columns']) > 5:
                f.write(f"        ... {len(table_data['columns']) - 5} more columns\n")
            f.write("    }\n")
            
            # Collect relationships
            for fk in table_data['foreign_keys']:
                rel = f"    {table_name} ||--o{{ {fk['REFERENCED_TABLE_NAME']} : \"{fk['COLUMN_NAME']}\""
                if rel not in relationships:
                    relationships.append(rel)
        
        # Add relationships
        for rel in relationships:
            f.write(rel + "\n")
        
        f.write("```\n\n")
        
        # Detailed table documentation
        f.write("## Table Details\n\n")
        
        for table_name in sorted(schema['tables'].keys()):
            table_data = schema['tables'][table_name]
            info = table_data['info']
            
            f.write(f"### {table_name}\n\n")
            
            # Table stats
            f.write(f"**Statistics:**\n")
            f.write(f"- Rows: {info['rows']:,}\n")
            f.write(f"- Data Size: {info['data_size']:,} bytes\n")
            f.write(f"- Index Size: {info['index_size']:,} bytes\n")
            if info['created']:
                f.write(f"- Created: {info['created']}\n")
            if info['comment']:
                f.write(f"- Comment: {info['comment']}\n")
            f.write("\n")
            
            # Columns table
            f.write("**Columns:**\n\n")
            f.write("| Column | Type | Nullable | Key | Default | Extra |\n")
            f.write("|--------|------|----------|-----|---------|-------|\n")
            
            for col in table_data['columns']:
                key_type = ''
                if col['COLUMN_KEY'] == 'PRI':
                    key_type = '🔑 PK'
                elif col['COLUMN_KEY'] == 'MUL':
                    key_type = '🔗 FK'
                elif col['COLUMN_KEY'] == 'UNI':
                    key_type = '📌 UK'
                
                f.write(f"| {col['COLUMN_NAME']} | {col['COLUMN_TYPE']} | {col['IS_NULLABLE']} | {key_type} | {col['COLUMN_DEFAULT'] or ''} | {col['EXTRA']} |\n")
            
            # Foreign keys
            if table_data['foreign_keys']:
                f.write("\n**Foreign Keys:**\n\n")
                for fk in table_data['foreign_keys']:
                    f.write(f"- `{fk['COLUMN_NAME']}` → `{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`\n")
            
            # Indexes
            if table_data['indexes']:
                f.write("\n**Indexes:**\n\n")
                index_groups = defaultdict(list)
                for idx in table_data['indexes']:
                    index_groups[idx['Key_name']].append(idx)
                
                for idx_name, idx_cols in index_groups.items():
                    idx_type = 'UNIQUE' if idx_cols[0]['Non_unique'] == 0 else 'INDEX'
                    cols = ', '.join([f"{ic['Column_name']}({ic['Sub_part']})" if ic['Sub_part'] else ic['Column_name'] for ic in idx_cols])
                    f.write(f"- `{idx_name}` ({idx_type}): {cols}\n")
            
            f.write("\n---\n\n")
        
        # Key tables for SCREAM
        f.write("## Key Tables for SCREAM Pipeline\n\n")
        f.write("Based on the schema analysis, these are the most important tables:\n\n")
        f.write("1. **recordings** - Main table containing all call recordings\n")
        f.write("2. **orksegments** - Links recordings to users\n")
        f.write("3. **orkusers** - User information (underwriters)\n")
        f.write("4. **call_transcripts** - Stores transcriptions and summaries\n")
        
    print(f"\n✅ Schema documentation saved to: {doc_file}")
    
    # Save JSON version for programmatic use
    json_file = f"oreka_database_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w') as f:
        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, bytes):
                return obj.decode('utf-8', errors='ignore')
            return str(obj)
        
        json.dump(schema, f, indent=2, default=serialize)
    
    print(f"✅ JSON schema saved to: {json_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 SCHEMA SUMMARY")
    print("=" * 80)
    
    # Find the main tables
    main_tables = ['recordings', 'orksegments', 'orkusers', 'call_transcripts']
    
    for table_name in main_tables:
        if table_name in schema['tables']:
            table_data = schema['tables'][table_name]
            print(f"\n🔹 {table_name.upper()}")
            print(f"   Rows: {table_data['info']['rows']:,}")
            
            # Show key columns
            key_cols = [col for col in table_data['columns'] if col['COLUMN_KEY'] in ('PRI', 'MUL')]
            if key_cols:
                print("   Key Columns:")
                for col in key_cols[:5]:
                    print(f"     - {col['COLUMN_NAME']} ({col['COLUMN_TYPE']})")
    
    cursor.close()
    connection.close()
    
except pymysql.Error as e:
    print(f"\n❌ Database connection failed!")
    print(f"Error: {e}")
    print("\nThis script needs to be run from a machine that can reach s40vpsoxweb002")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

print("\n" + "=" * 80)
print("Run this script on your RTX 4090 to extract the full database schema")
print("=" * 80)