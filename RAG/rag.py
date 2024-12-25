from RAG.db_layer import QdrantCloudManager
from qdrant_client.http import models

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

# Aggiungi alcuni documenti di esempio
 return qdrant.add_document(
   text=text,
    metadata=meta
  )

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