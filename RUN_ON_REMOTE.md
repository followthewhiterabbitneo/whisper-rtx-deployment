# Run Loan Search Test on Remote Server

Since we can't connect to the corporate database from local WSL2, these scripts need to be run on the remote server (s01vpsromuls001 or directly on s40vpsoxweb002).

## Steps to Run:

1. **Push to GitHub from local:**
```bash
git add test_loan_search_first_principles.py find_loan_numbers_in_db.py RUN_ON_REMOTE.md
git commit -m "Add loan search test scripts"
git push
```

2. **On remote server (s01vpsromuls001):**
```bash
cd /moneyball/whisper-rtx-deployment
git pull
python3 test_loan_search_first_principles.py
```

Or if you have direct access to s40vpsoxweb002:
```bash
python3 test_loan_search_first_principles.py
```

## What the test does:
1. Finds recent loan numbers from the database
2. Tests searching for each loan number
3. Shows all calls related to each loan
4. Tests loan officer network identification
5. Shows relevance rates (how many calls actually have loans)

## Expected Output:
- List of calls for each loan number
- Call details (date, duration, parties)
- Whether transcripts are available
- Loan officer statistics
- Network relevance rates

This is a "first principles" test - it uses direct SQL queries to understand the data structure before building more complex features.