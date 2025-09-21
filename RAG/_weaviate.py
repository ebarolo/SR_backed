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
from config import WCD_URL, WCD_API_KEY, WCD_COLLECTION_NAME, WCD_AVAILABLE
from models import RecipeDBSchema

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateSemanticEngine:
    """Classe per interrogare semanticamente la collection Weaviate"""
    
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
                "recipe_step": recipe.recipe_step
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
            
    def add_recipes_batch(self, recipes: List[RecipeDBSchema], collection_name: str = None) -> bool:
        """
        Aggiunge multiple ricette alla collection in batch
        
        Args:
            recipes: Lista di oggetti RecipeDBSchema
            collection_name: Nome della collection (default: WCD_COLLECTION_NAME)
            
        Returns:
            bool: True se tutte le ricette sono state aggiunte, False altrimenti
        """
        if collection_name is None:
            collection_name = WCD_COLLECTION_NAME
            
        try:
            # Verifica che la collection esista una sola volta
            if not self.client.collections.exists(collection_name):
              logger.error(f"Collection '{collection_name}' non esiste")
              self.create_collection(collection_name)
                
            collection = self.client.collections.use(collection_name)
            success_count = 0
            
            # Prepara raccolte distinte per inserimenti e aggiornamenti
            batch_to_insert = []
            batch_to_update = []
            
            for index, recipe in enumerate(recipes):
                try:
                    # Gestisce sia oggetti RecipeDBSchema che dizionari
                    if isinstance(recipe, dict):
                        shortcode = recipe.get('shortcode', '')
                        title = recipe.get('title', '')
                        description = recipe.get('description', '')
                        ingredients = recipe.get('ingredients', [])
                        category = recipe.get('category', [])
                        cuisine_type = recipe.get('cuisine_type', '')
                        diet = recipe.get('diet', '')
                        technique = recipe.get('technique', '')
                        language = recipe.get('language', '')
                        cooking_time = recipe.get('cooking_time', 0)
                        preparation_time = recipe.get('preparation_time', 0)
                        chef_advise = recipe.get('chef_advise', '')
                        tags = recipe.get('tags', [])
                        nutritional_info = recipe.get('nutritional_info', [])
                        recipe_step = recipe.get('recipe_step', [])
                        images = recipe.get('images', [])
                    else:
                        shortcode = recipe.shortcode
                        title = recipe.title
                        description = recipe.description
                        ingredients = recipe.ingredients
                        category = recipe.category
                        cuisine_type = recipe.cuisine_type
                        diet = recipe.diet
                        technique = recipe.technique
                        language = recipe.language
                        cooking_time = recipe.cooking_time
                        preparation_time = recipe.preparation_time
                        chef_advise = recipe.chef_advise
                        tags = recipe.tags
                        nutritional_info = recipe.nutritional_info
                        recipe_step = recipe.recipe_step
                        images = recipe.images
                    
                    print(f"Preparando ricetta {index + 1}/{len(recipes)}: {shortcode}")
                    
                    # Converte ingredienti in lista di stringhe
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
                    
                    # Prepara oggetto per Weaviate
                    recipe_object = {
                        "title": title,
                        "description": description,
                        "ingredients": ingredients_text,
                        "category": category,
                        "cuisine_type": cuisine_type or "",
                        "diet": diet or "",
                        "technique": technique or "",
                        "language": language,
                        "shortcode": shortcode,
                        "cooking_time": cooking_time or 0,
                        "preparation_time": preparation_time or 0,
                        "chef_advise": chef_advise or "",
                        "tags": tags or [],
                        "nutritional_info": nutritional_info or [],
                        "recipe_step": recipe_step,
                        "images": images or [],
                    }
                    
                    # Genera UUID deterministico dal shortcode
                    recipe_uuid = generate_uuid5(shortcode)

                    try:
                        exists = collection.data.exists(recipe_uuid)
                        
                    except Exception as exists_err:
                        logger.error(f"❌ Errore verifica esistenza {shortcode}: {exists_err}")
                        continue

                    target_batch = batch_to_update if exists else batch_to_insert
                    target_batch.append({
                        "uuid": recipe_uuid,
                        "properties": recipe_object
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Errore preparazione ricetta {shortcode}: {e}")
                    continue
            
            if batch_to_update:
                logger.info(f"Aggiornamento di {len(batch_to_update)} ricette esistenti")
                for obj in batch_to_update:
                    shortcode = obj["properties"].get("shortcode", "unknown")
                    try:
                        collection.data.update(obj["uuid"], obj["properties"])
                        success_count += 1
                    except Exception as update_err:
                        logger.error(f"❌ Errore aggiornamento {shortcode}: {update_err}")

            if batch_to_insert:
                try:
                 with collection.batch.dynamic() as batch:
                    for data_row in batch_to_insert:
                        batch.add_object(
                            properties=data_row["properties"],
                            uuid=data_row["uuid"]
                        )
                        success_count += 1
                except Exception as e:
                  logger.error(f"❌ Errore generale batch: {e}")
                          
            logger.info(f"✅ Processate {success_count}/{len(recipes)} ricette")
            
            return success_count == len(recipes)
            
        except Exception as e:
            logger.error(f"❌ Errore generale batch: {e}")
            return False
        

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
        """Chiude la connessione"""
        if hasattr(self, 'client') and self.client is not None:
            try:
                self.client.close()
                logger.info("Connessione Weaviate chiusa correttamente")
            except Exception as e:
                logger.warning(f"Errore durante chiusura connessione: {e}")
            finally:
                self.client = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - chiude automaticamente la connessione"""
        self.close()
