from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks, Request

from config import ( openAIclient, BASE_FOLDER_RICETTE, COLLECTION_NAME)

import uuid
import os
import uvicorn
import json

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

from models import RecipeDBSchema, JobStatus


from time import perf_counter
from importRicette.saveRecipe import process_video
from DB.chromaDB import RecipeDatabase
import logging
from logging_config import setup_logging, get_error_logger, clear_error_chain
from logging_config import request_id_var, job_id_var
import asyncio as _asyncio

from DB.chromaDB import ingest_json_to_chroma, search_recipes_chroma, get_recipe_by_shortcode_chroma, recipe_db

from config import EMBEDDING_MODEL

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
error_logger = get_error_logger(__name__)

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
        # Log solo errori e warning per ridurre verbosità
        if response.status_code >= 400:
            level = logging.ERROR if response.status_code >= 500 else logging.WARNING
            error_logger.logger.log(
                level,
                f"HTTP {response.status_code} {request.method} {request.url.path}",
                extra={
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                }
            )
        return response
    except Exception as e:
        duration_ms = int((perf_counter() - start) * 1000)
        error_logger.log_exception(
            f"unhandled_http_exception",
            e,
            {
                "path": request.url.path,
                "method": request.method,
                "duration_ms": duration_ms,
            }
        )
        raise
    finally:
        if token is not None:
            request_id_var.reset(token)

# Startup handler per inizializzazione
@app.on_event("startup")
async def on_startup():
    # Inizializza job store in-memory
    app.state.jobs = {}

def _ingest_urls_job(job_id: str, urls: List[str]):
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
        #texts_for_embedding = []
        metadatas = []
        success = 0
        failed = 0

        for i, url in enumerate(urls, start=1):
            idx0 = i - 1
            # Marca l'URL come in esecuzione
            try:
                progress["urls"][idx0].update({"status": "running", "stage": "download"})
            except Exception:
                pass  # Non loggiamo errori minori di aggiornamento progress

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
                    pass  # Non loggiamo errori minori di callback

            #processo i dati della ricetta
            try:
                recipe_data = await process_video(url, progress_cb=_cb)
                if not recipe_data:
                    failed += 1
                    if 0 <= idx0 < len(progress.get("urls", [])):
                        progress["urls"][idx0].update({"status": "failed", "stage": "error"})
                    progress["failed"] = failed
                    progress["percentage"] = _recalc_job_percentage()
                    raise Exception("Recipe data is empty")
                
                try:
                 filename = os.path.join(BASE_FOLDER_RICETTE, recipe_data.shortcode, "media_original", f"metadata_{recipe_data.shortcode}.json")
                 with open(filename, 'w', encoding='utf-8') as f:
                  json.dump(recipe_data.model_dump(), f, indent=1, ensure_ascii=False)

                except Exception as e:
                 error_logger.log_exception("save_metadata", e, {"shortcode": recipe_data.shortcode})
                 continue
             
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

        if metadatas:
            
            progress["stage"] = "indexing"
            progress["percentage"] = max(float(progress.get("percentage") or 0.0), 95.0)
            logging.getLogger(__name__).info(f"call ingest_json_to_chroma: {metadatas}", extra={})

            n, coll = ingest_json_to_chroma(metadatas, collection_name=COLLECTION_NAME)
            print(f"Inseriti {n} record nella collection '{coll}'.")
            
        # Completa job
        job_entry["result"] = {
            "indexed": len(metadatas),
            "total_urls": total,
            "success": success,
            "failed": failed,
        }
        if len(metadatas) > 0:
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
            pass  # Errore minore di cleanup
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


@app.post("/ingest/recipes", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
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

@app.get("/ingest/status/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = app.state.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trovato")
    progress = job.get("progress") or {}
    return JobStatus(job_id=job_id, status=job.get("status"), detail=job.get("detail"), result=job.get("result"), progress_percent=progress.get("percentage"), progress=progress)

@app.get("/recipe/{shortcode}")
def get_recipe_by_shortcode(shortcode: str):
    """
    Ritorna i metadati completi della ricetta identificata dallo shortcode.
    
    Usa il sistema ChromaDB ottimizzato con BGE-M3.
    """
    try:
        recipe_data = get_recipe_by_shortcode_chroma(shortcode)
        
        if not recipe_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ricetta non trovata")
        
        # Normalizza campi per frontend
        if "_id" not in recipe_data:
            recipe_data["_id"] = recipe_data.get("shortcode")
        
        images = recipe_data.get("images") or []
        if not recipe_data.get("image_url") and isinstance(images, list) and images:
            recipe_data["image_url"] = images[0]
        
        return recipe_data
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_exception("get_recipe", e, {"shortcode": shortcode})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore interno: {str(e)}")

@app.get("/search/")
def search_recipes(query: str, limit: int = 12, max_time: Optional[int] = None, difficulty: Optional[str] = None, diet: Optional[str] = None, cuisine: Optional[str] = None):
    """
    Ricerca semantica ottimizzata con ChromaDB e BGE-M3.
    
    Supporta filtri avanzati per tempo, difficoltà, dieta e cucina.
    """
    try:
        # Costruisci filtri da parametri query
        filters = {}
        if max_time is not None:
            filters["max_time"] = max_time
        if difficulty:
            filters["difficulty"] = difficulty
        if diet:
            filters["diet"] = diet  
        if cuisine:
            filters["cuisine"] = cuisine
        
        # Usa il sistema ChromaDB ottimizzato
        results = search_recipes_chroma(query, limit, filters)
        
        # Normalizza campi per frontend
        for result in results:
            try:
                if "_id" not in result and result.get("shortcode"):
                    result["_id"] = result.get("shortcode")
                
                images = result.get("images") or []
                if not result.get("image_url") and isinstance(images, list) and images:
                    result["image_url"] = images[0]
            except Exception:
                pass  # Errore minore di normalizzazione immagini
        return results
        
    except Exception as e:
        error_logger.log_exception("search", e, {"query": query[:50]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Errore in ricerca semantica")

# -------------------------------
# Endpoints amministrativi: gestione modello e ricalcolo embeddings
# -------------------------------

class SetModelBody(BaseModel):
    model_name: str

@app.get("/embeddings/info")
def embeddings_info():
    """
    Ritorna informazioni sul sistema di embedding ottimizzato
    """
    try:
        stats = recipe_db.get_stats()
        
        return {
            "status": "ok",
            "embedding_model": EMBEDDING_MODEL,
            "total_recipes": stats.get("total_recipes", 0),
            "collection_name": stats.get("collection_name", ""),
            "database_type": "ChromaDB",
            "optimization": "BGE-M3 multilingual"
        }
    except Exception as e:
        error_logger.log_exception("embeddings_info", e)
        return {"status": "error", "detail": str(e)}

@app.post("/embeddings/model")
def change_embedding_model(body: SetModelBody):
    """
    Cambia il modello di embedding (riavvio richiesto per applicare)
    """
    try:
        current_model = EMBEDDING_MODEL
        
        # Per ora ritorniamo il modello corrente 
        # Un cambio di modello richiederebbe riavvio dell'applicazione
        # Richiesta cambio modello
        
        return {
            "status": "info", 
            "current_model": current_model,
            "requested_model": body.model_name,
            "message": "Riavvio applicazione richiesto per cambiare modello"
        }
    except Exception as e:
        error_logger.log_exception("change_model", e, {"requested_model": body.model_name})
        return {"status": "error", "detail": str(e)}

class RecalcBody(BaseModel):
    model_name: Optional[str] = None
    out_path: Optional[str] = None

@app.post("/embeddings/recalculate")
def recalc_embeddings(body: RecalcBody):
    """
    Ricalcola embeddings con nuovo modello
    
    """
    try:
        # Ottieni la lista di tutte le cartelle dentro BASE_FOLDER_RICETTE
        recipe_folders = []
        
        # Verifica che la directory esista
        if not os.path.exists(BASE_FOLDER_RICETTE):
            return {
                "status": "error",
                "detail": f"La directory {BASE_FOLDER_RICETTE} non esiste"
            }
        
        recipe_db = RecipeDatabase()
         # Elenca tutte le entry nella directory
        for entry in os.listdir(BASE_FOLDER_RICETTE):
            entry_path = os.path.join(BASE_FOLDER_RICETTE, entry)
            # Controlla se è una directory
            if os.path.isdir(entry_path):
                recipe_folders.append(entry)
        
         # Ordina le cartelle alfabeticamente
        recipe_folders.sort()
        for recipe_folder in recipe_folders:
            json_file = os.path.join(recipe_folder, f"metadata_{recipe_folder}.json")
            if not os.path.isfile(json_file):
                error_logger.logger.log(f"no recipe med.js found in folder: {recipe_folder}")
                continue
            else:
             with open(json_file, 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)
                
             recipe_db.add_recipe(recipe_data)
        
        
    except Exception as e:
        error_logger.log_exception("recalc_info", e)
        return {"status": "error", "detail": str(e)}
    
# -------------------------------
# Endpoints per la validazione di stato e prova
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Check di salute esteso con info sul sistema ottimizzato
    """
    try:
        stats = recipe_db.get_stats()
        
        return {
            "status": "ok",
            "system": "Smart Recipe API",
            "version": "0.7 - Ottimizzato",
            "embedding_model": EMBEDDING_MODEL,
            "database": {
                "type": "ChromaDB",
                "total_recipes": stats.get("total_recipes", 0),
                "collection": stats.get("collection_name", ""),
                "optimization": "BGE-M3 multilingual"
            }
        }
    except Exception as e:
        error_logger.log_exception("health_check", e)
        return {
            "status": "degraded",
            "error": str(e),
            "system": "Smart Recipe API"
        }
        
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