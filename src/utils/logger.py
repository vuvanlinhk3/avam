"""
Logging system for AVAM
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import os

def setup_logger(name: str = "AVAM", log_level: str = "INFO") -> logging.Logger:
    """
    Setup root logger with file and console handlers
    
    Args:
        name: Ignored (kept for compatibility)
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Root logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"avam_{timestamp}.log"
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup
    root_logger.info(f"Logger initialized. Log file: {log_file}")
    root_logger.info(f"Python version: {sys.version}")
    root_logger.info(f"Current directory: {Path.cwd()}")
    
    return root_logger

def get_logger(name: str = "AVAM") -> logging.Logger:
    """
    Get root logger instance
    
    Args:
        name: Ignored (kept for compatibility)
        
    Returns:
        Root logger instance
    """
    return logging.getLogger()