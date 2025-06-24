#!/usr/bin/env python3
"""
Simplified loan network visualization - fixes dict error
"""

import pymysql
import json
from datetime import datetime

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def generate_simple_visualization(loan_number):
    """Generate simple HTML visualization"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get calls for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not calls:
        print(f"No calls found for loan {loan_number}")
        return None
    
    # Build simple HTML table
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Loan {loan_number} Calls</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #2196F3;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .stats {{
            margin: 20px 0;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Loan #{loan_number} - Call Details</h1>
        
        <div class="stats">
            <strong>Summary:</strong><br>
            Total Calls: {len(calls)}<br>
            Total Duration: {sum(c['duration'] for c in calls) / 60:.1f} minutes<br>
            Date Range: {calls[0]['timestamp'].strftime('%Y-%m-%d')} to {calls[-1]['timestamp'].strftime('%Y-%m-%d')}
        </div>
        
        <table>
            <tr>
                <th>Date/Time</th>
                <th>Duration</th>
                <th>From</th>
                <th>To</th>
                <th>User</th>
                <th>Call ID</th>
            </tr>
"""
    
    for call in calls:
        html_content += f"""
            <tr>
                <td>{call['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{call['duration']}s ({call['duration']/60:.1f}m)</td>
                <td>{call['localParty']}</td>
                <td>{call['remoteParty']}</td>
                <td>{call['user_name']}</td>
                <td>{call['orkuid']}</td>
            </tr>
"""
    
    html_content += """
        </table>
    </div>
</body>
</html>
"""
    
    # Save file
    filename = f"loan_calls_{loan_number}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename

def main():
    print("SIMPLE LOAN VISUALIZATION")
    print("="*50)
    
    loan_number = input("Enter loan number: ")
    
    print(f"\nGenerating visualization for loan {loan_number}...")
    
    filename = generate_simple_visualization(loan_number)
    
    if filename:
        print(f"\n✅ Success! Open this file in your browser:")
        print(f"   {filename}")
    else:
        print("\n❌ No data found for that loan number")

if __name__ == "__main__":
    main()