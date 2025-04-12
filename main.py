import os
from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, Mapped, mapped_column
from functools import lru_cache
import logging
import uvicorn
import traceback
import sys
import json

# Import per integrazione con Qdrant e NLP
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer
from models import RecipeSchema

from importRicette.saveRecipe import process_video

# -------------------------------
# Configurazione tramite variabili d'ambiente
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recipes.db")
QDRANT_URL = os.getenv("QDRANT_URL", "https://cd762cc1-d29b-42aa-8fa4-660b5c79871f.europe-west3-0.gcp.cloud.qdrant.io:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "smart-recipe")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.TI1jEYFRxKghin8baG_wtBiK-imMFOf98rOEejelcUI")  

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

# -------------------------------
# Configurazione Database
# -------------------------------
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True  # Verifica connessione attiva prima di usarla
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modello SQLAlchemy per la ricetta
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    recipe_step = Column(Text)
    description = Column(Text)
    ingredients = Column(Text)  # memorizzati come stringa in formato JSON
    preparation_time = Column(Integer)  # tempo in minuti
    cooking_time = Column(Integer)
    diet = Column(String)               # ad es. "vegano", "vegetariano", ecc.
    category = Column(String)           # ad es. "primo", "secondo", "dolce"
    technique = Column(String)          # ad es. "cottura al forno", "frittura"
    language = Column(String, default="it")
    chef_advise = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    nutritional_info = Column(String, nullable=True)
    cuisine_type = Column(String, nullable=True)
    ricetta_audio = Column(String, nullable=True)
    ricetta_caption = Column(String, nullable=True)
    ingredients_text = Column(String, nullable=True)
    video_path = Column(String, nullable=True)

# Creazione delle tabelle nel database
Base.metadata.create_all(bind=engine)

# -------------------------------
# Schemi Pydantic
# -------------------------------
   
class VideoURL(BaseModel):
    url: HttpUrl
    
    @validator('url')
    def validate_url(cls, v):
        allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com']
        if not any(domain in str(v) for domain in allowed_domains):
            raise ValueError(f"URL non supportato. Dominio deve essere tra: {', '.join(allowed_domains)}")
        return v

class SearchQuery(BaseModel):
    query: str
    diet: Optional[str] = None
    max_preparation_time: Optional[int] = None
    difficulty: Optional[str] = None

# -------------------------------
# Inizializzazione FastAPI e Dependency per il DB
# -------------------------------
app = FastAPI(title="Backend Smart Recipe")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# Inizializzazione del modello NLP e Qdrant
# -------------------------------
@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def get_qdrant_client():
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        prefer_grpc=True
    )
    
    try:
        client.get_collection(collection_name=QDRANT_COLLECTION)
    except Exception:
        model = get_embedding_model()
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=model.get_sentence_embedding_dimension(),
                distance=qmodels.Distance.COSINE,
            )
        )
    return client

# -------------------------------
# Helpers
# -------------------------------
def parse_ingredients(ingredients_str: str) -> List[str]:
    """Converte la stringa di ingredienti in lista"""
    if not ingredients_str:
        return []
    return [ing.strip() for ing in ingredients_str.split(",")]

def get_error_context():
    """Get the current file, line number and function name where the error occurred"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_traceback is not None:
        # Prendi il frame più in basso dello stack trace (dove è avvenuto l'errore)
        frame = traceback.extract_tb(exc_traceback)[-1]
        return f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}"
    return ""

# -------------------------------
# Endpoints API
# -------------------------------
@app.post("/recipes/", response_model=RecipeSchema, status_code=status.HTTP_201_CREATED)
async def create_recipe(video: VideoURL, db: Session = Depends(get_db)):
    try:
        # Check for Instagram credentials if it's an Instagram URL
        url = str(video.url)
        if 'instagram.com' in url:
            #instagram_username = os.getenv("ISTA_USERNAME")
            #instagram_password = os.getenv("ISTA_PASSWORD")
            #if not instagram_username or not instagram_password:
                #raise HTTPException(
                #    status_code=status.HTTP_400_BAD_REQUEST, 
                #    detail="Instagram credentials not configured. Set ISTA_USERNAME and ISTA_PASSWORD environment variables."
                #)
        
         # Valida l'URL prima di processare il video
         recipe_data = await process_video(url)
         logger.info(f" {recipe_data}")
         #RCdescription = recipe_data[0].get("description", "")
         #logger.info(f"recipe description {RCdescription}")

        if not recipe_data or len(recipe_data) == 0:
            error_context = get_error_context()
            logger.error(f"Impossibile elaborare il video. Nessun dato ricevuto. - {error_context}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Impossibile elaborare il video. Nessun dato ricevuto. - {error_context}"
            )
        
        recipe = recipe_data[0]  # Prendi la prima ricetta elaborata
        logger.info(f"recipe {recipe}")
        
        # Convert lists to strings for database storage
        ingredients_str = json.dumps(recipe.get("ingredients", []))
        recipe_step_str = json.dumps(recipe.get("prepration_step", []))
        category_str = json.dumps(recipe.get("category", []))
        tags_str = json.dumps(recipe.get("tags", []))
        nutritional_info_str = json.dumps(recipe.get("nutritional_info", []))

        # Create response data with required fields
        response_data = {
            "title": recipe.get("title", ""),
            "recipe_step": recipe_step_str,
            "description": recipe.get("ricetta_caption", ""),
            "ingredients": ingredients_str,
            "preparation_time": recipe.get("prepration_time"),
            "cooking_time": recipe.get("cooking_time"),
            "diet": recipe.get("diet", ""),
            "category": category_str,
            "technique": recipe.get("technique", ""),
            "language": recipe.get("language", "it"),
            "chef_advise": recipe.get("chef_advise", ""),
            "tags": tags_str,
            "nutritional_info": nutritional_info_str,
            "cuisine_type": recipe.get("cuisine_type", ""),
            "ricetta_audio": recipe.get("ricetta_audio", ""),
            "ricetta_caption": recipe.get("ricetta_caption", ""),
            "ingredients_text": recipe.get("ingredients_text", ""),
            "video_path": recipe.get("video", "")
        }

        # Create a new Recipe object from the dictionary data
        db_recipe = Recipe(**response_data)

        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        
        # Genera l'embedding dalla descrizione della ricetta
        model = get_embedding_model()
        text_for_embedding = f"{db_recipe.title} {json.loads(db_recipe.recipe_step)} {json.loads(db_recipe.ingredients)}"

        logger.info(f"text_for_embedding {text_for_embedding}")

        embedding = model.encode(text_for_embedding).tolist()
        
        # Inserisci l'embedding in Qdrant con un payload per il filtraggio
        client = get_qdrant_client()
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=db_recipe.id,
                    vector=embedding,
                    payload={
                        "title": db_recipe.title,
                        "diet": db_recipe.diet,
                        "preparation_time": db_recipe.preparation_time,
                        "cooking_time": db_recipe.cooking_time,
                        "category": json.loads(db_recipe.category)
                    }
                )
            ]
        )
        
        # Converti le stringhe JSON di nuovo in liste per la risposta
        response_data["recipe_step"] = json.loads(recipe_step_str)
        response_data["ingredients"] = json.loads(ingredients_str)
        response_data["category"] = json.loads(category_str)
        response_data["tags"] = json.loads(tags_str)
        response_data["nutritional_info"] = json.loads(nutritional_info_str)
        
        return response_data  # Return the properly formatted response data
    
    except ValueError as ve:
        error_context = get_error_context()
        logger.error(f"ValueError: {str(ve)} - {error_context}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"{str(ve)} - {error_context}"
        )
    
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Unexpected error: {str(e)} - {error_context}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"{str(e)} - {error_context}"
        )

@app.get("/recipes/{recipe_id}", response_model=RecipeSchema)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    try:
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            error_context = get_error_context()
            logger.error(f"Ricetta non trovata con ID {recipe_id} - {error_context}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Ricetta non trovata - {error_context}"
            )
        
        return recipe
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante il recupero della ricetta: {str(e)} - {error_context}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero della ricetta: {str(e)} - {error_context}"
        )

@app.get("/search/", response_model=List[RecipeSchema])
def search_recipes(
    query: str,
    diet: Optional[str] = None,
    max_preparation_time: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    try:
        # Genera embedding per la query utente
        model = get_embedding_model()
        query_embedding = model.encode(query).tolist()
        
        # Costruisci i filtri per Qdrant se specificati dall'utente
        conditions = []
        if diet:
            conditions.append(qmodels.FieldCondition(key="diet", match=qmodels.MatchValue(value=diet)))
        if max_preparation_time is not None:
            conditions.append(qmodels.FieldCondition(key="preparation_time", range=qmodels.Range(lte=max_preparation_time)))
        if difficulty:
            conditions.append(qmodels.FieldCondition(key="difficulty", match=qmodels.MatchValue(value=difficulty)))
        
        query_filter = qmodels.Filter(must=conditions) if conditions else None
        
        # Interroga Qdrant per ottenere i punti (ricette) più simili
        client = get_qdrant_client()
        results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter,
            with_payload=True
        )
        
        # Recupera gli ID delle ricette dai risultati e consulta il database
        recipe_ids = [int(point.id) for point in results]
        
        if not recipe_ids:
            return []
            
        recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
        
        # Ordina le ricette in base all'ordine dei risultati di Qdrant
        id_to_recipe = {recipe.id: recipe for recipe in recipes}
        ordered_recipes = [id_to_recipe.get(recipe_id) for recipe_id in recipe_ids if recipe_id in id_to_recipe]
        
        return ordered_recipes
    
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante la ricerca: {str(e)} - {error_context}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Errore durante la ricerca: {str(e)} - {error_context}"
        )

# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

# -------------------------------
# Avvio dell'applicazione
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)