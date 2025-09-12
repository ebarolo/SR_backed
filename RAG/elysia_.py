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
from utility import normalize_text
from models import RecipeDBSchema

# Import Elysia SDK
from elysia import (
    configure,
    preprocess,
    preprocessed_collection_exists,
    Tree
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
            base_model="gpt-4.1",
            base_provider="openai",
            complex_model="gpt-4.1",
            complex_provider="openai",
            openai_api_key=OPENAI_API_KEY
        )
        status = False
        client_manager = ClientManager()

        with client_manager.connect_to_client() as client:
            # Verifica/crea collection in Weaviate
            if not client.collections.exists(ELYSIA_COLLECTION_NAME):
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
                                normalized_name = normalize_text(getattr(ingredient, 'name', '') or '')
                                #cleaned_name = remove_stopwords_spacy(normalized_name)
                                qt = getattr(ingredient, 'qt', '')
                                um = getattr(ingredient, 'um', '') or ''
                                # Rappresentazione compatta della quantità, senza zeri superflui
                                qt_str = (
                                    (f"{float(qt):g}" if qt is not None else "").strip()
                                )
                                parts = [p for p in [qt_str, um.strip(), normalized_name.strip()] if p]
                                ingredients_text.append(" ".join(parts))
                            except Exception:
                                # In caso di ingrediente malformato, fallback al semplice str()
                                try:
                                    ingredients_text.append(str(ingredient))
                                except Exception:
                                    pass
                    
                    # Normalizza categorie (tollerante a None)
                    
                    cats_lem: List[str] = []
                    for category in recipe.category:
                        logging.info(f"category '{category}'")
                        normalized_cat = normalize_text(category)
                        logging.info(f"normalized_cat '{normalized_cat}'")
                        #cleaned_cat = remove_stopwords_spacy(normalized_cat)
                        if normalized_cat:
                            cats_lem.append(normalized_cat)
                        logging.info(f"cats_lem '{cats_lem}'")
            

                    tags_lem: List[str] = []
                    for tag in recipe.tags:
                        logging.info(f"tag '{tag}'")
                        normalized_tag = normalize_text(tag)
                        logging.info(f"normalized_tag '{normalized_tag}'")
                        #cleaned_cat = remove_stopwords_spacy(normalized_cat)
                        if normalized_tag:
                            tags_lem.append(normalized_tag)
                    
                    nutr_lem: List[str] = []
                    for nutr in recipe.nutritional_info:
                        logging.info(f"nutr '{nutr}'")
                        normalized_nutr = normalize_text(nutr)
                        logging.info(f"normalized_tag '{normalized_nutr}'")
                        #cleaned_cat = remove_stopwords_spacy(normalized_cat)
                        if normalized_nutr:
                            nutr_lem.append(normalized_nutr)

                    # Prepara oggetto per Weaviate con tipi sicuri (no None)
                    recipe_object = {
                        "title": recipe.title or "",
                        "description": recipe.description or "",
                        "ingredients": ingredients_text,
                        "category": cats_lem,
                        "cuisine_type": recipe.cuisine_type or "",
                        "diet": recipe.diet or "",
                        "technique": recipe.technique or "",
                        "language": recipe.language or "",
                        "shortcode": recipe.shortcode,
                        "cooking_time": recipe.cooking_time or 0,
                        "preparation_time": recipe.preparation_time or 0,
                        "chef_advise": recipe.chef_advise or "",
                        "tags": tags_lem,
                        "nutritional_info": nutr_lem,
                        "recipe_step": recipe.recipe_step,
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
