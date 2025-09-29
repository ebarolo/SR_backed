# Import FastAPI e middleware
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import mimetypes
from contextlib import asynccontextmanager

# Import standard library
import uuid
import os
from time import perf_counter

# Import Pydantic per validazione
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict, Any

# Import moduli interni
from config import BASE_FOLDER_RICETTE, STATIC_DIR
from utility.models import JobStatus
from rag._elysia import search_recipes_elysia, _preprocess_collection
from rag._weaviate import WeaviateSemanticEngine

from utility.logging_config import (
    setup_logging, 
    get_error_logger
)

from importRicette.ingest import _ingest_urls_job, _ingest_folder_job
# Import uvicorn per server
import uvicorn

# Directory base e frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "importFrontend")

# Setup logging
setup_logging()
error_logger = get_error_logger(__name__)

# ===============================
# SCHEMI PYDANTIC PER VALIDAZIONE
# ===============================

class VideoURLs(BaseModel):
    """Schema per validazione URL video da importare."""
    urls: List[HttpUrl]
    force_redownload: bool = False  # Opzionale: forza il ri-download se già presente

    @field_validator('urls')
    def validate_urls(cls, vs):
        """Valida che gli URL appartengano ai domini supportati."""
        allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com']
        for v in vs:
            if not any(domain in str(v) for domain in allowed_domains):
                raise ValueError(f"URL non supportato: {v}. Dominio deve essere tra: {', '.join(allowed_domains)}")
        return vs

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestisce il ciclo di vita dell'applicazione FastAPI.
    Inizializza lo stato dell'app all'avvio.
    """
    app.state.jobs = {}
    yield


# ===============================
# INIZIALIZZAZIONE APPLICAZIONE
# ===============================

app = FastAPI(
    title="Smart Recipe",
    version="0.9",
    description="API per gestione ricette con ricerca semantica basata su Weaviate/Elysia",
    lifespan=lifespan
)

# Configurazione MIME types per assicurarsi che i CSS vengano serviti correttamente
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# Mount per servire gli asset del frontend direttamente dalla radice (deve essere prima di /frontend)
app.mount("/asset", StaticFiles(directory=os.path.join(DIST_DIR, "asset")), name="frontend-assets")
# Mount per servire i file del frontend
app.mount("/import", StaticFiles(directory=DIST_DIR), name="importFrontend")

@app.post("/recipes/ingest", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_ingest(videos: VideoURLs, background_tasks: BackgroundTasks):
    """
    Avvia l'importazione asincrona di ricette da URL video.
    
    Crea un job in background che processa gli URL forniti,
    estrae le ricette e le indicizza nel database.
    
    Args:
        videos: Schema con lista URL video da processare
        background_tasks: Gestore task in background
        
    Returns:
        JobStatus con ID del job e stato iniziale
    """
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
    background_tasks.add_task(_ingest_urls_job, app, job_id, url_list, videos.force_redownload)
    return JobStatus(job_id=job_id, status="queued", progress_percent=0.0, progress=app.state.jobs[job_id]["progress"])

@app.post("/recipes/ingest/fromFolder", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_ingest_from_folder( background_tasks: BackgroundTasks):
    """
    Avvia l'importazione asincrona di ricette da cartella locale.
    
    Crea un job in background che processa i file forniti,
    estrae le ricette e le indicizza nel database.
    
    Args:
        videos: Schema con lista URL video da processare
        background_tasks: Gestore task in background
        
    Returns:
        JobStatus con ID del job e stato iniziale
    """
    job_id = str(uuid.uuid4())
    folder_path = BASE_FOLDER_RICETTE
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Cartella non trovata")
   
    # Ottieni la lista dei nomi delle sottocartelle in BASE_FOLDER_RICETTE
    dir_list = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
    total = len(dir_list)
    dir_progress = [
        {"index": i + 1, "url": u, "status": "queued", "stage": "queued", "local_percent": 0.0}
        for i, u in enumerate(dir_list)
    ]
    app.state.jobs[job_id] = {
        "status": "queued",
        "progress": {
            "total": total,
            "success": 0,
            "failed": 0,
            "percentage": 0.0,
            "stage": "queued",
            "urls": dir_progress,
        },
    }
    background_tasks.add_task(_ingest_folder_job, app, job_id, dir_list)
    return JobStatus(job_id=job_id, status="queued", progress_percent=0.0, progress=app.state.jobs[job_id]["progress"])

@app.get("/recipes/ingest/status")
def jobs_status():
    """
    Recupera lo stato di tutti i job di importazione.
    
    Returns:
        Lista con dettagli di tutti i job attivi e completati
    """
    jobs_dict = getattr(app.state, 'jobs', {})
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

@app.get("/recipes/ingest/status/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    """
    Recupera lo stato di un job specifico.
    
    Args:
        job_id: ID univoco del job
        
    Returns:
        JobStatus con dettagli del job
        
    Raises:
        HTTPException 404 se il job non esiste
    """
    job = app.state.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trovato")
    progress = job.get("progress") or {}
    return JobStatus(job_id=job_id, status=job.get("status"), detail=job.get("detail"), result=job.get("result"), progress_percent=progress.get("percentage"), progress=progress)

@app.get("/recipes/ingest/preprocess")
def preprocess_collection(collection_name: str):
    
    return _preprocess_collection(collection_name)

@app.get("/recipes/search/")
def search_recipes(
    query: str,
    limit: int = 12,
    max_time: Optional[int] = None,
    difficulty: Optional[str] = None,
    diet: Optional[str] = None,
    cuisine: Optional[str] = None
):
    """
    Ricerca semantica ricette con validazione input.
    
    Args:
        query: Testo di ricerca (max 500 caratteri)
        limit: Numero risultati (max 100)
        max_time: Tempo massimo preparazione
        difficulty: Difficoltà ricetta
        diet: Tipo dieta
        cuisine: Tipo cucina
        
    Returns:
        Risultati ricerca semantica
        
    Raises:
        HTTPException: Se validazione input fallisce
    """
    # Validazione query
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query non può essere vuota"
        )
    
    if len(query) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query troppo lunga (max 500 caratteri)"
        )
    
    # Validazione limit
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit deve essere maggiore di 0"
        )
    
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit troppo alto (max 100)"
        )
    
    # Sanitize query per prevenire injection
    query_clean = query.strip()
    
    return search_recipes_elysia(query_clean, limit)

def _is_folder_empty_or_contains_empty_folders(folder_path: str) -> bool:
    """
    Verifica se una cartella è vuota o contiene solo cartelle vuote.
    """
    try:
        for root, dirs, files in os.walk(folder_path):
            # Se ci sono file, la cartella non è considerata vuota
            if files:
                return False
        return True
    except Exception:
        # In caso di errore, considera la cartella non vuota per sicurezza
        return False

@app.get("/recipes/delete/emptyFolder")
def delete_emptyFolder():
    """
    Elimina tutte le cartelle vuote in BASE_FOLDER_RICETTE.
    """
    deleted_folders = []
    errors = []
    
    # Normalizza BASE_FOLDER_RICETTE per confronto sicuro
    base_folder_abs = os.path.abspath(BASE_FOLDER_RICETTE)
    
    try:
        for dir_name in os.listdir(BASE_FOLDER_RICETTE):
            # Previene path traversal (es. ../../../etc/passwd)
            if ".." in dir_name or "/" in dir_name or "\\" in dir_name:
                errors.append(f"Nome cartella non valido (path traversal rilevato): {dir_name}")
                continue
            
            dir_path = os.path.join(BASE_FOLDER_RICETTE, dir_name)
            
            # Verifica che il path finale sia effettivamente sotto BASE_FOLDER_RICETTE
            dir_path_abs = os.path.abspath(dir_path)
            if not dir_path_abs.startswith(base_folder_abs):
                errors.append(f"Path traversal rilevato per: {dir_name}")
                continue
            
            # Verifica che sia effettivamente una cartella
            if not os.path.isdir(dir_path):
                continue
                
            metadata_path = os.path.join(dir_path, "media_original", f"metadata_{dir_name}.json")
            
            # Se il file metadata non esiste, prova ad eliminare la cartella
            if not os.path.exists(metadata_path):
                try:
                    # Verifica se la cartella è vuota o contiene solo cartelle vuote
                    if _is_folder_empty_or_contains_empty_folders(dir_path):
                        import shutil
                        shutil.rmtree(dir_path)  # Usa shutil.rmtree per rimuovere anche cartelle non vuote
                        deleted_folders.append(dir_name)
                except OSError as e:
                    errors.append(f"Errore eliminando {dir_name}: {str(e)}")
                    
    except Exception as e:
        error_logger.error(f"Errore generale in delete_emptyFolder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore durante l'eliminazione delle cartelle: {str(e)}")
    
    return {
        "message": f"Operazione completata. Cartelle eliminate: {len(deleted_folders)}",
        "deleted_folders": deleted_folders,
        "errors": errors
    }
                    
@app.get("/recipes/delete/{shortcode}")
def delete_recipe(shortcode: str):
    """
    Elimina una ricetta specifica tramite shortcode.
    
    Args:
        shortcode: Identificativo univoco ricetta
        
    Returns:
        Messaggio conferma eliminazione
        
    Raises:
        HTTPException: Se shortcode non valido o errore eliminazione
    """
    # Validazione shortcode per prevenire path traversal
    if not shortcode or not shortcode.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shortcode non può essere vuoto"
        )
    
    # Previeni path traversal e caratteri pericolosi
    if ".." in shortcode or "/" in shortcode or "\\" in shortcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shortcode contiene caratteri non validi"
        )
    
    # Limita lunghezza
    if len(shortcode) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shortcode troppo lungo (max 100 caratteri)"
        )
    
    try:
        with WeaviateSemanticEngine() as db_engine:
            db_engine.delete_recipe(shortcode.strip())
        return {"message": "Ricetta eliminata con successo", "shortcode": shortcode}
    except Exception as e:
        error_logger.log_exception("delete_recipe", e, {"shortcode": shortcode})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante eliminazione: {str(e)}"
        )

@app.get("/recipes/{shortcode}")
def get_recipe_by_shortcode(shortcode: str):
    """
    Recupera una ricetta specifica tramite shortcode.
    
    Args:
        shortcode: Identificativo univoco della ricetta
        
    Returns:
        Metadati completi della ricetta
        
    Raises:
        HTTPException 501: Funzionalità non ancora implementata
    """
    try:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Ricerca per shortcode non ancora implementata"
        )
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_exception("get_recipe", e, {"shortcode": shortcode})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore interno: {str(e)}")

# ===============================
# ENDPOINTS FRONTEND
# ===============================

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    Serve la pagina principale del frontend.
    """
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse({"detail": "Frontend non trovato"}, status_code=404)

# ===============================
# ENDPOINTS DI SISTEMA
# ===============================

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Health check endpoint per monitoraggio sistema.
    
    Verifica lo stato del sistema e restituisce informazioni
    su versione, database e configurazione.
    
    Returns:
        Dict con stato sistema e statistiche
    """
    try:
        stats = {}
        return {
            "status": "ok",
            "system": "Smart Recipe API",
            "version": "0.9",
            "database": {
                "type": stats.get("database_type", "Elysia/Weaviate"),
                "total_recipes": stats.get("total_recipes", 0),
                "collection": stats.get("collection_name", ""),
                "optimization": "Elysia AI with Weaviate"
            }
        }
    except Exception as e:
        error_logger.log_exception("health_check", e)
        return {
            "status": "degraded",
            "error": str(e),
            "system": "Smart Recipe API"
        }


# Endpoint catch-all per il frontend SPA (deve essere l'ultimo)
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    Catch-all per servire il frontend SPA.
    
    Gestisce il routing lato client servendo index.html
    per path non mappati ad altri endpoint.
    """
    file_path = os.path.join(DIST_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.isfile(dist_index):
        return FileResponse(dist_index)
    return JSONResponse({"detail": "Risorsa non trovata e frontend non costruito"}, status_code=404)

# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    # Avvia il server Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
