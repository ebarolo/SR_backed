"""
Configurazione centralizzata dei timeout per Smart Recipe.

Definisce timeout ottimizzati per diverse operazioni per migliorare
l'esperienza utente ed evitare hangs dell'applicazione.

Author: Smart Recipe Team
"""

import os
from typing import Dict

# Timeout base (secondi)
class TimeoutConfig:
    """Configurazione timeout per diverse operazioni."""
    
    # === AI/ML Operations ===
    # Analisi frames video - operazione rapida
    ANALYZE_FRAMES: int = 60  # 1 minuto (ridotto da 5 min)
    
    # Estrazione info ricetta - OpenAI API complessa
    EXTRACT_RECIPE_INFO: int = 120  # 2 minuti (ridotto da 3 min)
    
    # Trascrizione audio Whisper - dipende da lunghezza file
    WHISPER_TRANSCRIPTION: int = 180  # 3 minuti (ridotto da 5 min)
    
    # Generazione immagini - operazione costosa ma dovrebbe essere più rapida
    GENERATE_IMAGES: int = 90  # 1.5 minuti (ridotto da 5 min)
    
    # === Network Operations ===
    # Download video standard
    VIDEO_DOWNLOAD: int = 300  # 5 minuti (appropriato per video grandi)
    
    # HTTP requests generici
    HTTP_REQUEST: int = 30  # 30 secondi
    
    # === Database Operations ===
    # Operazioni batch database
    DB_BATCH_OPERATION: int = 60  # 1 minuto
    
    # Query singole database
    DB_SINGLE_QUERY: int = 15  # 15 secondi
    
    # === File Operations ===
    # FFmpeg audio extraction
    FFMPEG_AUDIO_EXTRACTION: int = 120  # 2 minuti
    
    # File I/O operations
    FILE_IO: int = 30  # 30 secondi
    
    @classmethod
    def get_all_timeouts(cls) -> Dict[str, int]:
        """Ritorna tutti i timeout configurati."""
        return {
            attr: getattr(cls, attr) 
            for attr in dir(cls) 
            if not attr.startswith('_') and isinstance(getattr(cls, attr), int)
        }
    
    @classmethod
    def get_timeout_for_operation(cls, operation: str) -> int:
        """
        Ottiene timeout per operazione specifica.
        
        Args:
            operation: Nome dell'operazione
            
        Returns:
            Timeout in secondi, default 60 se non trovato
        """
        operation_upper = operation.upper()
        return getattr(cls, operation_upper, 60)
    
    @classmethod
    def adjust_for_file_size(cls, base_timeout: int, file_size_mb: float) -> int:
        """
        Aggiusta timeout basato sulla dimensione del file.
        
        Args:
            base_timeout: Timeout base in secondi
            file_size_mb: Dimensione file in MB
            
        Returns:
            Timeout aggiustato
        """
        if file_size_mb <= 10:
            return base_timeout
        elif file_size_mb <= 50:
            return int(base_timeout * 1.5)
        elif file_size_mb <= 100:
            return int(base_timeout * 2)
        else:
            return int(base_timeout * 3)
    
    @classmethod
    def get_progressive_timeout(cls, attempt: int, base_timeout: int) -> int:
        """
        Calcola timeout progressivo per retry.
        
        Args:
            attempt: Numero tentativo (1-based)
            base_timeout: Timeout base
            
        Returns:
            Timeout aggiustato per il tentativo
        """
        if attempt <= 1:
            return base_timeout
        elif attempt == 2:
            return int(base_timeout * 1.5)
        else:
            return int(base_timeout * 2)


# Environment override support
def load_timeout_from_env() -> None:
    """Carica override timeout da variabili d'ambiente."""
    for attr_name in dir(TimeoutConfig):
        if not attr_name.startswith('_') and isinstance(getattr(TimeoutConfig, attr_name), int):
            env_var = f"TIMEOUT_{attr_name}"
            env_value = os.getenv(env_var)
            if env_value and env_value.isdigit():
                setattr(TimeoutConfig, attr_name, int(env_value))


# Carica override all'import
load_timeout_from_env()


# Timeout context per debugging
class TimeoutContext:
    """Context manager per tracking timeout operations."""
    
    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            import time
            elapsed = time.time() - self.start_time
            
            # Log se operazione è stata vicina al timeout
            if elapsed > (self.timeout_seconds * 0.8):
                import logging
                logging.getLogger(__name__).warning(
                    f"Operation '{self.operation}' took {elapsed:.1f}s "
                    f"(timeout was {self.timeout_seconds}s)"
                )
