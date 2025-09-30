"""
FastAPI Middleware per Google Cloud Logging integration.

Implementa:
- Automatic request/trace context propagation
- Request/response logging
- Performance monitoring
- Error tracking con Cloud Error Reporting

Author: Smart Recipe Team
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utility.cloud_logging_config import (
    set_request_context,
    clear_context,
    request_id_var,
    trace_id_var
)


class CloudLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware per integrare Cloud Logging con FastAPI.
    
    Features:
    - Genera e propaga request_id e trace_id
    - Logga tutte le request/response
    - Traccia performance metrics
    - Integra con Cloud Trace per distributed tracing
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_requests: bool = True,
        log_responses: bool = True,
        exclude_paths: list[str] = None
    ):
        """
        Inizializza middleware.
        
        Args:
            app: ASGI application
            log_requests: Se True, logga tutte le request
            log_responses: Se True, logga tutte le response
            exclude_paths: Lista di path da escludere dal logging (es. /health)
        """
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
    
    def _extract_trace_id(self, request: Request) -> str:
        """
        Estrae trace ID da Google Cloud Trace header o genera uno nuovo.
        
        Google Cloud Trace usa l'header: X-Cloud-Trace-Context
        Formato: TRACE_ID/SPAN_ID;o=TRACE_TRUE
        
        Args:
            request: FastAPI Request
            
        Returns:
            Trace ID string
        """
        # Check per Cloud Trace header
        trace_header = request.headers.get("X-Cloud-Trace-Context")
        if trace_header:
            # Estrai solo TRACE_ID (prima del /)
            trace_id = trace_header.split("/")[0]
            return trace_id
        
        # Fallback: genera nuovo trace ID (32 caratteri hex)
        return uuid.uuid4().hex
    
    def _should_log(self, path: str) -> bool:
        """
        Determina se il path deve essere loggato.
        
        Args:
            path: Request path
            
        Returns:
            True se deve essere loggato
        """
        return not any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa request e response con logging.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response
        """
        # Genera request_id univoco
        request_id = str(uuid.uuid4())
        
        # Estrai o genera trace_id
        trace_id = self._extract_trace_id(request)
        
        # Imposta context per logging
        set_request_context(request_id, trace_id)
        
        # Aggiungi a request.state per accesso nei route handlers
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        
        # Inizio timing
        start_time = time.perf_counter()
        
        should_log = self._should_log(request.url.path)
        
        # Log request
        if self.log_requests and should_log:
            self.logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "http_request": {
                        "requestMethod": request.method,
                        "requestUrl": str(request.url),
                        "userAgent": request.headers.get("user-agent", ""),
                        "remoteIp": request.client.host if request.client else "unknown",
                        "referer": request.headers.get("referer", ""),
                    },
                    "request_id": request_id,
                    "trace_id": trace_id,
                }
            )
        
        # Processa request
        try:
            response = await call_next(request)
            
            # Fine timing
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            if self.log_responses and should_log:
                # Determina severity basato su status code
                if response.status_code >= 500:
                    log_level = logging.ERROR
                elif response.status_code >= 400:
                    log_level = logging.WARNING
                else:
                    log_level = logging.INFO
                
                self.logger.log(
                    log_level,
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "http_request": {
                            "requestMethod": request.method,
                            "requestUrl": str(request.url),
                            "status": response.status_code,
                            "latency": f"{duration_ms:.2f}ms",
                        },
                        "request_id": request_id,
                        "trace_id": trace_id,
                        "duration_ms": duration_ms,
                        "status_code": response.status_code,
                    }
                )
            
            # Aggiungi headers custom per trace tracking
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as exc:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            self.logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "http_request": {
                        "requestMethod": request.method,
                        "requestUrl": str(request.url),
                        "status": 500,
                        "latency": f"{duration_ms:.2f}ms",
                    },
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "duration_ms": duration_ms,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True
            )
            
            # Re-raise per permettere gestione standard
            raise
            
        finally:
            # Cleanup context (importante per async)
            clear_context()


class JobContextMiddleware:
    """
    Context manager per impostare job context nel logging.
    
    Usage:
        async with JobContextMiddleware(job_id):
            # Tutti i log qui avranno il job_id
            logger.info("Processing job")
    """
    
    def __init__(self, job_id: str):
        """
        Inizializza job context.
        
        Args:
            job_id: ID univoco del job
        """
        self.job_id = job_id
    
    def __enter__(self):
        """Imposta job context."""
        from utility.cloud_logging_config import set_job_context
        set_job_context(self.job_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pulisce job context."""
        from utility.cloud_logging_config import clear_context
        clear_context()
        return False  # Non sopprimere eccezioni
    
    async def __aenter__(self):
        """Async version di __enter__."""
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async version di __exit__."""
        return self.__exit__(exc_type, exc_val, exc_tb)


def get_request_context(request: Request) -> dict:
    """
    Ottiene context dalla request corrente.
    
    Args:
        request: FastAPI Request
        
    Returns:
        Dictionary con request_id e trace_id
    """
    return {
        "request_id": getattr(request.state, "request_id", "-"),
        "trace_id": getattr(request.state, "trace_id", "-"),
    }

