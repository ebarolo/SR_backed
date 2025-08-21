from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# Middleware: assegna un request_id a ogni richiesta
import uuid
from fastapi import BackgroundTasks, Request

import os
import uvicorn
import json

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

from sqlalchemy.ext.declarative import declarative_base

from models import RecipeDBSchema, JobStatus

import logging
from time import perf_counter
from importRicette.saveRecipe import process_video
from utility import get_error_context, clean_text, ensure_text_within_token_limit
from logging_config import setup_logging
from logging_config import request_id_var, job_id_var
from DB.rag_system import (
    index_database,
    search,
    load_embeddings_with_metadata_cached,
    set_rag_model,
    get_current_rag_model_name,
    recalculate_embeddings_from_npz,
    load_npz_info,
)

#from DB.mongoDB import get_mongo_collection, get_db
#from DB.embedding import get_embedding

#from chatbot.natural_language_recipe_finder_llm import LLMNaturalLanguageProcessor, RecipeFinder
#from chatbot.agent import get_recipes
from config import EMBEDDINGS_NPZ_PATH, EMBEDDING_MODEL
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Directory base e frontend (MVP statico)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend")

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

setup_logging()
logger = logging.getLogger(__name__)

# -------------------------------
# Inizializzazione FastAPI e Dependency per il DB
# -------------------------------
app = FastAPI(title="Smart Recipe", version="0.7")
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mediaRicette directory explicitly to ensure all dynamic subfolders are accessible
app.mount("/mediaRicette", StaticFiles(directory=os.path.join(BASE_DIR, "static", "mediaRicette")), name="mediaRicette")
# Mount static directory to serve HTML, CSS, JS and other assets
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")
# Mount frontend MVP so it is reachable at /frontend
app.mount("/frontend", StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True), name="frontend")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    token = None
    start = perf_counter()
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    client = getattr(request, "client", None)
    client_ip = getattr(client, "host", None) if client else None
    ua = request.headers.get("user-agent")
    try:
        token = request_id_var.set(rid)
        response = await call_next(request)
        duration_ms = int((perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        level = logging.ERROR if response.status_code >= 500 else (logging.WARNING if response.status_code >= 400 else logging.INFO)
        logger.log(
            level,
            "HTTP",
            extra={
                "path": request.url.path,
                "method": request.method,
                "query": request.url.query,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": ua,
            },
        )
        return response
    except Exception as e:
        duration_ms = int((perf_counter() - start) * 1000)
        logger.exception(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "query": request.url.query,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": ua,
            },
        )
        raise
    finally:
        if token is not None:
            request_id_var.reset(token)

# Warmup e cache embeddings su startup
@app.on_event("startup")
async def on_startup():
    try:
        # Forza caricamento cache se file presente
        if os.path.exists(EMBEDDINGS_NPZ_PATH):
            _E, _M, _I = load_embeddings_with_metadata_cached(EMBEDDINGS_NPZ_PATH)
            logger.info(f"Embeddings preload: vettori={_E.shape if _E is not None else None}")
    except Exception as e:
        logger.warning(f"Startup preload embeddings fallito: {e}")

    # Inizializza job store in-memory
    app.state.jobs = {}

def _ingest_urls_job(job_id: str, urls: List[str]):
    import asyncio as _asyncio
    total = len(urls)
    # Stato iniziale running e progress structure
    job_entry = app.state.jobs.get(job_id) or {}
    job_entry["status"] = "running"
    progress = job_entry.setdefault(
        "progress",
        {
            "total": total,
            "success": 0,
            "failed": 0,
            "percentage": 0.0,
            "stage": "running",
            "urls": [
                {
                    "index": i + 1,
                    "url": u,
                    "status": "queued",
                    "stage": "queued",
                    "local_percent": 0.0,
                }
                for i, u in enumerate(urls)
            ],
        },
    )
    progress["stage"] = "running"
    app.state.jobs[job_id] = job_entry

    def _recalc_job_percentage() -> float:
        try:
            url_entries = progress.get("urls") or []
            if total <= 0:
                return 0.0
            local_sum = sum(float(u.get("local_percent", 0.0)) for u in url_entries)
            # 0..90% per fase URL
            return round(min(90.0, (local_sum / (100.0 * max(1, total))) * 90.0), 2)
        except Exception:
            return float(progress.get("percentage", 0.0) or 0.0)

    async def _runner():
        from importRicette.saveRecipe import process_video
        texts_for_embedding = []
        metadatas = []
        success = 0
        failed = 0

        for i, url in enumerate(urls, start=1):
            idx0 = i - 1
            # Marca l'URL come in esecuzione
            try:
                progress["urls"][idx0].update({"status": "running", "stage": "download"})
            except Exception:
                pass

            def _cb(event: dict):
                try:
                    stage = event.get("stage")
                    lp = float(event.get("local_percent", 0.0))
                    if 0 <= idx0 < len(progress.get("urls", [])):
                        url_entry = progress["urls"][idx0]
                        if url_entry.get("status") not in ("success", "failed"):
                            url_entry["status"] = "running"
                        if stage:
                            url_entry["stage"] = stage
                        url_entry["local_percent"] = lp
                        if stage == "error" and "message" in event:
                            url_entry["error"] = str(event.get("message"))
                            url_entry["status"] = "failed"
                        progress["percentage"] = _recalc_job_percentage()
                except Exception:
                    pass

            try:
                recipe_data = await process_video(url, progress_cb=_cb)
                if not recipe_data:
                    failed += 1
                    if 0 <= idx0 < len(progress.get("urls", [])):
                        progress["urls"][idx0].update({"status": "failed", "stage": "error"})
                    progress["failed"] = failed
                    progress["percentage"] = _recalc_job_percentage()
                    continue

                from utility import clean_text, ensure_text_within_token_limit
                title_clean = clean_text(recipe_data.title)
                category_clean = ' '.join([clean_text(cat) for cat in recipe_data.category])
                steps_clean = ' '.join([clean_text(step) for step in recipe_data.recipe_step])
                ingredients_clean = ' '.join([clean_text(ing.name) for ing in recipe_data.ingredients])
                text_for_embedding = f"{title_clean}. {recipe_data.description}. {category_clean}. {ingredients_clean}. {steps_clean}"
                text_for_embedding = ensure_text_within_token_limit(text_for_embedding)
                texts_for_embedding.append(text_for_embedding)
                metadatas.append(recipe_data)

                success += 1
                if 0 <= idx0 < len(progress.get("urls", [])):
                    progress["urls"][idx0].update({"status": "success", "stage": "done", "local_percent": 100.0})
                progress["success"] = success
                progress["percentage"] = _recalc_job_percentage()
            except Exception:
                failed += 1
                if 0 <= idx0 < len(progress.get("urls", [])):
                    ue = progress["urls"][idx0]
                    if ue.get("stage") != "error":
                        ue["stage"] = "error"
                    ue["status"] = "failed"
                progress["failed"] = failed
                progress["percentage"] = _recalc_job_percentage()
                continue

        if texts_for_embedding:
            # Fase di indicizzazione
            progress["stage"] = "indexing"
            progress["percentage"] = max(float(progress.get("percentage") or 0.0), 95.0)
            index_database(texts_for_embedding, metadata=metadatas, append=True)

        # Completa job
        job_entry["result"] = {
            "indexed": len(texts_for_embedding),
            "total_urls": total,
            "success": success,
            "failed": failed,
        }
        if len(texts_for_embedding) > 0:
            job_entry["status"] = "completed"
        else:
            job_entry["status"] = "failed"
            job_entry["detail"] = job_entry.get("detail") or "Nessuna ricetta indicizzata"
        progress["stage"] = "done"
        progress["percentage"] = 100.0
        app.state.jobs[job_id] = job_entry

        return job_entry["result"]

    loop = _asyncio.new_event_loop()
    try:
        _asyncio.set_event_loop(loop)
        job_token = job_id_var.set(job_id)
        _ = loop.run_until_complete(_runner())
    except Exception as e:
        # Errore globale del job
        je = app.state.jobs.get(job_id, {})
        je["status"] = "failed"
        je["detail"] = str(e)
        prog = je.get("progress") or {}
        prog["stage"] = "done"
        prog["percentage"] = float(prog.get("percentage") or 0.0)
        je["progress"] = prog
        app.state.jobs[job_id] = je
    finally:
        try:
            job_id_var.reset(job_token)
        except Exception:
            pass
        loop.close()

@app.get("/", include_in_schema=False)
async def index():
    dist_index = os.path.join(DIST_DIR, "index.html")
    static_index = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.isfile(dist_index):
        return FileResponse(dist_index)
    if os.path.isfile(static_index):
        return FileResponse(static_index)
    return JSONResponse({"detail": "index.html non trovato"}, status_code=404)

'''
# -------------------------------
# OLD Endpoints per ingest delle ricette
# -------------------------------

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
        _ = index_database(texts_for_embedding, metadata=metadatas, append=True)
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
'''
@app.post("/ingest/", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_ingest(videos: VideoURLs, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    url_list = [str(u) for u in videos.urls]
    total = len(url_list)
    urls_progress = [
        {"index": i + 1, "url": u, "status": "queued", "stage": "queued", "local_percent": 0.0}
        for i, u in enumerate(url_list)
    ]
    app.state.jobs[job_id] = {
        "status": "queued",
        "progress": {
            "total": total,
            "success": 0,
            "failed": 0,
            "percentage": 0.0,
            "stage": "queued",
            "urls": urls_progress,
        },
    }
    background_tasks.add_task(_ingest_urls_job, job_id, url_list)
    return JobStatus(job_id=job_id, status="queued", progress_percent=0.0, progress=app.state.jobs[job_id]["progress"])

@app.get("/ingest/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = app.state.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trovato")
    progress = job.get("progress") or {}
    return JobStatus(job_id=job_id, status=job.get("status"), detail=job.get("detail"), result=job.get("result"), progress_percent=progress.get("percentage"), progress=progress)

@app.get("/ingest/status")
def jobs_status():
    jobs_dict = app.state.jobs
    if not jobs_dict:
        raise HTTPException(status_code=404, detail="nessun jobs non trovato")
    out = []
    for jid, job in jobs_dict.items():
        progress = job.get("progress") or {}
        out.append({
            "job_id": jid,
            "status": job.get("status"),
            "progress_percent": float(progress.get("percentage") or 0.0),
            "progress": progress,
            "result": job.get("result"),
            "detail": job.get("detail"),
        })
    return out

@app.get("/recipe/{shortcode}")
def get_recipe_by_shortcode(shortcode: str):
    """Ritorna i metadati completi della ricetta identificata dallo shortcode.

    I metadati sono prelevati dal file NPZ degli embeddings,
    dove ogni ricetta è stata salvata come JSON serializzato.
    """
    try:
        _, metadata, _ = load_embeddings_with_metadata_cached(EMBEDDINGS_NPZ_PATH)
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
        embeddings, metadata, _ = load_embeddings_with_metadata_cached(EMBEDDINGS_NPZ_PATH)
    except Exception as e:
        logger.error("Embeddings load failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Errore nel caricamento degli embeddings")

    if embeddings is None or embeddings.size == 0:
        logger.warning("No embeddings available", extra={"query": query})
        return []
    
    try:
        k = max(1, min(int(limit or 12), len(embeddings) if embeddings is not None else 1))
        similarity_results = search(query=query, embedding_matrix=embeddings, top_k=k)
    except Exception as e:
        logger.error("Search failed", extra={"query": query, "error": str(e)}, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Errore in ricerca semantica")

    # Rispetta il limite richiesto
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