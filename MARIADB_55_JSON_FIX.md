# MariaDB 5.5 JSON Compatibility Fix

## Problem
MariaDB 5.5.68 doesn't support the JSON data type, which was introduced in MariaDB 10.2. The error you're seeing:

```
pymysql.err.ProgrammingError: (1064, "You have an error in your SQL syntax... near 'JSON COMMENT 'Array of loan numbers found'")
```

## Solution
Use TEXT fields to store JSON data as strings, then handle JSON parsing/serialization in Python.

## Fixed Schema Differences

### Original (MariaDB 10.2+):
```sql
loan_numbers JSON COMMENT 'Array of loan numbers found',
key_facts JSON COMMENT 'Structured key facts extracted',
```

### Fixed (MariaDB 5.5):
```sql
loan_numbers TEXT COMMENT 'JSON array of loan numbers as text',
key_facts TEXT COMMENT 'JSON structured key facts as text',
```

## Usage Examples

### Inserting Data:
```python
import json

# Convert Python objects to JSON strings before inserting
loan_numbers = json.dumps(["123456789", "987654321"])
key_facts = json.dumps({
    "caller": "John Doe",
    "topic": "Payment inquiry",
    "resolution": "Provided payment history"
})

cursor.execute("""
    INSERT INTO call_transcripts_v2 
    (orkuid, loan_numbers, key_facts, ...) 
    VALUES (%s, %s, %s, ...)
""", (orkuid, loan_numbers, key_facts, ...))
```

### Querying Data:
```python
# Search for loan numbers using LIKE
loan_to_find = "123456789"
cursor.execute("""
    SELECT orkuid, loan_numbers 
    FROM call_transcripts_v2 
    WHERE loan_numbers LIKE %s
""", ('%"' + loan_to_find + '"%',))

# Extract and parse JSON data
cursor.execute("SELECT key_facts FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
row = cursor.fetchone()
if row and row[0]:
    key_facts_dict = json.loads(row[0])
    caller = key_facts_dict.get('caller')
```

## Running the Fixed Script

1. **Copy the fixed script to RTX workstation:**
   ```bash
   # On WSL2:
   git add create_hybrid_schema_mariadb55.py
   git commit -m "Add MariaDB 5.5 compatible schema"
   git push
   ```

2. **On RTX workstation (PowerShell):**
   ```powershell
   cd C:\Users\estillmane\.aria\whisper-rtx-deployment
   git pull
   python .\create_hybrid_schema_mariadb55.py
   ```

## Key Differences from JSON Type

1. **No JSON validation** - The database won't validate JSON syntax
2. **No JSON functions** - Can't use JSON_EXTRACT, JSON_CONTAINS, etc.
3. **Use LIKE for searches** - Instead of JSON_CONTAINS
4. **Manual parsing** - Must use json.loads() in Python

## Performance Considerations

- Full-text search on summary field still works efficiently
- LIKE queries on JSON text are less efficient than native JSON
- Consider adding specific indexed columns for frequently searched values

## Migration Path

When you eventually upgrade to MariaDB 10.2+:
1. Add proper JSON columns
2. Migrate data: `UPDATE table SET new_json_col = CAST(old_text_col AS JSON)`
3. Drop old TEXT columns
4. Use native JSON functions for better performance