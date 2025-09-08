from typing import List, Dict, Any, Optional

import logging

from config import (WCD_URL, WCD_API_KEY, ELYSIA_COLLECTION_NAME, ELYSIA_AVAILABLE, OPENAI_API_KEY)
from logging_config import get_error_logger, clear_error_chain
from utility import nfkc, lemmatize_it, remove_stopwords_spacy
from models import RecipeDBSchema

error_logger = get_error_logger(__name__)

class ElysiaRecipeDatabase:
    """Gestione database Elysia/Weaviate per ricette"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = ELYSIA_COLLECTION_NAME
        self.initialization_attempted = False
        self.initialization_successful = False
        self.initialize_database()
    
    def initialize_database(self):
        """Inizializza la connessione a Weaviate ed Elysia"""
        if self.initialization_attempted:
            return
            
        self.initialization_attempted = True
        
        if not ELYSIA_AVAILABLE:
            logging.getLogger(__name__).warning("Elysia non abilitato in configurazione")
            return
            
        # Verifica credenziali essenziali
        if not WCD_URL or not WCD_API_KEY or not OPENAI_API_KEY:
            logging.getLogger(__name__).error("Credenziali Elysia mancanti - WCD_URL, WCD_API_KEY o OPENAI_API_KEY non configurate")
            error_logger.log_exception("elysia_credentials_missing", 
                                     Exception("Credenziali mancanti"), 
                                     {"wcd_url_set": bool(WCD_URL), 
                                      "wcd_api_key_set": bool(WCD_API_KEY),
                                      "openai_api_key_set": bool(OPENAI_API_KEY)})
            return
            
        clear_error_chain()
        try:
            # Configurazione Elysia
            from elysia import configure
            from elysia.util.client import ClientManager
            import weaviate.classes.config as wvc
            
            # Configura Elysia con le credenziali
            configure(
                wcd_url=WCD_URL,
                wcd_api_key=WCD_API_KEY,
                base_model="gpt-4.1",
                base_provider="openai",
                complex_model="gpt-4.1",
                complex_provider="openai",
                openai_api_key=OPENAI_API_KEY
            )
            
            # Connetti al client Weaviate usando il context manager correttamente
            client_manager = ClientManager()
            client_context = client_manager.connect_to_client()
            self.client = client_manager.connect_to_client()
            
            # Crea o ottieni la collection
            try:
                # Prova a ottenere la collection esistente
                if self.client.collections.exists(self.collection_name):
                    self.collection = self.client.collections.get(self.collection_name)
                    logging.getLogger(__name__).info(f"Collection '{self.collection_name}' già esistente")
                else:
                    raise Exception("Collection non esiste")
                    
            except Exception:
                # Crea nuova collection con schema definito
                from weaviate.classes.config import Property, DataType, Configure
                
                try:
                    # Elimina collection se esiste con schema sbagliato
                    if self.client.collections.exists(self.collection_name):
                        logging.getLogger(__name__).warning(f"Eliminazione collection esistente '{self.collection_name}'")
                        self.client.collections.delete(self.collection_name)
                except:
                    pass
                
                self.collection = self.client.collections.create(
                    name=self.collection_name,
                    properties=[
                        Property(name="title", data_type=DataType.TEXT),
                        Property(name="description", data_type=DataType.TEXT),
                        Property(name="ingredients", data_type=DataType.TEXT),
                        Property(name="category", data_type=DataType.TEXT_ARRAY),
                        Property(name="cuisine_type", data_type=DataType.TEXT),
                        Property(name="diet", data_type=DataType.TEXT),
                        Property(name="technique", data_type=DataType.TEXT),
                        Property(name="language", data_type=DataType.TEXT),
                        Property(name="shortcode", data_type=DataType.TEXT),
                        Property(name="cooking_time", data_type=DataType.INT),
                        Property(name="preparation_time", data_type=DataType.INT)
                    ]
                    # Rimuovo vector_config per ora, usa default di Weaviate
                )
                logging.getLogger(__name__).info(f"Collection '{self.collection_name}' creata")
                
                # Pre-processing di Elysia verrà fatto quando ci sono dati
                logging.getLogger(__name__).info("Collection creata - pre-processing sarà fatto al primo inserimento dati")
                
            # Marca inizializzazione come riuscita
            self.initialization_successful = True
            logging.getLogger(__name__).info("✅ Database Elysia inizializzato con successo")
                
        except Exception as e:
            self.initialization_successful = False
            error_logger.log_exception("initialize_elysia_database", e, {
                "wcd_url": WCD_URL,
                "collection_name": self.collection_name,
                "credentials_available": bool(WCD_URL and WCD_API_KEY and OPENAI_API_KEY)
            })
            self.client = None
            self.collection = None
            logging.getLogger(__name__).error(f"❌ Inizializzazione database Elysia fallita: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica se il database è disponibile e funzionante"""
        return (self.initialization_successful and 
                self.client is not None and 
                self.collection is not None)
    
    def retry_initialization(self) -> bool:
        """Tenta di reinizializzare il database"""
        if self.initialization_successful:
            return True
            
        logging.getLogger(__name__).info("Tentativo di reinizializzazione database Elysia...")
        self.initialization_attempted = False
        self.initialize_database()
        return self.is_available()
    
    def add_recipe(self, recipe_data: RecipeDBSchema) -> bool:
        """Aggiunge una ricetta al database Weaviate"""
        logger = logging.getLogger(__name__)
        
        if not self.collection:
            logger.error(f"Collection non disponibile per recipe: {recipe_data.shortcode}")
            return False
            
        try:           
            logger.debug(f"Avvio processamento recipe: {recipe_data.shortcode}")

            # Processa ingredienti
            ingr_lem = []
            for ingredient in recipe_data.ingredients:
                i_n = nfkc(ingredient.name)
                i_s = remove_stopwords_spacy(i_n)
                ingr_lem.append(i_s)

            cats = [nfkc(x) for x in recipe_data.category]
            
            logger.debug(f"Recipe {recipe_data.shortcode}: {len(ingr_lem)} ingredienti processati, {len(cats)} categorie")
            
            # Crea testo per il documento
            document_text = (f"Titolo: {recipe_data.title}\n"
                             f"Descrizione: {recipe_data.description}\n"
                             f"Ingredienti: {'; '.join(ingr_lem)}\n"
                             f"Categoria: {'; '.join(cats)}\n"
            )

            # Prepara i dati per Weaviate
            recipe_object = {
                "title": recipe_data.title,
                "description": recipe_data.description,
                "ingredients": '; '.join(ingr_lem),
                "category": cats,  # Usa categorie processate, non ingredienti
                "cuisine_type": recipe_data.cuisine_type or "",
                "diet": recipe_data.diet or "",
                "technique": recipe_data.technique or "",
                "language": recipe_data.language,
                "shortcode": recipe_data.shortcode,
                "cooking_time": recipe_data.cooking_time or 0,
                "preparation_time": recipe_data.preparation_time or 0,
                #"document_text": document_text
            }
            
            # Genera UUID valido dal shortcode
            import uuid as uuid_lib
            recipe_uuid = uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, recipe_data.shortcode)
            logger.debug(f"Recipe {recipe_data.shortcode}: UUID generato = {recipe_uuid}")
            
            # Verifica se esiste già
            exists = self.collection.data.exists(recipe_uuid)
            logger.debug(f"Recipe {recipe_data.shortcode}: esiste già = {exists}")
            
            # Aggiungi o aggiorna nel database
            if exists:   
                self.collection.data.update(recipe_object, recipe_uuid)
                logger.info(f"✅ Recipe {recipe_data.shortcode} aggiornata con successo")
            else:
                self.collection.data.insert(recipe_object, recipe_uuid)
                logger.info(f"✅ Recipe {recipe_data.shortcode} inserita con successo")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore inserimento recipe {recipe_data.shortcode}: {str(e)}")
            error_logger.log_exception("add_recipe_elysia", e, {
                "shortcode": recipe_data.shortcode,
                "title": recipe_data.title,
                "ingredients_count": len(recipe_data.ingredients),
                "categories_count": len(recipe_data.category)
            })
            return False
    
    def search(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Ricerca semantica usando Elysia"""
        if not self.collection:
            return []
            
        try:
            from elysia import Tree
            
            # Usa Elysia Tree per la ricerca
            tree = Tree()
            risposta, oggetti = tree(
                query,
                collection_names=[self.collection_name],
                k=limit
            )
            
            # Formatta risultati per compatibilità con l'API esistente
            formatted_results = []
            for obj in oggetti[:limit]:
                try:
                    properties = obj.properties
                    result = {
                        "shortcode": properties.get("shortcode", ""),
                        "distances": 0.5,  # Elysia non espone score direttamente
                        "title": properties.get("document_text", "").split("\n")[0].replace("Titolo: ", ""),
                        "category": properties.get("category", "").split(";") if properties.get("category") else [],
                        "cuisine_type": properties.get("cuisine_type", ""),
                        "cooking_time": properties.get("cooking_time", 0),
                        "preparation_time": properties.get("preparation_time", 0)
                    }
                    formatted_results.append(result)
                except Exception as parse_error:
                    logging.getLogger(__name__).warning(f"Error parsing result: {parse_error}")
                    continue
                    
            return formatted_results
            
        except Exception as e:
            error_logger.log_exception("search_elysia", e, {
                "query": query[:50],
                "limit": limit,
                "filters": filters
            })
            return []
    
    def get_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Recupera ricetta per shortcode da Weaviate"""
        if not self.collection:
            return None
            
        try:
            # Genera UUID valido dal shortcode (stesso metodo di add_recipe)
            import uuid as uuid_lib
            recipe_uuid = uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, shortcode)
            
            # Cerca per UUID usando Weaviate
            result = self.collection.query.fetch_object_by_id(recipe_uuid)
            
            if result:
                properties = result.properties
                return {
                    "_id": shortcode,
                    "shortcode": shortcode,
                    "title": properties.get("title", ""),
                    "category": properties.get("category", "").split(";") if properties.get("category") else [],
                    "cuisine_type": properties.get("cuisine_type", ""),
                    "cooking_time": properties.get("cooking_time", 0),
                    "preparation_time": properties.get("preparation_time", 0),
                    "description": properties.get("description", ""),
                    "ingredients": properties.get("ingredients", "")
                }
            return None
            
        except Exception as e:
            error_logger.log_exception("get_by_shortcode_elysia", e, {"shortcode": shortcode})
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche del database Weaviate"""
        if not self.collection:
            return {
                "total_recipes": 0,
                "collection_name": "unavailable",
                "status": "Elysia not available"
            }
        
        try:
            # Ottieni statistiche dalla collection
            total_objects = self.collection.aggregate.over_all(total_count=True)
            count = total_objects.total_count if total_objects else 0
            
            return {
                "total_recipes": count,
                "collection_name": self.collection_name,
                "status": "active",
                "database_type": "Weaviate/Elysia"
            }
        except Exception as e:
            error_logger.log_exception("get_stats_elysia", e)
            return {
                "total_recipes": 0,
                "collection_name": "error",
                "status": f"error: {str(e)}"
            }

# Istanza globale per compatibilità
elysia_recipe_db = ElysiaRecipeDatabase()

# Funzioni di compatibilità per mantenere la stessa API di chromaDB.py
def ingest_json_to_elysia(metadatas: List[RecipeDBSchema], collection_name: str = None) -> tuple[int, str]:
    """
    Funzione di compatibilità per l'ingest di ricette in Elysia.
    
    Args:
        metadatas: Lista di ricette da inserire
        collection_name: Nome collection (ignorato, usa configurazione)
    
    Returns:
        tuple: (numero_ricette_inserite, nome_collection)
    """
    logger = logging.getLogger(__name__)
    
    # Validazione input
    if not metadatas:
        logger.warning("Lista ricette vuota per ingest")
        return 0, "empty_input"
    
    # Verifica disponibilità database con retry
    if not elysia_recipe_db.is_available():
        logger.warning("Database Elysia non disponibile, tentativo di reinizializzazione...")
        
        if not elysia_recipe_db.retry_initialization():
            logger.error("Database Elysia non disponibile dopo retry, tentativo fallback a ChromaDB...")
            
           
            error_logger.log_exception("ingest_json_to_elysia", 
                                     Exception("Database non disponibile dopo retry e fallback"), 
                                     {"input_count": len(metadatas),
                                      "initialization_attempted": elysia_recipe_db.initialization_attempted,
                                      "initialization_successful": elysia_recipe_db.initialization_successful})
            return 0, "unavailable"
        else:
            logger.info("✅ Database Elysia reinizializzato con successo")
    
    logger.info(f"Avvio ingest di {len(metadatas)} ricette in Elysia")
    
    success_count = 0
    failed_count = 0
    failed_shortcodes = []
    
    for i, metadata in enumerate(metadatas, 1):
        try:
            logger.info(f"[{i}/{len(metadatas)}] Ingesting recipe: {metadata.shortcode}")
            
            if elysia_recipe_db.add_recipe(metadata):
                success_count += 1
                logger.debug(f"✅ Recipe {metadata.shortcode} inserita con successo")
            else:
                failed_count += 1
                failed_shortcodes.append(metadata.shortcode)
                logger.warning(f"❌ Fallimento inserimento recipe: {metadata.shortcode}")
                
        except Exception as e:
            failed_count += 1
            failed_shortcodes.append(metadata.shortcode)
            logger.error(f"❌ Errore inserimento recipe {metadata.shortcode}: {str(e)}")
            error_logger.log_exception("ingest_recipe_single", e, {
                "shortcode": metadata.shortcode,
                "title": metadata.title,
                "progress": f"{i}/{len(metadatas)}"
            })
    
    # Logging riepilogo
    logger.info(f"✅ Ingest completato: {success_count} successi, {failed_count} fallimenti")
    if failed_shortcodes:
        logger.warning(f"❌ Shortcodes falliti: {failed_shortcodes[:10]}{'...' if len(failed_shortcodes) > 10 else ''}")
    
    # Pre-processa la collection dopo l'inserimento (solo se ci sono stati successi)
    if success_count > 0:
        try:
            from elysia import preprocess
            import asyncio
            
            logger.info("Avvio pre-processing collection Elysia...")
            
            # Controlla se siamo in un loop asincrono
            try:
                loop = asyncio.get_running_loop()
                logger.info("Pre-processing schedulato in background (loop asincrono attivo)")
            except RuntimeError:
                # Nessun loop attivo, esegui sincrono
                preprocess(elysia_recipe_db.collection_name)
                logger.info("✅ Collection pre-processata con successo")
                
        except Exception as e:
            logger.warning(f"⚠️ Errore nel pre-processing: {str(e)}")
            error_logger.log_exception("preprocess_after_ingest", e, {
                "success_count": success_count,
                "collection_name": elysia_recipe_db.collection_name
            })
    else:
        logger.warning("Nessun successo nell'ingest - pre-processing saltato")
    
    return success_count, elysia_recipe_db.collection_name

def search_recipes_elysia(query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Funzione di compatibilità per la ricerca con Elysia"""
    return elysia_recipe_db.search(query, limit, filters)

def get_recipe_by_shortcode_elysia(shortcode: str) -> Optional[Dict[str, Any]]:
    """Funzione di compatibilità per il recupero per shortcode con Elysia"""
    return elysia_recipe_db.get_by_shortcode(shortcode)

def get_elysia_status() -> Dict[str, Any]:
    """Restituisce lo stato dettagliato del database Elysia"""
    return {
        "available": elysia_recipe_db.is_available(),
        "initialization_attempted": elysia_recipe_db.initialization_attempted,
        "initialization_successful": elysia_recipe_db.initialization_successful,
        "client_connected": elysia_recipe_db.client is not None,
        "collection_available": elysia_recipe_db.collection is not None,
        "collection_name": elysia_recipe_db.collection_name,
        "credentials_configured": {
            "wcd_url": bool(WCD_URL),
            "wcd_api_key": bool(WCD_API_KEY),
            "openai_api_key": bool(OPENAI_API_KEY)
        }
    }
