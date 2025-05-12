from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

import json
import uvicorn
# Import per integrazione con MongoDB e NLP
from sentence_transformers import SentenceTransformer
from models import RecipeDBSchema, Ingredient

from importRicette.saveRecipe import process_video
from utility import get_error_context, logger,get_embedding,get_mongo_collection,get_db
from chatbot.agent import get_recipes
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    shortcode = Column(String, nullable=True)

# Creazione delle tabelle nel database
#Base.metadata.create_all(bind=engine)

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
app = FastAPI(title="Backend Smart Recipe", version="0.5")

# Mount mediaRicette directory explicitly to ensure all dynamic subfolders are accessible
app.mount("/mediaRicette", StaticFiles(directory="static/mediaRicette"), name="mediaRicette")


#-------------------------------
# Endpoints API
# -------------------------------
# -------------------------------
@app.get("/")
async def root():
    # In un template reale useresti Jinja2 o un'altra template-engine
    return {
        "message": "Vai su /static/index.html per provare i file statici"
}

@app.post("/recipes/", response_model=RecipeDBSchema, status_code=status.HTTP_201_CREATED)
async def insert_recipe(video: VideoURL):
    try:
        url = str(video.url)
        recipe_data = await process_video(url)
        logger.info(f"recipe_data: {recipe_data}")
        if not recipe_data:
            error_context = get_error_context()
            logger.error(f"Impossibile elaborare il video. Nessun dato ricevuto. - {error_context}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile elaborare il video. Nessun dato ricevuto. - {error_context}"
            )
        # Generate embedding
        #model = get_embedding_model()
        text_for_embedding = f"{recipe_data.title} {' '.join(recipe_data.recipe_step)} {json.dumps([ing.model_dump() for ing in recipe_data.ingredients])}"
        embedding = get_embedding(text_for_embedding)
        # Prepare document for MongoDB
        doc = {
            "title": recipe_data.title,
            "category": recipe_data.category,
            "preparation_time": recipe_data.preparation_time,
            "cooking_time": recipe_data.cooking_time,
            "ingredients": [ing.model_dump() for ing in recipe_data.ingredients],
            "recipe_step": recipe_data.recipe_step,
            "description": recipe_data.description,
            "diet": recipe_data.diet,
            "technique": recipe_data.technique,
            "language": recipe_data.language,
            "chef_advise": recipe_data.chef_advise,
            "tags": recipe_data.tags,
            "nutritional_info": recipe_data.nutritional_info,
            "cuisine_type": recipe_data.cuisine_type,
            "ricetta_audio": recipe_data.ricetta_audio,
            "ricetta_caption": recipe_data.ricetta_caption,
            "shortcode": recipe_data.shortcode,
            "embedding": embedding
        }
        mongo_coll = get_mongo_collection()
        mongo_coll.replace_one(
            {"shortcode": recipe_data.shortcode},
            doc,
            upsert=True
        )
        # Return response
        return RecipeDBSchema(
            title=doc["title"],
            category=doc["category"],
            preparation_time=doc["preparation_time"],
            cooking_time=doc["cooking_time"],
            ingredients=[Ingredient(**ing) for ing in doc["ingredients"]],
            recipe_step=doc["recipe_step"],
            description=doc["description"],
            diet=doc["diet"],
            technique=doc["technique"],
            language=doc["language"],
            chef_advise=doc["chef_advise"],
            tags=doc["tags"],
            nutritional_info=doc["nutritional_info"],
            cuisine_type=doc["cuisine_type"],
            ricetta_audio=doc["ricetta_audio"],
            ricetta_caption=doc["ricetta_caption"],
            shortcode=doc["shortcode"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f" {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{str(e)}"
        )

@app.get("/recipes/{recipe_id}", response_model=RecipeDBSchema)
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

@app.get("/search/")
def search_recipes( query: str ):
    try:
        logger.info(f"search query: {query}")
        recipes = get_recipes(query, k=3)
        return recipes
    except Exception as e:
        logger.error(f"Errore durante la ricerca delle ricette: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la ricerca delle ricette: {str(e)}"
        )
# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

# -------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)