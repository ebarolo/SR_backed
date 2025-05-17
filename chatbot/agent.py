# Importazioni necessarie
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List as PydanticList, Optional, Dict, Any # Rinominato List per evitare conflitti

from DB.embedding import get_embedding
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, MONGODB_VECTOR_SEARCH_INDEX_NAME, EMBEDDING_PATH, EMBEDDING_MODEL
from utility import logger

def get_recipes(user_query: str, k: int = 3) -> PydanticList[Dict[str, Any]]:
    """
    Suggerisce ricette da MongoDB basate sulla query dell'utente, categoria e ingrediente specifico.
    Utilizza ESCLUSIVAMENTE la ricerca vettoriale.
    """
    query_embedding = get_embedding(user_query)

    if query_embedding is None:
        logger.info(f"Impossibile generare l'embedding per la query. La ricerca vettoriale non può procedere.")
        return []

    results: PydanticList[Dict[str, Any]] = []
    mongo_client: Optional[MongoClient] = None

    try:
        # Imposta un timeout per la selezione del server per evitare blocchi indefiniti
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Verifica la connessione inviando un comando ping
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        collection = db[MONGODB_COLLECTION]

        # Pipeline di aggregazione MongoDB per la ricerca vettoriale
        # 1. $vectorSearch: trova i documenti semanticamente più vicini.
        # 2. $match: filtra ulteriormente i risultati in base a criteri specifici (categoria, ingrediente, lingua).
        # 3. $limit: limita il numero finale di risultati.
        # 4. $project: definisce i campi da restituire.
        vector_search_pipeline = [
            {
                "$vectorSearch": {
                    "index": MONGODB_VECTOR_SEARCH_INDEX_NAME, # Il nome del tuo indice di ricerca vettoriale
                    "path": "embedding",               # Il campo nel documento che contiene i vettori
                    "queryVector": query_embedding,    # Il vettore della query generato
                    "numCandidates": 250,              # Numero di candidati iniziali da considerare (aumenta per filtri $match stringenti)
                    "limit": 10                        # Numero massimo di risultati da restituire da questa fase
                }
            },
            {
                "$limit": k # Limita il numero finale di suggerimenti dopo il $match
            },
            {
                "$project": { # Seleziona i campi da restituire
                    "_id": 0, # Esclude l'ID di MongoDB per default
                    "title": 1,
                    "description": 1,
                    "category": 1,
                    "ingredients": 1, # Può essere utile per visualizzare gli ingredienti specifici
                    "vector_score": {"$meta": "vectorSearchScore"} # Include il punteggio di similarità della ricerca vettoriale
                }
            }
        ]
        
        try:
            results = list(collection.aggregate(vector_search_pipeline))
            logger.info(f"Ricerca vettoriale completata. Trovati {len(results)} risultati che soddisfano tutti i criteri.")
            if not results:
                logger.info(f"La ricerca vettoriale non ha prodotto risultati che soddisfano i criteri di $match specificati.")
        except OperationFailure as e:
            logger.error(f"Errore durante l'esecuzione della ricerca vettoriale: {e}")
            if "index not found" in str(e).lower() or "$vectorSearch" in str(e) and ("Unrecognized pipeline stage" in str(e) or "unknown operator" in str(e)):
                logger.error(f"L'indice di ricerca vettoriale '{MONGODB_VECTOR_SEARCH_INDEX_NAME}' potrebbe non esistere, non essere configurato correttamente,")
                logger.error("oppure la versione di MongoDB o la configurazione del cluster non supportano $vectorSearch.")
            else:
                logger.error("Si è verificato un problema con l'operazione di ricerca vettoriale.")
            results = [] # Assicura che i risultati siano una lista vuota in caso di errore
        except Exception as e: # Cattura altri possibili errori durante l'aggregazione
            logger.error(f"Errore imprevisto durante la pipeline di ricerca vettoriale: {e}")
            results = []

    except ConnectionFailure:
       logger.error(f"Errore: Impossibile connettersi a MongoDB a {MONGODB_URI}. Verifica l'URI e che il server sia in esecuzione.")
    except Exception as e:
        logger.error(f"Errore generico durante l'operazione con MongoDB: {e}")
    finally:
        if mongo_client:
            mongo_client.close()

    return results