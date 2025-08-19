from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import json

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from models import RecipeDBSchema, Ingredient, RecipeResponse

from importRicette.saveRecipe import process_video
from utility import get_error_context, logger, clean_text
from DB.rag_system import (
    index_database,
    search,
    visualize_space_query,
    load_embedding_matrix,
    load_embeddings_with_metadata,
    set_rag_model,
    get_current_rag_model_name,
    recalculate_embeddings_from_npz,
    load_npz_info,
)

#from DB.mongoDB import get_mongo_collection, get_db
#from DB.embedding import get_embedding

#from chatbot.natural_language_recipe_finder_llm import LLMNaturalLanguageProcessor, RecipeFinder
#from chatbot.agent import get_recipes
from config import MONGODB_URI, EMBEDDINGS_NPZ_PATH
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -------------------------------
# Schemi Pydantic
# -------------------------------

class VideoURLs(BaseModel):
    urls: List[HttpUrl]

    @validator('urls')
    def validate_urls(cls, vs):
        allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com']
        for v in vs:
            if not any(domain in str(v) for domain in allowed_domains):
                raise ValueError(f"URL non supportato: {v}. Dominio deve essere tra: {', '.join(allowed_domains)}")
        return vs

# -------------------------------
# Inizializzazione FastAPI e Dependency per il DB
# -------------------------------
app = FastAPI(title="Backend Smart Recipe", version="0.5")
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mediaRicette directory explicitly to ensure all dynamic subfolders are accessible
app.mount("/mediaRicette", StaticFiles(directory="static/mediaRicette"), name="mediaRicette")
# Mount static directory to serve HTML, CSS, JS and other assets
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

#-------------------------------
# Endpoints API
# -------------------------------
# -------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")

@app.post("/recipes/", response_model=List[RecipeDBSchema], status_code=status.HTTP_201_CREATED)
async def insert_recipe(videos: VideoURLs):
    urls = [str(u) for u in videos.urls]
    docs = []
    texts_for_embedding: List[str] = []
    metadatas: List[RecipeDBSchema] = []
    urlNoteElaborated = []
    for url in urls:
        try:
            recipe_data = await process_video(url)
            if not recipe_data:
                error_context = get_error_context()
                logger.error(f"Impossibile elaborare il video dall'URL '{url}'. Nessun dato ricetta ricevuto da process_video. Contesto: {error_context}")
                continue

            # Prepara i dati per l'embedding
            title_clean = clean_text(recipe_data.title)
            logger.info(f"Title clean: {title_clean}")
            category_clean = ' '.join([clean_text(cat) for cat in recipe_data.category])
            logger.info(f"Category clean: {category_clean}")
            steps_clean = ' '.join([clean_text(step) for step in recipe_data.recipe_step])
            logger.info(f"Steps clean: {steps_clean}")
            ingredients_clean = ' '.join([clean_text(ing.name) for ing in recipe_data.ingredients])
            logger.info(f"Ingredients clean: {ingredients_clean}")

            text_for_embedding = f"{title_clean}. {category_clean}. {ingredients_clean}. {steps_clean}"
            logger.info(f"Testo per embedding generato per ricetta (shortcode: {recipe_data.shortcode}). Lunghezza: {len(text_for_embedding)}")
            texts_for_embedding.append(text_for_embedding)
            metadatas.append(recipe_data)

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
                "shortcode": recipe_data.shortcode
            }
            docs.append(doc)
        except Exception as e:
            error_context = get_error_context()
            logger.error(f"Errore imprevisto durante l'elaborazione dell'URL '{url}': {str(e)}. Contesto: {error_context}", exc_info=True)
            urlNoteElaborated.append(url)
            continue

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nessun URL valido elaborato."
        )

    # Salvataggio embedding + metadati per batch
    try:
        _ = index_database(texts_for_embedding, metadata=metadatas)
    except Exception as e:
        logger.error(f"Errore durante la generazione/salvataggio degli embedding per il batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno durante la generazione dell'identificativo semantico."
        )

    # Salva (opzionale) elenco titoli
    try:
        with open('static/mediaRicette/ricette.json', 'w', encoding='utf-8') as f:
            json.dump([d['title'] for d in docs], f, ensure_ascii=False, indent=4)
    except Exception:
        pass

    return [
        RecipeDBSchema(
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
        ) for doc in docs
    ]

@app.get("/recipes/{recipe_id}", response_model=RecipeDBSchema)
def get_recipe(recipe_id: int):
    return ""

@app.get("/search/")
def search_recipes(query: str, limit: int = 3):
    try:
        embeddings, metadata, _ = load_embeddings_with_metadata(EMBEDDINGS_NPZ_PATH)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore nel caricamento degli embeddings: {str(e)}")

    if embeddings is None or embeddings.size == 0:
        return []

    similarity_results = search(query=query, embedding_matrix=embeddings)

    top_k = max(1, min(limit or 3, 3))
    top_results = similarity_results[:top_k]

    response = []
    for idx, score in top_results:
        meta = {}
        if metadata is not None and 0 <= idx < len(metadata):
            try:
                meta = dict(metadata[idx])
            except Exception:
                meta = {}
        meta.update({"score": float(score)})
        response.append(meta)

    return response
    #visualize_space_query(frasi, query, matrix)

# -------------------------------
# Endpoints amministrativi: gestione modello e ricalcolo embeddings
# -------------------------------

class SetModelBody(BaseModel):
    model_name: str

@app.get("/embeddings/info")
def embeddings_info():
    return load_npz_info(EMBEDDINGS_NPZ_PATH)

@app.post("/embeddings/model")
def change_embedding_model(body: SetModelBody):
    new_name = set_rag_model(body.model_name)
    return {"status": "ok", "model": new_name}

class RecalcBody(BaseModel):
    model_name: Optional[str] = None
    out_path: Optional[str] = None

@app.post("/embeddings/recalculate")
def recalc_embeddings(body: RecalcBody):
    E, meta, info = recalculate_embeddings_from_npz(
        npz_path=EMBEDDINGS_NPZ_PATH,
        model_name=body.model_name,
        out_path=body.out_path or EMBEDDINGS_NPZ_PATH,
    )
    return {
        "status": "ok",
        "num_vectors": int(E.shape[0]),
        "dim": int(E.shape[1] if E.size else 0),
        "model": get_current_rag_model_name(),
        "out_path": body.out_path or EMBEDDINGS_NPZ_PATH,
    }
    
# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)