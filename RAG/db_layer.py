import os
import logging
from typing import Dict, Any, List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.vectorstores import Qdrant as QdrantVectorStore
from langchain.embeddings.base import Embeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variabili d'ambiente per Qdrant Cloud
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL", "https://5aa12609-c34d-46d6-b115-8073a16dfe44.us-west-2-0.aws.cloud.qdrant.io")
QDRANT_CLOUD_API_KEY = os.getenv("QDRANT_CLOUD_API_KEY", "AXUa1GCLMydhdA4fEZQLnMZTAqcpJPa9PN9VRhyzQN2ysXTlxWtNyQ")  # se necessario per Qdrant Cloud
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "recipes")

class QdrantDBManager:
    """
    Classe per la gestione delle operazioni sul database Qdrant (in questo caso, su Qdrant Cloud).
    """

    def __init__(self, embeddings: Embeddings, vector_dimension: int = 768):
        """
        Inizializza il client Qdrant e si assicura che la collezione esista.
        
        :param embeddings: Istanza di Embeddings di LangChain.
        :param vector_dimension: Dimensione del vettore di embedding (default 768 per paraphrase-multilingual-mpnet-base-v2).
        """
        self.embeddings = embeddings
        try:
            # Connessione a Qdrant Cloud
            self.client = QdrantClient(
                url=QDRANT_CLOUD_URL,        # URL del cluster Qdrant Cloud
                api_key=QDRANT_CLOUD_API_KEY # API key fornita dal servizio Cloud
            )
        except Exception as e:
            logger.error("Errore durante la connessione a Qdrant Cloud: %s", e)
            raise e

        # Inizializza (o ottiene) la collezione
        self._init_collection(vector_dimension)

        # Creiamo un VectorStore di LangChain
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings
        )

    def _init_collection(self, vector_dimension: int):
        """
        Crea la collezione se non esiste, con i parametri desiderati (es. dimensione vettoriale).
        
        :param vector_dimension: Dimensione del vettore di embedding.
        """
        try:
            # Otteniamo la lista delle collezioni
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if QDRANT_COLLECTION_NAME not in collection_names:
                logger.info("Creazione nuova collezione '%s'...", QDRANT_COLLECTION_NAME)
                self.client.create_collection(
                    collection_name=QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(size=vector_dimension, distance=Distance.COSINE)
                )
            else:
                logger.info(
                    "La collezione '%s' esiste già; stato: %s",
                    QDRANT_COLLECTION_NAME,
                    self.client.get_collection(QDRANT_COLLECTION_NAME).status
                )
        except Exception as e:
            logger.error("Errore durante l'inizializzazione della collezione: %s", e)
            raise e

    def add_or_update_recipe(
        self,
        recipe_id: str,
        title: str,
        description: str,
        ingredients: List[str],
        tags: List[str],
        nutritional_info: Dict[str, Any],
        preparation_time: int,
        cuisine_type: str
    ) -> None:
        """
        Inserisce o aggiorna una ricetta nella collezione 'recipes'.
        """
        try:
            # Prepariamo un testo concatenato da embeddare (title + description + ingredients)
            text_for_embedding = f"{title}\n{description}\n{' '.join(ingredients)}"
            embedding_vector = self.embeddings.embed_query(text_for_embedding)

            metadata = {
                "recipe_id": recipe_id,
                "title": title,
                "description": description,
                "ingredients": ingredients,
                "tags": tags,
                "nutritional_info": nutritional_info,
                "preparation_time": preparation_time,
                "cuisine_type": cuisine_type,
            }

            # Upsert usando il VectorStore di LangChain
            self.vectorstore.add_texts(
                texts=[text_for_embedding],
                metadatas=[metadata],
                ids=[recipe_id]
            )

            logger.info(f"Ricetta '{title}' (ID: {recipe_id}) inserita/aggiornata con successo su Qdrant Cloud.")
        except Exception as e:
            logger.error("Errore durante l'operazione add_or_update_recipe: %s", e)

    def semantic_search(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca semantica nelle ricette, sulla base di una query in linguaggio naturale.
        """
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            results = []
            for d in docs:
                item = {
                    "score_context": d.page_content,  # testo su cui è calcolato l'embedding
                    "metadata": d.metadata
                }
                results.append(item)
            return results
        except Exception as e:
            logger.error("Errore durante la ricerca semantica: %s", e)
            return []