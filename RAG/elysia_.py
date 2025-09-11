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
    ELYSIA_COLLECTION_NAME,
    OPENAI_API_KEY
)

# Import utility e modelli
from logging_config import get_error_logger
from utility import nfkc, remove_stopwords_spacy
from models import RecipeDBSchema

# Import Elysia SDK
from elysia import (
    configure,
    preprocess,
    preprocessed_collection_exists,
    Tree
)
from elysia.preprocessing.collection import (
    preprocessed_collection_exists_async,
)
from elysia.util.client import ClientManager

# Import Weaviate
import weaviate.classes.config as wvc

# Inizializza logger
error_logger = get_error_logger(__name__)


def add_recipes_elysia(recipe_data: List[RecipeDBSchema]) -> bool:
    """
    Aggiunge o aggiorna ricette nel database vettoriale Weaviate.
    
    Processa una lista di ricette, normalizza i dati, e li indicizza
    in Weaviate. Dopo l'inserimento, preprocessa la collection con Elysia
    per ottimizzare la ricerca semantica.
    
    Args:
        recipe_data: Lista di oggetti RecipeDBSchema da indicizzare
        
    Returns:
        bool: True se l'operazione ha successo, False altrimenti
    """
    try:
        # Configura connessione a Weaviate/Elysia
        configure(
            wcd_url=WCD_URL,
            wcd_api_key=WCD_API_KEY,
            base_model="gpt-5-mini",
            base_provider="openai",
            complex_model="gpt-5",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )
        status = False
        client_manager = ClientManager()

        with client_manager.connect_to_client() as client:
            # Verifica/crea collection in Weaviate
            if client.collections.exists(ELYSIA_COLLECTION_NAME):
                logging.info(f"Collection '{ELYSIA_COLLECTION_NAME}' già esistente")
            else:
                client.collections.create(ELYSIA_COLLECTION_NAME)
                logging.info(f"Collection '{ELYSIA_COLLECTION_NAME}' creata con successo")

            recipe_collection = client.collections.get(ELYSIA_COLLECTION_NAME)

            # Processa ogni ricetta
            for recipe in recipe_data:
                try:
                    # Normalizza e processa ingredienti (rimuove stopwords) -> lista di stringhe serializzabili
                    # N.B.: Weaviate non può serializzare oggetti Pydantic. Convertiamo in stringhe semplici.
                    # Formato: "{qt} {um} {name}" (es. "100 g pomodori")
                    ingredients_text: List[str] = []
                    if recipe.ingredients:
                        for ingredient in recipe.ingredients:
                            try:
                                normalized_name = nfkc(getattr(ingredient, 'name', '') or '')
                                cleaned_name = remove_stopwords_spacy(normalized_name)
                                qt = getattr(ingredient, 'qt', None)
                                um = getattr(ingredient, 'um', '') or ''
                                # Rappresentazione compatta della quantità, senza zeri superflui
                                qt_str = (
                                    (f"{float(qt):g}" if qt is not None else "").strip()
                                )
                                parts = [p for p in [qt_str, um.strip(), cleaned_name.strip()] if p]
                                ingredients_text.append(" ".join(parts))
                            except Exception:
                                # In caso di ingrediente malformato, fallback al semplice str()
                                try:
                                    ingredients_text.append(str(ingredient))
                                except Exception:
                                    pass
                    
                    # Normalizza categorie
                    cats_lem = []
                    for category in recipe.category:
                        normalized_cat = nfkc(category)
                        cleaned_cat = remove_stopwords_spacy(normalized_cat)
                        cats_lem.append(cleaned_cat)

                    # Crea testo strutturato per embedding
                    document_text = (
                        f"Titolo: {recipe.title}\n"
                        f"Descrizione: {recipe.description}\n"
                        f"Ingredienti: {'; '.join(ingredients_text)}\n"
                        f"Categoria: {'; '.join(cats_lem)}\n"
                    )

                    # Prepara oggetto per Weaviate
                    recipe_object = {
                        "title": recipe.title,
                        "description": recipe.description,
                        # Importante: usare tipi nativi JSON (stringhe) per Weaviate
                        "ingredients": ingredients_text,
                        "category": cats_lem,
                        "cuisine_type": recipe.cuisine_type or "",
                        "diet": recipe.diet or "",
                        "technique": recipe.technique or "",
                        "language": recipe.language,
                        "shortcode": recipe.shortcode,
                        "cooking_time": recipe.cooking_time or 0,
                        "preparation_time": recipe.preparation_time or 0,
                        "chef_advise": recipe.chef_advise or "",
                        "tags": recipe.tags or [],
                        "nutritional_info": recipe.nutritional_info or [],
                        "recipe_step": recipe.recipe_step
                    }
                    
                    # Genera UUID deterministico dal shortcode per evitare duplicati
                    recipe_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, recipe.shortcode))
                    logging.debug(f"Recipe {recipe.shortcode}: UUID = {recipe_uuid}")
                    
                    # Verifica esistenza e aggiorna/inserisce
                    exists = recipe_collection.data.exists(recipe_uuid)
                    
                    if exists:
                        # Aggiorna ricetta esistente
                        recipe_collection.data.update(recipe_uuid, recipe_object)
                        logging.info(f"✅ Ricetta {recipe.shortcode} aggiornata")
                    else:
                        # Inserisce nuova ricetta
                        recipe_collection.data.insert(recipe_object)
                        logging.info(f"✅ Ricetta {recipe.shortcode} inserita")
                    
                except Exception as e:
                    # Log errore per singola ricetta (non blocca le altre)
                    logging.error(f"❌ Errore inserimento ricetta {recipe.shortcode}: {str(e)}")
                    error_logger.log_exception("add_recipe_elysia", e, {
                        "shortcode": recipe.shortcode,
                        "title": recipe.title,
                        "ingredients_count": len(recipe.ingredients) if recipe.ingredients else 0,
                        "categories_count": len(recipe.category) if recipe.category else 0
                    })
            
            # Preprocessa collection con Elysia per ottimizzare ricerca
            # Nota: il wrapper sincrono di Elysia usa nest_asyncio e fallisce con uvloop.
            # Se c'è un loop in esecuzione, eseguiamo il preprocess in un thread separato.
            def _run_preprocess_sync():
                try:
                    preprocess(ELYSIA_COLLECTION_NAME)
                except Exception as _e:
                    logging.error(f"❌ Errore preprocessing collection (thread): {_e}")

            try:
                asyncio.get_running_loop()
                t = threading.Thread(target=_run_preprocess_sync, daemon=True)
                t.start()
                t.join()
            except RuntimeError:
                # Nessun loop attivo: possiamo chiamare direttamente
                preprocess(ELYSIA_COLLECTION_NAME)

            logging.info(f"✅ Collection preprocessata con Elysia")
            status = True
    except Exception as e:
        # Log errore generale
        logging.error(f"❌ Errore preprocessing collection: {str(e)}")
        error_logger.log_exception("add_recipes_elysia", e, {})
        status = False
    finally:
        # Chiude connessione Weaviate per evitare ResourceWarning
        try:
            # Se possibile chiudiamo il client sincrono usato nel contesto
            # Nota: il context manager di ClientManager non chiude automaticamente il client
            with client_manager.connect_to_client() as client:
                try:
                    client.close()
                except Exception:
                    pass
        except Exception:
            pass
        # Proviamo anche a chiudere i client gestiti dal manager (best-effort)
        try:
            # Evita problemi con loop attivo: esegui in thread separato
            def _close_clients():
                try:
                    import asyncio as _a
                    _a.run(client_manager.close_clients())
                except Exception:
                    pass
            th = threading.Thread(target=_close_clients, daemon=True)
            th.start()
            th.join(timeout=2)
        except Exception:
            pass
        return status


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
                return preprocessed_collection_exists(ELYSIA_COLLECTION_NAME)
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
                    preprocess(ELYSIA_COLLECTION_NAME)
                except Exception as _e:
                    logging.error(f"❌ Errore preprocessing collection (thread): {_e}")
            try:
                asyncio.get_running_loop()
                t = threading.Thread(target=_run_preprocess_sync, daemon=True)
                t.start(); t.join()
            except RuntimeError:
                preprocess(ELYSIA_COLLECTION_NAME)

        # Esegue ricerca con Elysia Tree (AI search)
        tree = Tree()
        risposta, oggetti = tree(
            query,
            collection_names=[ELYSIA_COLLECTION_NAME]
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
