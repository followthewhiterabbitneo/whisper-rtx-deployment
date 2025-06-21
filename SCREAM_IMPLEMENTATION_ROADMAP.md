# SCREAM Implementation Roadmap

## Project Timeline: 10 Weeks

### Week 1-2: Infrastructure Setup & Access

#### Objectives
- Establish connectivity between systems
- Set up development environment
- Verify access permissions

#### Tasks
- [ ] Create read-only database user on s40vpsoxweb002
  ```sql
  CREATE USER 'scream_reader'@'rtx_workstation_ip' IDENTIFIED BY 'secure_password';
  GRANT SELECT ON oreka.* TO 'scream_reader'@'rtx_workstation_ip';
  ```
- [ ] Mount NFS share on RTX workstation (read-only)
  ```bash
  sudo mount -t nfs -o ro s40vpsoxweb002:/var/log/orkaudio.nfs.prod /mnt/orkaudio
  ```
- [ ] Test database connectivity from RTX
- [ ] Verify file access on NFS mount
- [ ] Create scream_processing table in oreka database
- [ ] Document network firewall requirements

#### Deliverables
- Network connectivity confirmed
- Database access verified
- NFS mount operational
- Access documentation complete

### Week 3-4: MariaDB Source Connector

#### Objectives
- Create database integration for SCREAM
- Implement call filtering logic
- Set up processing queue

#### Tasks
- [ ] Create `scream_mariadb_source.py`
- [ ] Implement query for calls ≥2 minutes
- [ ] Add processing status tracking
- [ ] Create batch processing scheduler
- [ ] Implement error handling and retry logic
- [ ] Test with production data

#### Code Structure
```python
# scream_mariadb_source.py
class MariaDBSource(Source):
    def __init__(self, config):
        self.db = OrekaDatabase(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
    
    def discover(self):
        calls = self.db.get_calls_to_process()
        for call in calls:
            audio_path = resolve_recording_path(call['filename'])
            yield AudioFile(
                path=audio_path,
                metadata={
                    'orkuid': call['orkuid'],
                    'underwriter': call['underwriter_name'],
                    'duration': call['duration']
                }
            )
```

#### Deliverables
- MariaDB source connector complete
- Batch processing tested
- Performance benchmarks documented

### Week 5-6: Enhanced Transcription & Summary

#### Objectives
- Implement loan number extraction
- Create legal-brief summary format
- Add speaker diarization

#### Tasks
- [ ] Create `scream_legal_summary.py`
- [ ] Implement regex patterns for loan numbers
- [ ] Add speaker separation logic
- [ ] Create summary template engine
- [ ] Implement fact extraction (amounts, dates, names)
- [ ] Test with real call recordings

#### Key Components
```python
# Loan number patterns
LOAN_PATTERNS = [
    r'loan\s*number\s*[:\s]*(\d{9,12})',
    r'loan\s*[:\s]*(\d{9,12})',
    r'application\s*number\s*[:\s]*(\d{9,12})'
]

# Key fact patterns
DOLLAR_AMOUNT = r'\$[\d,]+(?:\.\d{2})?'
INTEREST_RATE = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
DATE_PATTERN = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
```

#### Deliverables
- Legal summary generator complete
- Loan number extraction tested (95%+ accuracy)
- Speaker separation implemented

### Week 7-8: Sentiment Analysis & Storage

#### Objectives
- Implement sentiment analysis
- Create structured storage system
- Build search capabilities

#### Tasks
- [ ] Integrate sentiment analysis model
- [ ] Create sentiment scoring system (🟢🟡🔴)
- [ ] Design JSON storage schema
- [ ] Implement file-based storage with indexing
- [ ] Create search functionality
- [ ] Add data retention policies

#### Storage Structure
```
/summaries/
├── 2025/
│   ├── 01/
│   │   ├── 21/
│   │   │   ├── 20250121_141523_7823_summary.json
│   │   │   ├── 20250121_141523_7823_transcript.txt
│   │   │   └── daily_index.json
│   │   └── monthly_index.json
│   └── yearly_index.json
└── master_index.db (SQLite for fast searching)
```

#### Deliverables
- Sentiment analysis integrated
- Storage system operational
- Search functionality tested

### Week 9-10: Frontend Integration & Testing

#### Objectives
- Create API for frontend access
- Implement security measures
- Complete end-to-end testing

#### Tasks
- [ ] Create REST API endpoints
- [ ] Implement authentication
- [ ] Add CORS configuration for s01vpsromuls001
- [ ] Create API documentation
- [ ] Perform load testing (30k calls/day)
- [ ] Create monitoring dashboards

#### API Endpoints
```
GET  /api/summaries/search?loan={loan_number}
GET  /api/summaries/{orkuid}
GET  /api/summaries/date/{date}
GET  /api/summaries/underwriter/{id}
GET  /api/stats/sentiment
POST /api/summaries/reprocess/{orkuid}
```

#### Deliverables
- API fully functional
- Frontend integration complete
- System ready for production

## Parallel Tracks

### Documentation Track (Ongoing)
- [ ] Create user guide for underwriters
- [ ] Document API for frontend developers
- [ ] Create operations runbook
- [ ] Build troubleshooting guide

### Security Track (Weeks 5-10)
- [ ] Implement audit logging
- [ ] Set up access controls
- [ ] Configure data encryption
- [ ] Create security assessment report

### Performance Track (Weeks 7-10)
- [ ] Optimize transcription pipeline
- [ ] Implement caching strategies
- [ ] Set up monitoring tools
- [ ] Create performance dashboards

## Risk Mitigation

### Technical Risks
1. **NFS Performance**
   - Mitigation: Local caching of active files
   - Fallback: Direct file transfer if needed

2. **Database Load**
   - Mitigation: Read-only replica if available
   - Fallback: Batch queries during off-hours

3. **GPU Memory**
   - Mitigation: Process in smaller batches
   - Fallback: CPU processing for overflow

### Business Risks
1. **User Adoption**
   - Mitigation: Pilot with friendly users
   - Training: Create video tutorials

2. **Data Quality**
   - Mitigation: Manual review of first 1000 summaries
   - Improvement: Feedback loop for corrections

## Success Metrics

### Week 4 Checkpoint
- [ ] 100 calls successfully processed
- [ ] Database integration stable
- [ ] NFS access reliable

### Week 8 Checkpoint
- [ ] 1,000 calls processed daily
- [ ] 95%+ transcription accuracy
- [ ] Summary format approved by stakeholders

### Week 10 - Go Live
- [ ] 30,000 calls/day processing capacity
- [ ] < 1 hour processing latency
- [ ] 99.5% uptime achieved

## Resource Requirements

### Hardware
- RTX Workstation (existing)
- 2TB+ storage for summaries
- Network bandwidth for NFS access

### Software
- Python 3.11+
- CUDA 12.x
- Faster-whisper
- MariaDB client libraries

### Personnel
- 1 Developer (full-time)
- 1 DBA (part-time for setup)
- 1 Frontend developer (weeks 9-10)
- Business stakeholders for testing

## Communication Plan

### Weekly Status Updates
- Email to stakeholders
- Metrics dashboard
- Blockers and risks

### Milestone Reviews
- Week 4: Infrastructure complete
- Week 8: Core functionality demo
- Week 10: Production readiness review

---

*This roadmap will be updated weekly with actual progress and any adjustments needed.*