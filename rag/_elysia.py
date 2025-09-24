"""
Modulo di integrazione con Weaviate/Elysia per Smart Recipe.

Gestisce l'indicizzazione e la ricerca semantica delle ricette
utilizzando Weaviate come vector database e Elysia per il preprocessing
avanzato e la ricerca con AI.

Author: Smart Recipe Team
Version: 0.8 - Fixed async issues
"""

from typing import Any, Tuple
import asyncio
import logging
import concurrent.futures
from functools import wraps

# Import configurazione
from config import (
    WCD_URL,
    WCD_API_KEY,
    WCD_COLLECTION_NAME,
    OPENAI_API_KEY
)

# Import utility e modelli
from utility.logging_config import get_error_logger

# Import Elysia SDK
from elysia import (
    configure,
    preprocess,
    preprocessed_collection_exists,
    Tree
)

# Inizializza logger
error_logger = get_error_logger(__name__)

def run_in_executor(func):
    """
    Decorator per eseguire funzioni Elysia in un thread separato
    per evitare conflitti con l'event loop di FastAPI.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Verifica se siamo in un event loop
            loop = asyncio.get_running_loop()
            # Esegui in un thread separato
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(func, *args, **kwargs)
                return future.result()
        except RuntimeError:
            # Non siamo in un event loop, esegui direttamente
            return func(*args, **kwargs)
    return wrapper

@run_in_executor
def _configure_elysia():
    """Configura Elysia in modo thread-safe."""
    try:
        configure(
            wcd_url=WCD_URL,
            wcd_api_key=WCD_API_KEY,
            base_model="gpt-4o",
            base_provider="openai",
            complex_model="gpt-4o",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )
        return True
    except Exception as e:
        logging.error(f"❌ Errore configurazione Elysia: {e}")
        return False

@run_in_executor
def _check_collection_exists():
    """Verifica se la collection è preprocessata in modo thread-safe."""
    try:
        return preprocessed_collection_exists(WCD_COLLECTION_NAME)
    except Exception as e:
        logging.error(f"❌ Errore verifica collection: {e}")
        return False

@run_in_executor
def _preprocess_collection(collection_name: str):
    """Preprocessa la collection in modo thread-safe."""
    try:
        logging.info("🔄 Avvio preprocessing collection...")
        preprocess(collection_name)
        logging.info("✅ Preprocessing completato con successo")
        return True
    except Exception as e:
        logging.error(f"❌ Errore preprocessing collection: {e}")
        return False

@run_in_executor
def _search_with_tree(query: str, collection_name: str):
    """Esegue ricerca con Elysia Tree in modo thread-safe."""
    try:
        tree = Tree()
        risposta, oggetti = tree(
            query,
            collection_names=[collection_name]
        )
        return risposta, oggetti
    except Exception as e:
        logging.error(f"❌ Errore ricerca con Tree: {e}")
        return None, None

def search_recipes_elysia(query: str, limit: int = 10) -> Tuple[Any, Any]:
    """
    Esegue ricerca semantica delle ricette usando Elysia.
    
    Utilizza l'AI di Elysia per interpretare la query e trovare
    le ricette più rilevanti basandosi sulla similarità semantica.
    
    Args:
        query: Testo di ricerca in linguaggio naturale
        limit: Numero massimo di risultati da restituire
        
    Returns:
        tuple: (risposta_testuale, oggetti_ricette) o (None, None) in caso di errore
    """
    try:
        # 1. Configura Elysia
        if not _configure_elysia():
            logging.error("❌ Impossibile configurare Elysia")
            return None, None

        # 2. Verifica se la collection esiste e è preprocessata
        if not _check_collection_exists():
            logging.info("🔄 Collection non preprocessata, avvio preprocessing...")
            #if not _preprocess_collection():
                #logging.error("❌ Impossibile preprocessare la collection")
                #return None, None

        # 3. Esegue ricerca con Elysia Tree
        risposta, oggetti = _search_with_tree(query, WCD_COLLECTION_NAME)
        
        if oggetti is None:
            logging.warning("⚠️ Nessun risultato dalla ricerca Elysia")
            return None, []
        
        # Limita i risultati se necessario
        if limit and len(oggetti) > limit:
            oggetti = oggetti[:limit]
            
        logging.info(f"✅ Ricerca Elysia completata: {len(oggetti)} risultati")
        return risposta, oggetti

    except Exception as e:
        # Log errore ricerca
        error_logger.log_exception("search_recipe_elysia", e, {
            "query": query[:100],  # Log solo primi 100 caratteri query
            "limit": limit
        })
        logging.error(f"❌ Errore generale in search_recipes_elysia: {e}")
        return None, None
