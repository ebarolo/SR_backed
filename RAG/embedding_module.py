import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
logger = logging.getLogger(__name__)

def load_embedding_model(model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2"):
    """
    Carica il modello di embedding da HuggingFace e restituisce un oggetto Embeddings
    compatibile con LangChain.
    
    :param model_name: Nome/Percorso del modello su HuggingFace.
    :return: Istanza di HuggingFaceEmbeddings.
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        logger.info(f"Modello di embedding '{model_name}' caricato correttamente.")
        return embeddings
    except Exception as e:
        logger.error(f"Errore durante il caricamento del modello di embedding '{model_name}': {e}")
        raise e