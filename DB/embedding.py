from functools import lru_cache
from config import openAIclient, EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer

from utility import logger


@lru_cache(maxsize=1)
def get_OpenAIEmbedding(text_for_embedding):
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

@lru_cache(maxsize=1)
def get_SentenceTransformerEmbedding(text_for_embedding):
    model = SentenceTransformer('nickprock/sentence-bert-base-italian-uncased-sts-matryoshka')
    matryoshka_dim = 768
    embeddings = model.encode(text_for_embedding,precision='float32')
    embeddings = embeddings[..., :matryoshka_dim]  # Shrink the embedding dimensions
    logger.info(f"Embedding size: {len(embeddings)}")
    return embeddings

def get_embedding(text_for_embedding):
    match EMBEDDING_MODEL:
        case "text-embedding-3-small":
            return get_OpenAIEmbedding(text_for_embedding)
        case "sentence-bert-base-italian":
            return get_SentenceTransformerEmbedding(text_for_embedding)
        case _:
            logger.error(f"Unsupported embedding model: {EMBEDDING_MODEL}")
            return None
    