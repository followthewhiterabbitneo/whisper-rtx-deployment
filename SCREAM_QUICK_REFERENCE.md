# SCREAM Quick Reference Guide

## System Overview

**SCREAM** = Speech Conversion & Recognition Engine for Audio Management

### Purpose
Protect underwriters by creating legal-brief style summaries of all calls with brokers/loan officers

### Scale
- 2,745 underwriters
- 30,000 calls/day
- 2-minute minimum call duration
- 30-day retention

## Infrastructure

| Component | Details |
|-----------|---------|
| **Database** | s40vpsoxweb002:3306/oreka (MariaDB 5.5.68) |
| **NFS Mount** | /var/log/orkaudio.nfs.prod/ |
| **Processing** | RTX Workstation (CUDA/Whisper) |
| **Frontend** | s01vpsromuls001 (RHEL8/Preact/Vite) |

## Key Files & Paths

### Audio Files
```
/var/log/orkaudio.nfs.prod/audio/YYYY/MM/DD/HH/YYYYMMDD_HHMMSS_XXXX.wav
```

### Summary Storage
```
/summaries/YYYY/MM/DD/orkuid_summary.json
/summaries/YYYY/MM/DD/orkuid_transcript.txt
```

## Database Tables

- **orkuser** - Underwriter information
- **orksegment** - Call metadata
- **orktape** - File locations
- **scream_processing** - Processing status

## Quick Commands

### Check Backlog
```bash
python scream.py status --backlog
```

### Process Specific Call
```bash
python scream.py transcribe --orkuid 20250121_141523_7823
```

### Run Batch Processing
```bash
python scream.py run --batch --hours 24
```

### Monitor Real-time
```bash
python scream_watch.py --monitor
```

## Summary Format

```
LOAN #: [Extracted from transcript]
PARTICIPANTS: Underwriter & Broker
KEY FACTS: Dollar amounts, rates, dates
INSTRUCTIONS: What underwriter told broker
NEXT ACTIONS: Follow-up items
SENTIMENT: 🟢 Positive / 🟡 Neutral / 🔴 Negative
```

## API Endpoints

```
GET /api/summaries/search?loan=123456789
GET /api/summaries/{orkuid}
GET /api/summaries/underwriter/{id}/recent
```

## Troubleshooting

### Common Issues

1. **Cannot access NFS mount**
   ```bash
   sudo mount -t nfs -o ro s40vpsoxweb002:/var/log/orkaudio.nfs.prod /mnt/orkaudio
   ```

2. **Database connection failed**
   - Check firewall rules
   - Verify credentials
   - Test with: `mysql -h s40vpsoxweb002 -u scream_reader -p oreka`

3. **GPU out of memory**
   - Reduce batch size in config
   - Check with: `nvidia-smi`

4. **Summary not generated**
   - Check if loan number in transcript
   - Verify call duration ≥ 2 minutes
   - Check error logs

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Calls/hour | 1,250 | - |
| Processing time | <30s/call | - |
| Accuracy | 95%+ | - |
| Uptime | 99.5% | - |

## Support Contacts

- **System Issues**: [TBD]
- **Database**: [TBD]
- **Business Owner**: [TBD]

---

*For detailed documentation, see SCREAM_ENTERPRISE_INTEGRATION.md*