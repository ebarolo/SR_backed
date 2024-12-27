from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer, util
import logging

# Credenziali Qdrant Cloud (da sostituire con le tue)
QDRANT_URL = "https://5aa12609-c34d-46d6-b115-8073a16dfe44.us-west-2-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "F_kU8UqayUBmVQhrNeUjy6RDtrMmOB8qbZgllaNK5CilSJoowHgKIA"
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
collectionName = 'smart_Recipe'

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

def add_recipe(recipe_for_embedding, recipeMeta):
 qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
 )
 try:
  # Carichiamo il modello
  encoder = SentenceTransformer(model_name)

 # Create collection 
  if not qdrant.collection_exists(collectionName):
   qdrant.recreate_collection(
    collection_name=collectionName,
    vectors_config=models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(), # Vector size is defined by used model
        distance=models.Distance.COSINE
    )
  )

  resp = qdrant.upload_points(
    collection_name=collectionName,
    points=[
        models.PointStruct(
            id=recipeMeta.id,
            vector=encoder.encode(recipe_for_embedding).tolist(), 
            payload=recipeMeta 
        )
    ],
  )
  return resp
 except Exception as e:
  logger.error(f"Errore durante add_recipe to qDrant : {e}")
  raise e