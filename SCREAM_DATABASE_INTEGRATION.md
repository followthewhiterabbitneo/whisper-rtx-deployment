# SCREAM Database Integration Guide

## MariaDB Connection Details

### Server Information
- **Host**: s40vpsoxweb002
- **Port**: 3306 (default)
- **Database**: oreka
- **Version**: MariaDB 5.5.68
- **Current Access**: root/admin (to be replaced with readonly user)

## Database Schema Analysis

### Core Tables for Call Recording System

```sql
-- 1. orkuser: Underwriter information
CREATE TABLE orkuser (
    orkuser_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),           -- Underwriter full name
    extension VARCHAR(20),       -- Phone extension
    email VARCHAR(255),         -- Email address
    department VARCHAR(100),    -- Department/team
    active BOOLEAN DEFAULT 1,   -- Active status
    created_date TIMESTAMP
);

-- 2. orksegment: Call recording metadata
CREATE TABLE orksegment (
    segment_id INT PRIMARY KEY AUTO_INCREMENT,
    orkuid VARCHAR(50) UNIQUE,   -- Matches filename suffix
    orkuser_id INT,             -- Foreign key to orkuser
    timestamp TIMESTAMP,         -- Call start time
    duration INT,               -- Duration in seconds
    localparty VARCHAR(50),     -- Underwriter phone
    remoteparty VARCHAR(50),    -- Broker/LO phone
    direction VARCHAR(10),      -- 'inbound' or 'outbound'
    FOREIGN KEY (orkuser_id) REFERENCES orkuser(orkuser_id)
);

-- 3. orktape: Recording file information
CREATE TABLE orktape (
    tape_id INT PRIMARY KEY AUTO_INCREMENT,
    orkuid VARCHAR(50),         -- Links to orksegment
    filename VARCHAR(500),      -- Full file path
    filesize BIGINT,           -- Size in bytes
    compression VARCHAR(20),    -- Audio format
    archived BOOLEAN DEFAULT 0,
    FOREIGN KEY (orkuid) REFERENCES orksegment(orkuid)
);

-- 4. orkmetadata: Additional call metadata
CREATE TABLE orkmetadata (
    metadata_id INT PRIMARY KEY AUTO_INCREMENT,
    orkuid VARCHAR(50),
    key_name VARCHAR(100),     -- Metadata key
    key_value TEXT,           -- Metadata value
    FOREIGN KEY (orkuid) REFERENCES orksegment(orkuid)
);

-- 5. orktag: Call tags/categories
CREATE TABLE orktag (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    orkuid VARCHAR(50),
    tagtype_id INT,
    tag_value VARCHAR(255),
    created_by INT,
    created_date TIMESTAMP,
    FOREIGN KEY (orkuid) REFERENCES orksegment(orkuid),
    FOREIGN KEY (tagtype_id) REFERENCES orktagtype(tagtype_id)
);

-- 6. orktagtype: Tag definitions
CREATE TABLE orktagtype (
    tagtype_id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(100),     -- e.g., 'escalation', 'complaint'
    tag_description TEXT,
    active BOOLEAN DEFAULT 1
);

-- 7. orkgroup: User groups/teams
CREATE TABLE orkgroup (
    group_id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(100),   -- e.g., 'Senior Underwriters'
    group_type VARCHAR(50),
    manager_id INT,
    FOREIGN KEY (manager_id) REFERENCES orkuser(orkuser_id)
);

-- 8. orkgrouptouser: User-group relationships
CREATE TABLE orkgrouptouser (
    group_id INT,
    orkuser_id INT,
    role VARCHAR(50),         -- 'member', 'lead', etc.
    joined_date TIMESTAMP,
    PRIMARY KEY (group_id, orkuser_id),
    FOREIGN KEY (group_id) REFERENCES orkgroup(group_id),
    FOREIGN KEY (orkuser_id) REFERENCES orkuser(orkuser_id)
);
```

## Essential Queries for SCREAM

### 1. Find Calls to Process (≥2 minutes, last 24 hours)
```sql
SELECT 
    s.orkuid,
    s.timestamp,
    s.duration,
    s.localparty,
    s.remoteparty,
    u.name as underwriter_name,
    u.extension,
    t.filename
FROM orksegment s
INNER JOIN orkuser u ON s.orkuser_id = u.orkuser_id
INNER JOIN orktape t ON s.orkuid = t.orkuid
WHERE s.duration >= 120  -- 2 minutes or more
    AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND t.filename IS NOT NULL
ORDER BY s.timestamp DESC;
```

### 2. Get Call Details by orkuid
```sql
SELECT 
    s.*,
    u.name as underwriter_name,
    u.email as underwriter_email,
    t.filename,
    t.filesize,
    GROUP_CONCAT(
        CONCAT(m.key_name, ':', m.key_value) 
        SEPARATOR '; '
    ) as metadata
FROM orksegment s
INNER JOIN orkuser u ON s.orkuser_id = u.orkuser_id
INNER JOIN orktape t ON s.orkuid = t.orkuid
LEFT JOIN orkmetadata m ON s.orkuid = m.orkuid
WHERE s.orkuid = ?
GROUP BY s.orkuid;
```

### 3. Check if Call Already Processed
```sql
-- Add a processing status table for SCREAM
CREATE TABLE scream_processing (
    processing_id INT PRIMARY KEY AUTO_INCREMENT,
    orkuid VARCHAR(50) UNIQUE,
    status VARCHAR(20),        -- 'pending', 'processing', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    transcript_path VARCHAR(500),
    summary_path VARCHAR(500),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    FOREIGN KEY (orkuid) REFERENCES orksegment(orkuid)
);

-- Query to find unprocessed calls
SELECT s.* FROM orksegment s
LEFT JOIN scream_processing p ON s.orkuid = p.orkuid
WHERE p.orkuid IS NULL 
    OR p.status IN ('failed', 'pending')
    AND p.retry_count < 3;
```

### 4. Get Underwriter Call Volume
```sql
SELECT 
    u.name,
    u.extension,
    COUNT(*) as total_calls,
    SUM(s.duration) as total_seconds,
    AVG(s.duration) as avg_duration,
    DATE(s.timestamp) as call_date
FROM orksegment s
INNER JOIN orkuser u ON s.orkuser_id = u.orkuser_id
WHERE s.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY u.orkuser_id, DATE(s.timestamp)
ORDER BY call_date DESC, total_calls DESC;
```

### 5. Find Calls by Phone Number
```sql
-- Find all calls with a specific broker
SELECT 
    s.*,
    u.name as underwriter_name,
    t.filename
FROM orksegment s
INNER JOIN orkuser u ON s.orkuser_id = u.orkuser_id
INNER JOIN orktape t ON s.orkuid = t.orkuid
WHERE s.remoteparty = ? -- broker phone number
    OR s.remoteparty LIKE CONCAT('%', ?, '%')
ORDER BY s.timestamp DESC
LIMIT 100;
```

## Database User Setup

### Create Read-Only User for SCREAM
```sql
-- Create the user
CREATE USER 'scream_reader'@'%' IDENTIFIED BY 'secure_password_here';

-- Grant read permissions on oreka database
GRANT SELECT ON oreka.* TO 'scream_reader'@'%';

-- Grant write permissions only to scream_processing table
GRANT INSERT, UPDATE ON oreka.scream_processing TO 'scream_reader'@'%';

-- Apply permissions
FLUSH PRIVILEGES;

-- Verify permissions
SHOW GRANTS FOR 'scream_reader'@'%';
```

## Python Database Connection

### Using PyMySQL
```python
import pymysql
from contextlib import contextmanager

class OrekaDatabase:
    def __init__(self, host, user, password, database):
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    @contextmanager
    def get_connection(self):
        connection = pymysql.connect(**self.connection_params)
        try:
            yield connection
        finally:
            connection.close()
    
    def get_calls_to_process(self, hours=24, min_duration=120):
        """Get calls that need processing"""
        query = """
        SELECT 
            s.orkuid,
            s.timestamp,
            s.duration,
            s.localparty,
            s.remoteparty,
            u.name as underwriter_name,
            u.extension,
            t.filename
        FROM orksegment s
        INNER JOIN orkuser u ON s.orkuser_id = u.orkuser_id
        INNER JOIN orktape t ON s.orkuid = t.orkuid
        LEFT JOIN scream_processing p ON s.orkuid = p.orkuid
        WHERE s.duration >= %s
            AND s.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            AND (p.orkuid IS NULL OR p.status = 'failed')
        ORDER BY s.timestamp DESC
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (min_duration, hours))
                return cursor.fetchall()
    
    def mark_processing_started(self, orkuid):
        """Mark a call as being processed"""
        query = """
        INSERT INTO scream_processing (orkuid, status, started_at)
        VALUES (%s, 'processing', NOW())
        ON DUPLICATE KEY UPDATE 
            status = 'processing',
            started_at = NOW(),
            retry_count = retry_count + 1
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (orkuid,))
                conn.commit()
    
    def mark_processing_completed(self, orkuid, transcript_path, summary_path):
        """Mark a call as successfully processed"""
        query = """
        UPDATE scream_processing 
        SET status = 'completed',
            completed_at = NOW(),
            transcript_path = %s,
            summary_path = %s
        WHERE orkuid = %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (transcript_path, summary_path, orkuid))
                conn.commit()
```

## File Path Resolution

### Converting Database Path to NFS Path
```python
def resolve_recording_path(db_filename, nfs_mount="/var/log/orkaudio.nfs.prod"):
    """
    Convert database filename to actual NFS path
    
    Database might store: /audio/2025/01/21/14/20250121_141523_7823.wav
    NFS mount path: /var/log/orkaudio.nfs.prod/audio/2025/01/21/14/20250121_141523_7823.wav
    """
    # Remove leading slash if present
    if db_filename.startswith('/'):
        db_filename = db_filename[1:]
    
    # Construct full path
    full_path = os.path.join(nfs_mount, db_filename)
    
    # Verify file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Recording not found: {full_path}")
    
    return full_path
```

## Performance Considerations

### Indexing Strategy
```sql
-- Ensure these indexes exist for query performance
CREATE INDEX idx_segment_timestamp ON orksegment(timestamp);
CREATE INDEX idx_segment_duration ON orksegment(duration);
CREATE INDEX idx_segment_orkuser ON orksegment(orkuser_id);
CREATE INDEX idx_tape_orkuid ON orktape(orkuid);
CREATE INDEX idx_metadata_orkuid ON orkmetadata(orkuid);
CREATE INDEX idx_processing_status ON scream_processing(status);
```

### Connection Pooling
```python
from dbutils.pooled_db import PooledDB

# Create connection pool
pool = PooledDB(
    creator=pymysql,
    maxconnections=6,
    mincached=2,
    maxcached=5,
    blocking=True,
    host='s40vpsoxweb002',
    user='scream_reader',
    password='secure_password',
    database='oreka',
    charset='utf8mb4'
)

# Use connection from pool
connection = pool.connection()
```

## Monitoring Queries

### Processing Statistics
```sql
-- Daily processing summary
SELECT 
    DATE(started_at) as process_date,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as in_progress,
    AVG(TIMESTAMPDIFF(SECOND, started_at, completed_at)) as avg_process_time
FROM scream_processing
WHERE started_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(started_at)
ORDER BY process_date DESC;

-- Backlog check
SELECT 
    COUNT(*) as backlog_count,
    MIN(timestamp) as oldest_call
FROM orksegment s
LEFT JOIN scream_processing p ON s.orkuid = p.orkuid
WHERE s.duration >= 120
    AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND (p.orkuid IS NULL OR p.status != 'completed');
```

## Error Handling

### Common Database Errors
1. **Connection timeout**: Implement retry logic
2. **Lock wait timeout**: Use shorter transactions
3. **Max connections**: Use connection pooling
4. **Character encoding**: Ensure UTF-8 throughout

### Retry Logic Example
```python
import time
from functools import wraps

def retry_on_db_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except pymysql.Error as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

@retry_on_db_error()
def get_call_details(orkuid):
    # Database query here
    pass
```

---

*This guide provides the foundation for integrating SCREAM with the Oreka call recording database.*