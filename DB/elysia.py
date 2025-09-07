from typing import List, Dict, Any, Optional
import uuid
import json
import logging

from config import (WCD_URL, WCD_API_KEY, ELYSIA_COLLECTION_NAME, ELYSIA_AVAILABLE, 
                   OPENAI_API_KEY, openAIclient)
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
        self.initialize_database()
    
    def initialize_database(self):
        """Inizializza la connessione a Weaviate ed Elysia"""
        if not ELYSIA_AVAILABLE:
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
            
            # Connetti al client Weaviate
            self.client = ClientManager().connect_to_client()
            
            # Crea o ottieni la collection
            try:
                # Tenta di ottenere la collection esistente
                self.collection = self.client.collections.get(self.collection_name)
                logging.getLogger(__name__).info(f"Collection '{self.collection_name}' già esistente")
            except Exception:
                # Crea nuova collection se non esiste
                self.collection = self.client.collections.create(
                    name=self.collection_name,
                    vector_config=wvc.Configure.Vectors.auto()
                )
                logging.getLogger(__name__).info(f"Collection '{self.collection_name}' creata")
                
                # Pre-processa la collection per Elysia
                from elysia import preprocess
                preprocess(self.collection_name)
                
        except Exception as e:
            error_logger.log_exception("initialize_elysia_database", e, {
                "wcd_url": WCD_URL,
                "collection_name": self.collection_name
            })
            self.client = None
            self.collection = None
    
    def add_recipe(self, recipe_data: RecipeDBSchema) -> bool:
        """Aggiunge una ricetta al database Weaviate"""
        if not self.collection:
            return False
            
        try:           
            logging.getLogger(__name__).info(f"Adding recipe to Elysia: {recipe_data.shortcode}")

            # Processa ingredienti
            ingr_lem = []
            for ingredient in recipe_data.ingredients:
                i_n = nfkc(ingredient.name)
                i_s = remove_stopwords_spacy(i_n)
                ingr_lem.append(i_s)

            cats = [nfkc(x) for x in recipe_data.category]
            
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
                "category": recipe_data.ingredients,
                "cuisine_type": recipe_data.cuisine_type or "",
                "diet": recipe_data.diet or "",
                "technique": recipe_data.technique or "",
                "language": recipe_data.language,
                "shortcode": recipe_data.shortcode,
                "cooking_time": recipe_data.cooking_time or 0,
                "preparation_time": recipe_data.preparation_time or 0,
                #"document_text": document_text
            }
            
            # Aggiungi al database usando batch per efficienza
            with self.collection.batch.dynamic() as batch:
                batch.add_object(
                    properties=recipe_object,
                    uuid=recipe_data.shortcode  # Usa shortcode come UUID
                )
            
            logging.getLogger(__name__).info(f"Recipe {recipe_data.shortcode} added successfully")
            return True
            
        except Exception as e:
            error_logger.log_exception("add_recipe_elysia", e, {
                "shortcode": recipe_data.shortcode,
                "title": recipe_data.title
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
            # Cerca per shortcode usando Weaviate
            result = self.collection.query.fetch_object_by_id(shortcode)
            
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
    if not elysia_recipe_db.collection:
        return 0, "unavailable"
    
    success_count = 0
    for metadata in metadatas:
        logging.getLogger(__name__).info(f"Ingesting recipe to Elysia: {metadata.shortcode}")
        if elysia_recipe_db.add_recipe(metadata):
            success_count += 1
    
    # Pre-processa la collection dopo l'inserimento
    try:
        from elysia import preprocess
        preprocess(elysia_recipe_db.collection_name)
        logging.getLogger(__name__).info("Collection pre-processata con successo")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Errore nel pre-processing: {e}")
    
    return success_count, elysia_recipe_db.collection_name

def search_recipes_elysia(query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Funzione di compatibilità per la ricerca con Elysia"""
    return elysia_recipe_db.search(query, limit, filters)

def get_recipe_by_shortcode_elysia(shortcode: str) -> Optional[Dict[str, Any]]:
    """Funzione di compatibilità per il recupero per shortcode con Elysia"""
    return elysia_recipe_db.get_by_shortcode(shortcode)
