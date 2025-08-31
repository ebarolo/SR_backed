import re
import os
import traceback
import asyncio
from functools import wraps
from transformers import AutoTokenizer
import spacy
import unicodedata

from config import BASE_FOLDER_RICETTE, EMBEDDING_MODEL

from logging_config import get_error_logger

error_logger = get_error_logger(__name__)

_tokenizer_cache = {}

nlp_it = spacy.load("it_core_news_lg") 

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

def nfkc(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.casefold().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def remove_stopwords_spacy(text: str) -> str:
    """Rimuove le stop words italiane usando Spacy"""
    doc = nlp_it(text)
    # Filtra token che non sono stop words, punteggiatura o spazi
    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct and not token.is_space]
    return " ".join(tokens)
    
def lemmatize_it(token: str):
    doc = nlp_it(token)
    return [t.lemma_.casefold() for t in doc]

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
                error_logger.log_error("timeout", message, {"function": func.__name__, "timeout": seconds})
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
        error_logger.log_exception("tokenizer_init", e, {"model_name": model_name})
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
        
        # Log del troncamento per debug
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Testo troncato per limiti token - Original: {len(input_ids)} tokens, Truncated: {effective_max} tokens, Model: {model_name}")
        
        return truncated_text
    except Exception as e:
        error_logger.log_exception("token_check", e, {"model_name": model_name})
        return text
