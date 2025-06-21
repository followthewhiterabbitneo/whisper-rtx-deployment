#!/usr/bin/env python3
"""
SCREAM - Speech Conversion & Recognition Engine for Audio Management
Main CLI interface
"""

import argparse
import logging
import sys
from pathlib import Path

from scream_engine import (
    Pipeline, DirectorySource, WhisperEngine, FileSink,
    create_default_pipeline
)
from scream_config import ConfigLoader, create_example_config


def setup_logging(level: str = "INFO"):
    """Configure logging"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('scream.log')
        ]
    )


def cmd_run(args):
    """Run the pipeline"""
    # Load configuration
    loader = ConfigLoader()
    config = loader.load(args.config)
    
    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger("SCREAM")
    
    # Override config with command line args
    if args.source:
        config.source.path = args.source
    if args.output:
        config.sink.path = args.output
    if args.continuous is not None:
        config.continuous = args.continuous
        
    logger.info(f"Starting SCREAM pipeline")
    logger.info(f"Source: {config.source.path}")
    logger.info(f"Output: {config.sink.path}")
    logger.info(f"Continuous: {config.continuous}")
    
    # Create pipeline components
    source = DirectorySource(
        path=config.source.path,
        formats=config.source.formats
    )
    
    engine = WhisperEngine(
        model_path=config.engine.model_path,
        device=config.engine.device,
        compute_type=config.engine.compute_type
    )
    
    sink = FileSink(
        output_dir=config.sink.path,
        format=config.sink.format
    )
    
    # Create and run pipeline
    pipeline = Pipeline(source, engine, sink)
    
    try:
        pipeline.run(continuous=config.continuous)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


def cmd_config(args):
    """Configuration management commands"""
    if args.action == 'create':
        create_example_config()
        
    elif args.action == 'show':
        loader = ConfigLoader()
        config = loader.load(args.file)
        
        import yaml
        print("Current configuration:")
        print(yaml.dump(config.to_dict(), default_flow_style=False))
        
    elif args.action == 'validate':
        try:
            loader = ConfigLoader()
            config = loader.load(args.file)
            print(f"✓ Configuration is valid: {args.file or 'defaults'}")
        except Exception as e:
            print(f"✗ Configuration error: {e}")
            sys.exit(1)


def cmd_transcribe(args):
    """Quick transcribe a single file"""
    from scream_engine import WhisperEngine, AudioFile, FileSink, TranscriptionResult
    
    setup_logging("INFO")
    logger = logging.getLogger("SCREAM")
    
    # Check input file
    audio_path = Path(args.input)
    if not audio_path.exists():
        logger.error(f"File not found: {args.input}")
        sys.exit(1)
        
    # Create engine
    model_path = args.model or "models/faster-whisper-large-v3-turbo-ct2"
    engine = WhisperEngine(
        model_path=model_path,
        device=args.device,
        compute_type="int8_float16"
    )
    
    # Process file
    audio = AudioFile(
        path=audio_path,
        size=audio_path.stat().st_size,
        format=audio_path.suffix
    )
    
    result = engine.process(audio)
    
    if result.error:
        logger.error(f"Transcription failed: {result.error}")
        sys.exit(1)
        
    # Output result
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.text)
            
        logger.info(f"Saved transcription to: {output_path}")
    else:
        print("\n--- Transcription ---")
        print(result.text)
        print("\n--- Metadata ---")
        print(f"Language: {result.language}")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Processing time: {result.processing_time:.1f}s")
        speed = result.duration / result.processing_time if result.processing_time > 0 else 0
        print(f"Speed: {speed:.1f}x realtime")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SCREAM - Speech Conversion & Recognition Engine for Audio Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pipeline once on wav directory
  scream run
  
  # Run continuous monitoring
  scream run --continuous
  
  # Transcribe single file
  scream transcribe audio.wav
  
  # Create example config
  scream config create
  
  # Show current config
  scream config show
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the transcription pipeline')
    run_parser.add_argument('-c', '--config', help='Configuration file')
    run_parser.add_argument('-s', '--source', help='Source directory')
    run_parser.add_argument('-o', '--output', help='Output directory')
    run_parser.add_argument('--continuous', action='store_true', 
                          help='Run continuously, watching for new files')
    run_parser.set_defaults(func=cmd_run)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='action')
    
    config_create = config_subparsers.add_parser('create', 
                                                help='Create example config')
    
    config_show = config_subparsers.add_parser('show', 
                                              help='Show current config')
    config_show.add_argument('-f', '--file', help='Config file to show')
    
    config_validate = config_subparsers.add_parser('validate', 
                                                   help='Validate config file')
    config_validate.add_argument('-f', '--file', help='Config file to validate')
    
    config_parser.set_defaults(func=cmd_config)
    
    # Transcribe command
    trans_parser = subparsers.add_parser('transcribe', 
                                        help='Transcribe a single file')
    trans_parser.add_argument('input', help='Audio file to transcribe')
    trans_parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    trans_parser.add_argument('-m', '--model', help='Model path')
    trans_parser.add_argument('-d', '--device', default='cuda', 
                            choices=['cuda', 'cpu'], help='Device to use')
    trans_parser.set_defaults(func=cmd_transcribe)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
        
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()