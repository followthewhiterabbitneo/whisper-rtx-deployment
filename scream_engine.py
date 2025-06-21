#!/usr/bin/env python3
"""
SCREAM - Speech Conversion & Recognition Engine for Audio Management
Core pipeline implementation with pluggable source/sink architecture
"""

import os
import json
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional, Dict, Any
from queue import Queue
from threading import Thread

from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCREAM")


@dataclass
class AudioFile:
    """Represents an audio file in the pipeline"""
    path: Path
    size: int
    format: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TranscriptionResult:
    """Result from the transcription engine"""
    source: AudioFile
    text: str
    language: str
    duration: float
    processing_time: float
    segments: list = None
    error: str = None


class Source(ABC):
    """Abstract base for audio sources"""
    
    @abstractmethod
    def discover(self) -> Iterator[AudioFile]:
        """Yield audio files to process"""
        pass


class Engine(ABC):
    """Abstract base for transcription engines"""
    
    @abstractmethod
    def process(self, audio: AudioFile) -> TranscriptionResult:
        """Process an audio file and return transcription"""
        pass


class Sink(ABC):
    """Abstract base for output sinks"""
    
    @abstractmethod
    def deliver(self, result: TranscriptionResult):
        """Deliver transcription result to destination"""
        pass


class DirectorySource(Source):
    """Scan directory for audio files"""
    
    def __init__(self, path: str, formats: list = None):
        self.path = Path(path)
        self.formats = formats or ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        self.processed = set()
        
    def discover(self) -> Iterator[AudioFile]:
        """Scan directory and yield unprocessed audio files"""
        if not self.path.exists():
            logger.warning(f"Source directory {self.path} does not exist")
            return
            
        for format in self.formats:
            for audio_path in self.path.glob(f"*{format}"):
                if audio_path in self.processed:
                    continue
                    
                try:
                    audio = AudioFile(
                        path=audio_path,
                        size=audio_path.stat().st_size,
                        format=format
                    )
                    self.processed.add(audio_path)
                    logger.info(f"Discovered: {audio_path.name}")
                    yield audio
                except Exception as e:
                    logger.error(f"Error reading {audio_path}: {e}")


class WhisperEngine(Engine):
    """Whisper-based transcription engine"""
    
    def __init__(self, model_path: str, device: str = "cuda", 
                 compute_type: str = "int8_float16"):
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self._model = None
        
    @property
    def model(self):
        """Lazy load model"""
        if self._model is None:
            logger.info(f"Loading Whisper model from {self.model_path}")
            self._model = WhisperModel(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("Model loaded successfully")
        return self._model
        
    def process(self, audio: AudioFile) -> TranscriptionResult:
        """Transcribe audio file"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing: {audio.path.name}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                str(audio.path),
                beam_size=5
            )
            
            # Collect text
            full_text = []
            segment_list = []
            for segment in segments:
                text = segment.text.strip()
                full_text.append(text)
                segment_list.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': text
                })
            
            processing_time = time.time() - start_time
            
            result = TranscriptionResult(
                source=audio,
                text='\n'.join(full_text),
                language=info.language,
                duration=info.duration,
                processing_time=processing_time,
                segments=segment_list
            )
            
            speed_ratio = info.duration / processing_time if processing_time > 0 else 0
            logger.info(f"Completed: {audio.path.name} in {processing_time:.1f}s "
                       f"({speed_ratio:.1f}x realtime)")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {audio.path.name}: {e}")
            return TranscriptionResult(
                source=audio,
                text="",
                language="unknown",
                duration=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


class FileSink(Sink):
    """Save transcriptions to files"""
    
    def __init__(self, output_dir: str, format: str = "txt"):
        self.output_dir = Path(output_dir)
        self.format = format
        self.output_dir.mkdir(exist_ok=True)
        
    def deliver(self, result: TranscriptionResult):
        """Save transcription to file"""
        if result.error:
            logger.error(f"Skipping failed transcription: {result.source.path.name}")
            return
            
        output_file = self.output_dir / f"{result.source.path.stem}.{self.format}"
        
        try:
            if self.format == "txt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.text)
                    
            elif self.format == "json":
                data = {
                    'source': str(result.source.path),
                    'text': result.text,
                    'language': result.language,
                    'duration': result.duration,
                    'processing_time': result.processing_time,
                    'segments': result.segments
                }
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            logger.info(f"Saved: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save {output_file}: {e}")


class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, source: Source, engine: Engine, sink: Sink):
        self.source = source
        self.engine = engine
        self.sink = sink
        self.stats = {
            'processed': 0,
            'failed': 0,
            'total_time': 0
        }
        
    def run(self, continuous: bool = False):
        """Run the pipeline"""
        logger.info("Starting SCREAM pipeline")
        
        while True:
            found_files = False
            
            for audio in self.source.discover():
                found_files = True
                result = self.engine.process(audio)
                self.sink.deliver(result)
                
                # Update stats
                self.stats['processed'] += 1
                if result.error:
                    self.stats['failed'] += 1
                self.stats['total_time'] += result.processing_time
                
            if not continuous or not found_files:
                break
                
            # Wait before next scan
            time.sleep(5)
            
        self._print_stats()
        
    def _print_stats(self):
        """Print pipeline statistics"""
        logger.info("=" * 50)
        logger.info("Pipeline Statistics:")
        logger.info(f"Files processed: {self.stats['processed']}")
        logger.info(f"Files failed: {self.stats['failed']}")
        logger.info(f"Total time: {self.stats['total_time']:.1f}s")
        if self.stats['processed'] > 0:
            avg_time = self.stats['total_time'] / self.stats['processed']
            logger.info(f"Average time per file: {avg_time:.1f}s")


def create_default_pipeline(wav_dir: str = "wav", 
                          output_dir: str = "transcriptions",
                          model_path: str = "models/faster-whisper-large-v3-turbo-ct2"):
    """Create a pipeline with default configuration"""
    
    source = DirectorySource(wav_dir)
    engine = WhisperEngine(model_path)
    sink = FileSink(output_dir)
    
    return Pipeline(source, engine, sink)


if __name__ == "__main__":
    # Example usage
    pipeline = create_default_pipeline()
    pipeline.run(continuous=False)