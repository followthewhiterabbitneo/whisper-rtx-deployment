# MariaDB 5.5 JSON Compatibility Fix

## Problem
MariaDB 5.5.68 doesn't support the `JSON` data type (introduced in MariaDB 10.2).

## Solution
Use `TEXT` fields to store JSON data and handle serialization in Python.

## Key Changes

### Table Definition
```sql
-- WRONG (MariaDB 10.2+)
loan_numbers JSON,
key_facts JSON,

-- CORRECT (MariaDB 5.5)
loan_numbers TEXT COMMENT 'JSON array of loan numbers found',
key_facts TEXT COMMENT 'JSON structured key facts extracted',
```

### Inserting Data
```python
import json

# Prepare data
loan_numbers = ["123456789", "987654321"]
key_facts = {"caller": "Eric Rawlins", "topic": "Payment deferral"}

# Insert with json.dumps()
cursor.execute("""
    INSERT INTO call_transcripts_v2 
    (orkuid, loan_numbers, key_facts)
    VALUES (%s, %s, %s)
""", (orkuid, json.dumps(loan_numbers), json.dumps(key_facts)))
```

### Retrieving Data
```python
# Query
cursor.execute("SELECT loan_numbers, key_facts FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
row = cursor.fetchone()

# Parse JSON from TEXT
loan_numbers = json.loads(row[0])
key_facts = json.loads(row[1])
```

### Searching JSON Data
```sql
-- Search for loan number (use LIKE with JSON syntax)
SELECT * FROM call_transcripts_v2 
WHERE loan_numbers LIKE '%"123456789"%';

-- Search in key facts
SELECT * FROM call_transcripts_v2 
WHERE key_facts LIKE '%"topic": "Payment%';
```

## Files Updated
1. `create_hybrid_schema_mariadb55.py` - MariaDB 5.5 compatible schema
2. Pipeline scripts will use `json.dumps()` and `json.loads()`

## Run on RTX
```bash
git pull
python create_hybrid_schema_mariadb55.py
```