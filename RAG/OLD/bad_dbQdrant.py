from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Credenziali Qdrant Cloud
QDRANT_URL = "https://5aa12609-c34d-46d6-b115-8073a16dfe44.us-west-2-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "F_kU8UqayUBmVQhrNeUjy6RDtrMmOB8qbZgllaNK5CilSJoowHgKIA"

text = ["Lorem Ipsum is simply dummy text of the printing and typesetting industry..."]

def add_cocument(text, meta):
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    c_name = "test_3"

    # Crea la collezione se non esiste già
    if not client.collection_exists(c_name):
        client.create_collection(
            collection_name=c_name,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )

    # Imposta il modello
    #client.set_model("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    client.add(
        collection_name=c_name,
        documents=text
        )

    return "resp"

resp = add_cocument(text, {"source":"import recipe"})


