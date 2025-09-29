import os
import sys
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import (
    Configure,
    VectorDistances
)

from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5 

from weaviate.agents.query import QueryAgent

from typing import List, Dict, Any, Optional
import logging
import uuid as uuid_lib
import threading
import time
from config import WCD_URL, WCD_API_KEY, WCD_COLLECTION_NAME, WCD_AVAILABLE
from utility.models import RecipeDBSchema

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateSemanticEngine:
    """Classe per interrogare semanticamente la collection Weaviate"""
    
    # Class-level lock per operazioni batch thread-safe
    _batch_lock = threading.RLock()
    _operation_counters = {}
    _operation_lock = threading.Lock()
    
    def __init__(self):
        """Inizializza la connessione a Weaviate"""
        if not WCD_AVAILABLE:
            raise Exception("Weaviate non è disponibile. Controlla la configurazione.")
        
        try:
            # Configurazione client Weaviate
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=WCD_URL,
                auth_credentials=Auth.api_key(WCD_API_KEY),
                headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
            )
            
            # Verifica connessione
            if not self.client.is_ready():
                raise Exception("Impossibile connettersi a Weaviate")
                
            logger.info(f"Connesso a Weaviate: {WCD_URL}")
            logger.info(f"Collection: {WCD_COLLECTION_NAME}")
            
        except Exception as e:
            logger.error(f"Errore connessione Weaviate: {e}")
            raise
    
    @classmethod
    def _get_operation_id(cls, shortcode: str) -> str:
        """Genera ID univoco per operazione per evitare race conditions."""
        timestamp = int(time.time() * 1000)
        return f"{shortcode}_{timestamp}_{threading.current_thread().ident}"
    
    @classmethod
    def _is_operation_in_progress(cls, shortcode: str) -> bool:
        """Verifica se un'operazione per questo shortcode è già in corso."""
        with cls._operation_lock:
            return shortcode in cls._operation_counters and cls._operation_counters[shortcode] > 0
    
    @classmethod
    def _start_operation(cls, shortcode: str) -> None:
        """Marca l'inizio di un'operazione per questo shortcode."""
        with cls._operation_lock:
            cls._operation_counters[shortcode] = cls._operation_counters.get(shortcode, 0) + 1
    
    @classmethod
    def _end_operation(cls, shortcode: str) -> None:
        """Marca la fine di un'operazione per questo shortcode."""
        with cls._operation_lock:
            if shortcode in cls._operation_counters:
                cls._operation_counters[shortcode] -= 1
                if cls._operation_counters[shortcode] <= 0:
                    del cls._operation_counters[shortcode]
    
    def semantic_search(
        self, 
        query: str, 
        limit: int = 10, 
        distance_threshold: float = 0.7,
        properties: List[str] = None
    ):
        """
        Esegue una ricerca semantica nella collection
        
       """
        system_prompt="you are an RAG search agent, jut must search the correct answer in the collection and response in the same format of the collection" 
        
        try:
            # Proprietà di default se non specificate
            if properties is None:
                properties = ["*"]  # Tutte le proprietà
            
            # Verifica che la collection esista
            if not self.client.collections.exists(WCD_COLLECTION_NAME):
                logger.error(f"Collection '{WCD_COLLECTION_NAME}' non esiste")
                return False
            
            #collection = self.client.collections.use(WCD_COLLECTION_NAME)
            
            agent = QueryAgent(
                client=self.client,
                collections=[WCD_COLLECTION_NAME],
                system_prompt=system_prompt
                )
            response = agent.ask(query)
            return response
         
        except Exception as e:
            logger.error(f"Errore durante la ricerca semantica: {e}")
            raise
               
    def search_by_vector(
        self, 
        vector: List[float], 
        limit: int = 10,
        distance_threshold: float = 0.7,
        properties: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca usando un vettore pre-calcolato
        
        Args:
            vector: Vettore di embedding per la ricerca
            limit: Numero massimo di risultati
            distance_threshold: Soglia di distanza
            properties: Proprietà da includere
            
        Returns:
            Lista di risultati
        """
        try:
            if properties is None:
                properties = ["*"]
            
            query_builder = (
                self.client.query
                .get(WCD_COLLECTION_NAME, properties)
                .with_near_vector({"vector": vector})
                .with_limit(limit)
                .with_additional(["distance", "id"])
            )
            
            result = query_builder.do()
            
            if "data" in result and "Get" in result["data"]:
                items = result["data"]["Get"][WCD_COLLECTION_NAME]
                filtered_items = [
                    item for item in items 
                    if item.get("_additional", {}).get("distance", 1.0) <= distance_threshold
                ]
                return filtered_items
            else:
                return []
                
        except Exception as e:
            logger.error(f"Errore durante la ricerca per vettore: {e}")
            raise
    
    def hybrid_search(
        self, 
        query: str, 
        alpha: float = 0.5,
        limit: int = 10,
        properties: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca ibrida (semantica + keyword)
        
        Args:
            query: Testo della query
            alpha: Peso della ricerca semantica (0-1, 0.5 = bilanciato)
            limit: Numero massimo di risultati
            properties: Proprietà da includere
            
        Returns:
            Lista di risultati
        """
        try:
            if properties is None:
                properties = ["*"]
            
            query_builder = (
                self.client.query
                .get(WCD_COLLECTION_NAME, properties)
                .with_hybrid(
                    query=query,
                    alpha=alpha
                )
                .with_limit(limit)
                .with_additional(["distance", "id", "score"])
            )
            
            result = query_builder.do()
            
            if "data" in result and "Get" in result["data"]:
                items = result["data"]["Get"][WCD_COLLECTION_NAME]
                logger.info(f"Trovati {len(items)} risultati con ricerca ibrida")
                return items
            else:
                return []
                
        except Exception as e:
            logger.error(f"Errore durante la ricerca ibrida: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sulla collection"""
        try:
            schema = self.client.schema.get()
            collection_info = None
            
            for collection in schema.get("classes", []):
                if collection["class"] == WCD_COLLECTION_NAME:
                    collection_info = collection
                    break
            
            if collection_info:
                return {
                    "name": collection_info["class"],
                    "properties": [prop["name"] for prop in collection_info.get("properties", [])],
                    "vectorizer": collection_info.get("vectorizer", "N/A"),
                    "module_config": collection_info.get("moduleConfig", {})
                }
            else:
                return {"error": f"Collection '{WCD_COLLECTION_NAME}' non trovata"}
                
        except Exception as e:
            logger.error(f"Errore nel recupero info collection: {e}")
            return {"error": str(e)}
    
    def create_collection(self, collection_name: str = None) -> bool:
        """
        Crea una nuova collection Weaviate basata sullo schema RecipeDBSchema
        
        Args:
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se creata con successo, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            # Verifica se la collection esiste già
            if self.client.collections.exists(collection_name):
                logger.warning(f"Collection '{collection_name}' già esistente")
                return True
            
        
            # Crea la collection
            self.client.collections.create( collection_name, vector_config=Configure.Vectors.text2vec_openai(
            vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE
        ),
    ),  )
            logger.info(f"✅ Collection '{collection_name}' creata con successo")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore creazione collection '{collection_name}': {e}")
            return False
    
    def update_collection_schema(self, collection_name: str = None) -> bool:
        """
        Aggiorna lo schema di una collection esistente
        
        Args:
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se aggiornata con successo, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection '{collection_name}' non esiste")
                return False
            
            # Per Weaviate, l'aggiornamento schema richiede ricreazione
            # Prima esporta i dati esistenti
            logger.info(f"⚠️  Aggiornamento schema richiede ricreazione collection '{collection_name}'")
            logger.info("⚠️  I dati esistenti verranno persi. Usa backup se necessario.")
            
            # Elimina la collection esistente
            self.client.schema.delete_class(collection_name)
            logger.info(f"Collection '{collection_name}' eliminata")
            
            # Ricrea con nuovo schema
            return self.create_collection(collection_name)
            
        except Exception as e:
            logger.error(f"❌ Errore aggiornamento schema collection '{collection_name}': {e}")
            return False
    
    def add_recipe(self, recipe: RecipeDBSchema, collection_name: str = None) -> bool:
        """
        Aggiunge una singola ricetta alla collection
        
        Args:
            recipe: Oggetto RecipeDBSchema da aggiungere
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se aggiunta con successo, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            # Verifica che la collection esista
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection '{collection_name}' non esiste")
                return False
            
            collection = self.client.collections.use(collection_name)
            
            # Converte ingredienti in lista di stringhe
            ingredients_text = []
            if recipe.ingredients:
                for ingredient in recipe.ingredients:
                    qt_str = f"{float(ingredient.qt):g}" if ingredient.qt is not None else ""
                    parts = [p for p in [qt_str, ingredient.um.strip(), ingredient.name.strip()] if p]
                    ingredients_text.append(" ".join(parts))
            
            # Prepara oggetto per Weaviate
            recipe_object = {
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": ingredients_text,
                "category": recipe.category,
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
                "recipe_step": recipe.recipe_step,
                "images": recipe.images or [],
                "color_palette": recipe.palette_hex or []
            }
            
            # Genera UUID deterministico dal shortcode
            recipe_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, recipe.shortcode))
            
            # Verifica esistenza e aggiorna/inserisce
            exists = collection.data.exists(recipe_uuid)
            
            if exists:
                collection.data.update(recipe_uuid, recipe_object)
                logger.info(f"✅ Ricetta {recipe.shortcode} aggiornata")
            else:
                collection.data.insert(properties=recipe_object, uuid=recipe_uuid)
                logger.info(f"✅ Ricetta {recipe.shortcode} inserita")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore aggiunta ricetta {recipe.shortcode}: {e}")
            return False
            
    def _extract_recipe_data(self, recipe) -> Dict[str, Any]:
        """Estrae dati dalla ricetta in formato standardizzato."""
        if isinstance(recipe, dict):
            return {
                'shortcode': recipe.get('shortcode', ''),
                'title': recipe.get('title', ''),
                'description': recipe.get('description', ''),
                'ingredients': recipe.get('ingredients', []),
                'category': recipe.get('category', []),
                'cuisine_type': recipe.get('cuisine_type', ''),
                'diet': recipe.get('diet', ''),
                'technique': recipe.get('technique', ''),
                'language': recipe.get('language', ''),
                'cooking_time': recipe.get('cooking_time', 0),
                'preparation_time': recipe.get('preparation_time', 0),
                'chef_advise': recipe.get('chef_advise', ''),
                'tags': recipe.get('tags', []),
                'nutritional_info': recipe.get('nutritional_info', []),
                'recipe_step': recipe.get('recipe_step', []),
                'images': recipe.get('images', []),
                'color_palette': recipe.get('palette_hex', [])
            }
        else:
            return {
                'shortcode': recipe.shortcode,
                'title': recipe.title,
                'description': recipe.description,
                'ingredients': recipe.ingredients,
                'category': recipe.category,
                'cuisine_type': recipe.cuisine_type,
                'diet': recipe.diet,
                'technique': recipe.technique,
                'language': recipe.language,
                'cooking_time': recipe.cooking_time,
                'preparation_time': recipe.preparation_time,
                'chef_advise': recipe.chef_advise,
                'tags': recipe.tags,
                'nutritional_info': recipe.nutritional_info,
                'recipe_step': recipe.recipe_step,
                'images': recipe.images,
                'color_palette': recipe.palette_hex
            }
    
    def _convert_ingredients_to_text(self, ingredients) -> List[str]:
        """Converte ingredienti in lista di stringhe."""
        ingredients_text = []
        if ingredients:
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    qt = ingredient.get('qt', 0)
                    um = ingredient.get('um', '')
                    name = ingredient.get('name', '')
                else:
                    qt = ingredient.qt
                    um = ingredient.um
                    name = ingredient.name
                
                qt_str = f"{float(qt):g}" if qt is not None else ""
                parts = [p for p in [qt_str, um.strip(), name.strip()] if p]
                ingredients_text.append(" ".join(parts))
        return ingredients_text
    
    def _prepare_recipe_object(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara oggetto ricetta per Weaviate."""
        return {
            "title": recipe_data['title'],
            "description": recipe_data['description'],
            "ingredients": self._convert_ingredients_to_text(recipe_data['ingredients']),
            "category": recipe_data['category'],
            "cuisine_type": recipe_data['cuisine_type'] or "",
            "diet": recipe_data['diet'] or "",
            "technique": recipe_data['technique'] or "",
            "language": recipe_data['language'],
            "shortcode": recipe_data['shortcode'],
            "cooking_time": recipe_data['cooking_time'] or 0,
            "preparation_time": recipe_data['preparation_time'] or 0,
            "chef_advise": recipe_data['chef_advise'] or "",
            "tags": recipe_data['tags'] or [],
            "nutritional_info": recipe_data['nutritional_info'] or [],
            "recipe_step": recipe_data['recipe_step'],
            "images": recipe_data['images'] or [],
            "color_palette": recipe_data['color_palette'] or []
        }

    def add_recipes_batch(self, recipes: List[RecipeDBSchema], collection_name: str = None) -> bool:
        """
        Aggiunge multiple ricette alla collection in batch con thread-safety.
        
        Args:
            recipes: Lista di oggetti RecipeDBSchema
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se tutte le ricette sono state aggiunte, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
        
        # Thread-safe batch operation
        with self._batch_lock:
            try:
                # Verifica che la collection esista una sola volta
                if not self.client.collections.exists(collection_name):
                    logger.error(f"Collection '{collection_name}' non esiste")
                    self.create_collection(collection_name)
                    
                collection = self.client.collections.use(collection_name)
                success_count = 0
                failed_recipes = []
                
                # Prepara batch atomicamente
                batch_to_upsert = []
                
                for index, recipe in enumerate(recipes):
                    try:
                        # Estrai dati ricetta
                        recipe_data = self._extract_recipe_data(recipe)
                        shortcode = recipe_data['shortcode']
                        
                        # Skip se operazione già in corso per questo shortcode
                        if self._is_operation_in_progress(shortcode):
                            logger.warning(f"⚠️  Operazione per {shortcode} già in corso, saltata")
                            continue
                        
                        # Marca inizio operazione
                        self._start_operation(shortcode)
                        
                        try:
                            logger.debug(f"Preparando ricetta {index + 1}/{len(recipes)}: {shortcode}")
                            
                            # Prepara oggetto per Weaviate
                            recipe_object = self._prepare_recipe_object(recipe_data)
                            
                            # Genera UUID deterministico dal shortcode
                            recipe_uuid = generate_uuid5(shortcode)
                            
                            batch_to_upsert.append({
                                "uuid": recipe_uuid,
                                "properties": recipe_object,
                                "shortcode": shortcode
                            })
                            
                        finally:
                            # Termina operazione
                            self._end_operation(shortcode)
                            
                    except Exception as e:
                        error_shortcode = recipe_data.get('shortcode', 'unknown') if 'recipe_data' in locals() else 'unknown'
                        failed_recipes.append(error_shortcode)
                        logger.error(f"❌ Errore preparazione ricetta {error_shortcode}: {e}")
                        continue
                
                # Esegui batch operation atomica
                if batch_to_upsert:
                    logger.info(f"Esecuzione batch atomico per {len(batch_to_upsert)} ricette")
                    success_count = self._execute_batch_upsert(collection, batch_to_upsert)
                
                total_attempted = len(batch_to_upsert)
                logger.info(f"✅ Processate {success_count}/{total_attempted} ricette. Fallite: {len(failed_recipes)}")
                
                return success_count == total_attempted
                
            except Exception as e:
                logger.error(f"❌ Errore generale batch: {e}")
                return False
    
    def _execute_batch_upsert(self, collection, batch_to_upsert: List[Dict]) -> int:
        """Esegue operazioni batch in modo atomico con fallback."""
        success_count = 0
        
        try:
            # Prima prova batch operation
            with collection.batch.dynamic() as batch:
                for data_row in batch_to_upsert:
                    try:
                        batch.add_object(
                            properties=data_row["properties"],
                            uuid=data_row["uuid"]
                        )
                        success_count += 1
                    except Exception as upsert_err:
                        logger.warning(f"⚠️  Batch upsert fallito per {data_row['shortcode']}: {upsert_err}")
                        
        except Exception as batch_err:
            logger.warning(f"⚠️  Batch operation fallita: {batch_err}. Fallback a operazioni individuali")
            success_count = 0
            
            # Fallback a operazioni individuali
            for data_row in batch_to_upsert:
                try:
                    # Prova insert, se fallisce prova update
                    try:
                        collection.data.insert(
                            properties=data_row["properties"], 
                            uuid=data_row["uuid"]
                        )
                        success_count += 1
                        logger.debug(f"✅ Ricetta {data_row['shortcode']} inserita")
                    except Exception:
                        # Se insert fallisce, prova update
                        collection.data.update(data_row["uuid"], data_row["properties"])
                        success_count += 1
                        logger.debug(f"✅ Ricetta {data_row['shortcode']} aggiornata")
                        
                except Exception as individual_err:
                    logger.error(f"❌ Errore operazione individuale {data_row['shortcode']}: {individual_err}")
                    continue
        
        return success_count
        

    def delete_recipe(self, shortcode: str, collection_name: str = None) -> bool:
        """
        Elimina una ricetta dalla collection
        
        Args:
            shortcode: Shortcode della ricetta da eliminare
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se eliminata con successo, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection '{collection_name}' non esiste")
                return False
            
            collection = self.client.collections.use(collection_name)

            collection.data.delete_many(
                where=Filter.by_property("shortcode").equal(shortcode)
            )  
                      
            logger.info(f"✅ Ricetta {shortcode} eliminata")
            return True
           
                
        except Exception as e:
            logger.error(f"❌ Errore eliminazione ricetta {shortcode}: {e}")
            return False
    
    def get_recipe_by_shortcode(self, shortcode: str, collection_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Recupera una ricetta per shortcode
        
        Args:
            shortcode: Shortcode della ricetta
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            Dizionario con i dati della ricetta o None se non trovata
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection '{collection_name}' non esiste")
                return None
            
            collection = self.client.collections.get(collection_name)
            recipe_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, shortcode))
            
            if collection.data.exists(recipe_uuid):
                result = collection.data.get_by_id(recipe_uuid)
                return result
            else:
                logger.warning(f"Ricetta {shortcode} non trovata")
                return None
                
        except Exception as e:
            logger.error(f"❌ Errore recupero ricetta {shortcode}: {e}")
            return None
    
    def get_collection_stats(self, collection_name: str = None) -> Dict[str, Any]:
        """
        Ottiene statistiche sulla collection
        
        Args:
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            Dizionario con le statistiche della collection
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            if not self.client.collections.exists(collection_name):
                return {"error": f"Collection '{collection_name}' non esiste"}
            
            collection = self.client.collections.get(collection_name)
            
            # Conta oggetti nella collection
            result = collection.aggregate.over_all(total_count=True)
            total_count = result.total_count if hasattr(result, 'total_count') else 0
            
            return {
                "collection_name": collection_name,
                "total_recipes": total_count,
                "exists": True
            }
            
        except Exception as e:
            logger.error(f"❌ Errore statistiche collection '{collection_name}': {e}")
            return {"error": str(e)}
    
    def close(self):
        """Chiude la connessione in modo sicuro e completo"""
        if hasattr(self, 'client') and self.client is not None:
            try:
                # Chiusura principale del client (gestisce internamente tutte le connessioni)
                self.client.close()
                logger.info("Connessione Weaviate chiusa correttamente")
                
            except Exception as e:
                logger.error(f"Errore durante chiusura connessione Weaviate: {e}")
                # Non rilancia l'eccezione per evitare problemi durante cleanup
            finally:
                # Assicura che il client sia sempre settato a None
                try:
                    self.client = None
                except Exception:
                    pass  # Ignora errori durante cleanup finale
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - chiude automaticamente la connessione.
        
        Garantisce la chiusura anche in caso di eccezioni durante l'operazione.
        """
        try:
            self.close()
        except Exception as close_err:
            # Log errore ma non interrompere il flusso di cleanup
            logger.error(f"Errore durante __exit__ cleanup: {close_err}")
        
        # Non sopprime le eccezioni originali
        return False
