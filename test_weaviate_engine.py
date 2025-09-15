"""
Test suite per WeaviateSemanticEngine.

Testa tutte le funzionalità della classe per la gestione
delle collection Weaviate e la ricerca semantica.

Author: Smart Recipe Team
Version: 0.7
"""

import pytest
import uuid as uuid_lib
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import della classe da testare
from RAG._weaviate import WeaviateSemanticEngine, quick_semantic_search
from models import RecipeDBSchema, Ingredient


class TestWeaviateSemanticEngine:
    """Test suite per WeaviateSemanticEngine"""
    
    @pytest.fixture
    def mock_weaviate_client(self):
        """Mock del client Weaviate per i test"""
        mock_client = Mock()
        mock_client.is_ready.return_value = True
        mock_client.collections = Mock()
        mock_client.schema = Mock()
        return mock_client
    
    @pytest.fixture
    def mock_collection(self):
        """Mock di una collection Weaviate"""
        mock_collection = Mock()
        mock_collection.data = Mock()
        mock_collection.aggregate = Mock()
        return mock_collection
    
    @pytest.fixture
    def sample_recipe(self):
        """Ricetta di esempio per i test"""
        return RecipeDBSchema(
            title="Pasta Carbonara",
            description="Classica pasta carbonara romana",
            category=["primo", "pasta"],
            preparation_time=15,
            cooking_time=10,
            ingredients=[
                Ingredient(name="pasta", qt=400, um="g"),
                Ingredient(name="uova", qt=4, um="pz"),
                Ingredient(name="guanciale", qt=200, um="g")
            ],
            recipe_step=[
                "Cuocere la pasta in acqua salata",
                "Soffriggere il guanciale",
                "Mescolare uova e pecorino",
                "Unire tutto e servire"
            ],
            language="it",
            shortcode="test_carbonara_001",
            cuisine_type="italiana",
            diet="tradizionale",
            technique="bollitura",
            chef_advise="Servire subito",
            tags=["veloce", "tradizionale"],
            nutritional_info=["proteine", "carboidrati"],
            ricetta_audio="path/to/audio.mp3",
            ricetta_caption="Trascrizione audio della ricetta"
        )
    
    @pytest.fixture
    def sample_recipes(self, sample_recipe):
        """Lista di ricette di esempio"""
        recipe2 = RecipeDBSchema(
            title="Risotto ai Funghi",
            description="Cremoso risotto ai funghi porcini",
            category=["primo", "risotto"],
            preparation_time=20,
            cooking_time=25,
            ingredients=[
                Ingredient(name="riso", qt=320, um="g"),
                Ingredient(name="funghi porcini", qt=300, um="g"),
                Ingredient(name="brodo vegetale", qt=1, um="l")
            ],
            recipe_step=[
                "Tostare il riso",
                "Aggiungere i funghi",
                "Cuocere con brodo caldo",
                "Mantecare con parmigiano"
            ],
            language="it",
            shortcode="test_risotto_002",
            cuisine_type="italiana",
            diet="vegetariano",
            technique="risottatura",
            chef_advise="Mescolare continuamente",
            tags=["cremoso", "autunnale"],
            nutritional_info=["fibre", "vitamine"],
            ricetta_audio="path/to/risotto_audio.mp3",
            ricetta_caption="Trascrizione audio del risotto"
        )
        return [sample_recipe, recipe2]
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_init_success(self, mock_client_class, mock_weaviate_client):
        """Test inizializzazione corretta della classe"""
        mock_client_class.return_value = mock_weaviate_client
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            
            assert engine.client == mock_weaviate_client
            mock_client_class.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_init_weaviate_unavailable(self, mock_client_class):
        """Test inizializzazione quando Weaviate non è disponibile"""
        with patch('RAG._weaviate.WCD_AVAILABLE', False):
            with pytest.raises(Exception, match="Weaviate non è disponibile"):
                WeaviateSemanticEngine()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_init_connection_failed(self, mock_client_class, mock_weaviate_client):
        """Test inizializzazione con connessione fallita"""
        mock_weaviate_client.is_ready.return_value = False
        mock_client_class.return_value = mock_weaviate_client
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            with pytest.raises(Exception, match="Impossibile connettersi a Weaviate"):
                WeaviateSemanticEngine()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_semantic_search_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test ricerca semantica con successo"""
        # Setup mock
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_weaviate_client.query.get.return_value.with_near_text.return_value.with_limit.return_value.with_additional.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Recipe_Vector": [
                        {
                            "title": "Pasta Carbonara",
                            "description": "Classica pasta",
                            "_additional": {"distance": 0.2, "id": "test-id"}
                        }
                    ]
                }
            }
        }
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            results = engine.semantic_search("pasta carbonara", limit=5)
            
            assert len(results) == 1
            assert results[0]["title"] == "Pasta Carbonara"
            assert results[0]["_additional"]["distance"] == 0.2
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_semantic_search_no_results(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test ricerca semantica senza risultati"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_weaviate_client.query.get.return_value.with_near_text.return_value.with_limit.return_value.with_additional.return_value.do.return_value = {
            "data": {"Get": {"Recipe_Vector": []}}
        }
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            results = engine.semantic_search("query senza risultati")
            
            assert results == []
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_create_collection_success(self, mock_client_class, mock_weaviate_client):
        """Test creazione collection con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = False
        mock_weaviate_client.schema.create_class.return_value = None
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.create_collection("test_collection")
            
            assert result is True
            mock_weaviate_client.schema.create_class.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_create_collection_already_exists(self, mock_client_class, mock_weaviate_client):
        """Test creazione collection già esistente"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.create_collection("existing_collection")
            
            assert result is True
            mock_weaviate_client.schema.create_class.assert_not_called()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_add_recipe_success(self, mock_client_class, mock_weaviate_client, mock_collection, sample_recipe):
        """Test aggiunta ricetta con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_collection.data.exists.return_value = False
        mock_collection.data.insert.return_value = None
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.add_recipe(sample_recipe)
            
            assert result is True
            mock_collection.data.insert.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_add_recipe_update_existing(self, mock_client_class, mock_weaviate_client, mock_collection, sample_recipe):
        """Test aggiornamento ricetta esistente"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_collection.data.exists.return_value = True
        mock_collection.data.update.return_value = None
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.add_recipe(sample_recipe)
            
            assert result is True
            mock_collection.data.update.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_add_recipes_batch_success(self, mock_client_class, mock_weaviate_client, mock_collection, sample_recipes):
        """Test aggiunta batch ricette con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_collection.data.exists.return_value = False
        mock_collection.data.insert.return_value = None
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.add_recipes_batch(sample_recipes)
            
            assert result is True
            assert mock_collection.data.insert.call_count == len(sample_recipes)
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_delete_recipe_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test eliminazione ricetta con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_collection.data.exists.return_value = True
        mock_collection.data.delete_by_id.return_value = None
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.delete_recipe("test_shortcode")
            
            assert result is True
            mock_collection.data.delete_by_id.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_get_recipe_by_shortcode_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test recupero ricetta per shortcode con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_collection.data.exists.return_value = True
        mock_collection.data.get_by_id.return_value = {"title": "Test Recipe", "shortcode": "test_001"}
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            result = engine.get_recipe_by_shortcode("test_001")
            
            assert result is not None
            assert result["title"] == "Test Recipe"
            mock_collection.data.get_by_id.assert_called_once()
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_get_collection_stats_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test recupero statistiche collection con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.exists.return_value = True
        mock_weaviate_client.collections.get.return_value = mock_collection
        
        # Mock per aggregate
        mock_aggregate_result = Mock()
        mock_aggregate_result.total_count = 42
        mock_collection.aggregate.over_all.return_value = mock_aggregate_result
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            stats = engine.get_collection_stats()
            
            assert stats["total_recipes"] == 42
            assert stats["exists"] is True
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_get_collection_info_success(self, mock_client_class, mock_weaviate_client):
        """Test recupero info collection con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.schema.get.return_value = {
            "classes": [
                {
                    "class": "Recipe_Vector",
                    "properties": [
                        {"name": "title"},
                        {"name": "description"}
                    ],
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {"text2vec-openai": {}}
                }
            ]
        }
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            info = engine.get_collection_info()
            
            assert info["name"] == "Recipe_Vector"
            assert "title" in info["properties"]
            assert "description" in info["properties"]
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_search_by_vector_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test ricerca per vettore con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_weaviate_client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.with_additional.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Recipe_Vector": [
                        {
                            "title": "Vector Search Result",
                            "_additional": {"distance": 0.1, "id": "vector-id"}
                        }
                    ]
                }
            }
        }
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            test_vector = [0.1, 0.2, 0.3, 0.4]
            results = engine.search_by_vector(test_vector, limit=3)
            
            assert len(results) == 1
            assert results[0]["title"] == "Vector Search Result"
    
    @patch('RAG._weaviate.weaviate.Client')
    def test_hybrid_search_success(self, mock_client_class, mock_weaviate_client, mock_collection):
        """Test ricerca ibrida con successo"""
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.collections.get.return_value = mock_collection
        mock_weaviate_client.query.get.return_value.with_hybrid.return_value.with_limit.return_value.with_additional.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Recipe_Vector": [
                        {
                            "title": "Hybrid Search Result",
                            "_additional": {"distance": 0.15, "score": 0.85, "id": "hybrid-id"}
                        }
                    ]
                }
            }
        }
        
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            engine = WeaviateSemanticEngine()
            results = engine.hybrid_search("hybrid query", alpha=0.7)
            
            assert len(results) == 1
            assert results[0]["title"] == "Hybrid Search Result"
    
    def test_close_connection(self, mock_weaviate_client):
        """Test chiusura connessione"""
        with patch('RAG._weaviate.WCD_AVAILABLE', True):
            with patch('RAG._weaviate.weaviate.Client', return_value=mock_weaviate_client):
                engine = WeaviateSemanticEngine()
                engine.close()
                
                assert engine.client is None


class TestQuickSemanticSearch:
    """Test per la funzione di utilità quick_semantic_search"""
    
    @patch('RAG._weaviate.WeaviateSemanticEngine')
    def test_quick_semantic_search_success(self, mock_engine_class):
        """Test funzione quick_semantic_search con successo"""
        # Setup mock
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.semantic_search.return_value = [{"title": "Quick Result"}]
        
        results = quick_semantic_search("test query", limit=5)
        
        assert results == [{"title": "Quick Result"}]
        mock_engine.semantic_search.assert_called_once_with("test query", 5)
        mock_engine.close.assert_called_once()
    
    @patch('RAG._weaviate.WeaviateSemanticEngine')
    def test_quick_semantic_search_exception(self, mock_engine_class):
        """Test funzione quick_semantic_search con eccezione"""
        # Setup mock per sollevare eccezione
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.semantic_search.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            quick_semantic_search("test query")
        
        mock_engine.close.assert_called_once()


class TestRecipeDBSchemaIntegration:
    """Test integrazione con RecipeDBSchema"""
    
    def test_ingredient_conversion(self):
        """Test conversione ingredienti in formato stringa"""
        ingredient = Ingredient(name="pomodoro", qt=500, um="g")
        
        # Simula la logica di conversione dalla classe
        qt_str = f"{float(ingredient.qt):g}" if ingredient.qt is not None else ""
        parts = [p for p in [qt_str, ingredient.um.strip(), ingredient.name.strip()] if p]
        result = " ".join(parts)
        
        assert result == "500 g pomodoro"
    
    def test_recipe_uuid_generation(self):
        """Test generazione UUID deterministico per ricetta"""
        shortcode = "test_recipe_123"
        
        # Simula la logica di generazione UUID dalla classe
        recipe_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, shortcode))
        
        # Verifica che l'UUID sia deterministico
        recipe_uuid2 = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, shortcode))
        assert recipe_uuid == recipe_uuid2
        
        # Verifica che shortcode diversi producano UUID diversi
        different_uuid = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, "different_shortcode"))
        assert recipe_uuid != different_uuid


if __name__ == "__main__":
    # Esegui i test se il file viene eseguito direttamente
    pytest.main([__file__, "-v", "--tb=short"])
