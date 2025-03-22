import os
import logging
import json
import gzip
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional, List
from datetime import datetime

class GzipRotatingFileHandler(RotatingFileHandler):
    """
    Extended version of RotatingFileHandler that compresses logs when they're rotated.
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0):
        """Initialize with standard RotatingFileHandler params."""
        super().__init__(
            filename, mode, maxBytes, backupCount, encoding, delay
        )
    
    def doRollover(self):
        """
        Override doRollover to compress the rotated file.
        """
        # Close the current file
        if self.stream:
            self.stream.close()
            self.stream = None
            
        # Rotate the files as normal
        if self.backupCount > 0:
            # Remove the oldest log file if it exists
            oldest_log = f"{self.baseFilename}.{self.backupCount}.gz"
            if os.path.exists(oldest_log):
                os.remove(oldest_log)
                
            # Shift each log file to the next number
            for i in range(self.backupCount - 1, 0, -1):
                source = f"{self.baseFilename}.{i}"
                if os.path.exists(source):
                    target = f"{self.baseFilename}.{i + 1}.gz"
                    with open(source, 'rb') as f_in:
                        with gzip.open(target, 'wb') as f_out:
                            f_out.writelines(f_in)
                    os.remove(source)
                # Also check if there's already a gzipped version
                source = f"{self.baseFilename}.{i}.gz"
                if os.path.exists(source):
                    target = f"{self.baseFilename}.{i + 1}.gz"
                    os.rename(source, target)
            
            # Compress the most recently rotated file
            source = self.baseFilename
            target = f"{self.baseFilename}.1.gz"
            
            if os.path.exists(self.baseFilename):
                with open(source, 'rb') as f_in:
                    with gzip.open(target, 'wb') as f_out:
                        f_out.writelines(f_in)
        
        # Create a new log file
        if not self.delay:
            self.stream = self._open()

class SizedTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    A combination of TimedRotatingFileHandler and RotatingFileHandler.
    Rotates logs based on both time and size.
    """
    
    def __init__(
        self, filename, when='h', interval=1, backupCount=0, encoding=None, 
        delay=False, utc=False, atTime=None, maxBytes=0
    ):
        """
        Initialize with standard TimedRotatingFileHandler params plus maxBytes.
        
        Args:
            maxBytes: Maximum file size in bytes before rotation
        """
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime
        )
        self.maxBytes = maxBytes
    
    def shouldRollover(self, record):
        """
        Check if rollover should occur based on either time or size.
        
        Args:
            record: Log record
            
        Returns:
            True if rollover should occur, False otherwise
        """
        # Check if we should rotate based on time
        time_rotate = super().shouldRollover(record)
        
        # Check if we should rotate based on size
        size_rotate = False
        if self.maxBytes > 0:
            if self.stream is None:
                self.stream = self._open()
            if self.stream.tell() + self.computeRollover(record) >= self.maxBytes:
                size_rotate = True
                
        return time_rotate or size_rotate

class JsonLogFileHandler(logging.FileHandler):
    """
    A log handler that writes JSON formatted logs to a file.
    """
    
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        """Initialize with standard FileHandler params."""
        super().__init__(filename, mode, encoding, delay)
    
    def format(self, record):
        """
        Format the record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log entry
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread
        }
        
        # Add exception info if present
        if record.exc_info:
            exception_type = record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
            exception_msg = str(record.exc_info[1]) if record.exc_info[1] else ""
            log_data["exception"] = {
                "type": exception_type,
                "message": exception_msg,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in [
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)

class LogBufferHandler(logging.Handler):
    """
    A handler that keeps a buffer of recent log records in memory.
    Useful for accessing recent logs programmatically.
    """
    
    def __init__(self, capacity=1000):
        """
        Initialize with buffer capacity.
        
        Args:
            capacity: Maximum number of log records to keep in buffer
        """
        super().__init__()
        self.capacity = capacity
        self.buffer = []
    
    def emit(self, record):
        """
        Add record to buffer.
        
        Args:
            record: Log record
        """
        self.buffer.append({
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        })
        
        # Trim buffer if it exceeds capacity
        if len(self.buffer) > self.capacity:
            self.buffer = self.buffer[-self.capacity:]
    
    def get_logs(self, count=None, level=None, logger=None):
        """
        Get logs from buffer, optionally filtered.
        
        Args:
            count: Maximum number of logs to return
            level: Filter by log level
            logger: Filter by logger name
            
        Returns:
            List of log records
        """
        result = self.buffer
        
        if level:
            result = [r for r in result if r["level"] == level]
        
        if logger:
            result = [r for r in result if r["logger"] == logger]
        
        if count:
            result = result[-count:]
            
        return result
    
    def clear(self):
        """Clear the log buffer."""
        self.buffer = []