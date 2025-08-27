"""
ChromaDB integration for recipe search and storage.

Implementazione del sistema di database vettoriale per la ricerca semantica delle ricette.
"""
import logging
from typing import List, Dict, Any, Optional
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMADB_AVAILABLE = False

from config import CHROMA_LOCAL_PATH, USE_LOCAL_CHROMA, COLLECTION_NAME
from DB.embedding import recipe_embedder
from models import RecipeDBSchema

logger = logging.getLogger(__name__)

class RecipeDatabase:
    """Gestione database ChromaDB per ricette"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.initialize_database()
    
    def initialize_database(self):
        """Inizializza la connessione a ChromaDB"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB non disponibile - funzionalità limitata")
            return
            
        try:
            if USE_LOCAL_CHROMA and CHROMA_LOCAL_PATH:
                self.client = chromadb.PersistentClient(path=CHROMA_LOCAL_PATH)
            else:
                self.client = chromadb.Client()
                
            # Crea o ottiene la collection default
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Recipe collection con embeddings"}
            )
            logger.info("ChromaDB inizializzato con successo")
            
        except Exception as e:
            logger.error(f"Errore inizializzazione ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def add_recipe(self, recipe_data: RecipeDBSchema) -> bool:
        """Aggiunge una ricetta al database"""
        if not self.collection:
            logger.warning("ChromaDB non disponibile")
            return False
            
        try:
            # Genera embedding per la ricetta
            embedding = recipe_embedder.encode_recipe(recipe_data)
            
            # Prepara metadati
            metadata = {
                "title": recipe_data.title,
                "shortcode": recipe_data.shortcode,
                "category": ",".join(recipe_data.category) if recipe_data.category else "",
                "cuisine_type": recipe_data.cuisine_type or "",
                "cooking_time": recipe_data.cooking_time or 0,
                "preparation_time": recipe_data.preparation_time or 0
            }
            
            # Crea testo per il documento
            document_text = recipe_embedder.create_recipe_text(recipe_data)
            
            # Aggiungi al database
            self.collection.add(
                embeddings=[embedding],
                documents=[document_text],
                metadatas=[metadata],
                ids=[recipe_data.shortcode]
            )
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiunta ricetta: {e}")
            return False
    
    def search(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Ricerca semantica nel database"""
        if not self.collection:
            logger.warning("ChromaDB non disponibile")
            return []
            
        try:
            # Genera embedding per la query
            query_embedding = recipe_embedder.encode_query(query)
            
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
                where=where_clause if where_clause else None
            )
            
            # Formatta risultati
            formatted_results = []
            for i in range(len(results["ids"][0])):
                result = {
                    "_id": results["ids"][0][i],
                    "shortcode": results["ids"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # Converti distanza in score
                    "title": results["metadatas"][0][i].get("title", ""),
                    "category": results["metadatas"][0][i].get("category", "").split(",") if results["metadatas"][0][i].get("category") else [],
                    "cuisine_type": results["metadatas"][0][i].get("cuisine_type", ""),
                    "cooking_time": results["metadatas"][0][i].get("cooking_time", 0),
                    "preparation_time": results["metadatas"][0][i].get("preparation_time", 0)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Errore ricerca: {e}")
            return []
    
    def get_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Recupera ricetta per shortcode"""
        if not self.collection:
            logger.warning("ChromaDB non disponibile")
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
            logger.error(f"Errore recupero ricetta {shortcode}: {e}")
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
            logger.error(f"Errore statistiche: {e}")
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
        logger.warning("ChromaDB non disponibile per ingest")
        return 0, "unavailable"
    
    success_count = 0
    for metadata in metadatas:
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
