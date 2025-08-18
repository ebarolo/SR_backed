import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import spacy
from dotenv import load_dotenv
import uvicorn

# Carica variabili d'ambiente
load_dotenv()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recipe_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inizializza FastAPI
app = FastAPI(
    title="Smart Recipe Natural Language API",
    description="API per trovare ricette usando query in linguaggio naturale",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelli Pydantic
class QueryRequest(BaseModel):
    query: str = Field(..., description="Query in linguaggio naturale per cercare ricette")
    limit: int = Field(10, description="Numero massimo di risultati")

class RecipeResponse(BaseModel):
    _id: str
    title: str
    description: str
    category: List[str]
    cuisine_type: str
    ingredients: List[Dict[str, Any]]
    preparation_time: int
    cooking_time: int
    tags: List[str]
    chef_advise: Optional[str]
    match_score: float = Field(..., description="Score di rilevanza della ricetta")

class NaturalLanguageProcessor:
    """Classe per processare query in linguaggio naturale"""
    
    def __init__(self):
        try:
            # Carica il modello spaCy italiano
            self.nlp = spacy.load("it_core_news_sm")
            logger.info("Modello spaCy caricato con successo")
        except:
            logger.warning("Modello spaCy italiano non trovato, installo...")
            os.system("python -m spacy download it_core_news_sm")
            self.nlp = spacy.load("it_core_news_sm")
        
        # Mappatura categorie
        self.category_mapping = {
            'antipasto': ['antipasti', 'starter', 'appetizer'],
            'primo': ['primi', 'first course', 'pasta', 'risotto'],
            'secondo': ['secondi', 'main course', 'principale'],
            'contorno': ['contorni', 'side dish', 'verdure'],
            'dolce': ['dolci', 'dessert', 'torta', 'biscotti'],
            'bevanda': ['bevande', 'drink', 'cocktail']
        }
        
        # Mappatura tipi di cucina
        self.cuisine_mapping = {
            'medioevale': ['medievale', 'antica', 'storica'],
            'italiana': ['italiano', 'tradizionale'],
            'francese': ['french', 'francaise'],
            'asiatica': ['asiatico', 'orientale', 'cinese', 'giapponese'],
            'mediterranea': ['mediterraneo']
        }
        
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Estrae entità dalla query"""
        doc = self.nlp(query.lower())
        
        entities = {
            'ingredients': [],
            'category': None,
            'cuisine_type': None,
            'tags': [],
            'cooking_time': None,
            'diet': None
        }
        
        # Estrai ingredienti (nomi comuni)
        ingredients_pattern = r'\b(ranapescatrice|pomodor[oi]|cipoll[ae]|aglio|olio|sale|pepe|basilico|prezzemolo|' \
                            r'pasta|riso|carne|pesce|verdur[ae]|formaggio|latte|uov[ao]|farina|zucchero|' \
                            r'limone|arancia|mela|pera|fragol[ae]|banana|patate|carote|zucchine|melanzane|' \
                            r'peperoni|funghi|spinaci|insalata|lattuga|pollo|manzo|maiale|vitello|salmone|' \
                            r'tonno|gamberi|cozze|vongole|calamari|polpo|mozzarella|parmigiano|ricotta|' \
                            r'gorgonzola|pecorino)\b'
        
        found_ingredients = re.findall(ingredients_pattern, query.lower())
        entities['ingredients'] = list(set(found_ingredients))
        
        # Estrai categoria
        for word in doc:
            for category, variations in self.category_mapping.items():
                if word.text in variations or word.text == category:
                    entities['category'] = category
                    break
        
        # Estrai tipo di cucina
        for word in doc:
            for cuisine, variations in self.cuisine_mapping.items():
                if word.text in variations or word.text == cuisine:
                    entities['cuisine_type'] = cuisine
                    break
        
        # Estrai tags e altre informazioni
        if 'veloce' in query.lower() or 'rapido' in query.lower():
            entities['tags'].append('veloce')
            entities['cooking_time'] = 30  # max 30 minuti
        
        if 'facile' in query.lower() or 'semplice' in query.lower():
            entities['tags'].append('facile')
        
        # Estrai dieta
        diet_keywords = {
            'vegetariano': ['vegetariana', 'vegetariano', 'veggie'],
            'vegano': ['vegana', 'vegano', 'vegan'],
            'gluten-free': ['senza glutine', 'celiaco', 'celiaca'],
            'light': ['leggero', 'leggera', 'dietetico']
        }
        
        for diet, keywords in diet_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                entities['diet'] = diet
                break
        
        logger.info(f"Entità estratte: {entities}")
        return entities

class RecipeFinder:
    """Classe per cercare ricette nel database MongoDB"""
    
    def __init__(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client['smart-recipe']
            self.collection = self.db['recipe']
            # Test connessione
            self.client.admin.command('ping')
            logger.info("Connesso a MongoDB Atlas con successo")
        except ConnectionFailure as e:
            logger.error(f"Errore di connessione a MongoDB: {e}")
            raise
    
    def build_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Costruisce la query MongoDB basata sulle entità estratte"""
        query = {}
        
        # Query per ingredienti
        if entities['ingredients']:
            ingredient_conditions = []
            for ingredient in entities['ingredients']:
                # Cerca negli ingredienti con regex case-insensitive
                ingredient_conditions.append({
                    'ingredients.name': {
                        '$regex': ingredient,
                        '$options': 'i'
                    }
                })
            
            if len(ingredient_conditions) > 1:
                query['$and'] = ingredient_conditions
            else:
                query.update(ingredient_conditions[0])
        
        # Query per categoria
        if entities['category']:
            query['category'] = {
                '$regex': entities['category'],
                '$options': 'i'
            }
        
        # Query per tipo di cucina
        if entities['cuisine_type']:
            query['cuisine_type'] = {
                '$regex': entities['cuisine_type'],
                '$options': 'i'
            }
        
        # Query per tempo di cottura
        if entities['cooking_time']:
            query['$expr'] = {
                '$lte': [
                    {'$add': ['$preparation_time', '$cooking_time']},
                    entities['cooking_time']
                ]
            }
        
        # Query per dieta
        if entities['diet']:
            query['diet'] = {
                '$regex': entities['diet'],
                '$options': 'i'
            }
        
        # Query per tags
        if entities['tags']:
            query['tags'] = {
                '$in': entities['tags']
            }
        
        logger.info(f"Query MongoDB costruita: {query}")
        return query
    
    def search_recipes(self, entities: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Cerca ricette nel database"""
        try:
            # Se non ci sono criteri specifici, fai una ricerca testuale
            if not any(entities.values()):
                logger.warning("Nessuna entità estratta, ritorno ricette casuali")
                recipes = list(self.collection.find().limit(limit))
            else:
                query = self.build_query(entities)
                recipes = list(self.collection.find(query).limit(limit))
            
            # Calcola match score basato sulle entità trovate
            scored_recipes = []
            for recipe in recipes:
                score = self.calculate_match_score(recipe, entities)
                recipe['match_score'] = score
                scored_recipes.append(recipe)
            
            # Ordina per score
            scored_recipes.sort(key=lambda x: x['match_score'], reverse=True)
            
            logger.info(f"Trovate {len(scored_recipes)} ricette")
            return scored_recipes
            
        except OperationFailure as e:
            logger.error(f"Errore nella query MongoDB: {e}")
            raise

    def calculate_match_score(self, recipe: Dict[str, Any], entities: Dict[str, Any]) -> float:
        """Calcola un punteggio di rilevanza per la ricetta"""
        score = 0.0
        max_score = 0.0
        
        # Score per ingredienti (40% del peso)
        if entities['ingredients']:
            max_score += 40
            recipe_ingredients = [ing['name'].lower() for ing in recipe.get('ingredients', [])]
            matched_ingredients = sum(1 for ing in entities['ingredients'] 
                                    if any(ing in r_ing for r_ing in recipe_ingredients))
            score += (matched_ingredients / len(entities['ingredients'])) * 40
        
        # Score per categoria (20% del peso)
        if entities['category']:
            max_score += 20
            if entities['category'].lower() in [cat.lower() for cat in recipe.get('category', [])]:
                score += 20
        
        # Score per tipo di cucina (20% del peso)
        if entities['cuisine_type']:
            max_score += 20
            if entities['cuisine_type'].lower() in recipe.get('cuisine_type', '').lower():
                score += 20
        
        # Score per tags (10% del peso)
        if entities['tags']:
            max_score += 10
            recipe_tags = [tag.lower() for tag in recipe.get('tags', [])]
            matched_tags = sum(1 for tag in entities['tags'] if tag.lower() in recipe_tags)
            score += (matched_tags / len(entities['tags'])) * 10
        
        # Score per dieta (10% del peso)
        if entities['diet']:
            max_score += 10
            if entities['diet'].lower() in recipe.get('diet', '').lower():
                score += 10
        
        # Normalizza lo score
        return (score / max_score * 100) if max_score > 0 else 0.0

# Inizializza componenti
nlp_processor = NaturalLanguageProcessor()
recipe_finder = None

@app.on_event("startup")
async def startup_event():
    """Inizializza la connessione al database all'avvio"""
    global recipe_finder
    
    # Ottieni connection string da variabili d'ambiente o usa default
    connection_string = os.getenv('MONGODB_URI', 'mongodb+srv://username:password@cluster.mongodb.net/')
    
    try:
        recipe_finder = RecipeFinder(connection_string)
        logger.info("API avviata con successo")
    except Exception as e:
        logger.error(f"Errore durante l'avvio: {e}")
        raise

@app.get("/")
async def root():
    """Endpoint root"""
    return {
        "message": "Smart Recipe Natural Language API",
        "version": "1.0.0",
        "endpoints": {
            "/search": "POST - Cerca ricette usando linguaggio naturale",
            "/health": "GET - Controlla lo stato dell'API",
            "/docs": "GET - Documentazione Swagger UI"
        }
    }

@app.get("/health")
async def health_check():
    """Controlla lo stato dell'API e del database"""
    try:
        # Controlla connessione database
        recipe_finder.client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check fallito: {e}")
        raise HTTPException(status_code=503, detail="Database non disponibile")

@app.post("/search", response_model=List[RecipeResponse])
async def search_recipes(request: QueryRequest):
    """Cerca ricette usando una query in linguaggio naturale"""
    try:
        logger.info(f"Ricevuta query: {request.query}")
        
        # Estrai entità dalla query
        entities = nlp_processor.extract_entities(request.query)
        
        # Cerca ricette
        recipes = recipe_finder.search_recipes(entities, request.limit)
        
        # Converti ObjectId in string e prepara la risposta
        response_recipes = []
        for recipe in recipes:
            recipe['_id'] = str(recipe['_id'])
            response_recipes.append(RecipeResponse(**recipe))
        
        return response_recipes
        
    except Exception as e:
        logger.error(f"Errore durante la ricerca: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.get("/search/simple")
async def simple_search(
    q: str = Query(..., description="Query di ricerca in linguaggio naturale"),
    limit: int = Query(10, description="Numero massimo di risultati")
):
    """Endpoint GET semplificato per ricerca ricette"""
    request = QueryRequest(query=q, limit=limit)
    return await search_recipes(request)

if __name__ == "__main__":
    # Avvia il server
    uvicorn.run(
        "natural_language_recipe_finder:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 