import logging
from typing import List, Dict, Any

from RAG.db_layer import QdrantDBManager
from RAG.embedding_module import load_embedding_model

logger = logging.getLogger(__name__)

def initialize_app() -> QdrantDBManager:
    """
    Inizializza l'applicazione caricando il modello di embedding e preparando il DB manager.
    
    :return: Istanza di QdrantDBManager.
    """
    embeddings = load_embedding_model()
    db_manager = QdrantDBManager(embeddings=embeddings, vector_dimension=768)
    return db_manager

def add_new_recipe(
    db_manager: QdrantDBManager,
    recipe_id: str,
    title: str,
    description: str,
    ingredients: List[str],
    tags: List[str],
    nutritional_info: Dict[str, Any],
    preparation_time: int,
    cuisine_type: str
):
    """
    Aggiunge o aggiorna una ricetta nel database vettoriale.
    
    :param db_manager: Istanza di QdrantDBManager.
    :param recipe_id: Identificatore univoco della ricetta.
    :param title: Titolo della ricetta.
    :param description: Descrizione estesa della ricetta.
    :param ingredients: Lista di ingredienti principali.
    :param tags: Eventuali tag, e.g. "vegetariano", "senza glutine".
    :param nutritional_info: Informazioni nutrizionali (es. calorie, proteine).
    :param preparation_time: Tempo di preparazione in minuti.
    :param cuisine_type: Tipologia di cucina, e.g. "Italian", "Mexican".
    """
    db_manager.add_or_update_recipe(
        recipe_id=recipe_id,
        title=title,
        description=description,
        ingredients=ingredients,
        tags=tags,
        nutritional_info=nutritional_info,
        preparation_time=preparation_time,
        cuisine_type=cuisine_type
    )
    logger.info(f"Ricetta '{title}' aggiunta o aggiornata correttamente (ID: {recipe_id}).")


def search_recipes(db_manager: QdrantDBManager, query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Esegue una ricerca semantica delle ricette sulla base di una query in linguaggio naturale.
    
    :param db_manager: Istanza di QdrantDBManager.
    :param query: Query in linguaggio naturale.
    :param k: Numero di risultati da restituire.
    :return: Lista di risultati, ciascuno contenente contesto e metadati della ricetta.
    """
    results = db_manager.semantic_search(query, k=k)
    return results


def main():
    """
    Esempio di esecuzione stand-alone: inizializza il DB, aggiunge qualche ricetta e fa una ricerca.
    """

    """
    # Proviamo una ricerca in linguaggio naturale
    query = "Vorrei una ricetta italiana con pomodoro"
    logger.info(f"Eseguo la ricerca con query: '{query}'")

    results = search_recipes(db_manager, query, k=3)
    for idx, res in enumerate(results):
        metadata = res["metadata"]
        logger.info(f"Risultato {idx+1}: Ricetta ID={metadata['recipe_id']} - Titolo={metadata['title']}")
        logger.info(f"  -> context: {res['score_context']}\n")
     """
