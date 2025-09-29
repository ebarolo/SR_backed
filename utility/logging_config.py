import logging
import traceback
import inspect
from pythonjsonlogger.json import JsonFormatter
import contextvars
import os
from typing import Optional, Dict, Any
import atexit

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


class JSONArrayFileHandler(logging.FileHandler):
    """
    File handler that writes log records as a single valid JSON array.

    Notes:
    - Uses write mode ('w') to always create a fresh valid JSON array file.
    - Appends items with commas and closes the array on process exit.
    - Works best for single-process logging; rotation is not handled here.
    """

    def __init__(self, filename: str, encoding: str = "utf-8", array_indent: int = 2):
        # Always start a fresh valid JSON array
        super().__init__(filename, mode="w", encoding=encoding, delay=True)
        self._first = True
        self._closed = False
        self._array_indent = max(array_indent, 0)

        # Open the underlying stream and write the opening bracket
        self.acquire()
        try:
            self.stream = self._open()
            self.stream.write("[\n")
            self.stream.flush()
        finally:
            self.release()

        # Ensure we close the JSON array at interpreter exit
        atexit.register(self._finalize_array)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)  # Expect a JSON string from the formatter
            self.acquire()
            try:
                # Write comma between items
                if not self._first:
                    self.stream.write(",\n")
                else:
                    self._first = False

                # Indent the object within the array for readability
                indent_prefix = " " * self._array_indent
                for i, line in enumerate(msg.splitlines() or [msg]):
                    self.stream.write(indent_prefix + line)
                    if i < len(msg.splitlines()) - 1:
                        self.stream.write("\n")
                self.stream.flush()
            finally:
                self.release()
        except Exception:
            self.handleError(record)

    def _finalize_array(self) -> None:
        if self._closed:
            return
        try:
            self.acquire()
            try:
                self.stream.write("\n]\n")
                self.stream.flush()
                self._closed = True
            finally:
                self.release()
        except Exception:
            # Best-effort close; ignore errors during interpreter shutdown
            pass
        try:
            super().close()
        except Exception:
            pass


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
    json_path = json_file_path or os.getenv("LOG_JSON_PATH") or "backend.json"
    json_mode = (os.getenv("LOG_JSON_MODE") or "jsonl").lower()  # 'jsonl' (default) or 'array'
    # Pretty-print indent for JSON content (applies to each object; in array mode the array is indented too)
    try:
        json_indent_env = os.getenv("LOG_JSON_INDENT")
        json_indent = int(json_indent_env) if json_indent_env else None
    except ValueError:
        json_indent = None

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

    # JSON file handler - structured logs with full context
    if json_mode == "array":
        file_handler = JSONArrayFileHandler(json_path, encoding="utf-8", array_indent=2)
        json_fmt = JsonFormatter(
            fmt=(
                "%(asctime)s %(levelname)s %(name)s %(message)s "
                "%(request_id)s %(job_id)s %(pathname)s %(lineno)d "
                "%(source_file)s %(source_line)d %(source_func)s %(error_chain)s"
            ),
            json_indent=json_indent,           # pretty-print each object if requested
            json_ensure_ascii=False            # keep unicode as-is for readability
        )
    else:
        # Crea il file handler con gestione esplicita della chiusura per evitare ResourceWarning
        file_handler = None
        json_fmt = None
        try:
            # Prima chiudiamo eventuali handler esistenti per lo stesso file
            abs_json_path = os.path.abspath(json_path)
            for handler in list(root_logger.handlers):
                if isinstance(handler, logging.FileHandler):
                    try:
                        if os.path.abspath(handler.baseFilename) == abs_json_path:
                            handler.close()
                            root_logger.removeHandler(handler)
                    except (AttributeError, OSError):
                        continue
                    
            file_handler = logging.FileHandler(json_path, mode="w", encoding="utf-8", delay=False)
            json_fmt = JsonFormatter(
                fmt=(
                    "%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(request_id)s %(job_id)s %(pathname)s %(lineno)d "
                    "%(source_file)s %(source_line)d %(source_func)s %(error_chain)s"
                ),
                json_indent=json_indent,           # pretty-print JSONL if requested (multi-line per record)
                json_ensure_ascii=False            # keep unicode as-is for readability
            )
        except Exception as e:
            # Fallback in caso di errore
            import sys
            sys.stderr.write(f"Warning: Unable to configure file logging: {e}\n")
            if file_handler:
                try:
                    file_handler.close()
                except Exception:
                    pass
            file_handler = None
            json_fmt = None

    if file_handler and json_fmt:
        file_handler.setFormatter(json_fmt)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

    # Assicura che i file handler vengano chiusi correttamente all'uscita
    def cleanup_handlers():
        for handler in root_logger.handlers:
            if isinstance(handler, (logging.FileHandler, JSONArrayFileHandler)):
                try:
                    handler.close()
                except Exception:
                    pass
    
    atexit.register(cleanup_handlers)

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

