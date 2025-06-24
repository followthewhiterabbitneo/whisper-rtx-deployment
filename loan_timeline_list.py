#!/usr/bin/env python3
"""
LOAN TIMELINE LIST - Simple list view with enhanced timeline
Shows all calls in the network with transcript paths
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
import uvicorn

app = FastAPI(title="Loan Timeline List")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

@app.get("/", response_class=HTMLResponse)
async def home():
    """List loans to view timeline"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT loan_numbers, COUNT(*) as count
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY created_at DESC
        LIMIT 30
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Extract loans
    loan_links = ""
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                loan_links += f'<li><a href="/timeline/{loan}">Loan #{loan} ({row["count"]} mentions)</a></li>\n'
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Timeline List</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            ul {{ line-height: 2em; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Loan Timeline List</h1>
        <p>Select a loan to see its enhanced timeline:</p>
        <ul>
            {loan_links}
        </ul>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/timeline/{loan_number}", response_class=HTMLResponse)
async def show_timeline(loan_number: str):
    """Show enhanced timeline for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Step 1: Get direct mentions
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.loan_numbers,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    direct_calls = cursor.fetchall()
    
    # Step 2: Find loan officer (most common party)
    parties = {}
    for call in direct_calls:
        for party in [call['localParty'], call['remoteParty']]:
            parties[party] = parties.get(party, 0) + 1
    
    loan_officer = max(parties, key=parties.get) if parties else None
    
    # Step 3: Get extended network
    network_calls = []
    if loan_officer and len(direct_calls) > 0:
        # Get date range
        first_date = direct_calls[0]['timestamp']
        last_date = direct_calls[-1]['timestamp']
        
        cursor.execute("""
            SELECT 
                t.orkUid as orkuid,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty,
                ct.transcript_path,
                ct.loan_numbers,
                COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            WHERE (t.localParty = %s OR t.remoteParty = %s)
            AND t.timestamp BETWEEN DATE_SUB(%s, INTERVAL 30 DAY) AND DATE_ADD(%s, INTERVAL 30 DAY)
            ORDER BY t.timestamp
        """, (loan_officer, loan_officer, first_date, last_date))
        
        network_calls = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Build timeline
    call_rows = ""
    for idx, call in enumerate(network_calls if network_calls else direct_calls, 1):
        # Check if this call mentions the loan
        has_loan = False
        loan_list = []
        if call.get('loan_numbers'):
            try:
                loan_list = json.loads(call['loan_numbers'])
                has_loan = loan_number in loan_list
            except:
                pass
        
        # Highlight direct mentions
        row_class = 'direct-mention' if has_loan else 'network-call'
        
        call_rows += f"""
        <tr class="{row_class}">
            <td>{idx}</td>
            <td>{call['orkuid']}</td>
            <td>{call['timestamp']}</td>
            <td>{call['duration']}s</td>
            <td>{call['localParty']}</td>
            <td>{call['remoteParty']}</td>
            <td>{call['user_name']}</td>
            <td>{'✓ ' + loan_number if has_loan else ''}</td>
            <td class="transcript-path">{call.get('transcript_path', '') or ''}</td>
        </tr>
        """
    
    # Calculate stats
    total_calls = len(network_calls) if network_calls else len(direct_calls)
    direct_count = len(direct_calls)
    network_count = total_calls - direct_count
    total_duration = sum(c['duration'] for c in (network_calls if network_calls else direct_calls))
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan_number} Timeline</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px;
                background: #f5f5f5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .stats {{
                background: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
            }}
            .stat-box {{
                text-align: center;
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #0066cc;
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
                background: #0066cc;
                color: white;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background: #f5f5f5;
            }}
            .direct-mention {{
                background: #e8f8e8;
                font-weight: bold;
            }}
            .network-call {{
                color: #666;
            }}
            .transcript-path {{
                font-family: monospace;
                font-size: 0.9em;
                word-break: break-all;
            }}
            .back {{
                display: inline-block;
                margin-bottom: 20px;
                color: #0066cc;
                text-decoration: none;
            }}
            .legend {{
                margin: 20px 0;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }}
            .legend span {{
                margin-right: 20px;
            }}
            .direct-indicator {{
                background: #e8f8e8;
                padding: 2px 8px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back">← Back to Loans</a>
            
            <h1>Loan #{loan_number} - Enhanced Timeline</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{direct_count}</div>
                    <div>Direct Mentions</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total_calls}</div>
                    <div>Total Network Calls</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{network_count}</div>
                    <div>Related Calls</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total_duration/60:.1f}m</div>
                    <div>Total Duration</div>
                </div>
            </div>
            
            <div class="legend">
                <strong>Legend:</strong>
                <span class="direct-indicator">Green rows = Direct loan mention</span>
                <span>Gray rows = Related network calls</span>
            </div>
            
            <h2>Timeline of All Calls</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Call ID</th>
                    <th>Timestamp</th>
                    <th>Duration</th>
                    <th>From</th>
                    <th>To</th>
                    <th>User</th>
                    <th>Loan</th>
                    <th>Transcript Path</th>
                </tr>
                {call_rows}
            </table>
            
            <div style="margin-top: 20px;">
                <p><strong>Loan Officer:</strong> {loan_officer or 'Not identified'}</p>
                <p><strong>Timeline Span:</strong> {network_calls[0]['timestamp'] if network_calls else direct_calls[0]['timestamp'] if direct_calls else 'N/A'} 
                   to {network_calls[-1]['timestamp'] if network_calls else direct_calls[-1]['timestamp'] if direct_calls else 'N/A'}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting Loan Timeline List...")
    print("Open: http://localhost:8000")
    print("\nSimple list view with enhanced timeline!")
    uvicorn.run(app, host="0.0.0.0", port=8000)