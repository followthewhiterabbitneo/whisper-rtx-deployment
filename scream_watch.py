#!/usr/bin/env python3
"""
SCREAM Watch Mode - Real-time audio file monitoring
Uses watchdog for efficient filesystem monitoring
"""

import time
import logging
from pathlib import Path
from queue import Queue, Empty
from threading import Thread

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
except ImportError:
    print("Installing watchdog for file monitoring...")
    import os
    os.system("pip install watchdog")
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from scream_engine import Source, AudioFile


logger = logging.getLogger("SCREAM.Watch")


class WatchdogSource(Source):
    """Watch directory for new audio files using watchdog"""
    
    def __init__(self, path: str, formats: list = None):
        self.path = Path(path)
        self.formats = formats or ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        self.queue = Queue()
        self.observer = None
        self.handler = AudioFileHandler(self.queue, self.formats)
        
    def start(self):
        """Start watching directory"""
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)
            
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.path), recursive=False)
        self.observer.start()
        logger.info(f"Watching directory: {self.path}")
        
    def stop(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
    def discover(self):
        """Yield audio files as they appear"""
        while True:
            try:
                # Get file from queue with timeout
                file_path = self.queue.get(timeout=1)
                
                # Create AudioFile object
                audio = AudioFile(
                    path=file_path,
                    size=file_path.stat().st_size,
                    format=file_path.suffix
                )
                
                logger.info(f"New file detected: {file_path.name}")
                yield audio
                
            except Empty:
                # No new files, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing file: {e}")


class AudioFileHandler(FileSystemEventHandler):
    """Handle filesystem events for audio files"""
    
    def __init__(self, queue: Queue, formats: list):
        self.queue = queue
        self.formats = formats
        self.processing = set()  # Track files being processed
        
    def on_created(self, event):
        """Handle file creation"""
        if not isinstance(event, FileCreatedEvent):
            return
            
        self._handle_file(event.src_path)
        
    def on_modified(self, event):
        """Handle file modification"""
        if isinstance(event, FileModifiedEvent):
            # Wait a bit to ensure file is fully written
            time.sleep(0.5)
            self._handle_file(event.src_path)
            
    def _handle_file(self, path: str):
        """Process a potential audio file"""
        file_path = Path(path)
        
        # Check if it's an audio file
        if file_path.suffix.lower() not in self.formats:
            return
            
        # Skip if already processing
        if file_path in self.processing:
            return
            
        # Check if file is ready (not being written)
        if not self._is_file_ready(file_path):
            return
            
        # Add to queue
        self.processing.add(file_path)
        self.queue.put(file_path)
        
    def _is_file_ready(self, path: Path, timeout: int = 5) -> bool:
        """Check if file is ready for processing"""
        if not path.exists():
            return False
            
        # Check if file size is stable
        prev_size = -1
        for _ in range(timeout):
            try:
                current_size = path.stat().st_size
                if current_size == prev_size and current_size > 0:
                    return True
                prev_size = current_size
                time.sleep(1)
            except:
                return False
                
        return False


class RealtimePipeline:
    """Pipeline with real-time monitoring capabilities"""
    
    def __init__(self, watch_source, engine, sink):
        self.source = watch_source
        self.engine = engine
        self.sink = sink
        self.processing_thread = None
        self.running = False
        
    def start(self):
        """Start the real-time pipeline"""
        self.running = True
        
        # Start watching
        self.source.start()
        
        # Start processing thread
        self.processing_thread = Thread(target=self._process_loop)
        self.processing_thread.start()
        
        logger.info("Real-time pipeline started")
        
    def stop(self):
        """Stop the pipeline"""
        logger.info("Stopping real-time pipeline...")
        
        self.running = False
        self.source.stop()
        
        if self.processing_thread:
            self.processing_thread.join()
            
        logger.info("Pipeline stopped")
        
    def _process_loop(self):
        """Main processing loop"""
        for audio in self.source.discover():
            if not self.running:
                break
                
            # Process audio
            result = self.engine.process(audio)
            
            # Deliver result
            self.sink.deliver(result)
            
            # Remove from processing set
            if hasattr(self.source.handler, 'processing'):
                self.source.handler.processing.discard(audio.path)


def demo_realtime():
    """Demo real-time monitoring"""
    from scream_engine import WhisperEngine, FileSink
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create components
    source = WatchdogSource("wav")
    engine = WhisperEngine("models/faster-whisper-large-v3-turbo-ct2")
    sink = FileSink("transcriptions", format="json")
    
    # Create pipeline
    pipeline = RealtimePipeline(source, engine, sink)
    
    try:
        pipeline.start()
        
        print("\n" + "="*60)
        print("SCREAM Real-time Monitor Active")
        print("="*60)
        print(f"Watching: {source.path}")
        print(f"Output: {sink.output_dir}")
        print("\nDrop audio files into the watched directory.")
        print("Press Ctrl+C to stop.\n")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        pipeline.stop()
        print("Done!")


if __name__ == "__main__":
    demo_realtime()