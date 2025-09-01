from typing import List, Dict, Any, Optional
import uuid
import chromadb

from config import CHROMA_LOCAL_PATH, USE_LOCAL_CHROMA, COLLECTION_NAME, CHROMADB_AVAILABLE
from logging_config import get_error_logger, clear_error_chain
from utility import nfkc, lemmatize_it, remove_stopwords_spacy

from DB.embedding import RecipeEmbedder
from models import RecipeDBSchema
import logging
error_logger = get_error_logger(__name__)

class RecipeDatabase:
    """Gestione database ChromaDB per ricette"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedder = None
        self.initialize_database()
    
    def initialize_database(self):
        """Inizializza la connessione a ChromaDB"""
        if not CHROMADB_AVAILABLE:
            return
            
        clear_error_chain()  # Nuova operazione
        try:
            if USE_LOCAL_CHROMA and CHROMA_LOCAL_PATH:
                self.client = chromadb.PersistentClient(path=CHROMA_LOCAL_PATH)
            else:
                self.client = chromadb.Client()
                 
            # Crea o ottiene la collection default
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=None,
                metadata={"description": "Recipe collection con embeddings"},
                configuration={"hnsw": {"space": "cosine"}}
            )
            self.embedder = RecipeEmbedder()
            
        except Exception as e:
            error_logger.log_exception("initialize_database", e, {
                "chroma_path": CHROMA_LOCAL_PATH if USE_LOCAL_CHROMA else "memory",
                "collection_name": COLLECTION_NAME
            })
            self.client = None
            self.collection = None
    
    def add_recipe(self, recipe_data: RecipeDBSchema) -> bool:
        """Aggiunge una ricetta al database"""
        if not self.collection:
            return False
            
        try:           
            logging.getLogger(__name__).info(f"Adding recipe metadata: {recipe_data}", extra={})

            #ingr_raw = [nfkc(ingredient.name) for ingredient in recipe_data.ingredients]
            #ingr_s = [remove_stopwords_spacy(ingr_) for ingr_ in ingr_raw]
            ingr_lem = []
            for ingredient in recipe_data.ingredients:
             i_n = nfkc(ingredient.name)
             i_s = remove_stopwords_spacy(i_n)
             i_lem = lemmatize_it(i_s)
             ingr_lem.append(i_s)
             #logging.getLogger(__name__).info(f"i_n: {i_n} | i_s: {i_s} | i_lem: {i_lem}", extra={})
            
             #logging.getLogger(__name__).info(f"ingr_lem: {ingr_lem}", extra={})

            cats     = [nfkc(x) for x in recipe_data.category]
            
            # Crea testo per il documento
            document_text = (f"Titolo: {recipe_data.title}\n"
                             f"Descrizione: {recipe_data.description}\n"
                             f"Ingredienti: {'; '.join(ingr_lem)}\n"
                             f"Categoria: {'; '.join(cats)}\n"
            )
            logging.getLogger(__name__).info(f"document_text: {document_text}", extra={})

            # Genera embedding per la ricetta
            embedding = self.embedder.generate_embedding_sync(document_text)

            # Converti RecipeDBSchema in dict per ChromaDB
            md = {
                "cuisine_type": recipe_data.cuisine_type or "",
                "diet": recipe_data.diet or "",
                "category": ', '.join(cats) or "",
                "ingredients": ', '.join(ingr_lem) or "",
                "language": recipe_data.language or "",
                "technique": recipe_data.technique or "",
                "shortcode": recipe_data.shortcode or "",
                "cooking_time": recipe_data.cooking_time or 0,
                "preparation_time": recipe_data.preparation_time or 0
                }
            # Aggiungi al database
            resp = self.collection.upsert(
                embeddings=[embedding],
                documents=[document_text],
                metadatas=[md],
                ids=[recipe_data.shortcode]
            )
            
            logging.getLogger(__name__).info(f"upsert: {resp}", extra={})

            return True
            
        except Exception as e:
            error_logger.log_exception("add_recipe", e, {
                "shortcode": recipe_data.shortcode,
                "title": recipe_data.title
            })
            return False
    
    def search(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Ricerca semantica nel database"""
        if not self.collection:
            return []
            
        try:
            # Genera embedding per la query
            query_embedding = self.embedder.generate_embedding_sync(query)

            # Costruisci filtri Where
            where_clause = {}
            if filters:
                if filters.get("max_time"):
                    where_clause["cooking_time"] = {"$lte": filters["max_time"]}
                if filters.get("category"):
                    where_clause["category"] = {"$eq": filters["category"]}
                if filters.get("cuisine"):
                    where_clause["cuisine_type"] = {"$eq": filters["cuisine"]}
            
            # Esegui ricerca
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "distances", "metadatas"]
            )
            
            # Formatta risultati
            formatted_results = []
            for i in range(len(results["ids"][0])):
                result = {
                    "shortcode": results["ids"][0][i],
                    "distances": results["distances"][0][i],
                    "title": results["documents"][0][i],
                    "category": results["metadatas"][0][i].get("category", "").split(",") if results["metadatas"][0][i].get("category") else [],
                    "cuisine_type": results["metadatas"][0][i].get("cuisine_type", ""),
                    "cooking_time": results["metadatas"][0][i].get("cooking_time", 0),
                    "preparation_time": results["metadatas"][0][i].get("preparation_time", 0)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            error_logger.log_exception("search", e, {
                "query": query[:50],  # Primi 50 caratteri
                "limit": limit,
                "filters": filters
            })
            return []
    
    def get_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Recupera ricetta per shortcode"""
        if not self.collection:
            return None
            
        try:
            results = self.collection.get(ids=[shortcode])
            if results["ids"]:
                metadata = results["metadatas"][0]
                return {
                    "_id": shortcode,
                    "shortcode": shortcode,
                    "title": metadata.get("title", ""),
                    "category": metadata.get("category", "").split(",") if metadata.get("category") else [],
                    "cuisine_type": metadata.get("cuisine_type", ""),
                    "cooking_time": metadata.get("cooking_time", 0),
                    "preparation_time": metadata.get("preparation_time", 0)
                }
            return None
            
        except Exception as e:
            error_logger.log_exception("get_by_shortcode", e, {"shortcode": shortcode})
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche del database"""
        if not self.collection:
            return {
                "total_recipes": 0,
                "collection_name": "unavailable",
                "status": "ChromaDB not available"
            }
        
        try:
            count = self.collection.count()
            return {
                "total_recipes": count,
                "collection_name": self.collection.name,
                "status": "active"
            }
        except Exception as e:
            error_logger.log_exception("get_stats", e)
            return {
                "total_recipes": 0,
                "collection_name": "error",
                "status": f"error: {str(e)}"
            }

# Istanza globale
recipe_db = RecipeDatabase()

# Funzioni di compatibilità per main.py
def ingest_json_to_chroma(metadatas: List[RecipeDBSchema], collection_name: str = "smartRecipe") -> tuple[int, str]:
    """
    Funzione di compatibilità per l'ingest di ricette.
    
    Returns:
        tuple: (numero_ricette_inserite, nome_collection)
    """
    if not recipe_db.collection:
        return 0, "unavailable"
    
    success_count = 0
    for metadata in metadatas:
        logging.getLogger(__name__).info(f"Ingesting recipe: {metadata.shortcode}", extra={})

        if recipe_db.add_recipe(metadata):
            success_count += 1
    
    return success_count, collection_name

def search_recipes_chroma(query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Funzione di compatibilità per la ricerca.
    """
    return recipe_db.search(query, limit, filters)

def get_recipe_by_shortcode_chroma(shortcode: str) -> Optional[Dict[str, Any]]:
    """
    Funzione di compatibilità per il recupero per shortcode.
    """
    return recipe_db.get_by_shortcode(shortcode)
