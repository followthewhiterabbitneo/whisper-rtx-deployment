#!/usr/bin/env python3
"""
ENHANCED LOAN VIEWER - With copy button for transcript paths
Preserves Windows backslashes
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
from datetime import datetime
import uvicorn

app = FastAPI(title="Enhanced Loan Viewer")

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
    """List loans"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT loan_numbers
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Extract unique loans
    unique_loans = set()
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            unique_loans.update(loans)
        except:
            pass
    
    loan_list = ""
    for loan in sorted(list(unique_loans)):  # Show ALL loans, no limit
        loan_list += f'<li><a href="/loan/{loan}">Loan #{loan}</a></li>\n'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced Loan Viewer</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2c3e50;
                margin-bottom: 30px;
            }}
            ul {{
                list-style: none;
                padding: 0;
            }}
            li {{
                margin: 10px 0;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
                font-size: 18px;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enhanced Loan Viewer</h1>
            <ul>
                {loan_list}
            </ul>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/loan/{loan_number}", response_class=HTMLResponse)
async def view_loan(loan_number: str):
    """Enhanced loan view with overview cards"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all calls for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.summary,
            ct.sentiment,
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
        return HTMLResponse("<h1>No calls found for this loan</h1><a href='/'>Back</a>")
    
    # Calculate stats
    total_calls = len(calls)
    total_duration = sum(c['duration'] for c in calls)
    avg_duration = total_duration / total_calls if total_calls > 0 else 0
    
    # Date range
    first_date = calls[0]['timestamp']
    last_date = calls[-1]['timestamp']
    date_range = f"{first_date.strftime('%m/%d/%Y')} - {last_date.strftime('%m/%d/%Y')}"
    
    # Find primary contact (most common name)
    names = {}
    for call in calls:
        name = call['user_name']
        if name != 'Unknown':
            names[name] = names.get(name, 0) + 1
    
    primary_contact = max(names, key=names.get) if names else 'Unknown'
    
    # Get sentiment (if available)
    sentiments = [c['sentiment'] for c in calls if c.get('sentiment')]
    sentiment = sentiments[0] if sentiments else 'Neutral'
    
    # Build call rows with unique IDs for copy buttons
    call_rows = ""
    for idx, call in enumerate(calls):
        # Don't convert slashes - keep original path
        transcript_path = call.get('transcript_path', '') or ''
        
        call_rows += f"""
        <tr>
            <td>{call['timestamp'].strftime('%m/%d/%Y %I:%M %p')}</td>
            <td>{call['duration']}s ({call['duration']/60:.1f}m)</td>
            <td>{call['localParty']}</td>
            <td>{call['remoteParty']}</td>
            <td>{call['user_name']}</td>
            <td>
                <div class="transcript-cell">
                    <input type="text" id="path_{idx}" class="transcript-path" value="{transcript_path}" readonly>
                    <button class="copy-btn" onclick="copyPath({idx})">📋</button>
                </div>
            </td>
        </tr>
        """
    
    # Get summary if available
    summaries = [c['summary'] for c in calls if c.get('summary')]
    summary = summaries[0] if summaries else f"This loan has been discussed in {total_calls} calls spanning from {first_date.strftime('%B %d, %Y')} to {last_date.strftime('%B %d, %Y')}."
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan #{loan_number} - Enhanced View</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }}
            .header {{
                background: white;
                padding: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            h1 {{
                color: #2c3e50;
                margin: 0;
                font-size: 28px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat-label {{
                color: #7f8c8d;
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .stat-value {{
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
            }}
            .summary-section {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            .summary-title {{
                color: #2c3e50;
                font-size: 18px;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            .summary-text {{
                color: #34495e;
                line-height: 1.6;
            }}
            table {{
                width: 100%;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }}
            th {{
                background: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 500;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .transcript-cell {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            .transcript-path {{
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #2c3e50;
                background: #f8f9fa;
                border: 1px solid #ddd;
                padding: 4px 8px;
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .copy-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                white-space: nowrap;
            }}
            .copy-btn:hover {{
                background: #2980b9;
            }}
            .copy-btn:active {{
                transform: scale(0.95);
            }}
            .back-link {{
                color: #3498db;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }}
            .back-link:hover {{
                text-decoration: underline;
            }}
            .toast {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #27ae60;
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
                opacity: 0;
                transition: opacity 0.3s;
                pointer-events: none;
            }}
            .toast.show {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>Loan #{loan_number} Overview</h1>
            </div>
        </div>
        
        <div class="container">
            <a href="/" class="back-link">← Back to Loans</a>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Calls</div>
                    <div class="stat-value">{total_calls}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Duration</div>
                    <div class="stat-value">{int(total_duration/60)}m</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Date Range</div>
                    <div class="stat-value" style="font-size: 18px;">{date_range}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Primary Contact</div>
                    <div class="stat-value" style="font-size: 18px;">{primary_contact}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Call Length</div>
                    <div class="stat-value">{int(avg_duration/60)}m</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Sentiment Score</div>
                    <div class="stat-value" style="font-size: 18px;">{sentiment}</div>
                </div>
            </div>
            
            <div class="summary-section">
                <div class="summary-title">Summary: Loan #{loan_number} Timeline</div>
                <div class="summary-text">{summary}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Date/Time</th>
                        <th>Duration</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Contact</th>
                        <th style="width: 400px;">Transcript Path</th>
                    </tr>
                </thead>
                <tbody>
                    {call_rows}
                </tbody>
            </table>
        </div>
        
        <div id="toast" class="toast">Path copied!</div>
        
        <script>
            function copyPath(idx) {{
                const input = document.getElementById('path_' + idx);
                input.select();
                document.execCommand('copy');
                
                // Show toast
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting Enhanced Loan Viewer with Copy...")
    print("Open: http://localhost:8000")
    print("\nTranscript paths preserved with backslashes!")
    uvicorn.run(app, host="0.0.0.0", port=8000)