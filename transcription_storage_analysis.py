#!/usr/bin/env python3
"""
Cost/Benefit Analysis: Storing Transcriptions in Database vs Filesystem
For SCREAM Pipeline processing 30,000 calls/day
"""

from datetime import datetime

print("=" * 80)
print("TRANSCRIPTION STORAGE ANALYSIS")
print("=" * 80)

# Constants based on real-world data
CALLS_PER_DAY = 30_000
AVG_CALL_DURATION_SECONDS = 180  # 3 minutes average
WORDS_PER_MINUTE_SPEECH = 150
CHARS_PER_WORD = 5.5  # Average English word length + space
SUMMARY_COMPRESSION_RATIO = 0.15  # Summary is ~15% of transcript

# Calculate sizes
avg_words_per_call = (AVG_CALL_DURATION_SECONDS / 60) * WORDS_PER_MINUTE_SPEECH
avg_transcript_size = avg_words_per_call * CHARS_PER_WORD
avg_summary_size = avg_transcript_size * SUMMARY_COMPRESSION_RATIO

print(f"\n📊 BASELINE METRICS")
print(f"─" * 40)
print(f"Calls per day: {CALLS_PER_DAY:,}")
print(f"Average call duration: {AVG_CALL_DURATION_SECONDS} seconds")
print(f"Average transcript size: {avg_transcript_size:,.0f} bytes ({avg_transcript_size/1024:.1f} KB)")
print(f"Average summary size: {avg_summary_size:,.0f} bytes ({avg_summary_size/1024:.1f} KB)")

# Daily storage requirements
daily_transcript_storage = CALLS_PER_DAY * avg_transcript_size
daily_summary_storage = CALLS_PER_DAY * avg_summary_size
daily_total_storage = daily_transcript_storage + daily_summary_storage

print(f"\n📈 DAILY STORAGE REQUIREMENTS")
print(f"─" * 40)
print(f"Transcripts: {daily_transcript_storage/1024/1024:.1f} MB")
print(f"Summaries: {daily_summary_storage/1024/1024:.1f} MB")
print(f"Total: {daily_total_storage/1024/1024:.1f} MB/day")

# Projected growth
print(f"\n📅 STORAGE GROWTH PROJECTIONS")
print(f"─" * 40)
periods = [
    ("1 Week", 7),
    ("1 Month", 30),
    ("3 Months", 90),
    ("6 Months", 180),
    ("1 Year", 365)
]

for period_name, days in periods:
    total_gb = (daily_total_storage * days) / 1024 / 1024 / 1024
    print(f"{period_name}: {total_gb:.1f} GB")

print("\n" + "=" * 80)
print("💾 DATABASE STORAGE (MariaDB)")
print("=" * 80)

print("\n✅ BENEFITS:")
print("""
1. INTEGRATED QUERIES
   - Direct SQL joins with call metadata
   - Fast searches across all transcripts
   - Complex analytics without data movement
   
2. TRANSACTIONAL INTEGRITY
   - ACID compliance ensures data consistency
   - Atomic updates (transcript + summary + metadata)
   - Rollback capability for failed processing
   
3. CENTRALIZED ACCESS
   - Single source of truth
   - No file path management
   - Consistent access permissions
   
4. BUILT-IN FEATURES
   - Full-text search indexes
   - Automatic timestamp tracking
   - Query optimization
   - Backup/restore with database
   
5. OPERATIONAL SIMPLICITY
   - No filesystem permissions issues
   - No orphaned files
   - Easier disaster recovery
""")

print("\n❌ COSTS:")
print(f"""
1. STORAGE OVERHEAD
   - Database adds ~20-30% overhead
   - Indexes add additional space
   - Transaction logs grow
   - Estimated: {(daily_total_storage * 1.25)/1024/1024:.1f} MB/day with overhead
   
2. PERFORMANCE IMPACT
   - Large TEXT/BLOB fields slow queries
   - Backup times increase significantly
   - Database cache pollution
   - Replication lag for large transactions
   
3. MAINTENANCE BURDEN
   - Regular OPTIMIZE TABLE needed
   - Larger backup windows
   - More complex capacity planning
   - Index fragmentation
   
4. SCALABILITY LIMITS
   - Single database becomes bottleneck
   - Difficult to shard text data
   - Memory requirements increase
   - Connection pool pressure
""")

print("\n" + "=" * 80)
print("📁 FILESYSTEM STORAGE")
print("=" * 80)

print("\n✅ BENEFITS:")
print("""
1. PERFORMANCE
   - Direct file I/O is faster
   - No database overhead
   - Parallel read/write operations
   - Can use CDN/object storage
   
2. SCALABILITY
   - Horizontal scaling with NFS/S3
   - Easy to distribute across servers
   - No database size limits
   - Independent scaling from database
   
3. COST EFFICIENCY
   - Cheaper storage options available
   - Can use compression transparently
   - Archive to cold storage
   - No database licensing for storage
   
4. FLEXIBILITY
   - Easy to process with external tools
   - Simple backup/archive strategies
   - Can serve directly via web server
   - Format independence
""")

print("\n❌ COSTS:")
print("""
1. COMPLEXITY
   - File path management required
   - Potential for orphaned files
   - Need filesystem permissions
   - Sync issues between DB and files
   
2. SEARCH LIMITATIONS
   - No built-in full-text search
   - Requires external indexing (Elasticsearch)
   - Slower cross-reference queries
   - Additional infrastructure needed
   
3. CONSISTENCY CHALLENGES
   - No transactional guarantees
   - Manual cleanup of failed operations
   - Race conditions possible
   - Backup coordination complex
""")

print("\n" + "=" * 80)
print("🏆 RECOMMENDED HYBRID APPROACH")
print("=" * 80)

print("""
STORE IN DATABASE:
✓ Summaries (small, frequently queried)
✓ Key extracted data (loan numbers, names, dates)
✓ Searchable metadata
✓ Processing status and timestamps

STORE IN FILESYSTEM:
✓ Full transcripts (large, rarely accessed)
✓ Original audio files
✓ Archived/historical data

IMPLEMENTATION:
""")

print(f"""
1. Database Table Structure:
   ```sql
   CREATE TABLE call_transcripts (
       orkuid VARCHAR(50) PRIMARY KEY,
       summary TEXT,                    -- Store summary in DB
       transcript_path VARCHAR(255),    -- Path to full transcript
       loan_numbers JSON,               -- Extracted data
       key_facts JSON,                  -- Structured data
       created_at TIMESTAMP,
       INDEX idx_loan (loan_numbers),
       FULLTEXT idx_summary (summary)
   );
   ```

2. Filesystem Structure:
   ```
   /transcripts/
   ├── 2025/
   │   ├── 06/
   │   │   ├── 22/
   │   │   │   ├── 20250622_093021_ABCD.txt
   │   │   │   └── 20250622_093021_ABCD.json
   ```

3. Storage Projections (Hybrid):
   - Database: {(daily_summary_storage * 1.3)/1024/1024:.1f} MB/day (summaries + metadata)
   - Filesystem: {daily_transcript_storage/1024/1024:.1f} MB/day (transcripts)
   - Total: {daily_total_storage/1024/1024:.1f} MB/day
   
4. Query Example:
   ```sql
   -- Fast search in summaries
   SELECT t.*, r.filename, r.duration
   FROM call_transcripts t
   JOIN orktape r ON t.orkuid = r.uid
   WHERE MATCH(summary) AGAINST ('loan approval' IN BOOLEAN MODE)
   AND JSON_CONTAINS(loan_numbers, '"123456789"');
   ```
""")

print("\n" + "=" * 80)
print("💡 DECISION MATRIX")
print("=" * 80)

print("""
Factor              | Database | Filesystem | Hybrid
--------------------|----------|------------|--------
Query Performance   |    ⭐⭐⭐    |     ⭐      |   ⭐⭐⭐
Storage Cost        |     ⭐     |    ⭐⭐⭐     |   ⭐⭐⭐
Scalability         |     ⭐⭐    |    ⭐⭐⭐     |   ⭐⭐⭐
Maintenance         |     ⭐⭐    |     ⭐⭐     |   ⭐⭐
Search Capability   |    ⭐⭐⭐    |     ⭐      |   ⭐⭐⭐
Disaster Recovery   |    ⭐⭐⭐    |     ⭐⭐     |   ⭐⭐
Implementation      |    ⭐⭐⭐    |     ⭐⭐     |   ⭐⭐

RECOMMENDATION: Hybrid Approach
- Best of both worlds
- Optimizes for common queries
- Scales efficiently
- Manageable complexity
""")

# Save analysis
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
analysis_file = f"transcription_storage_analysis_{timestamp}.txt"

with open(analysis_file, 'w', encoding='utf-8') as f:
    f.write("TRANSCRIPTION STORAGE COST/BENEFIT ANALYSIS\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Generated: {datetime.now()}\n")
    f.write(f"Calls per day: {CALLS_PER_DAY:,}\n")
    f.write(f"Daily storage requirement: {daily_total_storage/1024/1024:.1f} MB\n")
    f.write(f"Yearly storage requirement: {(daily_total_storage*365)/1024/1024/1024:.1f} GB\n\n")
    f.write("RECOMMENDATION: Hybrid Approach\n")
    f.write("- Store summaries and metadata in database\n")
    f.write("- Store full transcripts in filesystem\n")
    f.write("- Link via transcript_path field\n")

print(f"\n✅ Analysis saved to: {analysis_file}")
print("=" * 80)