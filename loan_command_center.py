#!/usr/bin/env python3
"""
LOAN COMMAND CENTER - All loan features in one web interface
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import pymysql
import json
from datetime import datetime
import os
import uvicorn
import subprocess

app = FastAPI(title="Loan Command Center")

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
    """Command center home with all features"""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Command Center</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }
            .header {
                background: white;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                margin: 0;
                color: #2c3e50;
                text-align: center;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature-card {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                transition: all 0.3s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .feature-icon {
                font-size: 48px;
                margin-bottom: 15px;
            }
            .feature-title {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .feature-desc {
                color: #7f8c8d;
                margin-bottom: 20px;
            }
            .feature-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                text-decoration: none;
                display: inline-block;
            }
            .feature-btn:hover {
                background: #2980b9;
            }
            .quick-search {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                text-align: center;
            }
            .search-input {
                padding: 12px 20px;
                font-size: 16px;
                border: 1px solid #ddd;
                border-radius: 5px;
                width: 300px;
                margin-right: 10px;
            }
            .search-btn {
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .search-btn:hover {
                background: #229954;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Loan Command Center</h1>
        </div>
        
        <div class="container">
            <div class="quick-search">
                <h2>Quick Loan Search</h2>
                <input type="text" id="loanNumber" class="search-input" placeholder="Enter loan number...">
                <button class="search-btn" onclick="quickSearch()">Search</button>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Loan Timeline</div>
                    <div class="feature-desc">View call timeline with feedback options</div>
                    <a href="/timeline" class="feature-btn">Open Timeline</a>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📄</div>
                    <div class="feature-title">Generate Loan Brief</div>
                    <div class="feature-desc">Create comprehensive loan summary PDF</div>
                    <button class="feature-btn" onclick="showBriefModal()">Generate Brief</button>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Find Untranscribed</div>
                    <div class="feature-desc">Identify calls needing transcription</div>
                    <button class="feature-btn" onclick="showUntranscribedModal()">Find Calls</button>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📞</div>
                    <div class="feature-title">Broker Activity</div>
                    <div class="feature-desc">Track broker calls across loans</div>
                    <a href="/broker-tracker" class="feature-btn">Track Brokers</a>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">➕</div>
                    <div class="feature-title">Add Missing Call</div>
                    <div class="feature-desc">Insert calls into loan timeline</div>
                    <button class="feature-btn" onclick="showAddCallModal()">Add Call</button>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📈</div>
                    <div class="feature-title">Loan Analytics</div>
                    <div class="feature-desc">View loans with 10+ calls</div>
                    <a href="/analytics" class="feature-btn">View Analytics</a>
                </div>
            </div>
        </div>
        
        <!-- Modals -->
        <div id="briefModal" class="modal" style="display:none;">
            <div class="modal-content">
                <span class="close" onclick="closeBriefModal()">&times;</span>
                <h2>Generate Loan Brief</h2>
                <input type="text" id="briefLoanNumber" placeholder="Enter loan number">
                <button onclick="generateBrief()">Generate</button>
                <div id="briefResult"></div>
            </div>
        </div>
        
        <div id="untranscribedModal" class="modal" style="display:none;">
            <div class="modal-content">
                <span class="close" onclick="closeUntranscribedModal()">&times;</span>
                <h2>Find Untranscribed Calls</h2>
                <button onclick="findUntranscribedForLoan()">For Specific Loan</button>
                <button onclick="findAllUntranscribed()">System-Wide Summary</button>
                <div id="untranscribedResult"></div>
            </div>
        </div>
        
        <div id="addCallModal" class="modal" style="display:none;">
            <div class="modal-content">
                <span class="close" onclick="closeAddCallModal()">&times;</span>
                <h2>Add Missing Call</h2>
                <input type="text" id="addLoanNumber" placeholder="Loan number">
                <input type="text" id="addOrkuid" placeholder="Call ID (orkUid)">
                <button onclick="addMissingCall()">Add Call</button>
                <div id="addCallResult"></div>
            </div>
        </div>
        
        <style>
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }
            .modal-content {
                background-color: white;
                margin: 15% auto;
                padding: 30px;
                border-radius: 8px;
                width: 500px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            .close:hover {
                color: black;
            }
            .modal-content input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            .modal-content button {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            .modal-content button:hover {
                background: #2980b9;
            }
            #briefResult, #untranscribedResult, #addCallResult {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 4px;
                max-height: 300px;
                overflow-y: auto;
            }
        </style>
        
        <script>
            function quickSearch() {
                const loanNumber = document.getElementById('loanNumber').value;
                if (loanNumber) {
                    window.location.href = `/loan-view/${loanNumber}`;
                }
            }
            
            function showBriefModal() {
                document.getElementById('briefModal').style.display = 'block';
            }
            
            function closeBriefModal() {
                document.getElementById('briefModal').style.display = 'none';
            }
            
            function showUntranscribedModal() {
                document.getElementById('untranscribedModal').style.display = 'block';
            }
            
            function closeUntranscribedModal() {
                document.getElementById('untranscribedModal').style.display = 'none';
            }
            
            function showAddCallModal() {
                document.getElementById('addCallModal').style.display = 'block';
            }
            
            function closeAddCallModal() {
                document.getElementById('addCallModal').style.display = 'none';
            }
            
            async function generateBrief() {
                const loanNumber = document.getElementById('briefLoanNumber').value;
                if (!loanNumber) return;
                
                const resultDiv = document.getElementById('briefResult');
                resultDiv.innerHTML = 'Generating brief...';
                
                const response = await fetch(`/api/generate-brief/${loanNumber}`);
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <p>✅ Brief generated successfully!</p>
                        <p>File: ${result.filename}</p>
                        <a href="/download-brief/${loanNumber}" target="_blank">Download Brief</a>
                    `;
                } else {
                    resultDiv.innerHTML = `<p>❌ Error: ${result.error}</p>`;
                }
            }
            
            async function findUntranscribedForLoan() {
                const loanNumber = prompt('Enter loan number:');
                if (!loanNumber) return;
                
                const resultDiv = document.getElementById('untranscribedResult');
                resultDiv.innerHTML = 'Searching...';
                
                const response = await fetch(`/api/untranscribed/${loanNumber}`);
                const result = await response.json();
                
                let html = `<h3>Untranscribed Calls for Loan ${loanNumber}</h3>`;
                if (result.count === 0) {
                    html += '<p>✅ All calls transcribed!</p>';
                } else {
                    html += `<p>⚠️ Found ${result.count} untranscribed calls</p>`;
                    html += '<ul>';
                    result.calls.forEach(call => {
                        html += `<li>${call.timestamp} - ${call.duration}s - ${call.orkuid}</li>`;
                    });
                    html += '</ul>';
                }
                resultDiv.innerHTML = html;
            }
            
            async function findAllUntranscribed() {
                const resultDiv = document.getElementById('untranscribedResult');
                resultDiv.innerHTML = 'Analyzing system...';
                
                const response = await fetch('/api/untranscribed-summary');
                const result = await response.json();
                
                let html = '<h3>System-Wide Untranscribed Summary</h3>';
                html += `<p>Total untranscribed: ${result.total}</p>`;
                html += '<p>Top loans needing transcription:</p>';
                html += '<ul>';
                result.top_loans.forEach(loan => {
                    html += `<li>Loan ${loan.loan_number}: ${loan.count} calls</li>`;
                });
                html += '</ul>';
                resultDiv.innerHTML = html;
            }
            
            async function addMissingCall() {
                const loanNumber = document.getElementById('addLoanNumber').value;
                const orkuid = document.getElementById('addOrkuid').value;
                
                if (!loanNumber || !orkuid) return;
                
                const resultDiv = document.getElementById('addCallResult');
                resultDiv.innerHTML = 'Adding call...';
                
                const response = await fetch('/api/add-call', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        loan_number: loanNumber,
                        orkuid: orkuid
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = '✅ Call added successfully!';
                } else {
                    resultDiv.innerHTML = `❌ Error: ${result.error}`;
                }
            }
            
            // Close modals when clicking outside
            window.onclick = function(event) {
                if (event.target.className === 'modal') {
                    event.target.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/api/generate-brief/{loan_number}")
async def api_generate_brief(loan_number: str):
    """API to generate loan brief"""
    try:
        # Import and run the generate_loan_brief function
        from generate_loan_brief import generate_loan_brief
        
        filename = generate_loan_brief(loan_number)
        
        return JSONResponse({
            "success": True,
            "filename": filename,
            "message": "Brief generated successfully"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/download-brief/{loan_number}")
async def download_brief(loan_number: str):
    """Download generated loan brief"""
    filename = f"LOAN_BRIEF_{loan_number}.txt"
    if os.path.exists(filename):
        return FileResponse(filename, filename=filename)
    else:
        return HTMLResponse("Brief not found", status_code=404)

@app.get("/api/untranscribed/{loan_number}")
async def api_untranscribed_loan(loan_number: str):
    """Find untranscribed calls for a loan"""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        AND (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return JSONResponse({
        "loan_number": loan_number,
        "count": len(calls),
        "calls": [
            {
                "orkuid": c['orkuid'],
                "timestamp": c['timestamp'].strftime('%m/%d/%Y %I:%M %p'),
                "duration": c['duration']
            } for c in calls
        ]
    })

@app.get("/api/untranscribed-summary")
async def api_untranscribed_summary():
    """System-wide untranscribed summary"""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM call_transcripts_v2
        WHERE (transcript_path IS NULL OR transcript_path = '')
        AND (transcript_text IS NULL OR transcript_text = '')
    """)
    total = cursor.fetchone()['count']
    
    # Top loans
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as count
        FROM call_transcripts_v2
        WHERE (transcript_path IS NULL OR transcript_path = '')
        AND (transcript_text IS NULL OR transcript_text = '')
        AND loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY count DESC
        LIMIT 10
    """)
    
    top_loans = []
    for row in cursor.fetchall():
        try:
            loans = json.loads(row['loan_numbers'])
            if loans:
                top_loans.append({
                    "loan_number": loans[0],
                    "count": row['count']
                })
        except:
            pass
    
    cursor.close()
    conn.close()
    
    return JSONResponse({
        "total": total,
        "top_loans": top_loans
    })

@app.post("/api/add-call")
async def api_add_call(data: dict):
    """Add missing call to loan"""
    loan_number = data.get('loan_number')
    orkuid = data.get('orkuid')
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    try:
        # Check if call exists
        cursor.execute("SELECT * FROM orktape WHERE orkUid = %s", (orkuid,))
        if not cursor.fetchone():
            return JSONResponse({"success": False, "error": "Call not found"})
        
        # Check existing assignments
        cursor.execute("SELECT loan_numbers FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
        existing = cursor.fetchone()
        
        current_loans = []
        if existing and existing.get('loan_numbers'):
            current_loans = json.loads(existing['loan_numbers'])
        
        if loan_number not in current_loans:
            current_loans.append(loan_number)
            new_json = json.dumps(current_loans)
            
            if existing:
                cursor.execute("""
                    UPDATE call_transcripts_v2 
                    SET loan_numbers = %s, updated_at = NOW()
                    WHERE orkuid = %s
                """, (new_json, orkuid))
            else:
                cursor.execute("""
                    INSERT INTO call_transcripts_v2 (orkuid, loan_numbers, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (orkuid, new_json))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        cursor.close()
        conn.close()
        return JSONResponse({"success": False, "error": str(e)})

# Add redirects to other apps
@app.get("/timeline")
async def redirect_timeline():
    return HTMLResponse('<meta http-equiv="refresh" content="0; url=http://localhost:8001">')

@app.get("/broker-tracker")
async def redirect_broker():
    return HTMLResponse('<meta http-equiv="refresh" content="0; url=http://localhost:8003">')

@app.get("/analytics")
async def redirect_analytics():
    return HTMLResponse('<meta http-equiv="refresh" content="0; url=http://localhost:8001">')

if __name__ == "__main__":
    print("Starting Loan Command Center...")
    print("Open: http://localhost:8004")
    print("\nAll loan features in one place!")
    uvicorn.run(app, host="0.0.0.0", port=8004)