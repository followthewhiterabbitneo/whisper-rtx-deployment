# 🚀 LOAN TIMELINE - QUICK START GUIDE

## ✅ WORKING SCRIPTS FOR LOAN ANALYSIS

### 1. 📊 VIEW LOAN TIMELINE (Web Interface)
```bash
# Start the APIs (2 terminals needed)
python loan_search_api.py          # Terminal 1 - Port 8000
python loan_timeline_api.py        # Terminal 2 - Port 8001

# Open the viewer
# Open enhanced_loan_viewer.html in browser
# Enter loan number: 1225290972
```

### 2. 🤖 GENERATE LEGAL SUMMARY (AI-Powered)
```bash
# This WORKS perfectly - generates beautiful legal briefs
python llama3_legal_summary_CPU.py "C:\transcripts\2025\06\02\20250602_115752_IPBU.txt"

# Output includes:
# - Executive Summary
# - Key Facts (loan amounts, rates, dates)
# - Parties Involved
# - Main Discussion Points
# - Action Items/Agreements
# - Compliance Notes
```

### 3. 💰 EXTRACT LOAN FACTS (Numbers Only)
```bash
# Extract all numbers, rates, amounts from transcripts
python extract_loan_facts.py 1225290972

# Finds:
# - Loan amounts
# - Interest rates
# - Monthly payments
# - Credit scores
# - Income amounts
# - Important dates
```

### 4. 📝 GENERATE FULL LOAN SUMMARY (All Transcripts)
```bash
# Summarize ALL transcripts for a loan
python generate_legal_loan_summary.py 1225290972

# Creates comprehensive legal brief for entire loan
```

### 5. 🔍 SEARCH FOR LOANS
```bash
# By loan number
curl http://localhost:8000/search?q=1225290972

# By user name
curl http://localhost:8000/search/by-user?user=Krall
```

## 📁 KEY FILES

- **enhanced_loan_viewer.html** - Main web interface
- **llama3_legal_summary_CPU.py** - WORKING legal summary generator
- **loan_timeline_api.py** - Timeline data API (port 8001)
- **loan_search_api.py** - Search API (port 8000)
- **extract_loan_facts.py** - Number extraction tool

## 🎯 EXAMPLE LOAN: 1225290972
- 12 calls total
- Participants: Jonathan Boatright, Raghava Nyapathy, Russell Barratt, Celina Krall
- Use this for testing!

## 📊 QUICK COMMANDS

```bash
# See all transcripts for a loan
python get_loan_transcripts.py 1225290972

# Create batch file to open all transcripts
python open_transcripts.py 1225290972

# Find all AI models on system
python find_all_models.py
```

## ⚡ CURRENT STATUS
- ✅ Legal summaries work PERFECTLY (using CPU at 14-21 tok/s)
- ✅ Timeline viewer shows all calls beautifully
- ✅ Facts extraction finds all numbers
- ⚠️ GPU acceleration not working yet (but CPU is fine for now)

---
**Last Updated:** June 2025
**Working Model:** Llama-3-8B-Instruct at C:/Users/estillmane/models/