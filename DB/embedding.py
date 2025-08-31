from pydantic import BaseModel
from FlagEmbedding import BGEM3FlagModel

from typing import List


class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

class RecipeEmbedder:
    def __init__(self):
        self.model = BGEM3FlagModel('BAAI/bge-m3')

    async def generate_embeddings_batch(self, texts: List[str]):
     if self.model is None:
        raise "Model not loaded"
    
     try:
        
        # Generate embeddings in batch
        embeddings = self.model.encode(texts)
        result = [emb.tolist() for emb in embeddings['dense_vecs']]
        
        return {"embeddings": result}
        
     except Exception as e:
        
        raise f"Error generating embeddings: {str(e)}"

    def generate_embedding_sync(self, text: str) -> List[float]:
        """Versione sincrona per generare embedding da stringa."""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            # Generate embedding using BGEM3
            embeddings = self.model.encode([text], batch_size=512)
            # Estrai il primo embedding dalla lista (per un singolo testo)
            embedding = embeddings['dense_vecs'][0].tolist()
            
            # Debug: verifica che sia una lista di float
            if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], (int, float)):
                return embedding
            else:
                raise ValueError(f"Formato embedding non valido: {type(embedding)}, primo elemento: {type(embedding[0]) if embedding else 'vuoto'}")
            
        except Exception as e:
            raise ValueError(f"Error generating embedding: {str(e)}")
