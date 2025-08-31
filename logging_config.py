import logging
import traceback
import inspect
from pythonjsonlogger import jsonlogger
import contextvars
import os
from typing import Optional, Dict, Any

# Context variables to carry request/job identifiers across logs
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
job_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("job_id", default="-")
error_chain_var: contextvars.ContextVar[list] = contextvars.ContextVar("error_chain")


class EnhancedContextFilter(logging.Filter):
    """Injects contextvars and enhanced debugging info into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add context variables
        try:
            record.request_id = request_id_var.get()
        except LookupError:
            record.request_id = "-"
        try:
            record.job_id = job_id_var.get()
        except LookupError:
            record.job_id = "-"
        
        # Add enhanced location info for error/exception levels
        if record.levelno >= logging.WARNING:
            frame = inspect.currentframe()
            try:
                # Skip logging framework frames to find actual caller
                while frame and (
                    'logging' in frame.f_code.co_filename or 
                    'logging_config.py' in frame.f_code.co_filename
                ):
                    frame = frame.f_back
                
                if frame:
                    record.source_file = os.path.basename(frame.f_code.co_filename)
                    record.source_line = frame.f_lineno
                    record.source_func = frame.f_code.co_name
                else:
                    record.source_file = "unknown"
                    record.source_line = 0
                    record.source_func = "unknown"
            finally:
                del frame
        
        # Add error chain for tracking cascading errors
        try:
            error_chain = error_chain_var.get()
            if error_chain:
                record.error_chain = " -> ".join(error_chain[-3:])  # Last 3 errors
            else:
                record.error_chain = "-"
        except LookupError:
            record.error_chain = "-"
            
        return True


def log_error_chain(error_context: str) -> None:
    """Add error context to the chain for tracking cascading errors."""
    try:
        current_chain = error_chain_var.get()
    except LookupError:
        current_chain = []
    
    current_chain.append(error_context)
    error_chain_var.set(current_chain[-5:])  # Keep only last 5 errors


def clear_error_chain() -> None:
    """Clear the error chain (call this at start of new operations)."""
    error_chain_var.set([])


def setup_logging(level: str | None = None, json_file_path: str | None = None, console: bool = True) -> None:
    """
    Configure root logging with enhanced error tracking:
    - Console handler (concise, with error location for warnings+)
    - File handler with JSON formatter (structured logs with full context)

    Args:
        level: Log level string (e.g., "INFO"). If None, uses env LOG_LEVEL or INFO.
        json_file_path: Path for JSON log file. If None, defaults to ./backend.log
        console: Whether to also log to console with a readable formatter.
    """
    log_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    json_path = json_file_path or os.getenv("LOG_JSON_PATH") or "backend.log"

    root_logger = logging.getLogger()
    # Clear existing handlers to avoid duplicate logs when reloading
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.setLevel(log_level)
    context_filter = EnhancedContextFilter()

    # Console handler - concise but informative
    if console:
        console_handler = logging.StreamHandler()
        
        class ConciseFormatter(logging.Formatter):
            """Custom formatter that shows error location only for warnings and errors."""
            
            def format(self, record):
                if record.levelno >= logging.WARNING and hasattr(record, 'source_file'):
                    # For errors/warnings: show timestamp, file:line and error chain if present
                    location = f"{record.source_file}:{record.source_line}"
                    error_chain = getattr(record, 'error_chain', '-')
                    base_fmt = f"%(asctime)s %(levelname)s [{location}] %(name)s: %(message)s"
                    if error_chain != '-':
                        base_fmt += f" (chain: {error_chain})"
                else:
                    # For info/debug: timestamp and simple format
                    base_fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
                
                formatter = logging.Formatter(base_fmt)
                return formatter.format(record)
        
        console_handler.setFormatter(ConciseFormatter())
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)

    # JSON file handler - full context for analysis
    file_handler = logging.FileHandler(json_path, encoding="utf-8")
    json_fmt = jsonlogger.JsonFormatter(
        fmt=(
            "%(asctime)s %(levelname)s %(name)s %(message)s "
            "%(request_id)s %(job_id)s %(pathname)s %(lineno)d "
            "%(source_file)s %(source_line)d %(source_func)s %(error_chain)s"
        )
    )
    file_handler.setFormatter(json_fmt)
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    # Make module-level loggers propagate to root
    logging.captureWarnings(True)


class ErrorLogger:
    """Utility class for enhanced error logging with chain tracking."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_exception(self, operation: str, exc: Exception, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log exception with enhanced context and chain tracking."""
        log_error_chain(f"{operation}: {type(exc).__name__}")
        
        # Use logger.exception to get full traceback
        extra_info = {
            "operation": operation,
            "exception_type": type(exc).__name__,
            **(extra or {})
        }
        
        self.logger.exception(
            f"Error in {operation}: {exc}",
            extra=extra_info
        )
    
    def log_error(self, operation: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error with chain tracking (without exception traceback)."""
        log_error_chain(f"{operation}: {message}")
        
        extra_info = {
            "operation": operation,
            **(extra or {})
        }
        
        self.logger.error(f"Error in {operation}: {message}", extra=extra_info)
    
    def clear_chain(self) -> None:
        """Clear error chain for new operation."""
        clear_error_chain()


def get_error_logger(name: str) -> ErrorLogger:
    """Get an enhanced error logger for a module."""
    return ErrorLogger(logging.getLogger(name))


