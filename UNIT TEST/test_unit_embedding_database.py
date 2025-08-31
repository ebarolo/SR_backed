"""
Unit test per RecipeEmbeddingEngine e RecipeDatabase

Test completi delle funzionalità core del sistema di embedding e database vettoriale.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import numpy as np
from typing import List, Dict, Any
import os
import tempfile
import sys

# Aggiungi path della directory parent per gli import
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Mock moduli mancanti prima degli import
torch_mock = MagicMock()
torch_mock.__spec__ = MagicMock()
torch_mock.cuda = MagicMock()
torch_mock.cuda.is_available = MagicMock(return_value=False)

transformers_mock = MagicMock()
transformers_mock.AutoTokenizer = MagicMock()

chromadb_mock = MagicMock()
chromadb_mock.config = MagicMock()
chromadb_mock.config.Settings = MagicMock()
chromadb_mock.PersistentClient = MagicMock()
chromadb_mock.Client = MagicMock()

sentence_transformers_mock = MagicMock()
sentence_transformers_mock.SentenceTransformer = MagicMock()

flagembedding_mock = MagicMock()
flagembedding_mock.BGEM3FlagModel = MagicMock()

mock_modules = {
    'FlagEmbedding': flagembedding_mock,
    'sentence_transformers': sentence_transformers_mock,
    'chromadb': chromadb_mock,
    'chromadb.config': chromadb_mock.config,
    'torch': torch_mock,
    'transformers': transformers_mock,
    'accelerate': MagicMock(),
    'tokenizers': MagicMock()
}

for module_name, mock_module in mock_modules.items():
    if module_name not in sys.modules:
        sys.modules[module_name] = mock_module

# Import delle classi da testare
from DB.embedding import RecipeEmbeddingEngine
from DB.chromaDB import RecipeDatabase
from models import RecipeDBSchema, Ingredient


class TestRecipeEmbeddingEngine(unittest.TestCase):
    """Test per la classe RecipeEmbeddingEngine"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.sample_recipe = RecipeDBSchema(
            title="Pasta al Pomodoro",
            category=["Primo Piatto", "Italiana"],
            preparation_time=15,
            cooking_time=20,
            ingredients=[
                Ingredient(name="pasta", qt=300, um="grammi"),
                Ingredient(name="pomodori", qt=400, um="grammi")
            ],
            recipe_step=[
                "Bollire l'acqua",
                "Cuocere la pasta",
                "Preparare il sugo"
            ],
            description="Classica pasta italiana",
            diet="vegetariano",
            technique="bollitura",
            language="italiano",
            chef_advise="Usare pomodori maturi",
            tags=["facile", "veloce"],
            nutritional_info=["350 kcal"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="PASTA001"
        )

    def test_init_default_model(self):
        """Test inizializzazione con modello di default"""
        with patch('DB.embedding.FLAGEMBEDDING_AVAILABLE', True):
            with patch('DB.embedding.BGEM3FlagModel') as mock_model:
                mock_model.return_value = Mock()
                engine = RecipeEmbeddingEngine()
                self.assertEqual(engine.model_name, "BAAI/bge-m3")
                self.assertIsNotNone(engine.model)

    def test_init_custom_model(self):
        """Test inizializzazione con modello personalizzato"""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_st.return_value = Mock()
            engine = RecipeEmbeddingEngine("sentence-transformers/all-MiniLM-L6-v2")
            self.assertEqual(engine.model_name, "sentence-transformers/all-MiniLM-L6-v2")
            mock_st.assert_called_once()

    def test_fallback_to_sentence_transformer(self):
        """Test fallback a SentenceTransformer quando BGE-M3 non è disponibile"""
        with patch('DB.embedding.FLAGEMBEDDING_AVAILABLE', False):
            with patch('sentence_transformers.SentenceTransformer') as mock_st:
                mock_st.return_value = Mock()
                engine = RecipeEmbeddingEngine("BAAI/bge-m3")
                self.assertEqual(engine.model_name, "sentence-transformers/all-MiniLM-L6-v2")
                mock_st.assert_called_once()

    def test_fallback_to_openai(self):
        """Test fallback a OpenAI quando tutti i modelli locali falliscono"""
        with patch('sentence_transformers.SentenceTransformer', side_effect=Exception("Modello non disponibile")):
            engine = RecipeEmbeddingEngine("sentence-transformers/test-model")
            self.assertIsNone(engine.model)
            self.assertEqual(engine.model_name, "text-embedding-3-small")

    def test_create_recipe_text_complete(self):
        """Test creazione testo ricetta con tutti i campi"""
        engine = RecipeEmbeddingEngine()
        text = engine.create_recipe_text(self.sample_recipe)
        
        self.assertIn("Ricetta: Pasta al Pomodoro", text)
        self.assertIn("Descrizione: Classica pasta italiana", text)
        self.assertIn("Ingredienti: 300.0 grammi di pasta", text)
        self.assertIn("Preparazione: Bollire l'acqua", text)
        self.assertIn("Cucina italiana", text)
        self.assertIn("Tecnica: bollitura", text)
        self.assertIn("Dieta: vegetariano", text)
        self.assertIn("Categoria: Primo Piatto, Italiana", text)
        self.assertIn("Tags: facile, veloce", text)
        self.assertIn("Consiglio: Usare pomodori maturi", text)

    def test_create_recipe_text_minimal(self):
        """Test creazione testo ricetta con campi minimi"""
        minimal_recipe = RecipeDBSchema(
            title="Pasta Semplice",
            category=["Primo"],
            ingredients=[Ingredient(name="pasta", qt=100, um="g")],
            recipe_step=["Cuocere"],
            description="Pasta base",
            language="italiano",
            shortcode="SIMPLE001"
        )
        
        engine = RecipeEmbeddingEngine()
        text = engine.create_recipe_text(minimal_recipe)
        
        self.assertIn("Ricetta: Pasta Semplice", text)
        self.assertIn("100.0 g di pasta", text)
        self.assertNotIn("Tecnica:", text)  # Campo non presente

    def test_create_recipe_text_exception_handling(self):
        """Test gestione eccezioni in create_recipe_text"""
        engine = RecipeEmbeddingEngine()
        
        # Simula errore con ingrediente None
        broken_recipe = RecipeDBSchema(
            title="Test",
            category=["Test"],
            ingredients=None,  # Questo potrebbe causare errore
            recipe_step=["Test"],
            description="Test",
            language="italiano",
            shortcode="TEST001"
        )
        
        with patch('DB.embedding.logger') as mock_logger:
            result = engine.create_recipe_text(broken_recipe)
            # Dovrebbe ritornare stringa vuota in caso di errore
            self.assertEqual(result, "")
            mock_logger.error.assert_called()

    @patch('DB.embedding.recipe_embedder.model')
    def test_encode_bge_m3_model(self, mock_model):
        """Test encoding con modello BGE-M3"""
        # Setup mock per BGE-M3
        mock_model.encode.return_value = {'dense_vecs': np.array([[0.1, 0.2, 0.3]])}
        
        engine = RecipeEmbeddingEngine()
        engine.model = mock_model
        engine.model_name = "BAAI/bge-m3"
        
        result = engine._encode_internal(["test text"], 1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 3)
        mock_model.encode.assert_called_once()

    @patch('DB.embedding.recipe_embedder.model')
    def test_encode_sentence_transformer(self, mock_model):
        """Test encoding con SentenceTransformer"""
        # Setup mock per SentenceTransformer
        mock_model.encode.return_value = np.array([[0.4, 0.5, 0.6]])
        
        engine = RecipeEmbeddingEngine()
        engine.model = mock_model
        engine.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        result = engine._encode_internal(["test text"], 1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 3)
        mock_model.encode.assert_called_once()

    @patch('DB.embedding.recipe_embedder.model')
    def test_encode_sentence_transformer_fallback_normalize(self, mock_model):
        """Test fallback per normalize_embeddings non supportato"""
        # Mock per simulare TypeError con normalize_embeddings
        def side_effect(*args, **kwargs):
            if 'normalize_embeddings' in kwargs:
                raise TypeError("unexpected keyword argument 'normalize_embeddings'")
            return np.array([[0.4, 0.5, 0.6]])
        
        mock_model.encode.side_effect = side_effect
        
        engine = RecipeEmbeddingEngine()
        engine.model = mock_model
        engine.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        with patch('numpy.linalg.norm') as mock_norm:
            mock_norm.return_value = np.array([[1.0]])
            result = engine._encode_internal(["test text"], 1)
            
            self.assertEqual(len(result), 1)
            # Verifica che sia stato chiamato il fallback
            mock_norm.assert_called()

    @patch('DB.embedding.openAIclient')
    def test_encode_openai_fallback(self, mock_client):
        """Test encoding con fallback OpenAI"""
        # Setup mock per OpenAI
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_client.embeddings.create.return_value = mock_response
        
        engine = RecipeEmbeddingEngine()
        engine.model = None  # Forza uso OpenAI
        
        result = engine._encode_internal(["test text"], 1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], [0.1, 0.2, 0.3])
        mock_client.embeddings.create.assert_called_once()

    def test_encode_recipe(self):
        """Test encoding completo di una ricetta"""
        with patch.object(RecipeEmbeddingEngine, '_encode_internal') as mock_encode:
            mock_encode.return_value = [[0.1, 0.2, 0.3]]
            
            engine = RecipeEmbeddingEngine()
            result = engine.encode_recipe(self.sample_recipe)
            
            self.assertEqual(result, [0.1, 0.2, 0.3])
            mock_encode.assert_called_once()

    def test_encode_recipe_empty_embedding(self):
        """Test gestione embedding vuoto in encode_recipe"""
        with patch.object(RecipeEmbeddingEngine, '_encode_internal') as mock_encode:
            mock_encode.return_value = []  # Embedding vuoto
            
            engine = RecipeEmbeddingEngine()
            
            with self.assertRaises(ValueError) as context:
                engine.encode_recipe(self.sample_recipe)
            
            self.assertIn("Errore generazione embedding", str(context.exception))

    def test_encode_query(self):
        """Test encoding di una query"""
        with patch.object(RecipeEmbeddingEngine, '_encode_internal') as mock_encode:
            mock_encode.return_value = [[0.4, 0.5, 0.6]]
            
            engine = RecipeEmbeddingEngine()
            result = engine.encode_query("pasta veloce")
            
            self.assertEqual(result, [0.4, 0.5, 0.6])
            mock_encode.assert_called_once()

    def test_preprocess_query(self):
        """Test pre-processing delle query"""
        engine = RecipeEmbeddingEngine()
        
        # Test espansione termini
        result = engine._preprocess_query("ricetta veloce vegetariano")
        self.assertIn("veloce facile rapido", result)
        self.assertIn("vegetariano verdure legumi", result)
        
        # Test query normale
        result = engine._preprocess_query("pasta al pomodoro")
        self.assertEqual(result, "pasta al pomodoro")

    def test_encode_caching(self):
        """Test funzionalità di caching LRU"""
        with patch.object(RecipeEmbeddingEngine, '_encode_internal') as mock_encode:
            mock_encode.return_value = [[0.1, 0.2, 0.3]]
            
            engine = RecipeEmbeddingEngine()
            
            # Prima chiamata
            result1 = engine.encode(("test text",))
            # Seconda chiamata identica (dovrebbe usare cache)
            result2 = engine.encode(("test text",))
            
            self.assertEqual(result1, result2)
            # _encode_internal dovrebbe essere chiamato solo una volta
            mock_encode.assert_called_once()


class TestRecipeDatabase(unittest.TestCase):
    """Test per la classe RecipeDatabase"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.sample_recipe = RecipeDBSchema(
            title="Risotto ai Funghi",
            category=["Primo Piatto"],
            preparation_time=10,
            cooking_time=25,
            ingredients=[
                Ingredient(name="riso", qt=320, um="grammi"),
                Ingredient(name="funghi", qt=200, um="grammi")
            ],
            recipe_step=["Preparare il brodo", "Tostare il riso"],
            description="Risotto cremoso ai funghi",
            diet="vegetariano",
            technique="mantecatura",
            language="italiano",
            chef_advise="Mantecare bene",
            tags=["cremoso"],
            cuisine_type="italiana",
            shortcode="RISOTTO001"
        )

    @patch('DB.chromaDB.CHROMADB_AVAILABLE', True)
    @patch('DB.chromaDB.chromadb')
    def test_initialize_database_local(self, mock_chromadb):
        """Test inizializzazione database locale"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        with patch('DB.chromaDB.USE_LOCAL_CHROMA', True):
            with patch('DB.chromaDB.CHROMA_LOCAL_PATH', '/test/path'):
                db = RecipeDatabase()
                
                self.assertIsNotNone(db.client)
                self.assertIsNotNone(db.collection)
                mock_chromadb.PersistentClient.assert_called_once_with(path='/test/path')

    @patch('DB.chromaDB.CHROMADB_AVAILABLE', True)
    @patch('DB.chromaDB.chromadb')
    def test_initialize_database_memory(self, mock_chromadb):
        """Test inizializzazione database in-memory"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.Client.return_value = mock_client
        
        with patch('DB.chromaDB.USE_LOCAL_CHROMA', False):
            db = RecipeDatabase()
            
            self.assertIsNotNone(db.client)
            self.assertIsNotNone(db.collection)
            mock_chromadb.Client.assert_called_once()

    @patch('DB.chromaDB.CHROMADB_AVAILABLE', False)
    def test_initialize_database_unavailable(self):
        """Test inizializzazione quando ChromaDB non è disponibile"""
        db = RecipeDatabase()
        
        self.assertIsNone(db.client)
        self.assertIsNone(db.collection)

    @patch('DB.chromaDB.CHROMADB_AVAILABLE', True)
    @patch('DB.chromaDB.chromadb')
    def test_initialize_database_exception(self, mock_chromadb):
        """Test gestione eccezioni durante inizializzazione"""
        mock_chromadb.Client.side_effect = Exception("Connection failed")
        
        with patch('DB.chromaDB.logger') as mock_logger:
            db = RecipeDatabase()
            
            self.assertIsNone(db.client)
            self.assertIsNone(db.collection)
            mock_logger.error.assert_called()

    def test_add_recipe_no_collection(self):
        """Test aggiunta ricetta senza collection disponibile"""
        db = RecipeDatabase()
        db.collection = None
        
        result = db.add_recipe(self.sample_recipe)
        
        self.assertFalse(result)

    @patch('DB.chromaDB.recipe_embedder')
    def test_add_recipe_success(self, mock_embedder):
        """Test aggiunta ricetta con successo"""
        # Setup mocks
        mock_embedder.encode_recipe.return_value = [0.1, 0.2, 0.3]
        mock_embedder.create_recipe_text.return_value = "Risotto cremoso"
        
        mock_collection = Mock()
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        result = db.add_recipe(self.sample_recipe)
        
        self.assertTrue(result)
        mock_collection.add.assert_called_once()
        
        # Verifica parametri chiamata
        call_args = mock_collection.add.call_args
        self.assertEqual(call_args[1]['embeddings'], [[0.1, 0.2, 0.3]])
        self.assertEqual(call_args[1]['documents'], ["Risotto cremoso"])
        self.assertEqual(call_args[1]['ids'], ["RISOTTO001"])
        
        # Verifica metadati
        metadata = call_args[1]['metadatas'][0]
        self.assertEqual(metadata['title'], "Risotto ai Funghi")
        self.assertEqual(metadata['shortcode'], "RISOTTO001")
        self.assertEqual(metadata['category'], "Primo Piatto")

    @patch('DB.chromaDB.recipe_embedder')
    def test_add_recipe_embedding_error(self, mock_embedder):
        """Test gestione errore durante generazione embedding"""
        mock_embedder.encode_recipe.side_effect = ValueError("Embedding error")
        
        mock_collection = Mock()
        db = RecipeDatabase()
        db.collection = mock_collection
        
        with patch('DB.chromaDB.logger') as mock_logger:
            result = db.add_recipe(self.sample_recipe)
            
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_search_no_collection(self):
        """Test ricerca senza collection disponibile"""
        db = RecipeDatabase()
        db.collection = None
        
        result = db.search("pasta")
        
        self.assertEqual(result, [])

    @patch('DB.chromaDB.recipe_embedder')
    def test_search_success(self, mock_embedder):
        """Test ricerca con successo"""
        # Setup mock embedding
        mock_embedder.encode_query.return_value = [0.4, 0.5, 0.6]
        
        # Setup mock risultati
        mock_collection = Mock()
        mock_results = {
            "ids": [["RISOTTO001", "PASTA001"]],
            "distances": [[0.2, 0.3]],
            "metadatas": [[
                {
                    "title": "Risotto ai Funghi",
                    "shortcode": "RISOTTO001",
                    "category": "Primo Piatto",
                    "cuisine_type": "italiana",
                    "cooking_time": 25,
                    "preparation_time": 10
                },
                {
                    "title": "Pasta al Pomodoro",
                    "shortcode": "PASTA001",
                    "category": "Primo Piatto",
                    "cuisine_type": "italiana",
                    "cooking_time": 20,
                    "preparation_time": 15
                }
            ]]
        }
        mock_collection.query.return_value = mock_results
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        result = db.search("risotto", limit=5)
        
        self.assertEqual(len(result), 2)
        
        # Verifica primo risultato
        first_result = result[0]
        self.assertEqual(first_result["_id"], "RISOTTO001")
        self.assertEqual(first_result["title"], "Risotto ai Funghi")
        self.assertEqual(first_result["score"], 0.8)  # 1.0 - 0.2
        self.assertEqual(first_result["category"], ["Primo Piatto"])
        
        # Verifica chiamata query
        mock_collection.query.assert_called_once_with(
            query_embeddings=[[0.4, 0.5, 0.6]],
            n_results=5,
            where=None
        )

    @patch('DB.chromaDB.recipe_embedder')
    def test_search_with_filters(self, mock_embedder):
        """Test ricerca con filtri"""
        mock_embedder.encode_query.return_value = [0.1, 0.2, 0.3]
        
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]]
        }
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        filters = {
            "max_time": 30,
            "category": "Primo Piatto",
            "cuisine": "italiana"
        }
        
        db.search("pasta", filters=filters)
        
        # Verifica filtri Where
        call_args = mock_collection.query.call_args
        where_clause = call_args[1]['where']
        
        self.assertEqual(where_clause["cooking_time"]["$lte"], 30)
        self.assertEqual(where_clause["category"]["$eq"], "Primo Piatto")
        self.assertEqual(where_clause["cuisine_type"]["$eq"], "italiana")

    @patch('DB.chromaDB.recipe_embedder')
    def test_search_exception(self, mock_embedder):
        """Test gestione eccezioni durante ricerca"""
        mock_embedder.encode_query.side_effect = Exception("Query error")
        
        mock_collection = Mock()
        db = RecipeDatabase()
        db.collection = mock_collection
        
        with patch('DB.chromaDB.logger') as mock_logger:
            result = db.search("pasta")
            
            self.assertEqual(result, [])
            mock_logger.error.assert_called()

    def test_get_by_shortcode_no_collection(self):
        """Test get_by_shortcode senza collection"""
        db = RecipeDatabase()
        db.collection = None
        
        result = db.get_by_shortcode("TEST001")
        
        self.assertIsNone(result)

    def test_get_by_shortcode_success(self):
        """Test get_by_shortcode con successo"""
        mock_collection = Mock()
        mock_results = {
            "ids": ["RISOTTO001"],
            "metadatas": [{
                "title": "Risotto ai Funghi",
                "category": "Primo Piatto",
                "cuisine_type": "italiana",
                "cooking_time": 25,
                "preparation_time": 10
            }]
        }
        mock_collection.get.return_value = mock_results
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        result = db.get_by_shortcode("RISOTTO001")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "RISOTTO001")
        self.assertEqual(result["title"], "Risotto ai Funghi")
        self.assertEqual(result["category"], ["Primo Piatto"])
        
        mock_collection.get.assert_called_once_with(ids=["RISOTTO001"])

    def test_get_by_shortcode_not_found(self):
        """Test get_by_shortcode quando ricetta non trovata"""
        mock_collection = Mock()
        mock_collection.get.return_value = {"ids": []}
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        result = db.get_by_shortcode("NOTFOUND")
        
        self.assertIsNone(result)

    def test_get_stats_no_collection(self):
        """Test statistiche senza collection"""
        db = RecipeDatabase()
        db.collection = None
        
        result = db.get_stats()
        
        self.assertEqual(result["total_recipes"], 0)
        self.assertEqual(result["collection_name"], "unavailable")
        self.assertEqual(result["status"], "ChromaDB not available")

    def test_get_stats_success(self):
        """Test statistiche con successo"""
        mock_collection = Mock()
        mock_collection.count.return_value = 42
        mock_collection.name = "smartRecipe"
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        result = db.get_stats()
        
        self.assertEqual(result["total_recipes"], 42)
        self.assertEqual(result["collection_name"], "smartRecipe")
        self.assertEqual(result["status"], "active")

    def test_get_stats_exception(self):
        """Test gestione eccezioni in get_stats"""
        mock_collection = Mock()
        mock_collection.count.side_effect = Exception("Stats error")
        
        db = RecipeDatabase()
        db.collection = mock_collection
        
        with patch('DB.chromaDB.logger') as mock_logger:
            result = db.get_stats()
            
            self.assertEqual(result["total_recipes"], 0)
            self.assertEqual(result["collection_name"], "error")
            self.assertIn("error:", result["status"])
            mock_logger.error.assert_called()


class TestCompatibilityFunctions(unittest.TestCase):
    """Test per le funzioni di compatibilità"""
    
    @patch('DB.chromaDB.recipe_db')
    def test_ingest_json_to_chroma(self, mock_recipe_db):
        """Test funzione di compatibilità ingest_json_to_chroma"""
        from DB.chromaDB import ingest_json_to_chroma
        
        # Setup mock
        mock_recipe_db.collection = Mock()
        mock_recipe_db.add_recipe.side_effect = [True, False, True]  # 2 successi, 1 fallimento
        
        # Dati test
        recipes = [Mock(), Mock(), Mock()]
        
        result_count, result_name = ingest_json_to_chroma(recipes, "test_collection")
        
        self.assertEqual(result_count, 2)  # 2 successi
        self.assertEqual(result_name, "test_collection")
        self.assertEqual(mock_recipe_db.add_recipe.call_count, 3)

    @patch('DB.chromaDB.recipe_db')
    def test_search_recipes_chroma(self, mock_recipe_db):
        """Test funzione di compatibilità search_recipes_chroma"""
        from DB.chromaDB import search_recipes_chroma
        
        expected_results = [{"title": "Test Recipe"}]
        mock_recipe_db.search.return_value = expected_results
        
        result = search_recipes_chroma("test query", limit=5, filters={"category": "test"})
        
        self.assertEqual(result, expected_results)
        mock_recipe_db.search.assert_called_once_with("test query", 5, {"category": "test"})

    @patch('DB.chromaDB.recipe_db')
    def test_get_recipe_by_shortcode_chroma(self, mock_recipe_db):
        """Test funzione di compatibilità get_recipe_by_shortcode_chroma"""
        from DB.chromaDB import get_recipe_by_shortcode_chroma
        
        expected_result = {"_id": "TEST001", "title": "Test Recipe"}
        mock_recipe_db.get_by_shortcode.return_value = expected_result
        
        result = get_recipe_by_shortcode_chroma("TEST001")
        
        self.assertEqual(result, expected_result)
        mock_recipe_db.get_by_shortcode.assert_called_once_with("TEST001")


if __name__ == "__main__":
    # Configurazione logging per i test
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Esegui i test
    unittest.main(verbosity=2)
