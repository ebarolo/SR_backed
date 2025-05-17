from functools import lru_cache
from config import openAIclient, EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer
from typing import List as PydanticList, Optional, Dict, Any # Rinominato List per evitare conflitti

from utility import logger


def OpenAIEmbedding(text_for_embedding):
    #model= SentenceTransformer("all-MiniLM-L6-v2")
    #return model.encode(text_for_embedding).tolist()
    """Generate an embedding for the given text using OpenAI's API."""
    # Check for valid input
    if not text_for_embedding or not isinstance(text_for_embedding, str):
        logger.error(f"Error in get_embedding: input is not a valid string (type: {type(text_for_embedding).__name__}, value: '{text_for_embedding}')")
        return None
    try:
        # Call OpenAI API to get the embedding
        embedding = openAIclient.embeddings.create(input=text_for_embedding, model=EMBEDDING_MODEL).data[0].embedding
        return embedding
    except Exception as e:
        logger.error(f"Error in get_embedding during OpenAI API call for text: '{text_for_embedding[:100]}...': {e}", exc_info=True)
        return None

def SentenceTransformerEmbedding(text: str) -> Optional[PydanticList[float]]:
    """
    Genera un embedding vettoriale per il testo dato utilizzando il modello pre-caricato.
    """
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    try:
        # .tolist() converte l'array numpy (output di encode) in una lista Python standard,
        # che è il formato atteso da MongoDB per i campi vettoriali.
        embedding_vector = embedding_model.encode(text, convert_to_tensor=False).tolist()
        return embedding_vector
    except Exception as e:
        logger.error(f"Errore durante la generazione dell'embedding per il testo '{text}': {e}")
        return None
    
def get_embedding(text_for_embedding):
    match EMBEDDING_MODEL:
        case "text-embedding-3-small":
            return OpenAIEmbedding(text_for_embedding)
        case model if "sentence-transformers" in model:
                return SentenceTransformerEmbedding(text_for_embedding)
        case model if "efederici" in model:
                return SentenceTransformerEmbedding(text_for_embedding)
        case _:
            logger.error(f"Unsupported embedding model: {EMBEDDING_MODEL}")
            return None
    