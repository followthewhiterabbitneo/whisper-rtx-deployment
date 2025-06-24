#!/usr/bin/env python3
"""
ENHANCED LOAN BRIEF HOME - Clickable call IDs and transcript links
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
import pymysql
import json
import os
import uvicorn

app = FastAPI(title="Loan Brief Home Enhanced")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

@app.get("/", response_class=HTMLResponse)
def home():
    """Homepage with known loans"""
    
    known_loans = [
        "1225237672",
        "1225381964", 
        "1225344762",
        "0460002",
        "0461546"
    ]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Brief System</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1976d2;
                text-align: center;
            }
            .loan-list {
                list-style: none;
                padding: 0;
            }
            .loan-item {
                padding: 15px;
                margin: 10px 0;
                background: #e3f2fd;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .loan-item:hover {
                background: #bbdefb;
                transform: translateX(5px);
            }
            .search-box {
                text-align: center;
                margin: 30px 0;
            }
            input {
                padding: 10px;
                width: 300px;
                border: 2px solid #1976d2;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                padding: 10px 20px;
                background: #1976d2;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background: #1565c0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 Loan Brief System</h1>
            
            <div class="search-box">
                <form action="/search" method="get">
                    <input type="text" name="loan" placeholder="Enter loan number..." required />
                    <button type="submit">Search</button>
                </form>
            </div>
            
            <h2>Quick Access Loans:</h2>
            <ul class="loan-list">
    """
    
    for loan in known_loans:
        html += f"""
                <li class="loan-item" onclick="window.location.href='/search?loan={loan}'">
                    📋 Loan #{loan}
                </li>
        """
    
    html += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/search", response_class=HTMLResponse)
def search_loan(loan: str):
    """Search for a specific loan with enhanced links"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    loan = loan.strip()
    
    # Get calls with transcript info
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.summary,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp DESC
    """, (f'%{loan}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan} - Details</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #1976d2; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background: #1976d2; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .back {{ display: inline-block; margin-bottom: 20px; color: #1976d2; text-decoration: none; }}
            .back:hover {{ text-decoration: underline; }}
            a {{ color: #1976d2; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .call-id {{ font-weight: bold; }}
            .transcript-link {{ color: #4CAF50; }}
            .summary {{ background: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back">← Back to Home</a>
            <h1>📋 Loan #{loan}</h1>
            <p>Found <strong>{len(calls)}</strong> calls | Total duration: <strong>{sum(c['duration'] for c in calls) / 60:.1f}</strong> minutes</p>
    """
    
    if calls:
        html += """
            <table>
                <tr>
                    <th>Call ID</th>
                    <th>Date/Time</th>
                    <th>Duration</th>
                    <th>From → To</th>
                    <th>User</th>
                    <th>Actions</th>
                </tr>
        """
        
        for call in calls:
            orkuid = call['orkuid']
            html += f"""
                <tr>
                    <td>
                        <a href="/brief/{orkuid}" class="call-id" title="View loan brief">
                            {orkuid}
                        </a>
                    </td>
                    <td>{call['timestamp']}</td>
                    <td>{call['duration']}s</td>
                    <td>{call['localParty']} → {call['remoteParty']}</td>
                    <td>{call['user_name']}</td>
                    <td>
                        <a href="/brief/{orkuid}" title="View brief">📄 Brief</a> | 
                        <a href="/transcript/{orkuid}" class="transcript-link" title="View transcript">📝 Transcript</a>
                    </td>
                </tr>
            """
        
        html += "</table>"
        
        # Show first summary if available
        for call in calls:
            if call.get('summary'):
                html += f"""
                <div class="summary">
                    <h3>Sample Brief (from {call['orkuid']}):</h3>
                    <p>{call['summary']}</p>
                </div>
                """
                break
    else:
        html += "<p>No calls found for this loan number.</p>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/brief/{orkuid}", response_class=HTMLResponse)
def show_brief(orkuid: str):
    """Show loan brief for a specific call"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ct.*,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            t.filename,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.orkuid = %s
    """, (orkuid,))
    
    call = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not call:
        return HTMLResponse("<h1>Call not found</h1><a href='/'>Back to Home</a>")
    
    # Parse loan numbers
    loans = []
    try:
        loans = json.loads(call['loan_numbers']) if call['loan_numbers'] else []
    except:
        pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Brief - {orkuid}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #1976d2; }}
            .back {{ display: inline-block; margin-bottom: 20px; color: #1976d2; text-decoration: none; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .info-box {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
            .summary {{ background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .transcript-link {{ display: inline-block; margin: 20px 0; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
            .transcript-link:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/search?loan={loans[0] if loans else ''}" class="back">← Back to Loan</a>
            
            <h1>📄 Loan Brief: {orkuid}</h1>
            
            <div class="info-grid">
                <div class="info-box">
                    <h3>Call Information</h3>
                    <p><strong>Date:</strong> {call['timestamp']}</p>
                    <p><strong>Duration:</strong> {call['duration']} seconds ({call['duration']/60:.1f} minutes)</p>
                    <p><strong>Parties:</strong> {call['localParty']} ↔ {call['remoteParty']}</p>
                    <p><strong>User:</strong> {call['user_name']}</p>
                </div>
                
                <div class="info-box">
                    <h3>Loan Details</h3>
                    <p><strong>Loan Numbers:</strong> {', '.join(loans) if loans else 'None detected'}</p>
                    <p><strong>Audio File:</strong> {call['filename']}</p>
                    <p><strong>Processed:</strong> {call['created_at']}</p>
                </div>
            </div>
            
            <div class="summary">
                <h3>Summary / Brief</h3>
                <p>{call['summary'] if call['summary'] else 'No summary available yet.'}</p>
            </div>
            
            <a href="/transcript/{orkuid}" class="transcript-link">
                📝 View Full Transcript
            </a>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/transcript/{orkuid}", response_class=PlainTextResponse)
def show_transcript(orkuid: str):
    """Show full transcript for a call"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT transcript_text, transcript_path
        FROM call_transcripts_v2
        WHERE orkuid = %s
    """, (orkuid,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result:
        return "Transcript not found"
    
    # Return transcript text if available
    if result['transcript_text']:
        return result['transcript_text']
    
    # Otherwise try to read from file
    if result['transcript_path']:
        try:
            # Handle Windows paths
            path = result['transcript_path'].replace('\\', '/')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            pass
    
    return "Transcript file not accessible"

if __name__ == "__main__":
    print("Starting Enhanced Loan Brief System...")
    print("Open: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)