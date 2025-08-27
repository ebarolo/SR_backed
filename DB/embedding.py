import torch
from functools import lru_cache
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
from config import openAIclient, EMBEDDING_MODEL
from utility import logger, ensure_text_within_token_limit
from models import RecipeDBSchema

# Import opzionali gestiti nei metodi
try:
    from FlagEmbedding import BGEM3FlagModel
    FLAGEMBEDDING_AVAILABLE = True
    logger.info("FlagEmbedding disponibile")
except ImportError:
    BGEM3FlagModel = None
    FLAGEMBEDDING_AVAILABLE = False
    logger.warning("FlagEmbedding non disponibile - funzionalità BGE-M3 limitata")

class RecipeEmbeddingEngine:
    """
    Sistema di embedding ottimizzato per ricette culinarie italiane usando BGE-M3
    """
    
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Inizializza il motore di embedding
        
        Args:
            model_name: Nome del modello da utilizzare (default BGE-M3)
        """
        self.model_name = model_name
        self.model = None
        logger.info(f"Modello di embedding: {self.model_name}")

        self._initialize_model()
        
    def _initialize_model(self):
        """Inizializza il modello di embedding appropriato con fallback robusti"""
        logger.info(f"Inizializza il modello di embedding: {self.model_name}")
        try:
            if self.model_name == "BAAI/bge-m3":
                logger.info(f"FLAGEMBEDDING_AVAILABLE {FLAGEMBEDDING_AVAILABLE}")
                if not FLAGEMBEDDING_AVAILABLE or BGEM3FlagModel is None:
                    logger.warning("FlagEmbedding non disponibile, fallback a SentenceTransformer")
                    self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                    self.model = SentenceTransformer(self.model_name)
                else:
                    try:
                        self.model = BGEM3FlagModel(
                            self.model_name,
                            use_fp16=True,  # Riduce memoria del 50%
                            device='cuda' if torch.cuda.is_available() else 'cpu'
                        )
                        logger.info(f"Modello BGE-M3 caricato con successo")
                    except Exception as e:
                        logger.warning(f"Errore caricamento BGE-M3: {e}")
                        logger.info("Fallback a SentenceTransformer")
                        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                        self.model = SentenceTransformer(self.model_name)
                    
            elif "sentence-transformers" in self.model_name:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Modello SentenceTransformer caricato: {self.model_name}")
            else:
                logger.warning(f"Modello non riconosciuto: {self.model_name}, uso OpenAI API")
                self.model = None  # Userà OpenAI API
                
        except Exception as e:
            logger.error(f"Errore caricamento modello {self.model_name}: {e}")
            logger.warning("Fallback a modalità solo-OpenAI")
            self.model = None
            self.model_name = "text-embedding-3-small"
    
    def create_recipe_text(self, recipe_data: RecipeDBSchema) -> str:
        """
        Crea testo ottimizzato per embedding di ricette italiane
        
        Args:
            recipe_data: Oggetto RecipeDBSchema con dati della ricetta
            
        Returns:
            Testo strutturato per embedding semantico
        """
        components = []
        
        # 1. Titolo e descrizione (peso semantico alto)
        if recipe_data.title:
            components.append(f"Ricetta: {recipe_data.title}")
        
        if recipe_data.description:
            components.append(f"Descrizione: {recipe_data.description}")
        
        # 2. Ingredienti (cruciale per ricerca)
        if recipe_data.ingredients:
            ingredients_text = "Ingredienti: " + ", ".join([
                f"{ing.qt} {ing.um} di {ing.name}"
                for ing in recipe_data.ingredients
            ])
            components.append(ingredients_text)
        
        # 3. Preparazione (tecniche culinarie)
        if recipe_data.recipe_step:
            steps = " ".join(recipe_data.recipe_step)
            components.append(f"Preparazione: {steps[:300]}")  # Limita lunghezza
        
        # 4. Metadati culinari
        culinary_info = []
        
        if recipe_data.cuisine_type:
            culinary_info.append(f"Cucina {recipe_data.cuisine_type}")
        
        if recipe_data.technique:
            culinary_info.append(f"Tecnica: {recipe_data.technique}")
        
        if recipe_data.diet:
            culinary_info.append(f"Dieta: {recipe_data.diet}")
        
        if recipe_data.category:
            categories = recipe_data.category if isinstance(recipe_data.category, list) else [recipe_data.category]
            culinary_info.append(f"Categoria: {', '.join(categories)}")
        
        if culinary_info:
            components.append(" ".join(culinary_info))
        
        # 5. Tags e consigli
        if recipe_data.tags:
            tags = recipe_data.tags if isinstance(recipe_data.tags, list) else [recipe_data.tags]
            components.append(f"Tags: {', '.join(tags)}")
        
        if recipe_data.chef_advise:
            components.append(f"Consiglio: {recipe_data.chef_advise}")
        
        # Combina con separatori semantici
        embedding_text = " | ".join(filter(None, components))
        
        # Assicura rispetto limiti del modello
        return ensure_text_within_token_limit(embedding_text)
    
    @lru_cache(maxsize=500)  # Cache per embedding frequenti
    def encode(self, texts: Union[str, tuple], batch_size: int = 16) -> List[List[float]]:
        """
        Genera embeddings ottimizzati (con cache LRU)
        
        Args:
            texts: Testo singolo o tupla di testi (tupla per cache)
            batch_size: Dimensione batch per elaborazione
            
        Returns:
            Lista di embeddings normalizzati
        """
        # Converte tuple in lista per elaborazione
        if isinstance(texts, tuple):
            texts_list = list(texts)
        elif isinstance(texts, str):
            texts_list = [texts]
        else:
            texts_list = texts
        
        return self._encode_internal(texts_list, batch_size)
    
    def _encode_internal(self, texts: List[str], batch_size: int) -> List[List[float]]:
        """Implementazione interna per encoding con gestione robusta dei fallback"""
        
        try:
            # Se non c'è modello caricato, usa OpenAI
            logger.info(f"encode_internal self.model is {self.model}")
            if self.model is None:
                logger.info("Uso OpenAI API per embedding")
                results = []
                for text in texts:
                    embedding = self._openai_embedding(text)
                    if embedding:
                        results.append(embedding)
                    else:
                        results.append([0.0] * 1536)  # Dimensione OpenAI default
                return results
            
            # Gestisci diversi tipi di modelli
            if self.model_name == "BAAI/bge-m3" and hasattr(self.model, 'encode'):
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    max_length=512,  # Ottimale per ricette
                    normalize_embeddings=True,  # Importante per cosine similarity
                    show_progress_bar=len(texts) > 10
                )
                # BGE-M3 ritorna un dict con 'dense_vecs'
                if isinstance(embeddings, dict) and 'dense_vecs' in embeddings:
                    return embeddings['dense_vecs'].tolist()
                else:
                    return embeddings.tolist()
                
            elif "sentence-transformers" in self.model_name and hasattr(self.model, 'encode'):
                try:
                    # Prova prima con normalize_embeddings (versioni recenti)
                    embeddings = self.model.encode(
                        texts,
                        batch_size=batch_size,
                        normalize_embeddings=True,
                        show_progress_bar=len(texts) > 10
                    )
                except TypeError:
                    # Fallback per versioni vecchie senza normalize_embeddings
                    logger.info("normalize_embeddings non supportato, uso normalizzazione manuale")
                    embeddings = self.model.encode(
                        texts,
                        batch_size=batch_size,
                        show_progress_bar=len(texts) > 10
                    )
                    # Normalizzazione manuale
                    import numpy as np
                    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                
                return embeddings.tolist()
                
            else:
                # Fallback OpenAI per casi non gestiti
                logger.warning(f"Modello non riconosciuto, uso OpenAI API: {self.model_name}")
                results = []
                for text in texts:
                    embedding = self._openai_embedding(text)
                    if embedding:
                        results.append(embedding)
                    else:
                        results.append([0.0] * 1536)  # Dimensione OpenAI
                return results
        
        except Exception as e:
            logger.error(f"Errore generazione embedding: {e}")
            # Ritorna embeddings vuoti con dimensione appropriata invece di lista vuota
            if self.model_name and "sentence-transformers" in self.model_name:
                embedding_dim = 384  # Dimensione tipica per MiniLM
            else:
                embedding_dim = 1536  # Dimensione OpenAI
            return [[0.0] * embedding_dim for _ in texts]
    
    def _openai_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding usando OpenAI API"""
        try:
            if not text or not isinstance(text, str):
                return None
            
            response = openAIclient.embeddings.create(
                input=text, 
                model=self.model_name
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Errore OpenAI embedding: {e}")
            return None
    
    def encode_recipe(self, recipe_data: RecipeDBSchema) -> List[float]:
        """
        Genera embedding per una singola ricetta
        
        Args:
            recipe_data: Oggetto RecipeDBSchema con dati della ricetta
            
        Returns:
            Embedding normalizzato
        """
        logger.info(f"start encode_recipe self.model is {self.model}")
        recipe_text = self.create_recipe_text(recipe_data)
        logger.info(f"recipe_text is {recipe_text}")
        # Usa tupla per cache LRU
        embeddings = self.encode((recipe_text,))
        if not embeddings or len(embeddings) == 0:
            logger.error("Impossibile generare embedding per ricetta")
            raise ValueError("Errore generazione embedding per ricetta")
        return embeddings[0]
    
    def encode_query(self, query: str) -> List[float]:
        """
        Genera embedding per query di ricerca
        
        Args:
            query: Query dell'utente
            
        Returns:
            Embedding della query
        """
        processed_query = self._preprocess_query(query)
        embeddings = self.encode((processed_query,))
        if not embeddings or len(embeddings) == 0:
            logger.error("Impossibile generare embedding per query")
            raise ValueError("Errore generazione embedding per query")
        return embeddings[0]
    
    def _preprocess_query(self, query: str) -> str:
        """Pre-processa query per ricerca ottimale"""
        # Espansioni semantiche per termini culinari italiani
        culinary_expansions = {
            "veloce": "veloce facile rapido semplice",
            "vegetariano": "vegetariano verdure legumi senza carne",
            "primo": "primo piatto pasta riso risotto",
            "secondo": "secondo piatto carne pesce",
            "dolce": "dolce dessert torta",
            "antipasto": "antipasto aperitivo"
        }
        
        expanded_query = query.lower()
        for term, expansion in culinary_expansions.items():
            if term in expanded_query:
                expanded_query = expanded_query.replace(term, expansion)
        
        return expanded_query

# Funzione di compatibilità per codice esistente
def get_embedding(text_for_embedding):
    """
    Funzione di compatibilità per codice esistente
    DEPRECATA: Usa recipe_embedder.encode() invece
    """
    logger.warning("get_embedding() è deprecata, usa recipe_embedder.encode()")
    if isinstance(text_for_embedding, list):
        return recipe_embedder.encode(text_for_embedding)
    else:
        return recipe_embedder.encode([text_for_embedding])[0]

# Istanza globale ottimizzata
recipe_embedder = RecipeEmbeddingEngine(EMBEDDING_MODEL)  
