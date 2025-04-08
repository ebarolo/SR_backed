import os
from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, Mapped, mapped_column
import uvicorn
from functools import lru_cache
import logging

# Import per integrazione con Qdrant e NLP
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer

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
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    recipe_step = Column(Text)
    description = Column(Text)
    ingredients = Column(Text)  # memorizzati come stringa in formato JSON
    preparation_time = Column(Integer)  # tempo in minuti
    cooking_time = Column(Integer)
    difficulty = Column(String)         # ad es. "facile", "media", "difficile"
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
class Ingredient(BaseModel):
    name: str
    qt: float
    um: str

class Recipe(BaseModel):
    recipe_id: str
    title: str
    category: List[str]
    prepration_time: int
    cooking_time: int
    ingredients: List[Ingredient]
    recipe_step: List[str]
    description: str
    difficulty: str
    diet: str
    technique: str
    language: str = "it"
    chef_advise: Optional[str] = None
    tags: Optional[str] = None
    nutritional_info: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    ricetta_audio: Optional[str] = None
    ricetta_caption: Optional[str] = None
    ingredients_text: Optional[str] = None
    video: Optional[str] = None
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        allowed = ["facile", "media", "difficile"]
        if v.lower() not in allowed:
            raise ValueError(f"Difficoltà deve essere uno tra: {', '.join(allowed)}")
        return v

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

# -------------------------------
# Endpoints API
# -------------------------------
@app.post("/recipes/", response_model=Recipe, status_code=status.HTTP_201_CREATED)
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Impossibile elaborare il video. Nessun dato ricevuto."
            )
        
        recipe = recipe_data[0]  # Prendi la prima ricetta elaborata
        
        # Converti la lista degli ingredienti in una stringa
        ingredients_str = ", ".join([f"{ing['qt']} {ing['um']} {ing['name']}" for ing in recipe.get("ingredients", [])])
        logger.info(f"ingredients_str {ingredients_str}")

        prepration_step = ", ".join([f"{step['step']}" for step in recipe.get("prepration_step", [])])
        logger.info(f"prepration_step {prepration_step}")
        
        db_recipe = recipe
        db_recipe.recipe_step = prepration_step
        db_recipe.ingredients = ingredients_str
       
        #db_recipe = Recipe(
        #    title=recipe.get("title", ""),
        #    description=prepration_step,
        #    ingredients=ingredients_str,
        #    preparation_time=recipe.get("prepration_time", 0),  # Corretto il typo "prepration_time"
        #    cooking_time=recipe.get("cooking_time", 0),
        #    difficulty=recipe.get("difficulty", ""),
        #    diet=recipe.get("diet", ""),
        #    category=", ".join(recipe.get("category", [])),
        #    technique=recipe.get("technique", ""),
        #    language=recipe.get("language", "it"),
        #    chef_advise=recipe.get("chef_advise", ""),
        #    tags=", ".join(recipe.get("tags", [])),
        #    nutritional_info=", ".join(recipe.get("nutritional_info", [])),
        #    cuisine_type=recipe.get("cuisine_type", "")
        #)
        
        #logger.info(f"db_recipe {db_recipe}")

        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        
        # Genera l'embedding dalla descrizione della ricetta
        model = get_embedding_model()
        text_for_embedding = f"{db_recipe.title} {prepration_step} {ingredients_str}"

        logger.info(f"text_for_embedding {text_for_embedding}")

        embedding = model.encode(text_for_embedding).tolist()
        
        # Inserisci l'embedding in Qdrant con un payload per il filtraggio
        client = get_qdrant_client()
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=recipe.id,
                    vector=embedding,
                    payload={
                        "title": recipe.title,
                        "diet": recipe.diet,
                        "preparation_time": recipe.prepration_time,
                        "cooking_time": recipe.cooking_time,
                        "difficulty": recipe.difficulty,
                        "category": recipe.category
                    }
                )
            ]
        )
        
        return recipe
    
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"{str(ve)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"{str(e)}"
        )

@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Ricetta non trovata"
        )
    
    #ingredients_list = parse_ingredients(recipe.ingredients)
    
    return recipe

@app.get("/search/", response_model=List[Recipe])
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Errore durante la ricerca: {str(e)}"
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