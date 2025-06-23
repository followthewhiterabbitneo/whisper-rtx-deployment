#!/usr/bin/env python3
"""
Generate Entity Relationship Diagram (ERD) for Oreka Database
Creates both text-based and graphviz visualizations
"""

import pymysql
from datetime import datetime
import graphviz
import os

print("=" * 80)
print("DATABASE ERD GENERATOR")
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

def format_bytes(bytes_val):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

print(f"\n🔌 Connecting to {DB_CONFIG['host']}...")

try:
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    print("✓ Connected!")
    
    # Get all tables with sizes
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            TABLE_ROWS,
            DATA_LENGTH + INDEX_LENGTH as TOTAL_SIZE
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        ORDER BY DATA_LENGTH + INDEX_LENGTH DESC
    """, (DB_CONFIG['database'],))
    
    tables = cursor.fetchall()
    
    print(f"\n📊 Database Overview:")
    print(f"   Tables: {len(tables)}")
    total_size = sum(t['TOTAL_SIZE'] for t in tables if t['TOTAL_SIZE'])
    print(f"   Total Size: {format_bytes(total_size)}")
    
    # Create text-based visualization
    print("\n" + "=" * 80)
    print("📐 TABLE RELATIONSHIPS (Text Visualization)")
    print("=" * 80)
    
    # Get all foreign key relationships
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME
    """, (DB_CONFIG['database'],))
    
    relationships = cursor.fetchall()
    
    # Build relationship map
    rel_map = {}
    for rel in relationships:
        src = rel['TABLE_NAME']
        dst = rel['REFERENCED_TABLE_NAME']
        if src not in rel_map:
            rel_map[src] = []
        rel_map[src].append({
            'table': dst,
            'via': f"{rel['COLUMN_NAME']} → {rel['REFERENCED_COLUMN_NAME']}"
        })
    
    # Display core tables and their relationships
    core_tables = ['recordings', 'orksegments', 'orkusers', 'call_transcripts']
    
    print("\n🎯 CORE TABLES:")
    print("─" * 50)
    
    for table_name in core_tables:
        # Get table info
        table_info = next((t for t in tables if t['TABLE_NAME'] == table_name), None)
        if not table_info:
            continue
            
        print(f"\n📦 {table_name.upper()}")
        print(f"   Records: {table_info['TABLE_ROWS']:,}")
        print(f"   Size: {format_bytes(table_info['TOTAL_SIZE'])}")
        
        # Get primary key
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s
            AND COLUMN_KEY = 'PRI'
        """, (DB_CONFIG['database'], table_name))
        
        pk = cursor.fetchone()
        if pk:
            print(f"   Primary Key: {pk['COLUMN_NAME']}")
        
        # Show relationships
        if table_name in rel_map:
            print("   References:")
            for ref in rel_map[table_name]:
                print(f"     → {ref['table']} ({ref['via']})")
        
        # Show tables that reference this one
        refs_to_this = []
        for src, refs in rel_map.items():
            for ref in refs:
                if ref['table'] == table_name:
                    refs_to_this.append(f"{src} ({ref['via']})")
        
        if refs_to_this:
            print("   Referenced by:")
            for ref in refs_to_this:
                print(f"     ← {ref}")
    
    # Create GraphViz ERD
    print("\n" + "=" * 80)
    print("🎨 GENERATING GRAPHVIZ ERD")
    print("=" * 80)
    
    # Create a new directed graph
    dot = graphviz.Digraph(comment='Oreka Database ERD')
    dot.attr(rankdir='TB', nodesep='1', ranksep='1.5')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    
    # Add nodes for each table
    for table in tables:
        table_name = table['TABLE_NAME']
        
        # Get columns for this table
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                COLUMN_TYPE,
                COLUMN_KEY
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            LIMIT 10
        """, (DB_CONFIG['database'], table_name))
        
        columns = cursor.fetchall()
        
        # Build label
        label = f"{{{table_name}|"
        col_list = []
        
        for col in columns:
            col_str = col['COLUMN_NAME']
            if col['COLUMN_KEY'] == 'PRI':
                col_str = f"PK: {col_str}"
            elif col['COLUMN_KEY'] == 'MUL':
                col_str = f"FK: {col_str}"
            col_list.append(col_str)
        
        if len(columns) == 10:
            col_list.append("...")
        
        label += "\\l".join(col_list) + "\\l}"
        
        # Color code by table type
        if table_name in core_tables:
            dot.node(table_name, label, fillcolor='lightcoral')
        elif 'transcript' in table_name.lower():
            dot.node(table_name, label, fillcolor='lightgreen')
        else:
            dot.node(table_name, label)
    
    # Add edges for relationships
    for rel in relationships:
        dot.edge(rel['TABLE_NAME'], rel['REFERENCED_TABLE_NAME'], 
                label=rel['COLUMN_NAME'], fontsize='10')
    
    # Save the graph
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'oreka_database_erd_{timestamp}'
    
    # Render as PNG and PDF
    dot.render(output_file, format='png', cleanup=True)
    dot.render(output_file, format='pdf', cleanup=True)
    
    print(f"\n✅ ERD diagrams saved:")
    print(f"   - {output_file}.png")
    print(f"   - {output_file}.pdf")
    
    # Create simplified ASCII diagram
    print("\n" + "=" * 80)
    print("📋 SIMPLIFIED ASCII DIAGRAM")
    print("=" * 80)
    print("""
    ┌─────────────────┐
    │   orkusers      │
    │ (Underwriters)  │
    └────────┬────────┘
             │ uid
             │
    ┌────────▼────────┐     ┌─────────────────┐
    │  orksegments    │     │   recordings    │
    │ (Links)         ├─────┤ (Audio Files)   │
    └─────────────────┘     └────────┬────────┘
                                     │ orkuid
                                     │
                            ┌────────▼────────┐
                            │ call_transcripts│
                            │ (Transcriptions)│
                            └─────────────────┘
    
    Key Relationships:
    - orkusers ←→ orksegments: Links users to call segments
    - orksegments ←→ recordings: Links segments to recordings
    - recordings ←→ call_transcripts: Stores transcription results
    """)
    
    # Close connection
    cursor.close()
    connection.close()
    
    print("\n✅ Schema extraction complete!")
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nMake sure to run this from a machine that can reach s01vdsoxweb047")
    
except ImportError:
    print("\n❌ Missing dependency: graphviz")
    print("Install with: pip install graphviz")
    print("Also need system graphviz: apt-get install graphviz (Linux) or choco install graphviz (Windows)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)