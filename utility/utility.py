"""
Modulo di utility per Smart Recipe.

Contiene funzioni di supporto per:
- Sanitizzazione testo e nomi file
- Normalizzazione stringhe
- Gestione token per embeddings
- Processing linguistico con spaCy

Author: Smart Recipe Team

"""

import re
import os
import traceback
import asyncio
from functools import wraps


from utility.cloud_logging_config import get_error_logger

# Inizializzazioni
error_logger = get_error_logger(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)
    
def sanitize_text(text: str) -> str:
    """
    Sanitizza il testo rimuovendo caratteri problematici.
    
    Rimuove:
    - Emoji e simboli non ASCII
    - Hashtag (#esempio)
    - Menzioni (@utente)
    
    Args:
        text: Testo da sanitizzare
        
    Returns:
        Testo pulito
    """
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Rimuove non-ASCII
    text = re.sub(r'#\w+', '', text)            # Rimuove hashtag
    text = re.sub(r'@[\w]+', '', text)          # Rimuove menzioni
    text = text.strip()
    return text

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza un nome file rimuovendo caratteri non validi.
    
    Mantiene solo caratteri alfanumerici e spazi.
    
    Args:
        filename: Nome file da sanitizzare
        
    Returns:
        Nome file sanitizzato
    """
    return "".join(c for c in filename if c.isalnum() or c.isspace()).strip()

def sanitize_folder_name(folder_name: str) -> str:
    """
    Sanitizza un nome cartella per filesystem.
    
    Sostituisce caratteri non validi per Windows/Unix con underscore.
    
    Args:
        folder_name: Nome cartella da sanitizzare
        
    Returns:
        Nome cartella sanitizzato
    """
    return re.sub(r'[<>:"/\\|?*]', '_', folder_name)

def get_error_context() -> str:
    """
    Ottiene il contesto dell'errore corrente.
    
    Estrae informazioni su file, linea e funzione
    dove si è verificato l'errore.
    
    Returns:
        Stringa con informazioni di contesto
    """
    stack = traceback.extract_stack()
    if len(stack) > 1:
        frame = stack[-2]
        return f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}"
    return ""

def timeout(seconds: int):
    """
    Decorator per timeout su funzioni asincrone.
    
    Interrompe l'esecuzione se supera il tempo limite.
    
    Args:
        seconds: Timeout in secondi
        
    Returns:
        Funzione decorata con timeout
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                message = f"Timeout dopo {seconds} secondi in {func.__name__}"
                error_logger.log_error(
                    "timeout",
                    message,
                    {"function": func.__name__, "timeout": seconds}
                )
                raise TimeoutError(message)
        return wrapper
    return decorator
 
# ===============================
# GESTIONE JOB E PROGRESSO
# ===============================

def extract_shortcode_from_url(url: str) -> str:
    """
    Estrae shortcode/ID da URL video di diverse piattaforme.
    
    Supporta:
    - Instagram (p/, reel/, tv/)
    - YouTube (v=, youtu.be/)
    - Altri URL (ultima parte del path)
    
    Args:
        url: URL video da analizzare
        
    Returns:
        Shortcode/ID estratto o "unknown" se non trovato
    """
    try:
        url_lower = url.lower()
        
        if "instagram.com" in url_lower:
            # Estrai shortcode da URL Instagram
            url_parts = url.split("/")
            for i_part, part in enumerate(url_parts):
                if part in ["p", "reel", "tv"] and i_part + 1 < len(url_parts):
                    return url_parts[i_part + 1]
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            # Estrai video ID da URL YouTube
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
        else:
            # Per altri URL, usa l'ultima parte del path
            return url.split("/")[-1].split("?")[0]
            
    except Exception:
        pass
    
    return "unknown"

def calculate_job_percentage(progress: dict, total: int) -> float:
    """
    Calcola la percentuale di completamento del job.
    
    Args:
        progress: Dizionario progresso con urls
        total: Numero totale URL da processare
        
    Returns:
        Percentuale calcolata (0-90% per fase URL)
    """
    try:
        url_entries = progress.get("urls") or []
        if total <= 0:
            return 0.0
        
        local_sum = sum(float(u.get("local_percent", 0.0)) for u in url_entries)
        # 0..90% per fase URL
        return round(min(90.0, (local_sum / (100.0 * max(1, total))) * 90.0), 2)
    except Exception:
        return float(progress.get("percentage", 0.0) or 0.0)

def create_progress_callback(progress: dict, url_index: int, total: int):
    """
    Crea callback per aggiornamento progresso URL.
    
    Args:
        progress: Dizionario progresso
        url_index: Indice URL corrente (0-based)
        total: Numero totale URL
        
    Returns:
        Funzione callback per aggiornamento progresso
    """
    def _callback(event: dict):
        try:
            stage = event.get("stage")
            local_percent = float(event.get("local_percent", 0.0))
            
            if 0 <= url_index < len(progress.get("urls", [])):
                url_entry = progress["urls"][url_index]
                
                # Aggiorna stato solo se non già completato
                if url_entry.get("status") not in ("success", "failed"):
                    url_entry["status"] = "running"
                
                if stage:
                    url_entry["stage"] = stage
                    
                url_entry["local_percent"] = local_percent
                
                # Gestisci errori
                if stage == "error" and "message" in event:
                    url_entry["error"] = str(event.get("message"))
                    url_entry["status"] = "failed"
                
                # Ricalcola percentuale totale
                progress["percentage"] = calculate_job_percentage(progress, total)
                
        except Exception:
            pass  # Non loggiamo errori minori di callback
    
    return _callback

def update_url_progress(progress: dict, url_index: int, status: str, stage: str = None, 
                       local_percent: float = None, error: str = None):
    """
    Aggiorna il progresso di un singolo URL.
    
    Args:
        progress: Dizionario progresso
        url_index: Indice URL (0-based)
        status: Nuovo stato URL
        stage: Fase corrente (opzionale)
        local_percent: Percentuale locale (opzionale)
        error: Messaggio errore (opzionale)
    """
    try:
        if 0 <= url_index < len(progress.get("urls", [])):
            url_entry = progress["urls"][url_index]
            url_entry["status"] = status
            
            if stage is not None:
                url_entry["stage"] = stage
            if local_percent is not None:
                url_entry["local_percent"] = local_percent
            if error is not None:
                url_entry["error"] = error
                
    except Exception:
        pass  # Non loggiamo errori minori di aggiornamento

def save_recipe_metadata(recipe_data, base_folder: str) -> bool:
    """
    Salva i metadati della ricetta in file JSON.
    
    Args:
        recipe_data: Oggetto ricetta con metadati
        base_folder: Cartella base per salvataggio
        
    Returns:
        True se salvato con successo, False altrimenti
    """
    try:
        import json
        filename = os.path.join(
            base_folder, 
            recipe_data.shortcode, 
            "media_original", 
            f"metadata_{recipe_data.shortcode}.json"
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recipe_data.model_dump(), f, indent=1, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        error_logger.log_exception("save_metadata", e, {"shortcode": recipe_data.shortcode})
        return False
