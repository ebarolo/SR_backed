import re
import os
import logging
import traceback
import asyncio
from functools import wraps
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
