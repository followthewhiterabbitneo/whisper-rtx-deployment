# SCREAM Pipeline - First Principles Design

## Core Concept
SCREAM (Speech Conversion & Recognition Engine for Audio Management) is a pipeline that:
1. **Discovers** audio files
2. **Processes** them through Whisper
3. **Delivers** transcriptions to their destination

## First Principles Analysis

### What is a Pipeline?
A pipeline is a series of data transformations where:
- **Input** → **Process** → **Output**
- Each stage has clear responsibilities
- Data flows in one direction
- Stages are loosely coupled

### Essential Components

#### 1. Source (Audio Discovery)
```
WHERE are the audio files?
WHEN do new files arrive?
WHAT formats are supported?
```

#### 2. Engine (SCREAM/Whisper)
```
HOW to process efficiently?
WHAT compute resources to use?
WHERE to handle errors?
```

#### 3. Sink (Output Delivery)
```
WHERE do transcriptions go?
WHAT format is needed?
HOW to handle completion?
```

## Pipeline Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SOURCE    │────▶│   ENGINE    │────▶│    SINK     │
│             │     │  (SCREAM)   │     │             │
│ • File scan │     │ • Load model│     │ • Save text │
│ • Watch dir │     │ • Transcribe│     │ • Database  │
│ • Queue     │     │ • Progress  │     │ • API call  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
   [Config]            [Config]            [Config]
```

## Implementation Stages

### Stage 1: Minimal Pipeline (Direct)
```python
# The absolute minimum
for audio_file in Path("wav").glob("*.wav"):
    text = transcribe(audio_file)
    save(text, f"transcriptions/{audio_file.stem}.txt")
```

### Stage 2: Queue-Based Pipeline
```python
# Decoupled with queue
audio_queue = Queue()
result_queue = Queue()

# Source feeds queue
def source_worker():
    for audio_file in watch_directory("wav"):
        audio_queue.put(audio_file)

# Engine processes queue
def engine_worker():
    while True:
        audio_file = audio_queue.get()
        text = transcribe(audio_file)
        result_queue.put((audio_file, text))

# Sink saves results
def sink_worker():
    while True:
        audio_file, text = result_queue.get()
        save(text, audio_file)
```

### Stage 3: Event-Driven Pipeline
```python
# React to filesystem events
class AudioPipeline:
    def on_file_created(self, path):
        self.process_audio(path)
    
    def on_file_modified(self, path):
        if self.should_reprocess(path):
            self.process_audio(path)
```

## Configuration Philosophy

### What Needs Configuration?
1. **Paths** - Where to find/save files
2. **Formats** - What audio types to process
3. **Performance** - Batch size, parallelism
4. **Behavior** - Error handling, retries

### Configuration Hierarchy
```
1. Defaults (in code)
2. Config file (scream.yaml)
3. Environment variables
4. Command line arguments
```

## Error Handling Strategy

### Types of Errors
1. **Source errors** - File not found, corrupted
2. **Engine errors** - Out of memory, model failure
3. **Sink errors** - Disk full, network down

### Recovery Patterns
```python
# Retry with backoff
@retry(max_attempts=3, backoff=exponential)
def process_with_retry(audio_file):
    return transcribe(audio_file)

# Dead letter queue
def process_with_dlq(audio_file):
    try:
        return transcribe(audio_file)
    except Exception as e:
        dead_letter_queue.put((audio_file, e))
```

## Performance Considerations

### Bottlenecks
1. **I/O bound** - Reading/writing files
2. **GPU bound** - Model inference
3. **Memory bound** - Large audio files

### Optimization Strategies
1. **Batch processing** - Process multiple files per GPU load
2. **Streaming** - Process long files in chunks
3. **Caching** - Skip already processed files

## Monitoring & Observability

### Key Metrics
- Files processed per minute
- Average processing time
- Error rate
- Queue depth

### Logging Levels
```
INFO:  File X processed in Y seconds
WARN:  File X skipped (already exists)
ERROR: File X failed: reason
DEBUG: Model loaded, batch size: N
```