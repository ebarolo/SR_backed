import logging
from pythonjsonlogger import jsonlogger
import contextvars
import os

# Context variables to carry request/job identifiers across logs
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
job_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("job_id", default="-")


class ContextFilter(logging.Filter):
    """Injects contextvars (request_id, job_id) into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = request_id_var.get()
        except LookupError:
            record.request_id = "-"
        try:
            record.job_id = job_id_var.get()
        except LookupError:
            record.job_id = "-"
        return True


def setup_logging(level: str | None = None, json_file_path: str | None = None, console: bool = True) -> None:
    """
    Configure root logging with:
    - Console handler (human-readable, single line)
    - File handler with JSON formatter (structured logs)

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
    context_filter = ContextFilter()

    # Console handler (readable, includes request/job ids)
    if console:
        console_handler = logging.StreamHandler()
        console_fmt = (
            "%(asctime)s %(levelname)s [req:%(request_id)s job:%(job_id)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(logging.Formatter(console_fmt))
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)

    # JSON file handler
    file_handler = logging.FileHandler(json_path, encoding="utf-8")
    json_fmt = jsonlogger.JsonFormatter(
        fmt=(
            "%(asctime)s %(levelname)s %(name)s %(message)s "
            "%(request_id)s %(job_id)s %(pathname)s %(lineno)d"
        )
    )
    file_handler.setFormatter(json_fmt)
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    # Make module-level loggers propagate to root
    logging.captureWarnings(True)


