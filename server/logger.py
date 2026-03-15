#!/usr/bin/env python3
"""Custom logging module with daily rotation, request ID tracking, and async-safe logging.

This module provides a production-ready logging system with:
- Daily log rotation with Chinese filename format (app-年_月_日.log)
- Request ID tracking using contextvars (async-safe)
- Class name detection from call stack
- QueueHandler + QueueListener pattern for non-blocking async logging
- Chinese format labels (时间, 进程ID, 线程ID)
"""

import contextvars
import inspect
import logging
import logging.handlers
import os
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Context variable for request ID (async-safe)
_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

# Global listener reference for cleanup
_listener: Optional[logging.handlers.QueueListener] = None
_lock = threading.Lock()


def get_request_id() -> Optional[str]:
    """Get current request ID from context.
    
    Returns:
        Current request ID string, or None if not set.
    """
    return _request_id.get()


def set_request_id(request_id: str) -> contextvars.Token:
    """Set request ID in context.
    
    Args:
        request_id: The request ID to set.
        
    Returns:
        Token for resetting the context variable.
    """
    return _request_id.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    """Reset request ID using token.
    
    Args:
        token: The token returned by set_request_id().
    """
    _request_id.reset(token)


class ChineseFormatter(logging.Formatter):
    """Custom formatter with Chinese labels and class name detection."""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """Initialize formatter with optional format strings.
        
        Args:
            fmt: Log format string.
            datefmt: Date format string.
        """
        # Default format with Chinese labels
        if fmt is None:
            fmt = "[时间：%(asctime)s][进程ID:%(process)d][线程ID:%(thread)d][%(class_name)s][%(funcName)s][%(request_id)s] - %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H-%M-%S"
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with class name and request ID.
        
        Args:
            record: The log record to format.
            
        Returns:
            Formatted log string.
        """
        # Detect class name from call stack
        record.class_name = self._detect_class_name()
        record.request_id = get_request_id()
        return super().format(record)
    
    def _detect_class_name(self) -> str:
        """Detect calling class name from stack frame.
        
        Returns:
            Class name if found, otherwise module name.
        """
        # Walk stack to find first frame outside logging module
        for frame_info in inspect.stack()[4:]:  # Skip logging frames
            frame = frame_info.frame
            if 'self' in frame.f_locals:
                return frame.f_locals['self'].__class__.__name__
            if 'cls' in frame.f_locals:
                return frame.f_locals['cls'].__name__
            # Fallback to module name (filename without .py)
            module_name = frame_info.filename.split('/')[-1].replace('.py', '')
            if module_name != '__init__':
                return module_name
        # Final fallback
        return "unknown"
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format timestamp with milliseconds.
        
        Args:
            record: The log record.
            datefmt: Date format string.
            
        Returns:
            Formatted timestamp string.
        """
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            # Append milliseconds
            return ct.strftime(datefmt) + f".{int(record.msecs):03d}"
        return ct.isoformat()


class DailyRotatingHandler(logging.handlers.TimedRotatingFileHandler):
    """Daily rotating file handler with Chinese filename format."""
    
    def __init__(self, filename: str, backupCount: int = 30, **kwargs):
        """Initialize handler with daily rotation.
        
        Args:
            filename: Base log file path.
            backupCount: Number of backup files to keep.
            **kwargs: Additional arguments for TimedRotatingFileHandler.
        """
        super().__init__(
            filename, 
            when='midnight', 
            backupCount=backupCount,
            encoding='utf-8',
            **kwargs
        )
        self.namer = self._chinese_namer
        self.rotator = self._chinese_rotator
    
    def _chinese_namer(self, default_name: str) -> str:
        """Generate filename in format app-年_月_日.log.
        
        Args:
            default_name: The default name generated by parent class.
            
        Returns:
            Filename with Chinese date format.
        """
        date_str = datetime.now().strftime("%Y_%m_%d")
        return f"app-{date_str}.log"
    
    def _chinese_rotator(self, source: str, dest: str) -> None:
        """Custom rotator that moves current log to dated file.
        
        Args:
            source: Current log file path.
            dest: Destination log file path (dated).
        """
        # If source doesn't exist (first run), nothing to rotate
        if not os.path.exists(source):
            return
        
        # Read current file content
        with open(source, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Write to dated file
        dest_dir = os.path.dirname(dest)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
            
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Clear source file (don't delete, just truncate)
        with open(source, 'w', encoding='utf-8') as f:
            pass


def setup_logging(config) -> Optional[logging.handlers.QueueListener]:
    """Configure production logging with QueueHandler pattern.
    
    This function sets up non-blocking async logging using the QueueHandler
    + QueueListener pattern. All log records are queued and processed by a
    background thread, preventing I/O from blocking the event loop.
    
    Args:
        config: LoggingConfig from Pydantic with enabled, level, dir, format, date_format fields.
        
    Returns:
        QueueListener for cleanup on shutdown, or None if logging is disabled.
    """
    global _listener
    
    if not config.enabled:
        # Return a dummy listener that does nothing
        return None
    
    # Create log directory
    log_dir = Path(config.dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create queue for non-blocking logging
    log_queue = queue.Queue(-1)
    
    # Create formatter
    formatter = ChineseFormatter(
        fmt=config.format,
        datefmt=config.date_format
    )
    
    # Create handlers
    # 1. Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 2. File handler with daily rotation
    log_file = log_dir / "app.log"  # Base file, rotates to app-年_月_日.log
    file_handler = DailyRotatingHandler(
        filename=str(log_file),
        backupCount=30,
    )
    file_handler.setFormatter(formatter)
    
    # Create QueueListener (background thread for I/O)
    _listener = logging.handlers.QueueListener(
        log_queue,
        console_handler,
        file_handler,
        respect_handler_level=True
    )
    _listener.start()
    
    # Create QueueHandler (non-blocking)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    
    # Configure root logger
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(queue_handler)
    root.setLevel(getattr(logging, config.level.upper()))
    
    return _listener


def shutdown_logging() -> None:
    global _listener
    if _listener:
        _listener.stop()
        _listener = None


def get_logger(name: str = __name__) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name, typically __name__ of the calling module.
        
    Returns:
        Logger instance configured for use with this logging system.
    """
    return logging.getLogger(name)


    
    
# Logger class for wrapping class for easier testing
class Logger:
    """Wrapper class for easier testing and usage."""
    
    def __init__(self, log_dir: str, log_filename: str = "app", 
                 level: int = logging.INFO, 
                 format_string: str = "%(asctime)s | %(process)d | %(thread)d | %(class_name)s | %(funcName)s | %(request_id)s | %(message)s",
                 use_queue: bool = True):
        """Initialize Logger.
        
        Args:
            log_dir: Directory for log files.
            log_filename: Base log filename.
            level: Log level (default: INFO).
            format_string: Log format string.
            use_queue: Use QueueHandler pattern (default: True). Set False for testing.
        """
        self.log_dir = Path(log_dir)
        self.log_filename = log_filename
        self.level = level
        self.format_string = format_string
        self.use_queue = use_queue
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(log_filename)
        self.logger.setLevel(level)
        # Clear any existing handlers to avoid duplicates
        self.logger.handlers = []
        
        self._queue: queue.Queue = queue.Queue(-1)
        self._handlers: list[logging.Handler] = []
        self._listener: Optional[logging.handlers.QueueListener] = None
        
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ChineseFormatter(
            fmt=self.format_string,
            datefmt="%Y-%m-%d %H-%M-%S"
        ))
        self._handlers.append(console_handler)
        
        log_file = Path(self.log_dir) / f"{self.log_filename}.log"
        file_handler = DailyRotatingHandler(
            filename=str(log_file),
            backupCount=30
        )
        file_handler.setFormatter(ChineseFormatter(
            fmt=self.format_string,
            datefmt="%Y-%m-%d %H-%M-%S"
        ))
        self._handlers.append(file_handler)
        
        if self.use_queue:
            self._listener = logging.handlers.QueueListener(
                self._queue,
                *self._handlers,
                respect_handler_level=True
            )
            self._listener.start()
            
            queue_handler = logging.handlers.QueueHandler(self._queue)
            self.logger.addHandler(queue_handler)
        else:
            for handler in self._handlers:
                self.logger.addHandler(handler)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


# Add request_id_context fixture alias for backward compatibility
request_id_context = _request_id


__all__ = [
    "get_request_id",
    "set_request_id",
    "reset_request_id",
    "ChineseFormatter",
    "DailyRotatingHandler",
    "setup_logging",
    "shutdown_logging",
    "get_logger",
    "Logger",
    "request_id_context",
]


# Module exports
__all__ = [
    "get_request_id",
    "set_request_id",
    "reset_request_id",
    "ChineseFormatter",
    "DailyRotatingHandler",
    "setup_logging",
    "shutdown_logging",
    "get_logger",
]
