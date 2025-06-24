#!/usr/bin/env python3
"""
FIRST PRINCIPLES LOAN BRIEF - No hardcoding, loads real loans
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
import uvicorn

app = FastAPI(title="First Principles Loan Brief")

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
    """First principles - show what's actually in the database"""
    
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        # Simple query - just get some loans
        cursor.execute("""
            SELECT loan_numbers
            FROM call_transcripts_v2
            WHERE loan_numbers != '[]'
            ORDER BY created_at DESC
            LIMIT 50
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
        
        # Build simple HTML
        loan_list = ""
        for loan in sorted(list(unique_loans))[:20]:  # First 20
            loan_list += f'<li><a href="/loan/{loan}">Loan #{loan}</a></li>\n'
        
    except Exception as e:
        loan_list = f'<li>Error loading loans: {str(e)}</li>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>First Principles Loan Brief</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            ul {{ line-height: 2em; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Recent Loans</h1>
        <p>Found in database (first principles):</p>
        <ul>
            {loan_list}
        </ul>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/loan/{loan_number}", response_class=HTMLResponse)
async def show_loan(loan_number: str):
    """Show calls for a loan"""
    
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.orkUid,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            WHERE ct.loan_numbers LIKE %s
            ORDER BY t.timestamp
        """, (f'%{loan_number}%',))
        
        calls = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Build table
        rows = ""
        for call in calls:
            rows += f"""
            <tr>
                <td>{call['orkUid']}</td>
                <td>{call['timestamp']}</td>
                <td>{call['duration']}s</td>
                <td>{call['localParty']}</td>
                <td>{call['remoteParty']}</td>
            </tr>
            """
        
    except Exception as e:
        rows = f'<tr><td colspan="5">Error: {str(e)}</td></tr>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan_number}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #f0f0f0; }}
            a {{ color: #0066cc; }}
        </style>
    </head>
    <body>
        <a href="/">← Back</a>
        <h1>Loan #{loan_number}</h1>
        <table>
            <tr>
                <th>Call ID</th>
                <th>Date</th>
                <th>Duration</th>
                <th>From</th>
                <th>To</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting First Principles Loan Brief...")
    print("Open: http://localhost:8000")
    print("\nThis loads REAL loans from your database!")
    uvicorn.run(app, host="0.0.0.0", port=8000)