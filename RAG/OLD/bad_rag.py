import logging
from typing import Dict, Any
from RAG.db_layer import QdrantCloudManager

class QdrantException(Exception):
    """Eccezione personalizzata per errori relativi a Qdrant"""
    pass

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

# Credenziali Qdrant Cloud (da sostituire con le tue)
QDRANT_URL = "https://5aa12609-c34d-46d6-b115-8073a16dfe44.us-west-2-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "F_kU8UqayUBmVQhrNeUjy6RDtrMmOB8qbZgllaNK5CilSJoowHgKIA"

# Inizializza il manager
qdrant = QdrantCloudManager(
  api_key=QDRANT_API_KEY,
  url=QDRANT_URL,
  collection_name="smartRecipe"
)

def add_document(text, meta):
    """
    Aggiunge un documento alla collezione Qdrant.
    
    Args:
        text (str): Il testo da memorizzare
        meta (dict): I metadati associati al documento
        
    Returns:
        int: L'ID del documento inserito
        
    Raises:
        QdrantException: Se si verifica un errore durante l'inserimento
        ValueError: Se il testo o i metadati non sono validi
    """
    if not text or not isinstance(text, str):
        raise ValueError("Il testo deve essere una stringa non vuota")
        
    if not meta or not isinstance(meta, dict):
        raise ValueError("I metadati devono essere un dizionario non vuoto")
    
    logger.info(f"add_document: {text}")
    try:
        resp = qdrant.add_document(
            text=text,
            metadata=meta,
            id=None
        )

        logger.info(f"aggiunto del documento: {str(resp)}")
        return resp
        
    except Exception as e:
        logger.error(f"Errore durante l'aggiunta del documento: {str(e)}")
        raise QdrantException(f"Errore nell'inserimento del documento: {str(e)}") from e

def search(query):
 # Esegui una ricerca
  return qdrant.search(
      query=query,
      limit=5,
      score_threshold=0.7
   )

'''
 Stampa i risultati
    for result in results:
        print(f"\nDocumento ID: {result['id']}")
        print(f"Score: {result['score']:.2f}")
        print(f"Testo: {result['text']}")
        print(f"Categoria: {result['category']}")
        print(f"Tags: {', '.join(result['tags'])}")
'''