"""
Gestione standardizzata degli errori per Smart Recipe.

Fornisce decoratori e classi per gestire errori in modo consistente
attraverso tutta l'applicazione, con logging appropriato e retry logic.

Author: Smart Recipe Team
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Dict, Optional, Type, Union, List
from enum import Enum

from utility.cloud_logging_config import get_error_logger


class ErrorSeverity(Enum):
    """Livelli di severità degli errori."""
    LOW = "low"           # Errore recuperabile, operazione può continuare
    MEDIUM = "medium"     # Errore importante ma non critico
    HIGH = "high"         # Errore critico, operazione deve essere interrotta
    CRITICAL = "critical" # Errore sistemico, richiede attenzione immediata


class ErrorAction(Enum):
    """Azioni da intraprendere per diversi tipi di errori."""
    CONTINUE = "continue"       # Logga e continua
    RETRY = "retry"            # Logga e riprova
    RAISE = "raise"            # Logga e rilancia eccezione
    ABORT = "abort"            # Logga e interrompe operazione


class StandardError(Exception):
    """Eccezione standard con metadata estesi."""
    
    def __init__(
        self, 
        message: str, 
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        action: ErrorAction = ErrorAction.RAISE,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.severity = severity
        self.action = action
        self.context = context or {}
        self.original_error = original_error


class ErrorHandler:
    """Gestore centralizzato degli errori."""
    
    def __init__(self, module_name: str):
        self.logger = get_error_logger(module_name)
        self.module_name = module_name
    
    def handle_error(
        self,
        error: Exception,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        action: ErrorAction = ErrorAction.RAISE,
        context: Optional[Dict[str, Any]] = None,
        custom_message: Optional[str] = None
    ) -> None:
        """
        Gestisce un errore in modo standardizzato.
        
        Args:
            error: Eccezione da gestire
            operation: Nome dell'operazione che ha causato l'errore
            severity: Livello di severità
            action: Azione da intraprendere
            context: Informazioni aggiuntive di contesto
            custom_message: Messaggio personalizzato (opzionale)
        """
        message = custom_message or str(error)
        context = context or {}
        
        # Logga sempre l'errore
        self.logger.log_exception(operation, error, {
            "severity": severity.value,
            "action": action.value,
            "module": self.module_name,
            **context
        })
        
        # Azione basata su policy
        if action == ErrorAction.RAISE:
            if isinstance(error, StandardError):
                raise error
            raise StandardError(
                message=message,
                operation=operation,
                severity=severity,
                action=action,
                context=context,
                original_error=error
            )
        elif action == ErrorAction.ABORT:
            # Per errori critici che richiedono stop immediato
            raise SystemExit(f"CRITICAL ERROR in {operation}: {message}")
        # Per CONTINUE e RETRY, non rilancia l'eccezione
    
    def safe_execute(
        self,
        func: Callable,
        operation: str,
        *args,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        action: ErrorAction = ErrorAction.RAISE,
        context: Optional[Dict[str, Any]] = None,
        default_return: Any = None,
        **kwargs
    ) -> Any:
        """
        Esegue una funzione con gestione errori standardizzata.
        
        Args:
            func: Funzione da eseguire
            operation: Nome operazione per logging
            *args: Argomenti per la funzione
            severity: Livello severità errori
            action: Azione per errori
            context: Contesto aggiuntivo
            default_return: Valore di default se errore e action=CONTINUE
            **kwargs: Keyword arguments per la funzione
            
        Returns:
            Risultato della funzione o default_return se errore
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, operation, severity, action, context)
            return default_return
    
    async def safe_execute_async(
        self,
        func: Callable,
        operation: str,
        *args,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        action: ErrorAction = ErrorAction.RAISE,
        context: Optional[Dict[str, Any]] = None,
        default_return: Any = None,
        **kwargs
    ) -> Any:
        """Versione asincrona di safe_execute."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, operation, severity, action, context)
            return default_return


def standardize_error_handling(
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    action: ErrorAction = ErrorAction.RAISE,
    context: Optional[Dict[str, Any]] = None
):
    """
    Decorator per standardizzare la gestione errori in funzioni.
    
    Args:
        operation: Nome dell'operazione
        severity: Livello di severità
        action: Azione da intraprendere
        context: Contesto aggiuntivo
    """
    def decorator(func: Callable) -> Callable:
        handler = ErrorHandler(func.__module__)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await handler.safe_execute_async(
                    func, operation, *args,
                    severity=severity,
                    action=action,
                    context=context,
                    **kwargs
                )
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return handler.safe_execute(
                    func, operation, *args,
                    severity=severity,
                    action=action,
                    context=context,
                    **kwargs
                )
            return sync_wrapper
    
    return decorator


class BatchErrorHandler:
    """Gestore errori per operazioni batch."""
    
    def __init__(self, module_name: str):
        self.handler = ErrorHandler(module_name)
        self.errors = []
        self.successes = []
    
    def add_error(
        self,
        error: Exception,
        item_id: str,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ):
        """Aggiunge un errore alla lista senza interrompere il batch."""
        error_info = {
            "item_id": item_id,
            "error": error,
            "operation": operation,
            "severity": severity,
            "context": context or {}
        }
        self.errors.append(error_info)
        
        # Log immediato dell'errore
        self.handler.handle_error(
            error, operation, severity, ErrorAction.CONTINUE, 
            {**(context or {}), "item_id": item_id}
        )
    
    def add_success(self, item_id: str, result: Any = None):
        """Aggiunge un successo alla lista."""
        self.successes.append({"item_id": item_id, "result": result})
    
    def get_summary(self) -> Dict[str, Any]:
        """Ritorna un summary delle operazioni batch."""
        total = len(self.errors) + len(self.successes)
        return {
            "total": total,
            "successes": len(self.successes),
            "errors": len(self.errors),
            "success_rate": len(self.successes) / total if total > 0 else 0.0,
            "failed_items": [e["item_id"] for e in self.errors],
            "error_details": self.errors
        }
    
    def should_abort(self, error_threshold: float = 0.5) -> bool:
        """Determina se il batch dovrebbe essere interrotto."""
        total = len(self.errors) + len(self.successes)
        if total == 0:
            return False
        
        error_rate = len(self.errors) / total
        return error_rate >= error_threshold
    
    def clear(self):
        """Resetta contatori per nuovo batch."""
        self.errors.clear()
        self.successes.clear()
