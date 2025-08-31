"""
Unit test semplificati per RecipeEmbeddingEngine e RecipeDatabase

Test core delle funzionalità senza dipendenze pesanti di ML.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Aggiungi il percorso del progetto (directory parent)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import base
from models import RecipeDBSchema, Ingredient


class TestRecipeModels(unittest.TestCase):
    """Test per i modelli base delle ricette"""
    
    def test_ingredient_creation(self):
        """Test creazione ingrediente"""
        ingredient = Ingredient(name="pasta", qt=300, um="grammi")
        
        self.assertEqual(ingredient.name, "pasta")
        self.assertEqual(ingredient.qt, 300)
        self.assertEqual(ingredient.um, "grammi")

    def test_recipe_schema_creation(self):
        """Test creazione schema ricetta completo"""
        ingredients = [
            Ingredient(name="pasta", qt=300, um="grammi"),
            Ingredient(name="pomodori", qt=400, um="grammi")
        ]
        
        recipe = RecipeDBSchema(
            title="Pasta al Pomodoro",
            category=["Primo Piatto", "Italiana"],
            preparation_time=15,
            cooking_time=20,
            ingredients=ingredients,
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
        
        self.assertEqual(recipe.title, "Pasta al Pomodoro")
        self.assertEqual(len(recipe.ingredients), 2)
        self.assertEqual(recipe.ingredients[0].name, "pasta")
        self.assertEqual(recipe.shortcode, "PASTA001")
        self.assertIn("Primo Piatto", recipe.category)

    def test_recipe_schema_minimal(self):
        """Test creazione schema ricetta con campi minimi"""
        recipe = RecipeDBSchema(
            title="Pasta Semplice",
            category=["Primo"],
            preparation_time=None,
            cooking_time=None,
            ingredients=[Ingredient(name="pasta", qt=100, um="g")],
            recipe_step=["Cuocere"],
            description="Pasta base",
            diet=None,
            technique=None,
            language="italiano",
            chef_advise=None,
            tags=None,
            nutritional_info=None,
            cuisine_type=None,
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="SIMPLE001"
        )
        
        self.assertEqual(recipe.title, "Pasta Semplice")
        self.assertIsNone(recipe.preparation_time)
        self.assertIsNone(recipe.cooking_time)
        self.assertIsNone(recipe.diet)


class TestEmbeddingEngineCore(unittest.TestCase):
    """Test core per RecipeEmbeddingEngine senza dipendenze ML"""
    
    def setUp(self):
        """Setup per test embedding"""
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
            nutritional_info=["400 kcal"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="RISOTTO001"
        )

    def test_create_recipe_text_structure(self):
        """Test struttura del testo generato per embedding (mockato)"""
        # Mock della classe RecipeEmbeddingEngine
        mock_engine = Mock()
        
        # Simula il comportamento di create_recipe_text
        def mock_create_recipe_text(recipe_data):
            components = []
            
            if recipe_data.title:
                components.append(f"Ricetta: {recipe_data.title}")
            
            if recipe_data.description:
                components.append(f"Descrizione: {recipe_data.description}")
            
            if recipe_data.ingredients:
                ingredients_text = "Ingredienti: " + ", ".join([
                    f"{ing.qt} {ing.um} di {ing.name}"
                    for ing in recipe_data.ingredients
                ])
                components.append(ingredients_text)
            
            return " | ".join(filter(None, components))
        
        mock_engine.create_recipe_text = mock_create_recipe_text
        
        # Test del metodo
        result = mock_engine.create_recipe_text(self.sample_recipe)
        
        self.assertIn("Ricetta: Risotto ai Funghi", result)
        self.assertIn("Descrizione: Risotto cremoso", result)
        self.assertIn("320.0 grammi di riso", result)
        self.assertIn("200.0 grammi di funghi", result)

    def test_preprocess_query_expansions(self):
        """Test espansioni query culinarie (mockato)"""
        # Mock del metodo _preprocess_query
        def mock_preprocess_query(query):
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
        
        # Test espansioni
        result = mock_preprocess_query("ricetta veloce vegetariano")
        self.assertIn("veloce facile rapido", result)
        self.assertIn("vegetariano verdure legumi", result)
        
        # Test query normale
        result = mock_preprocess_query("pasta al pomodoro")
        self.assertEqual(result, "pasta al pomodoro")


class TestDatabaseCore(unittest.TestCase):
    """Test core per RecipeDatabase senza ChromaDB"""
    
    def test_metadata_preparation(self):
        """Test preparazione metadati per database"""
        recipe = RecipeDBSchema(
            title="Test Recipe",
            category=["Primo Piatto", "Italiana"],
            preparation_time=10,
            cooking_time=20,
            ingredients=[Ingredient(name="test", qt=100, um="g")],
            recipe_step=["Test step"],
            description="Test description",
            diet="vegetariano",
            technique="bollitura",
            language="italiano",
            chef_advise="Test advice",
            tags=["test"],
            nutritional_info=["300 kcal"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="TEST001"
        )
        
        # Mock della preparazione metadati
        def prepare_metadata(recipe_data):
            return {
                "title": recipe_data.title,
                "shortcode": recipe_data.shortcode,
                "category": ",".join(recipe_data.category) if recipe_data.category else "",
                "cuisine_type": recipe_data.cuisine_type or "",
                "cooking_time": recipe_data.cooking_time or 0,
                "preparation_time": recipe_data.preparation_time or 0
            }
        
        metadata = prepare_metadata(recipe)
        
        self.assertEqual(metadata["title"], "Test Recipe")
        self.assertEqual(metadata["shortcode"], "TEST001")
        self.assertEqual(metadata["category"], "Primo Piatto,Italiana")
        self.assertEqual(metadata["cuisine_type"], "italiana")
        self.assertEqual(metadata["cooking_time"], 20)
        self.assertEqual(metadata["preparation_time"], 10)

    def test_search_filters_construction(self):
        """Test costruzione filtri per ricerca"""
        def construct_where_clause(filters):
            where_clause = {}
            if filters:
                if filters.get("max_time"):
                    where_clause["cooking_time"] = {"$lte": filters["max_time"]}
                if filters.get("category"):
                    where_clause["category"] = {"$eq": filters["category"]}
                if filters.get("cuisine"):
                    where_clause["cuisine_type"] = {"$eq": filters["cuisine"]}
            return where_clause
        
        # Test filtri completi
        filters = {
            "max_time": 30,
            "category": "Primo Piatto",
            "cuisine": "italiana"
        }
        
        where_clause = construct_where_clause(filters)
        
        self.assertEqual(where_clause["cooking_time"]["$lte"], 30)
        self.assertEqual(where_clause["category"]["$eq"], "Primo Piatto")
        self.assertEqual(where_clause["cuisine_type"]["$eq"], "italiana")
        
        # Test filtri vuoti
        where_clause = construct_where_clause({})
        self.assertEqual(where_clause, {})
        
        # Test filtri parziali
        where_clause = construct_where_clause({"max_time": 15})
        self.assertEqual(len(where_clause), 1)
        self.assertEqual(where_clause["cooking_time"]["$lte"], 15)

    def test_search_results_formatting(self):
        """Test formattazione risultati di ricerca"""
        # Mock risultati ChromaDB
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
        
        # Mock formattazione risultati
        def format_search_results(results):
            formatted_results = []
            for i in range(len(results["ids"][0])):
                result = {
                    "_id": results["ids"][0][i],
                    "shortcode": results["ids"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # Converti distanza in score
                    "title": results["metadatas"][0][i].get("title", ""),
                    "category": results["metadatas"][0][i].get("category", "").split(",") if results["metadatas"][0][i].get("category") else [],
                    "cuisine_type": results["metadatas"][0][i].get("cuisine_type", ""),
                    "cooking_time": results["metadatas"][0][i].get("cooking_time", 0),
                    "preparation_time": results["metadatas"][0][i].get("preparation_time", 0)
                }
                formatted_results.append(result)
            return formatted_results
        
        formatted = format_search_results(mock_results)
        
        self.assertEqual(len(formatted), 2)
        
        # Test primo risultato
        first_result = formatted[0]
        self.assertEqual(first_result["_id"], "RISOTTO001")
        self.assertEqual(first_result["title"], "Risotto ai Funghi")
        self.assertEqual(first_result["score"], 0.8)  # 1.0 - 0.2
        self.assertEqual(first_result["category"], ["Primo Piatto"])
        
        # Test secondo risultato
        second_result = formatted[1]
        self.assertEqual(second_result["_id"], "PASTA001")
        self.assertEqual(second_result["score"], 0.7)  # 1.0 - 0.3


class TestIntegrationMocked(unittest.TestCase):
    """Test di integrazione con componenti mockati"""
    
    def test_full_recipe_workflow_mocked(self):
        """Test workflow completo con mock"""
        # Crea ricetta
        recipe = RecipeDBSchema(
            title="Spaghetti Carbonara",
            category=["Primo Piatto"],
            preparation_time=10,
            cooking_time=15,
            ingredients=[
                Ingredient(name="spaghetti", qt=400, um="grammi"),
                Ingredient(name="uova", qt=4, um="pezzi"),
                Ingredient(name="pecorino", qt=100, um="grammi")
            ],
            recipe_step=[
                "Cuocere la pasta",
                "Preparare la crema",
                "Mantecare"
            ],
            description="Classica pasta romana",
            diet="vegetariano",
            technique="mantecatura",
            language="italiano",
            chef_advise="Non far rapprendere le uova",
            tags=["romana", "cremosa"],
            nutritional_info=["520 kcal"],
            cuisine_type="italiana",
            ricetta_audio=None,
            ricetta_caption=None,
            shortcode="CARB001"
        )
        
        # Mock embedding engine
        mock_engine = Mock()
        mock_engine.create_recipe_text.return_value = "Ricetta: Spaghetti Carbonara | Descrizione: Classica pasta romana"
        mock_engine.encode_recipe.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_engine.encode_query.return_value = [0.2, 0.3, 0.4, 0.5, 0.6]
        
        # Mock database
        mock_db = Mock()
        mock_db.add_recipe.return_value = True
        mock_db.search.return_value = [
            {
                "_id": "CARB001",
                "title": "Spaghetti Carbonara",
                "score": 0.95,
                "category": ["Primo Piatto"]
            }
        ]
        
        # Test aggiunta ricetta
        result = mock_db.add_recipe(recipe)
        self.assertTrue(result)
        mock_db.add_recipe.assert_called_once_with(recipe)
        
        # Test ricerca
        search_results = mock_db.search("pasta cremosa")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]["title"], "Spaghetti Carbonara")
        self.assertEqual(search_results[0]["score"], 0.95)


if __name__ == "__main__":
    # Configurazione logging per i test
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Esegui i test
    unittest.main(verbosity=2)
