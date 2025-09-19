"""
Modulo di integrazione con Weaviate/Elysia per Smart Recipe.

Gestisce l'indicizzazione e la ricerca semantica delle ricette
utilizzando Weaviate come vector database e Elysia per il preprocessing
avanzato e la ricerca con AI.

Author: Smart Recipe Team
Version: 0.7
"""

from typing import List, Dict, Any, Optional
import asyncio
import threading
import uuid as uuid_lib
import logging

# Import configurazione
from config import (
    WCD_URL,
    WCD_API_KEY,
    WCD_COLLECTION_NAME,
    OPENAI_API_KEY
)

# Import utility e modelli
from logging_config import get_error_logger

# Import Elysia SDK
from elysia import (
    configure,
    preprocess,
    preprocessed_collection_exists,
    Tree
)

# Inizializza logger
error_logger = get_error_logger(__name__)

def search_recipes_elysia(query: str, limit: int = 10) -> tuple[Any, Any]:
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
        # Configura connessione
        configure(
            wcd_url=WCD_URL,
            wcd_api_key=WCD_API_KEY,
            base_model="gpt-4.1",
            base_provider="openai",
            complex_model="gpt-4.1",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )

        # Verifica preprocessing collection in modo compatibile con uvloop
        def _exists_sync() -> bool:
            try:
                return preprocessed_collection_exists(WCD_COLLECTION_NAME)
            except Exception:
                return False

        exists: bool = False
        try:
            asyncio.get_running_loop()
            res: Dict[str, Any] = {}
            def _check():
                res["exists"] = _exists_sync()
            t = threading.Thread(target=_check, daemon=True)
            t.start(); t.join()
            exists = bool(res.get("exists", False))
        except RuntimeError:
            exists = _exists_sync()

        if not exists:
            logging.info("Collection non preprocessata, avvio preprocessing...")
            def _run_preprocess_sync():
                try:
                    preprocess(WCD_COLLECTION_NAME)
                except Exception as _e:
                    logging.error(f"❌ Errore preprocessing collection (thread): {_e}")
            try:
                asyncio.get_running_loop()
                t = threading.Thread(target=_run_preprocess_sync, daemon=True)
                t.start(); t.join()
            except RuntimeError:
                preprocess(WCD_COLLECTION_NAME)

        # Esegue ricerca con Elysia Tree (AI search)
        tree = Tree()
        risposta, oggetti = tree(
            query,
            collection_names=[WCD_COLLECTION_NAME]
        )
        
        logging.info(f"✅ Ricerca completata: {len(oggetti) if oggetti else 0} risultati")
        return risposta, oggetti

    except Exception as e:
        # Log errore ricerca
        error_logger.log_exception("search_recipe_elysia", e, {
            "query": query[:100],  # Log solo primi 100 caratteri query
            "limit": limit
        })
        return None, None
