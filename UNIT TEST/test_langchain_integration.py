"""
Test unitari per l'integrazione Langchain
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from DB.langchain import LangchainRecipeDB
from models import RecipeDBSchema, Ingredient


class TestLangchainRecipeDB(unittest.TestCase):
    """Test per LangchainRecipeDB"""
    
    @patch('DB.langchain.OpenAIEmbeddings')
    @patch('DB.langchain.Chroma')
    @patch('DB.langchain.ChatOpenAI')
    def setUp(self, mock_chat, mock_chroma, mock_embeddings):
        """Setup per i test"""
        # Mock delle dipendenze
        self.mock_embeddings = mock_embeddings.return_value
        self.mock_vectorstore = mock_chroma.return_value
        self.mock_llm = mock_chat.return_value
        
        # Mock collection
        self.mock_collection = MagicMock()
        self.mock_collection.count.return_value = 0
        self.mock_vectorstore._collection = self.mock_collection
        
        # Inizializza database
        self.db = LangchainRecipeDB(
            openai_api_key="test-key",
            persist_directory="/tmp/test",
            collection_name="test_recipes"
        )
    
    def test_initialization(self):
        """Test inizializzazione corretta"""
        self.assertIsNotNone(self.db.embeddings)
        self.assertIsNotNone(self.db.vectorstore)
        self.assertIsNotNone(self.db.llm)
        self.assertEqual(self.db.collection_name, "test_recipes")
    
    def test_recipe_to_documents(self):
        """Test conversione ricetta in documenti"""
        recipe = RecipeDBSchema(
            title="Test Recipe",
            category=["Test"],
            preparation_time=10,
            cooking_time=20,
            ingredients=[
                Ingredient(name="test ingredient", qt=100, um="g")
            ],
            recipe_step=["Step 1", "Step 2"],
            description="Test description",
            diet="test",
            technique="test",
            language="it",
            chef_advise="Test advice",
            tags=["test"],
            nutritional_info=["Test nutrition"],
            cuisine_type="test",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="TEST001"
        )
        
        documents = self.db._recipe_to_documents(recipe)
        
        # Verifica che i documenti siano stati creati
        self.assertGreater(len(documents), 0)
        self.assertEqual(documents[0].metadata["shortcode"], "TEST001")
        self.assertEqual(documents[0].metadata["title"], "Test Recipe")
        self.assertIn("Test Recipe", documents[0].page_content)
    
    @patch('DB.langchain.logger')
    def test_add_recipe(self, mock_logger):
        """Test aggiunta ricetta"""
        recipe = RecipeDBSchema(
            title="Test Recipe",
            category=["Test"],
            preparation_time=10,
            cooking_time=20,
            ingredients=[
                Ingredient(name="test", qt=100, um="g")
            ],
            recipe_step=["Step 1"],
            description="Test",
            diet="test",
            technique="test",
            language="it",
            chef_advise=None,
            tags=["test"],
            nutritional_info=[],
            cuisine_type="test",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="TEST001"
        )
        
        # Mock del metodo add_documents
        self.mock_vectorstore.add_documents.return_value = None
        self.mock_vectorstore.persist.return_value = None
        
        result = self.db.add_recipe(recipe)
        
        # Verifica
        self.assertTrue(result)
        self.mock_vectorstore.add_documents.assert_called_once()
        self.mock_vectorstore.persist.assert_called_once()
        self.assertEqual(self.db.stats["total_recipes"], 1)
    
    def test_search_similar(self):
        """Test ricerca semantica"""
        # Mock risultati di ricerca
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "shortcode": "TEST001",
            "title": "Test Recipe",
            "category": "Test",
            "cuisine_type": "test",
            "diet": "test",
            "cooking_time": 20,
            "preparation_time": 10,
            "total_time": 30
        }
        mock_doc.page_content = "Test content"
        
        self.mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc, 0.85)
        ]
        
        # Esegui ricerca
        results = self.db.search_similar("test query", k=5)
        
        # Verifica
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["shortcode"], "TEST001")
        self.assertEqual(results[0]["score"], 0.85)
        self.mock_vectorstore.similarity_search_with_score.assert_called_once()
    
    def test_search_with_filters(self):
        """Test ricerca con filtri"""
        # Mock risultati
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "shortcode": "TEST001",
            "title": "Quick Recipe",
            "category": "Fast",
            "cuisine_type": "italian",
            "diet": "vegetarian",
            "cooking_time": 15,
            "preparation_time": 10,
            "total_time": 25
        }
        mock_doc.page_content = "Quick recipe content"
        
        self.mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc, 0.90)
        ]
        
        # Esegui ricerca con filtri
        filters = {
            "max_time": 30,
            "diet": "vegetarian"
        }
        results = self.db.search_similar("quick recipe", k=5, filter_dict=filters)
        
        # Verifica che i filtri siano stati applicati
        call_args = self.mock_vectorstore.similarity_search_with_score.call_args
        self.assertIn("filter", call_args[1])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["total_time"], 25)
    
    def test_get_statistics(self):
        """Test recupero statistiche"""
        self.mock_collection.count.return_value = 10
        
        stats = self.db.get_statistics()
        
        self.assertEqual(stats["total_documents"], 10)
        self.assertEqual(stats["estimated_recipes"], 5)  # 10 docs / 2 chunks per recipe
        self.assertEqual(stats["embedding_model"], "text-embedding-3-large")
        self.assertEqual(stats["status"], "active")
    
    def test_error_handling(self):
        """Test gestione errori"""
        # Simula errore in add_recipe
        self.mock_vectorstore.add_documents.side_effect = Exception("Test error")
        
        recipe = RecipeDBSchema(
            title="Error Recipe",
            category=["Test"],
            preparation_time=10,
            cooking_time=20,
            ingredients=[Ingredient(name="test", qt=100, um="g")],
            recipe_step=["Step 1"],
            description="Test",
            diet="test",
            technique="test",
            language="it",
            chef_advise=None,
            tags=["test"],
            nutritional_info=[],
            cuisine_type="test",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="ERROR001"
        )
        
        result = self.db.add_recipe(recipe)
        
        # Verifica che l'errore sia gestito
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()


