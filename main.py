from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import uvicorn
import json

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

from sqlalchemy.ext.declarative import declarative_base

from models import RecipeDBSchema

from importRicette.saveRecipe import process_video
from utility import get_error_context, logger, clean_text, ensure_text_within_token_limit
from DB.rag_system import (
    index_database,
    search,
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
from config import MONGODB_URI, EMBEDDINGS_NPZ_PATH, EMBEDDING_MODEL
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

# --- Statici React (build Vite) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
ASSETS_DIR = os.path.join(DIST_DIR, "assets")
# mount degli asset fingerprinted di Vite (JS/CSS/img) solo se esistono
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/", include_in_schema=False)
async def index():
    dist_index = os.path.join(DIST_DIR, "index.html")
    static_index = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.isfile(dist_index):
        return FileResponse(dist_index)
    if os.path.isfile(static_index):
        return FileResponse(static_index)
    return JSONResponse({
        "message": "Frontend non disponibile. Esegui 'npm ci && npm run build' nella cartella 'frontend' per generare la build."
    })

@app.post("/recipes/", status_code=status.HTTP_201_CREATED)
async def insert_recipe(videos: VideoURLs):
    urls = [str(u) for u in videos.urls]
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

            text_for_embedding = f"{title_clean}. {recipe_data.description}. {category_clean}. {ingredients_clean}. {steps_clean}"
            logger.info(f"Testo per embedding generato per ricetta (shortcode: {recipe_data.shortcode}). Lunghezza: {len(text_for_embedding)}")
            
            # Controlla/tronca la lunghezza in token rispetto al modello embeddings corrente
            text_for_embedding = ensure_text_within_token_limit(text_for_embedding)

            texts_for_embedding.append(text_for_embedding)
            metadatas.append(recipe_data)

        except Exception as e:
            #error_context = get_error_context()
            logger.error(f"Errore imprevisto durante l'elaborazione dell'URL '{url}'| {str(e)}", exc_info=True)
            urlNoteElaborated.append("{url} | {str(e)}")
            continue

    # Salvataggio embedding + metadati per batch
    try:
        _ = index_database(texts_for_embedding, metadata=metadatas)
    except Exception as e:
        logger.error(f"Errore durante la generazione/salvataggio degli embedding per il batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la generazione dell'embedding semantico."
        )

    if not urlNoteElaborated:
        return ["ok"]
    else:
        return urlNoteElaborated

@app.get("/ricette/{shortcode}")
def get_recipe_by_shortcode(shortcode: str):
    """Ritorna i metadati completi della ricetta identificata dallo shortcode.

    I metadati sono prelevati dal file NPZ degli embeddings,
    dove ogni ricetta è stata salvata come JSON serializzato.
    """
    try:
        _, metadata, _ = load_embeddings_with_metadata(EMBEDDINGS_NPZ_PATH)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore nel caricamento degli embeddings: {str(e)}")

    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nessuna ricetta disponibile")

    for m in metadata:
        try:
            if str(m.get("shortcode", "")) == str(shortcode):
                # normalizza alcuni campi utili al frontend
                result = dict(m)
                if "_id" not in result:
                    result["_id"] = result.get("shortcode")
                images = result.get("images") or []
                if not result.get("image_url") and isinstance(images, list) and images:
                    result["image_url"] = images[0]
                return result
        except Exception:
            continue

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ricetta non trovata")

@app.get("/search/")
def search_recipes(query: str, limit: int = 12):
    try:
        embeddings, metadata, _ = load_embeddings_with_metadata(EMBEDDINGS_NPZ_PATH)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore nel caricamento degli embeddings: {str(e)}")

    if embeddings is None or embeddings.size == 0:
        return []

    similarity_results = search(query=query, embedding_matrix=embeddings)

    # Rispetta il limite richiesto senza cappare a 3
    top_k = max(1, min(int(limit or 12), len(similarity_results)))
    top_results = similarity_results[:top_k]

    response = []
    for idx, score in top_results:
        meta = {}
        if metadata is not None and 0 <= idx < len(metadata):
            try:
                meta = dict(metadata[idx])
            except Exception:
                meta = {}

        # normalizza campi utili al frontend
        try:
            if "_id" not in meta and meta.get("shortcode"):
                meta["_id"] = meta.get("shortcode")
            images = meta.get("images") or []
            if not meta.get("image_url") and isinstance(images, list) and images:
                meta["image_url"] = images[0]
        except Exception:
            pass

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

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    file_path = os.path.join(DIST_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.isfile(dist_index):
        return FileResponse(dist_index)
    return JSONResponse({"detail": "Risorsa non trovata e frontend non costruito"}, status_code=404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)