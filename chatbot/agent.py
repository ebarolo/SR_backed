#from google.adk.agents import Agent
#from google.adk.tools.retrieval import RetrievalTool
#from google.adk.models.lite_llm import LiteLlm
#from google.adk.runners import Runner
#from google.adk.sessions import InMemorySessionService
#from google.genai import types

from utility import get_embedding
from utility import get_mongo_client
from utility import logger
from config import MONGODB_DB, MONGODB_COLLECTION, MONGODB_VECTOR_SEARCH_INDEX_NAME, EMBEDDING_FIELD_NAME

def get_recipes(query: str, k: int = 5) -> list[dict]:
    # 1. Embedding della query
    # Connessione a MongoDB Atlas
    client     = get_mongo_client()
    db         = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]

    query_vector = get_embedding(query)
    if query_vector is None:
        logger.error(f"Impossibile generare l'embedding per la query: '{query}'. La ricerca non può procedere.")
        return [] # Restituisce una lista vuota in caso di fallimento dell'embedding
    
    logger.info(f"Vettore query generato con successo per la query: '{query}', dimensione: {len(query_vector)}")

    # 2. Aggregazione con $vectorSearch
    pipeline = [
        {
            "$vectorSearch": {
                "path": EMBEDDING_FIELD_NAME,
                "queryVector": query_vector,
                "limit": k,
                "index": MONGODB_VECTOR_SEARCH_INDEX_NAME,
                "numCandidates": k * 10
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "ingredients": 1,
                "steps": 1,
                "tags": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    try:
        response_cursor = collection.aggregate(pipeline)
        results = list(response_cursor)
        logger.info(f"Ricerca completata. Trovate {len(results)} ricette per la query: '{query}'.")
        return results
    except Exception as e:
        logger.error(f"Errore durante l'aggregazione $vectorSearch per la query '{query}': {e}", exc_info=True)
        return [] # Restituisce una lista vuota in caso di errore nella ricerca
