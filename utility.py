import re
import os
from datetime import datetime
import logging
import random
import traceback
import asyncio
from functools import wraps
from typing import List
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import AutoTokenizer

from config import BASE_FOLDER_RICETTE, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_tokenizer_cache = {}

# Sanificazione iniziale del testo
def sanitize_text(text):
    # Rimuove emoji, simboli non ASCII e hashtag
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'#\w+', '', text)  # Rimuove hashtag
    text = re.sub(r'@[\w]+', '', text)  # Rimuove menzioni
    text = text.strip()
    return text

def sanitize_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c.isspace()).strip()

def sanitize_folder_name(folder_name: str) -> str:
    # Sostituisce i caratteri non validi con un carattere di sottolineatura
    return re.sub(r'[<>:"/\\|?*]', '_', folder_name)

def is_number(value):
    """Verifica se il valore è un numero."""
    try:
        float(str(value))
        return True
    except (ValueError, TypeError):
        return False
    
def create_date_folder() -> str:
    """Crea una cartella con la data odierna se non esiste già."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(BASE_FOLDER_RICETTE, today)
    os.makedirs(date_folder, exist_ok=True)
    return date_folder

def rename_files(video_folder,file_name:str):
    # Check if the folder exists
    if not os.path.exists(video_folder):
        error_context = get_error_context()
        logger.error(f"Cannot rename files: folder {video_folder} does not exist - {error_context}")
        return ""
        
    # Rinominare tutti i file nella cartella video_folder_new mantenendo l'estensione originale
    try:
        for filename in os.listdir(video_folder):
            old_file_path = os.path.join(video_folder, filename)
            name, ext = os.path.splitext(filename)  # Separare nome ed estensione
            new_file_path = os.path.join(video_folder, f"{file_name}{ext}")
            os.rename(old_file_path, new_file_path)
        return ""
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Error renaming files in {video_folder}: {e} - {error_context}")
        return ""

def rename_folder(percorso_vecchio: str, nuovo_nome: str) -> bool:
    """
    Rinomina una cartella in modo sicuro.
    
    Args:
        percorso_vecchio: Percorso completo della cartella da rinominare
        nuovo_nome: Nuovo nome della cartella
        
    Returns:
        bool: True se il rinominamento è avvenuto con successo, False altrimenti
    """
    try:
        if not os.path.exists(percorso_vecchio):
            error_context = get_error_context()
            logger.error(f"La cartella {percorso_vecchio} non esiste - {error_context}")
            return percorso_vecchio
            
        cartella_base = os.path.dirname(percorso_vecchio)
        percorso_nuovo = os.path.join(cartella_base, nuovo_nome)
        
        if os.path.exists(percorso_nuovo):
            error_context = get_error_context()
            logger.error(f"Esiste già una cartella chiamata {nuovo_nome} - {error_context}")
            percorso_nuovo = percorso_nuovo+"_"+str(random.randint(0,100)) 
        os.rename(percorso_vecchio, percorso_nuovo)
        logger.info(f"Cartella rinominata da {percorso_vecchio} a {percorso_nuovo}")
        return percorso_nuovo
        
    except OSError as e:
        error_context = get_error_context()
        logger.error(f"Errore durante il rinominamento della cartella: {e} - {error_context}")
        return percorso_vecchio

def get_error_context():
    """Get the current file, line number and function name where the error occurred"""
    stack = traceback.extract_stack()
    if len(stack) > 1:
        frame = stack[-2]
        return f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}"
    return ""

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                message = f"Timeout dopo {seconds} secondi nella funzione {func.__name__}"
                logger.error(message)
                raise TimeoutError(message)
        return wrapper
    return decorator
 
def parse_ingredients(ingredients_str: str) -> List[str]:
    """Converte la stringa di ingredienti in lista"""
    if not ingredients_str:
        return []
    return [ing.strip() for ing in ingredients_str.split(",")]

# Funzione per pulire il testo
def clean_text(text):
    # Converti in minuscolo e rimuovi caratteri speciali
    text = re.sub(r'[^\w\s]', ' ', (text or '').lower())
    # Tokenizza e rimuovi stop words con fallback se risorse NLTK mancano
    try:
        tokens = word_tokenize(text)
        try:
            stop_words = set(stopwords.words('italian'))
        except LookupError:
            # Fallback: lista minima di stopwords italiane
            stop_words = { 'e', 'ed', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'che', 'del', 'della', 'dei', 'delle' }
        filtered_tokens = [word for word in tokens if word not in stop_words]
        return ' '.join(filtered_tokens)
    except LookupError:
        # Se manca anche il tokenizer, fallback basato su split semplice
        tokens = (text or '').split()
        filtered_tokens = tokens
        return ' '.join(filtered_tokens)

def _get_embedding_tokenizer_and_max(model_name: str):
    cached = _tokenizer_cache.get(model_name)
    if cached:
        return cached
    try:
        tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        max_len = getattr(tok, "model_max_length", None)
        # Alcuni tokenizer usano un sentinella enorme per "nessun limite"
        if not isinstance(max_len, int) or max_len is None or max_len > 100000:
            max_len = tok.max_model_input_sizes.get(getattr(tok, "name_or_path", model_name), None)
        if not isinstance(max_len, int) or max_len is None or max_len > 100000:
            max_len = 512
        _tokenizer_cache[model_name] = (tok, int(max_len))
        return tok, int(max_len)
    except Exception as e:
        # In caso di errore, fallback conservativo
        logger.error(f"Impossibile inizializzare tokenizer per modello '{model_name}': {str(e)}", exc_info=True)
        return None, 512

def ensure_text_within_token_limit(text: str) -> str:
    model_name = EMBEDDING_MODEL
    tok, max_len = _get_embedding_tokenizer_and_max(model_name)
    if tok is None:
        return text
    try:
        try:
            special_tokens = tok.num_special_tokens_to_add(pair=False)
        except Exception:
            special_tokens = 0
        effective_max = max(8, int(max_len) - int(special_tokens or 0))
        input_ids = tok.encode(text, add_special_tokens=False)
        if len(input_ids) <= effective_max:
            return text
        truncated_ids = input_ids[:effective_max]
        truncated_text = tok.decode(truncated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        logger.warning(
            f"Testo per embedding eccede il limite di {max_len} token del modello '{model_name}'. "
            f"Troncato a {effective_max} token effettivi. Lunghezza originale: {len(input_ids)}"
        )
        return truncated_text
    except Exception as e:
        logger.error(f"Errore nel controllo/troncamento dei token per embedding: {str(e)}", exc_info=True)
        return text
