# RTX 4090 Deployment Guide - Loan Search System

## Overview
This guide covers deploying the complete loan search system on your RTX 4090 workstation. The system processes recordings for Eric Rawlins, Celina Fischer, and Negin Rahimifar, extracting loan numbers and creating a searchable database.

## Prerequisites
- RTX 4090 with Whisper large-v3-turbo model installed
- Python environment with required packages
- SSH access to s40vpsoxweb002
- Database access to MariaDB on s40vpsoxweb002

## Step 1: Update Code on RTX 4090

```bash
# On RTX 4090, pull latest changes
cd C:\Users\estillmane\.aria\whisper-rtx-deployment
git pull
```

## Step 2: Install API Dependencies

```bash
# Install FastAPI and dependencies for the loan search API
pip install -r requirements_api.txt
```

If requirements_api.txt is missing, install manually:
```bash
pip install fastapi==0.104.1 uvicorn==0.24.0 pymysql==1.1.0 pydantic==2.5.0
```

## Step 3: Process Recordings for Three Users

Run the batch processing script to transcribe and index all recordings:

```bash
python process_three_users_june.py
```

This script will:
1. Find all recordings for Eric Rawlins, Celina Fischer, and Negin Rahimifar
2. Date range: June 1-20, 2025
3. Transcribe each recording using Whisper
4. Generate legal brief summaries using Gemma
5. Extract loan numbers and populate the search index
6. Store results in hybrid database/filesystem storage

Expected output:
```
Processing recordings for 3 users (June 1-20, 2025)...
Found 45 recordings for Eric Rawlins
Found 38 recordings for Celina Fischer  
Found 42 recordings for Negin Rahimifar
Total: 125 recordings to process

Processing 1/125: Eric Rawlins - 20250601_093422_ABCD.wav
  ✓ Transcribed (duration: 3m 42s, speed: 18.5x)
  ✓ Summary generated
  ✓ Found loan numbers: ['12345678']
  ✓ Saved to database
  ✓ Loan index updated
...
```

## Step 4: Start the Loan Search API

Once processing is complete, start the FastAPI server:

```bash
# Terminal 1: Start loan search API
python loan_search_api.py
```

This starts the API on http://localhost:8000 with endpoints:
- `/search/loan/{loan_number}` - Search by loan number
- `/search/user/{user_name}` - Get user loan summary
- `/users/summary` - List all users with loans
- `/analytics` - Get loan analytics

## Step 5: Start the Loan Timeline API

In a second terminal:

```bash
# Terminal 2: Start timeline API  
python loan_timeline_api.py
```

This starts the timeline API on http://localhost:8001 with endpoints:
- `/timeline/{loan_number}` - Get complete timeline
- `/insights/{loan_number}` - Get AI-powered insights
- `/timeline/{loan_number}/export` - Export timeline data

## Step 6: Test the APIs

Test loan search:
```bash
# Example: Search for Eric's loan
curl http://localhost:8000/search/loan/12345678

# Get user summary
curl http://localhost:8000/search/user/Eric%20Rawlins

# Get analytics
curl http://localhost:8000/analytics
```

Test timeline:
```bash
# Get timeline for a loan
curl http://localhost:8001/timeline/12345678

# Get insights
curl http://localhost:8001/insights/12345678
```

## Step 7: Connect React Frontend

On s01vpsromuls001 (or your React development machine):

1. Update your React app's environment variables:
```env
VITE_API_URL=http://your-rtx-ip:8000
VITE_TIMELINE_API_URL=http://your-rtx-ip:8001
```

2. Use the provided React components:
- `LoanSearch.tsx` - Basic loan search
- `LoanTimelineView.tsx` - Timeline visualization

3. Install required packages:
```bash
npm install axios date-fns
```

## Expected Loan Numbers

Based on the user's message, each person has ONE loan number:
- Eric Rawlins: One loan number
- Celina Fischer: One loan number  
- Negin Rahimifar: One loan number

The system will automatically:
- Find all occurrences of each loan number
- Create timelines showing all calls about each loan
- Generate aggregated summaries across all calls
- Extract key milestones and insights

## Monitoring Progress

While processing runs, you can monitor:
- Processing logs in the terminal
- Database tables being populated
- Transcript files being created in `transcriptions/`

## Troubleshooting

1. **SSH Connection Issues**
   - Ensure passwordless SSH is configured
   - Test with: `python test_ssh_connection.py`

2. **Database Connection Issues**
   - Verify MariaDB is accessible
   - Check credentials: root/admin

3. **Memory Issues**
   - The RTX 4090 has 24GB VRAM
   - Both Whisper and Gemma models should fit comfortably
   - Monitor GPU usage with `nvidia-smi`

4. **API CORS Issues**
   - APIs are configured to accept connections from any origin
   - If issues persist, check Windows Firewall settings

## Next Steps

After successful deployment:
1. Access the loan search from your React app
2. Search for any loan number to see the complete timeline
3. View AI-powered insights and risk indicators
4. Export data for reporting

The system provides:
- ⚡ Fast loan number search (indexed)
- 📊 Complete call timelines
- 🤖 AI-generated summaries and insights
- 📈 Sentiment analysis trends
- 🎯 Key milestone extraction
- 📋 Action item generation

## Support

If you encounter issues:
1. Check the logs in each terminal
2. Verify all dependencies are installed
3. Ensure database schema is up to date
4. Test individual components separately