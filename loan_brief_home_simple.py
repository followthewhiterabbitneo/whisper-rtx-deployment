#!/usr/bin/env python3
"""
LOAN BRIEF HOME - Simplified version, better URL handling
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
import uvicorn

app = FastAPI(title="Loan Brief Home")

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
    """Simple homepage with working links"""
    
    # Hardcode some known loans for testing
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
        <title>Loan Brief Home</title>
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
            }
            .loan-item:hover {
                background: #bbdefb;
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 Loan Brief Home</h1>
            
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
                    Loan #{loan}
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
    """Search for a specific loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Clean the loan number
    loan = loan.strip()
    
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
        ORDER BY t.timestamp DESC
    """, (f'%{loan}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #1976d2; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #1976d2; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .back {{ display: inline-block; margin-bottom: 20px; color: #1976d2; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back">← Back to Home</a>
            <h1>Loan #{loan}</h1>
            <p>Found {len(calls)} calls</p>
    """
    
    if calls:
        html += """
            <table>
                <tr>
                    <th>Date/Time</th>
                    <th>Duration</th>
                    <th>From</th>
                    <th>To</th>
                    <th>User</th>
                </tr>
        """
        
        for call in calls:
            html += f"""
                <tr>
                    <td>{call['timestamp']}</td>
                    <td>{call['duration']}s</td>
                    <td>{call['localParty']}</td>
                    <td>{call['remoteParty']}</td>
                    <td>{call['user_name']}</td>
                </tr>
            """
        
        html += "</table>"
    else:
        html += "<p>No calls found for this loan number.</p>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    print("Starting Simple Loan Brief Home...")
    print("Open: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)