
from qdrant_client import QdrantClient, models
#from fastembed import TextEmbedding
from sentence_transformers import SentenceTransformer
import logging
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Credenziali Qdrant Cloud
QDRANT_URL = "https://5aa12609-c34d-46d6-b115-8073a16dfe44.us-west-2-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "F_kU8UqayUBmVQhrNeUjy6RDtrMmOB8qbZgllaNK5CilSJoowHgKIA"
model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

class vectorEngine:
    def __init__(self, collection_name: str):
        """
        Inizializza il motore di ricerca per testi in italiano.
        """


        # Inizializza Qdrant
        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
        )

        #self.qdrant.set_model("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        #self.qdrant.set_model("sentence-transformers/distiluse-base-multilingual-cased-v2")
        self.embedder = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2', device='cpu')

        # Crea collezione se non esiste
        self.collection_name = collection_name
        self._create_collection()

    def _create_collection(self):
        """
        Crea la collezione in Qdrant se non esiste.
        """
        collections = self.qdrant.get_collections().collections
        if not any(col.name == self.collection_name for col in collections):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=512,
                    distance=models.Distance.COSINE
                )
            )
           # Definizione degli indici di payload per ricerche efficienti
            self.qdrant.create_payload_index(
             collection_name=self.collection_name,
             field_name="tags",
             field_schema=models.PayloadSchemaType.KEYWORD
            )

            self.qdrant.create_payload_index(
             collection_name=self.collection_name,
             field_name="prepration_time",
             field_schema=models.PayloadSchemaType.INTEGER
            )

            self.qdrant.create_payload_index(
             collection_name=self.collection_name,
             field_name="category",
             field_schema=models.PayloadSchemaType.KEYWORD
            )
            # Indici per gli ingredienti
            self.qdrant.create_payload_index(
              collection_name=self.collection_name,
              field_name="ingredients_text",
              field_schema=models.PayloadSchemaType.TEXT
            )

    def add_documents(self, text_for_embedding, meta):
        """
        Aggiunge documenti all'indice.

        Args:
            documents: lista di dict con 'id' e 'text'
        """

        try:
         embedding = self.embedder.encode(text_for_embedding, device='cpu')
         #print(embedding.tolist())

         result= self.qdrant.upsert(
          collection_name=self.collection_name,
          points=[
            models.PointStruct(
                id=meta["recipe_id"],
                vector=embedding.tolist(),
                payload=meta
            )
           ]
         )
         return result

        except Exception as e:
         #print(f"Error during embedding generation: {e}")
         return e

    def search(self, query, filtri=None, limite=5):
        """
        Esegue ricerca semantica.

        Args:
            query: testo della ricerca in italiano
            limit: numero massimo risultati
        """
        query_vector = self.embedder.encode(query).tolist()

        # Costruzione dei filtri
        search_filters = None

        # Initialize filter_conditions before the if statement
        filter_conditions = []

        if filtri:
            for chiave, valore in filtri.items():
                if isinstance(valore, list):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=chiave,
                            match=models.MatchAny(any=valore)
                        )
                    )
                elif isinstance(valore, tuple) and len(valore) == 2:
                    # Per range numerici (es. tempo_preparazione)
                    filter_conditions.append(
                        models.FieldCondition(
                            key=chiave,
                            range=models.Range(
                                gte=valore[0],
                                lte=valore[1]
                            )
                        )
                    )
                else:
                    filter_conditions.append(
                        models.FieldCondition(
                            key=chiave,
                            match=models.MatchValue(value=valore)
                        )
                    )
        #print("filter codition")
        #print(filter_conditions)

        if filter_conditions:
         search_filters = models.Filter(
            must=filter_conditions
         )

        risultati = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limite,
            query_filter=search_filters
        )

        return risultati