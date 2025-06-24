# Bootstrap Loan Analysis Project

## Quick Start (Fresh Machine)

```bash
# 1. Clone repo
git clone git@github.com:followthewhiterabbitneo/whisper-rtx-deployment.git
cd whisper-rtx-deployment

# 2. Run bootstrap
python bootstrap_loan_project.py

# 3. Start analysis
python get_all_loan_ids.py
```

## Manual Bootstrap Steps

### 1. Environment Setup
```bash
# Install Python 3.8+
python --version

# Install dependencies
pip install pymysql requests fastapi uvicorn
```

### 2. Clone Repository
```bash
git clone git@github.com:followthewhiterabbitneo/whisper-rtx-deployment.git
cd whisper-rtx-deployment
```

### 3. Database Configuration
```python
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}
```

### 4. Core Scripts Workflow

```bash
# Step 1: Get all loan IDs
python get_all_loan_ids.py
# Output: all_loan_ids.txt

# Step 2: Find loan networks
python smart_loan_network_finder.py
# Output: loan officer networks

# Step 3: Generate visualizations
python visualize_loan_network.py
# Output: HTML visualization files

# Step 4: Process specific loans
python test_one_loan_first_principles.py
```

## Project Structure
```
whisper-rtx-deployment/
├── get_all_loan_ids.py         # Extract loan IDs
├── smart_loan_network_finder.py # Find networks
├── visualize_loan_network.py   # Create visuals
├── loan_search_api.py          # Search API
├── all_loan_ids.txt            # Generated loan list
└── visualizations/             # HTML outputs
```

## Key Concepts
- **Loan ID**: 8-digit identifier (e.g., 1225381964)
- **Network**: All calls between loan officer and customer
- **Timeline**: Chronological sequence of calls
- **CTC**: Clear to Close - loan approval status

## Troubleshooting

### Can't connect to database
- Check VPN/network connection to s40vpsoxweb002
- Verify credentials in DB_CONFIG

### Missing dependencies
```bash
pip install -r requirements.txt
```

### Git issues
```bash
git pull --rebase
git push
```

## Next Features
- [ ] Thumbs down feedback for incorrect associations
- [ ] Loan number correction
- [ ] Batch visualization generation
- [ ] Export to GSE format