"""
Modulo di utility per Smart Recipe.

Contiene funzioni di supporto per:
- Sanitizzazione testo e nomi file
- Normalizzazione stringhe
- Gestione token per embeddings
- Processing linguistico con spaCy

Author: Smart Recipe Team
Version: 0.7
"""

import re
import os
import traceback
import asyncio
import unicodedata
from functools import wraps

# Import librerie NLP
from transformers import AutoTokenizer
import spacy

# Import configurazione e logging
from config import BASE_FOLDER_RICETTE, EMBEDDING_MODEL
from logging_config import get_error_logger

# Inizializzazioni
error_logger = get_error_logger(__name__)
_tokenizer_cache = {}  # Cache per tokenizer
nlp_it = spacy.load("it_core_news_lg")

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

def nfkc(s: str) -> str:
    """
    Normalizza una stringa usando NFKC.
    
    Applica:
    - Normalizzazione Unicode NFKC
    - Conversione in minuscolo (casefold)
    - Rimozione spazi multipli
    
    Args:
        s: Stringa da normalizzare
        
    Returns:
        Stringa normalizzata
    """
    s = unicodedata.normalize("NFKC", s)
    s = s.casefold().strip()
    s = re.sub(r"\s+", " ", s)  # Collassa spazi multipli
    return s

def normalize_text(txt: str) -> str:
    doc = nlp_it(txt)
    # Lemmatize tokens
    lemma_list = [token.lemma_ for token in doc]
    # Remove stop words
    filtered_sentence = [word for word in lemma_list if not nlp_it.vocab[word].is_stop]
    # Remove punctuations
    punctuations = "?:!.,;"
    filtered_sentence = [word for word in filtered_sentence if word not in punctuations]
    return filtered_sentence

def remove_stopwords_spacy(text: str) -> str:
    """
    Rimuove le stop words italiane usando spaCy.
    
    Filtra token che sono:
    - Stop words (articoli, preposizioni, etc.)
    - Punteggiatura
    - Spazi
    
    Args:
        text: Testo da processare
        
    Returns:
        Testo senza stop words
    """
    doc = nlp_it(text)
    tokens = [
        token.text for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space
    ]
    return " ".join(tokens)
    
def lemmatize_it(token: str) -> list[str]:
    """
    Lemmatizza un token italiano.
    
    Converte le parole nella loro forma base (lemma).
    
    Args:
        token: Token da lemmatizzare
        
    Returns:
        Lista di lemmi in minuscolo
    """
    doc = nlp_it(token)
    return [t.lemma_.casefold() for t in doc]

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
 
def _get_embedding_tokenizer_and_max(model_name: str) -> tuple:
    """
    Ottiene tokenizer e lunghezza massima per un modello.
    
    Usa cache per evitare re-inizializzazioni.
    
    Args:
        model_name: Nome del modello di embedding
        
    Returns:
        Tupla (tokenizer, max_length) o (None, 512) se errore
    """
    # Controlla cache
    cached = _tokenizer_cache.get(model_name)
    if cached:
        return cached
    
    try:
        # Carica tokenizer
        tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        max_len = getattr(tok, "model_max_length", None)
        
        # Gestisce valori sentinella per "nessun limite"
        if not isinstance(max_len, int) or max_len is None or max_len > 100000:
            max_len = tok.max_model_input_sizes.get(
                getattr(tok, "name_or_path", model_name), None
            )
        if not isinstance(max_len, int) or max_len is None or max_len > 100000:
            max_len = 512  # Default conservativo
        
        # Salva in cache
        _tokenizer_cache[model_name] = (tok, int(max_len))
        return tok, int(max_len)
    except Exception as e:
        # Fallback su errore
        error_logger.log_exception("tokenizer_init", e, {"model_name": model_name})
        return None, 512

def ensure_text_within_token_limit(text: str) -> str:
    """
    Assicura che il testo rientri nei limiti token del modello.
    
    Tronca il testo se supera il limite massimo di token
    supportato dal modello di embedding.
    
    Args:
        text: Testo da verificare/troncare
        
    Returns:
        Testo eventualmente troncato
    """
    model_name = EMBEDDING_MODEL
    tok, max_len = _get_embedding_tokenizer_and_max(model_name)
    
    if tok is None:
        return text
    
    try:
        # Calcola token speciali
        try:
            special_tokens = tok.num_special_tokens_to_add(pair=False)
        except Exception:
            special_tokens = 0
        
        # Calcola limite effettivo
        effective_max = max(8, int(max_len) - int(special_tokens or 0))
        
        # Tokenizza e verifica lunghezza
        input_ids = tok.encode(text, add_special_tokens=False)
        if len(input_ids) <= effective_max:
            return text
        
        # Tronca se necessario
        truncated_ids = input_ids[:effective_max]
        truncated_text = tok.decode(
            truncated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        # Log warning per debug
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Testo troncato - Original: {len(input_ids)} tokens, "
            f"Truncated: {effective_max} tokens, Model: {model_name}"
        )
        
        return truncated_text
    except Exception as e:
        error_logger.log_exception("token_check", e, {"model_name": model_name})
        return text

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
