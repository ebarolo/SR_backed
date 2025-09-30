"""
Google Cloud Logging configuration for Smart Recipe.

Implementa best practices per logging su Google Cloud Platform:
- Automatic resource detection per Compute Engine VM
- Structured logging con labels e jsonPayload
- Trace context integration per correlazione request
- Severity mapping standard
- Error Reporting integration
- Support per local fallback in development

Author: Smart Recipe Team
"""

import logging
import os
import sys
import contextvars
import inspect
from typing import Optional, Dict, Any, Union
from enum import Enum

# Context variables per tracking request/job attraverso async contexts
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
job_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("job_id", default="-")
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")
error_chain_var: contextvars.ContextVar[list] = contextvars.ContextVar("error_chain", default=[])


class LoggingBackend(Enum):
    """Backend disponibili per il logging."""
    CLOUD = "cloud"      # Google Cloud Logging
    LOCAL = "local"      # File-based logging (JSONL)
    HYBRID = "hybrid"    # Entrambi


class CloudLoggingHandler(logging.Handler):
    """
    Custom handler per Google Cloud Logging con best practices.
    
    Features:
    - Automatic resource detection (Compute Engine VM)
    - Structured logging con labels
    - Trace context per request correlation
    - Error chain tracking
    - Severity mapping standard
    """
    
    def __init__(
        self,
        client=None,
        name: str = "smart-recipe",
        resource: Optional[Any] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Inizializza Cloud Logging Handler.
        
        Args:
            client: Google Cloud Logging Client (auto-detect se None)
            name: Nome del log (default: smart-recipe)
            resource: Resource descriptor (auto-detect per Compute Engine)
            labels: Labels globali da aggiungere a tutti i log
        """
        super().__init__()
        
        try:
            from google.cloud import logging as cloud_logging
            from google.cloud.logging_v2.resource import Resource
            
            # Inizializza client se non fornito
            if client is None:
                self.client = cloud_logging.Client()
            else:
                self.client = client
            
            # Crea logger per il nome specificato
            self.logger = self.client.logger(name)
            
            # Auto-detect resource se non fornito
            if resource is None:
                self.resource = self._detect_resource()
            else:
                self.resource = resource
                
            self.global_labels = labels or {}
            self.enabled = True
            
        except ImportError:
            # Fallback se google-cloud-logging non è disponibile
            sys.stderr.write(
                "Warning: google-cloud-logging not available. "
                "Cloud logging disabled. Install with: pip install google-cloud-logging\n"
            )
            self.enabled = False
        except Exception as e:
            sys.stderr.write(f"Warning: Could not initialize Cloud Logging: {e}\n")
            self.enabled = False
    
    def _detect_resource(self) -> Optional[Any]:
        """
        Auto-detect resource type per Compute Engine VM.
        
        Returns:
            Resource descriptor per GCE instance o None se non su GCE
        """
        try:
            from google.cloud.logging_v2.resource import Resource
            import requests
            
            # Tenta di recuperare metadata da Compute Engine metadata server
            metadata_server = "http://metadata.google.internal/computeMetadata/v1/"
            metadata_headers = {"Metadata-Flavor": "Google"}
            
            try:
                # Timeout breve per non bloccare in ambienti non-GCE
                response = requests.get(
                    f"{metadata_server}instance/id",
                    headers=metadata_headers,
                    timeout=1
                )
                
                if response.status_code == 200:
                    # Siamo su Compute Engine, recupera metadata
                    instance_id = response.text
                    
                    # Recupera zona
                    zone_response = requests.get(
                        f"{metadata_server}instance/zone",
                        headers=metadata_headers,
                        timeout=1
                    )
                    # Formato: projects/PROJECT_NUM/zones/ZONE
                    zone_full = zone_response.text
                    zone = zone_full.split('/')[-1] if zone_response.status_code == 200 else "unknown"
                    
                    # Recupera project ID
                    project_response = requests.get(
                        f"{metadata_server}project/project-id",
                        headers=metadata_headers,
                        timeout=1
                    )
                    project_id = project_response.text if project_response.status_code == 200 else None
                    
                    # Crea resource descriptor per GCE instance
                    return Resource(
                        type="gce_instance",
                        labels={
                            "instance_id": instance_id,
                            "zone": zone,
                            "project_id": project_id or "unknown"
                        }
                    )
            except (requests.RequestException, requests.Timeout):
                # Non siamo su Compute Engine o metadata server non disponibile
                pass
            
            # Fallback: generic resource
            return Resource(
                type="generic_node",
                labels={
                    "location": os.getenv("GCP_REGION", "unknown"),
                    "namespace": "smart-recipe",
                    "node_id": os.getenv("HOSTNAME", "localhost")
                }
            )
            
        except Exception as e:
            sys.stderr.write(f"Warning: Could not detect resource: {e}\n")
            return None
    
    def _get_severity(self, levelno: int) -> str:
        """
        Map Python logging level a Cloud Logging severity.
        
        Args:
            levelno: Python logging level number
            
        Returns:
            Cloud Logging severity string
        """
        # Mapping secondo standard Cloud Logging
        if levelno >= logging.CRITICAL:
            return "CRITICAL"
        elif levelno >= logging.ERROR:
            return "ERROR"
        elif levelno >= logging.WARNING:
            return "WARNING"
        elif levelno >= logging.INFO:
            return "INFO"
        elif levelno >= logging.DEBUG:
            return "DEBUG"
        else:
            return "DEFAULT"
    
    def _extract_trace_context(self, record: logging.LogRecord) -> Optional[str]:
        """
        Estrae trace context per correlazione request.
        
        Args:
            record: Log record
            
        Returns:
            Trace string in formato Cloud Logging o None
        """
        try:
            trace_id = trace_id_var.get()
            if trace_id and trace_id != "-":
                # Formato: projects/[PROJECT_ID]/traces/[TRACE_ID]
                project_id = os.getenv("GCP_PROJECT_ID", "unknown")
                return f"projects/{project_id}/traces/{trace_id}"
        except LookupError:
            pass
        
        return None
    
    def _build_structured_payload(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Costruisce payload strutturato per Cloud Logging.
        
        Args:
            record: Log record
            
        Returns:
            Dictionary con structured payload
        """
        # Base payload
        payload = {
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pathname": record.pathname,
        }
        
        # Aggiungi context variables
        try:
            request_id = request_id_var.get()
            if request_id != "-":
                payload["request_id"] = request_id
        except LookupError:
            pass
        
        try:
            job_id = job_id_var.get()
            if job_id != "-":
                payload["job_id"] = job_id
        except LookupError:
            pass
        
        # Aggiungi error chain per warning/error
        if record.levelno >= logging.WARNING:
            try:
                error_chain = error_chain_var.get()
                if error_chain:
                    payload["error_chain"] = error_chain[-5:]  # Ultimi 5 errori
            except LookupError:
                pass
            
            # Aggiungi source location per errori
            if hasattr(record, 'source_file'):
                payload["source_location"] = {
                    "file": record.source_file,
                    "line": record.source_line,
                    "function": record.source_func
                }
        
        # Aggiungi exception info se presente
        if record.exc_info:
            import traceback
            payload["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Aggiungi extra fields dal record
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith('_'):
                # Evita di duplicare campi già presenti
                if key not in payload:
                    payload[key] = value
        
        return payload
    
    def _build_labels(self, record: logging.LogRecord) -> Dict[str, str]:
        """
        Costruisce labels per Cloud Logging.
        
        Args:
            record: Log record
            
        Returns:
            Dictionary con labels
        """
        labels = dict(self.global_labels)
        
        # Aggiungi labels standard
        labels["severity"] = self._get_severity(record.levelno)
        labels["logger"] = record.name
        
        # Aggiungi request_id e job_id come labels per facilitare filtering
        try:
            request_id = request_id_var.get()
            if request_id != "-":
                labels["request_id"] = request_id
        except LookupError:
            pass
        
        try:
            job_id = job_id_var.get()
            if job_id != "-":
                labels["job_id"] = job_id
        except LookupError:
            pass
        
        # Aggiungi environment
        env = os.getenv("ENVIRONMENT", "production")
        labels["environment"] = env
        
        return labels
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emette log record a Cloud Logging.
        
        Args:
            record: Log record da emettere
        """
        if not self.enabled:
            return
        
        try:
            # Costruisci payload strutturato
            payload = self._build_structured_payload(record)
            
            # Costruisci labels
            labels = self._build_labels(record)
            
            # Estrai trace context
            trace = self._extract_trace_context(record)
            
            # Determina severity
            severity = self._get_severity(record.levelno)
            
            # Invia log a Cloud Logging
            self.logger.log_struct(
                payload,
                severity=severity,
                labels=labels,
                resource=self.resource,
                trace=trace
            )
            
        except Exception as e:
            # Fallback a stderr per non perdere il log
            sys.stderr.write(f"Error sending log to Cloud Logging: {e}\n")
            sys.stderr.write(f"Original log: {record.getMessage()}\n")


class EnhancedContextFilter(logging.Filter):
    """
    Filter che arricchisce log records con context variables e debugging info.
    
    Compatibile con sia file logging che cloud logging.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Arricchisce record con context e source location.
        
        Args:
            record: Log record da arricchire
            
        Returns:
            True per permettere propagazione del log
        """
        # Aggiungi context variables
        try:
            record.request_id = request_id_var.get()
        except LookupError:
            record.request_id = "-"
        
        try:
            record.job_id = job_id_var.get()
        except LookupError:
            record.job_id = "-"
        
        try:
            record.trace_id = trace_id_var.get()
        except LookupError:
            record.trace_id = "-"
        
        # Aggiungi enhanced source location per warnings e errors
        if record.levelno >= logging.WARNING:
            frame = inspect.currentframe()
            try:
                # Skip logging framework frames
                while frame and (
                    'logging' in frame.f_code.co_filename or
                    'cloud_logging_config.py' in frame.f_code.co_filename or
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
        
        # Aggiungi error chain
        try:
            error_chain = error_chain_var.get()
            if error_chain:
                record.error_chain = " -> ".join(error_chain[-3:])
            else:
                record.error_chain = "-"
        except LookupError:
            record.error_chain = "-"
        
        return True


def setup_cloud_logging(
    backend: Union[LoggingBackend, str] = LoggingBackend.HYBRID,
    level: Optional[str] = None,
    log_name: str = "smart-recipe",
    console: bool = True,
    local_file_path: Optional[str] = None,
    global_labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Configura logging per Google Cloud con fallback locale.
    
    Best practices implementate:
    - Auto-detection di Compute Engine resource
    - Structured logging con jsonPayload
    - Trace context per request correlation
    - Labels per filtering e grouping
    - Severity mapping standard
    - Error Reporting integration
    - Fallback locale in development
    
    Args:
        backend: Backend da usare (CLOUD, LOCAL, o HYBRID)
        level: Log level (INFO, DEBUG, etc). Default da env LOG_LEVEL o INFO
        log_name: Nome del log in Cloud Logging
        console: Se True, logga anche su console
        local_file_path: Path per file log locale (se backend LOCAL o HYBRID)
        global_labels: Labels globali da aggiungere a tutti i log
        
    Environment Variables:
        LOG_BACKEND: "cloud", "local", o "hybrid" (override backend parameter)
        LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        GCP_PROJECT_ID: Project ID per Cloud Logging
        ENVIRONMENT: Environment name (development, staging, production)
        
    Example:
        # Production (Cloud Logging)
        setup_cloud_logging(backend=LoggingBackend.CLOUD, level="INFO")
        
        # Development (Local file)
        setup_cloud_logging(backend=LoggingBackend.LOCAL, level="DEBUG")
        
        # Hybrid (entrambi)
        setup_cloud_logging(backend=LoggingBackend.HYBRID)
    """
    # Determina backend da usare
    backend_str = os.getenv("LOG_BACKEND", "").lower()
    if backend_str:
        try:
            backend = LoggingBackend(backend_str)
        except ValueError:
            pass
    elif isinstance(backend, str):
        backend = LoggingBackend(backend.lower())
    
    # Determina log level
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    
    # Setup root logger
    root_logger = logging.getLogger()
    
    # Rimuovi handler esistenti
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    
    root_logger.setLevel(log_level)
    
    # Crea context filter
    context_filter = EnhancedContextFilter()
    
    # Aggiungi console handler se richiesto
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Formatter conciso per console
        console_formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)
    
    # Aggiungi Cloud Logging handler se richiesto
    if backend in (LoggingBackend.CLOUD, LoggingBackend.HYBRID):
        try:
            cloud_handler = CloudLoggingHandler(
                name=log_name,
                labels=global_labels
            )
            if cloud_handler.enabled:
                cloud_handler.setLevel(log_level)
                cloud_handler.addFilter(context_filter)
                root_logger.addHandler(cloud_handler)
                
                # Log startup message
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Cloud Logging initialized",
                    extra={
                        "log_name": log_name,
                        "backend": backend.value,
                        "resource_type": cloud_handler.resource.type if cloud_handler.resource else "unknown"
                    }
                )
            else:
                sys.stderr.write("Warning: Cloud Logging handler not enabled, using fallback\n")
                # Fallback a local se cloud non disponibile
                backend = LoggingBackend.LOCAL
        except Exception as e:
            sys.stderr.write(f"Error setting up Cloud Logging: {e}\n")
            # Fallback a local se cloud fallisce
            backend = LoggingBackend.LOCAL
    
    # Aggiungi file handler locale se richiesto
    if backend in (LoggingBackend.LOCAL, LoggingBackend.HYBRID):
        try:
            from pythonjsonlogger.json import JsonFormatter
            
            file_path = local_file_path or os.getenv("LOG_FILE_PATH", "backend.jsonl")
            
            # Crea directory se non esiste
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # File handler con JSON formatter
            file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            file_handler.setLevel(log_level)
            
            json_formatter = JsonFormatter(
                fmt=(
                    "%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(request_id)s %(job_id)s %(trace_id)s "
                    "%(pathname)s %(lineno)d %(error_chain)s"
                ),
                json_ensure_ascii=False
            )
            file_handler.setFormatter(json_formatter)
            file_handler.addFilter(context_filter)
            root_logger.addHandler(file_handler)
            
        except ImportError:
            sys.stderr.write(
                "Warning: python-json-logger not available. "
                "Using standard file logging.\n"
            )
            # Fallback a standard file handler
            file_path = local_file_path or "backend.log"
            file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s [%(request_id)s]: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(context_filter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Error setting up file logging: {e}\n")
    
    # Capture warnings
    logging.captureWarnings(True)


def log_error_chain(error_context: str) -> None:
    """
    Aggiunge contesto alla catena di errori per tracking cascading errors.
    
    Args:
        error_context: Descrizione del contesto dell'errore
    """
    try:
        current_chain = error_chain_var.get()
    except LookupError:
        current_chain = []
    
    current_chain = list(current_chain)  # Copy
    current_chain.append(error_context)
    error_chain_var.set(current_chain[-5:])  # Keep last 5


def clear_error_chain() -> None:
    """Pulisce la catena di errori (chiamare all'inizio di nuove operazioni)."""
    error_chain_var.set([])


def set_request_context(request_id: str, trace_id: Optional[str] = None) -> None:
    """
    Imposta context per una request.
    
    Args:
        request_id: ID univoco della request
        trace_id: Trace ID per Cloud Trace integration (opzionale)
    """
    request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)
    clear_error_chain()


def set_job_context(job_id: str) -> None:
    """
    Imposta context per un job.
    
    Args:
        job_id: ID univoco del job
    """
    job_id_var.set(job_id)
    clear_error_chain()


def clear_context() -> None:
    """Pulisce tutti i context variables."""
    request_id_var.set("-")
    job_id_var.set("-")
    trace_id_var.set("-")
    clear_error_chain()


class ErrorLogger:
    """
    Utility class per enhanced error logging con Cloud Logging integration.
    
    Compatibile con ErrorLogger esistente per backward compatibility.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Inizializza ErrorLogger.
        
        Args:
            logger: Logger instance da usare
        """
        self.logger = logger
    
    def log_exception(
        self,
        operation: str,
        exc: Exception,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Logga exception con enhanced context e chain tracking.
        
        Args:
            operation: Nome dell'operazione
            exc: Exception da loggare
            extra: Context aggiuntivo
        """
        log_error_chain(f"{operation}: {type(exc).__name__}")
        
        extra_info = {
            "operation": operation,
            "exception_type": type(exc).__name__,
            "exception_module": type(exc).__module__,
            **(extra or {})
        }
        
        self.logger.exception(
            f"Error in {operation}: {exc}",
            extra=extra_info,
            exc_info=True
        )
    
    def log_error(
        self,
        operation: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Logga error senza exception traceback.
        
        Args:
            operation: Nome dell'operazione
            message: Messaggio di errore
            extra: Context aggiuntivo
        """
        log_error_chain(f"{operation}: {message}")
        
        extra_info = {
            "operation": operation,
            **(extra or {})
        }
        
        self.logger.error(
            f"Error in {operation}: {message}",
            extra=extra_info
        )
    
    def clear_chain(self) -> None:
        """Pulisce error chain."""
        clear_error_chain()


def get_error_logger(name: str) -> ErrorLogger:
    """
    Ottiene ErrorLogger per un modulo.
    
    Args:
        name: Nome del modulo
        
    Returns:
        ErrorLogger instance
    """
    return ErrorLogger(logging.getLogger(name))

