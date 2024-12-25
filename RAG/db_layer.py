from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from typing import List, Dict, Optional, Union
from datetime import datetime

class QdrantCloudManager:
    def __init__(
        self,
        api_key: str,
        url: str,
        collection_name: str,
        prefer_grpc: bool = True
    ):
        """
        Inizializza il manager per Qdrant Cloud
        
        Args:
            api_key: API key di Qdrant Cloud
            url: URL dell'istanza Qdrant Cloud (es: 'https://xxxx.qdrant.tech')
            collection_name: Nome della collezione
            prefer_grpc: Usa gRPC invece di REST quando possibile
        """
        # Inizializza l'embedder multilingue
        self.model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
        
        # Connessione a Qdrant Cloud
        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            prefer_grpc=prefer_grpc
        )
        
        self.collection_name = collection_name
        self.vector_size = 512  # Dimensione del vettore per distiluse-base-multilingual-cased-v2
        
        # Inizializza la collezione
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Inizializza la collezione se non esiste"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # La collezione non esiste, la creiamo
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            # Creiamo gli indici per ottimizzare le ricerche
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="timestamp",
                field_schema="datetime"
            )
    
    def add_document(
        self,
        text: str,
        metadata: Dict = None,
        id: Optional[int] = None
    ) -> int:
        """
        Aggiunge un documento alla collezione
        
        Args:
            text: Testo da memorizzare
            metadata: Metadata aggiuntivi
            id: ID personalizzato (opzionale)
            
        Returns:
            ID del documento inserito
        """
        # Genera l'embedding
        embedding = self.model.encode(text)
        
        # Prepara il payload
        payload = metadata or {}
        payload.update({
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Se non viene fornito un ID, ne generiamo uno basato sul timestamp
        if id is None:
            id = int(datetime.now().timestamp() * 1000)
        
        # Inserisce il punto
        self.client.upsert(
            collection_name=self.collection_name,
            points=[models.PointStruct(
                id=id,
                vector=embedding.tolist(),
                payload=payload
            )]
        )
        
        return id
    
    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = 0.7,
        filter_conditions: Optional[List[models.FieldCondition]] = None
    ) -> List[Dict]:
        """
        Cerca documenti simili alla query
        
        Args:
            query: Testo da cercare
            limit: Numero massimo di risultati
            score_threshold: Soglia minima di similarità (0-1)
            filter_conditions: Lista di condizioni di filtro aggiuntive
            
        Returns:
            Lista di dizionari con i risultati e i metadata
        """
        # Genera l'embedding della query
        query_vector = self.model.encode(query).tolist()
        
        # Esegue la ricerca
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=models.Filter(
                must=filter_conditions
            ) if filter_conditions else None
        )
        
        # Formatta i risultati
        return [
            {
                "id": hit.id,
                "score": hit.score,
                **hit.payload
            }
            for hit in results
        ]
    
    def delete_documents(self, ids: Union[int, List[int]]):
        """
        Elimina uno o più documenti dalla collezione
        
        Args:
            ids: ID singolo o lista di ID da eliminare
        """
        if isinstance(ids, int):
            ids = [ids]
            
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points=ids
            )
        )
    
    def get_collection_info(self) -> Dict:
        """
        Ottiene informazioni sulla collezione
        
        Returns:
            Dizionario con le informazioni della collezione
        """
        return self.client.get_collection(self.collection_name).dict()
