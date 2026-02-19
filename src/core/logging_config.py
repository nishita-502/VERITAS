"""
Logging Configuration for VERITAS
"""
import logging
import sys
from pathlib import Path
from src.core.config import LOG_DIR, LOG_LEVEL

class VeritasLogger:
    """Centralized logging for VERITAS system"""
    
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get or create a logger instance"""
        
        if name in VeritasLogger._loggers:
            return VeritasLogger._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File Handler (with UTF-8 encoding for emoji support)
        log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Disable propagation to root logger
        logger.propagate = False
        
        VeritasLogger._loggers[name] = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get logger"""
    return VeritasLogger.get_logger(name)
