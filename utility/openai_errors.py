"""
Gestione errori OpenAI per Smart Recipe.

Definisce eccezioni custom e logica di retry intelligente
per API OpenAI (Whisper, GPT-4, DALL-E).

Author: Smart Recipe Team
"""

from typing import Optional, Dict, Any
from enum import Enum


class OpenAIErrorType(Enum):
    """Tipi di errori OpenAI."""
    QUOTA_EXCEEDED = "quota_exceeded"      # Quota esaurita
    RATE_LIMIT = "rate_limit"              # Troppi request
    INVALID_API_KEY = "invalid_api_key"    # API key non valida
    TIMEOUT = "timeout"                     # Timeout
    SERVER_ERROR = "server_error"           # Errore server OpenAI
    INVALID_REQUEST = "invalid_request"     # Richiesta non valida
    UNKNOWN = "unknown"                     # Errore sconosciuto


class OpenAIError(Exception):
    """
    Eccezione base per errori OpenAI.
    
    Fornisce informazioni dettagliate sull'errore e messaggi
    user-friendly per il frontend.
    """
    
    def __init__(
        self,
        message: str,
        error_type: OpenAIErrorType,
        user_message: str,
        operation: str,
        should_retry: bool = False,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Inizializza l'errore OpenAI.
        
        Args:
            message: Messaggio tecnico per logging
            error_type: Tipo di errore
            user_message: Messaggio user-friendly per il frontend
            operation: Operazione che ha causato l'errore
            should_retry: Se True, l'operazione può essere ritentata
            context: Informazioni aggiuntive di contesto
            original_error: Eccezione originale
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.user_message = user_message
        self.operation = operation
        self.should_retry = should_retry
        self.context = context or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte l'errore in dizionario per serializzazione."""
        return {
            "error_type": self.error_type.value,
            "message": self.user_message,
            "operation": self.operation,
            "should_retry": self.should_retry,
            "context": self.context
        }


class QuotaExceededError(OpenAIError):
    """Errore quando la quota OpenAI è esaurita."""
    
    def __init__(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Quota OpenAI esaurita durante {operation}",
            error_type=OpenAIErrorType.QUOTA_EXCEEDED,
            user_message=(
                "⚠️ Quota OpenAI esaurita. Verifica il tuo piano su "
                "https://platform.openai.com/account/billing e ricarica crediti."
            ),
            operation=operation,
            should_retry=False,  # Non fare retry su quota esaurita
            context=context,
            original_error=original_error
        )


class RateLimitError(OpenAIError):
    """Errore quando si superano i limiti di rate OpenAI."""
    
    def __init__(
        self,
        operation: str,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        ctx = context or {}
        if retry_after:
            ctx["retry_after_seconds"] = retry_after
            
        super().__init__(
            message=f"Rate limit OpenAI superato durante {operation}",
            error_type=OpenAIErrorType.RATE_LIMIT,
            user_message=(
                f"⚠️ Troppi request OpenAI. "
                f"{'Riprova tra ' + str(retry_after) + ' secondi.' if retry_after else 'Riprova più tardi.'}"
            ),
            operation=operation,
            should_retry=True,  # Può essere ritentato dopo attesa
            context=ctx,
            original_error=original_error
        )


class InvalidAPIKeyError(OpenAIError):
    """Errore quando l'API key OpenAI non è valida."""
    
    def __init__(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=f"API key OpenAI non valida durante {operation}",
            error_type=OpenAIErrorType.INVALID_API_KEY,
            user_message=(
                "❌ API key OpenAI non valida. Verifica la configurazione "
                "in config.py o nelle variabili d'ambiente."
            ),
            operation=operation,
            should_retry=False,
            context=context,
            original_error=original_error
        )


class ServerError(OpenAIError):
    """Errore server OpenAI (5xx)."""
    
    def __init__(
        self,
        operation: str,
        status_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        ctx = context or {}
        if status_code:
            ctx["status_code"] = status_code
            
        super().__init__(
            message=f"Errore server OpenAI durante {operation}",
            error_type=OpenAIErrorType.SERVER_ERROR,
            user_message=(
                "⚠️ Errore server OpenAI. Il servizio potrebbe essere "
                "temporaneamente non disponibile. Riprova tra qualche minuto."
            ),
            operation=operation,
            should_retry=True,
            context=ctx,
            original_error=original_error
        )


def classify_openai_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> OpenAIError:
    """
    Classifica un errore OpenAI e crea l'eccezione custom appropriata.
    
    Args:
        error: Eccezione originale
        operation: Operazione che ha causato l'errore
        context: Contesto aggiuntivo
        
    Returns:
        OpenAIError appropriata
    """
    error_str = str(error).lower()
    
    # Importa dinamicamente per evitare dipendenze circolari
    try:
        import openai
        
        # Quota esaurita (429 insufficient_quota)
        if isinstance(error, openai.RateLimitError):
            if "insufficient_quota" in error_str or "quota" in error_str:
                return QuotaExceededError(operation, context, error)
            else:
                # Rate limit ma non quota
                return RateLimitError(operation, context=context, original_error=error)
        
        # API key non valida (401)
        if isinstance(error, openai.AuthenticationError):
            return InvalidAPIKeyError(operation, context, error)
        
        # Errore server (5xx)
        if isinstance(error, (openai.InternalServerError, openai.APIError)):
            status_code = getattr(error, "status_code", None)
            return ServerError(operation, status_code, context, error)
        
        # Timeout
        if isinstance(error, openai.APITimeoutError):
            return OpenAIError(
                message=f"Timeout OpenAI durante {operation}",
                error_type=OpenAIErrorType.TIMEOUT,
                user_message="⚠️ Timeout richiesta OpenAI. L'operazione ha impiegato troppo tempo.",
                operation=operation,
                should_retry=True,
                context=context,
                original_error=error
            )
        
        # Request non valido (400)
        if isinstance(error, openai.BadRequestError):
            return OpenAIError(
                message=f"Richiesta non valida durante {operation}",
                error_type=OpenAIErrorType.INVALID_REQUEST,
                user_message="❌ Richiesta non valida. Verifica i parametri.",
                operation=operation,
                should_retry=False,
                context=context,
                original_error=error
            )
    
    except ImportError:
        pass
    
    # Errore generico
    return OpenAIError(
        message=f"Errore OpenAI durante {operation}: {error}",
        error_type=OpenAIErrorType.UNKNOWN,
        user_message=f"❌ Errore durante {operation}. Riprova più tardi.",
        operation=operation,
        should_retry=False,
        context=context,
        original_error=error
    )
