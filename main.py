# Import FastAPI e middleware
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from contextlib import asynccontextmanager

# Import standard library
import uuid
import os
import json
import logging
import asyncio as _asyncio
from time import perf_counter

# Import Pydantic per validazione
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict, Any

# Import moduli interni
from config import BASE_FOLDER_RICETTE, EMBEDDING_MODEL, WCD_COLLECTION_NAME
from models import RecipeDBSchema, JobStatus, Ingredient
from RAG._elysia import search_recipes_elysia, _preprocess_collection
from RAG._weaviate import WeaviateSemanticEngine
from importRicette.saveRecipe import process_video
from utility import (
    extract_shortcode_from_url,
    calculate_job_percentage,
    create_progress_callback,
    update_url_progress,
    save_recipe_metadata
)
from logging_config import (
    setup_logging, 
    get_error_logger, 
    request_id_var, 
    job_id_var
)

# Import uvicorn per server
import uvicorn

# Directory base e frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend")

# Setup logging
setup_logging()
error_logger = get_error_logger(__name__)

# ===============================
# SCHEMI PYDANTIC PER VALIDAZIONE
# ===============================

class VideoURLs(BaseModel):
    """Schema per validazione URL video da importare."""
    urls: List[HttpUrl]

    @field_validator('urls')
    def validate_urls(cls, vs):
        """Valida che gli URL appartengano ai domini supportati."""
        allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com']
        for v in vs:
            if not any(domain in str(v) for domain in allowed_domains):
                raise ValueError(f"URL non supportato: {v}. Dominio deve essere tra: {', '.join(allowed_domains)}")
        return vs

class RecalcBody(BaseModel):
    """Schema per richiesta di ricalcolo embeddings (deprecato)."""
    model_name: Optional[str] = None
    out_path: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestisce il ciclo di vita dell'applicazione FastAPI.
    
    Inizializza lo stato dell'app all'avvio e gestisce la pulizia
    allo shutdown.
    """
    # Startup: inizializza il dizionario dei job
    app.state.jobs = {}
    yield
    # Shutdown: pulizia risorse (se necessario in futuro)
    pass

# ===============================
# JOB IN BACKGROUND
# ===============================

async def _ingest_urls_job(job_id: str, urls: List[str]):
    """
    Job principale per l'importazione di ricette da URL video.
    
    Processa una lista di URL video, estrae le informazioni delle ricette,
    genera i metadati e li indicizza nel database vettoriale Elysia/Weaviate.
    
    Args:
        job_id: ID univoco del job per tracking
        urls: Lista di URL video da processare
    """
    total = len(urls)
    
    # Inizializza stato job
    job_entry = app.state.jobs.get(job_id) or {}
    job_entry["status"] = "running"
    progress = job_entry.setdefault("progress", {
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
    })
    progress["stage"] = "running"
    app.state.jobs[job_id] = job_entry

    async def _process_urls():
        """Processa tutti gli URL e gestisce il progresso."""
        metadatas = []
        success = 0
        failed = 0
        error_details = []
        with WeaviateSemanticEngine() as indexing_engine:
            for i, url in enumerate(urls, start=1):
                url_index = i - 1
                
                # Aggiorna stato URL a running
                update_url_progress(progress, url_index, "running", "download")
                
                # Crea callback per progresso
                progress_callback = create_progress_callback(progress, url_index, total)
                
                try:
                    # Processa video
                    recipe_data = await process_video(url, progress_cb=progress_callback)
                    
                    if not recipe_data:
                        raise ValueError("Recipe data is empty")
                    
                    # Salva metadati
                    if not save_recipe_metadata(recipe_data, BASE_FOLDER_RICETTE):
                        continue
                    
                    metadatas.append(recipe_data)
                    success += 1
                    update_url_progress(progress, url_index, "success", "done", 100.0)
                    progress["success"] = success
                    
                except Exception as e:
                    failed += 1
                    error_message = str(e)
                    shortcode = extract_shortcode_from_url(url)
                    
                    error_details.append(f"URL {i} ({shortcode}): {error_message}")
                    update_url_progress(progress, url_index, "failed", "error", error=error_message)
                    progress["failed"] = failed
                    
                    error_logger.log_exception("process_video_job", e, {"url": url, "shortcode": shortcode})
                    continue
                
                # Ricalcola percentuale totale
                progress["percentage"] = calculate_job_percentage(progress, total)

            # Indicizza ricette se disponibili
            if metadatas:
                progress["stage"] = "indexing"
                progress["percentage"] = max(float(progress.get("percentage") or 0.0), 95.0)
                
                logging.getLogger(__name__).info("call add_recipes_batch")
                if indexing_engine.add_recipes_batch(metadatas):
                    logging.getLogger(__name__).info("ricette inserite con successo")
                else:
                    logging.getLogger(__name__).error("errore nell'inserimento delle ricette")
        
        # Completa job
        _finalize_job(job_entry, metadatas, total, success, failed, error_details)
        return job_entry["result"]

    def _finalize_job(job_entry, metadatas, total, success, failed, error_details):
        """Finalizza il job con risultati e stato."""
        job_entry["result"] = {
            "indexed": len(metadatas),
            "total_urls": total,
            "success": success,
            "failed": failed,
        }
        
        if len(metadatas) > 0:
            job_entry["status"] = "completed"
            if error_details:
                job_entry["detail"] = f"Completato con {len(metadatas)} ricette. Errori: {'; '.join(error_details)}"
        else:
            job_entry["status"] = "failed"
            if error_details:
                job_entry["detail"] = "; ".join(error_details)
            else:
                job_entry["detail"] = "Nessuna ricetta indicizzata"
        
        job_entry["progress"]["stage"] = "done"
        job_entry["progress"]["percentage"] = 100.0
        app.state.jobs[job_id] = job_entry

    # CORREZIONE: Esegui direttamente la funzione asincrona
    try:
        job_token = job_id_var.set(job_id)
        await _process_urls()
    except Exception as e:
        # Gestisci errore globale del job
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

async def _ingest_folder_job(job_id: str, dir_list: List[str]):
    """
    Job principale per l'importazione di ricette da cartella locale.
    
    Processa una cartella locale, estrae le informazioni delle ricette,
    genera i metadati e li indicizza nel database vettoriale Elysia/Weaviate.
    """
    total = len(dir_list)
    
    # Inizializza stato job
    job_entry = app.state.jobs.get(job_id) or {}
    job_entry["status"] = "running"
    progress = job_entry.setdefault("progress", {
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
            for i, u in enumerate(dir_list)
        ],
    })
    progress["stage"] = "running"
    app.state.jobs[job_id] = job_entry

    async def _process_dir_list():
        """Processa tutti gli URL e gestisce il progresso."""
        metadatas = []
        success = 0
        failed = 0
        error_details = []
        
        # Ottieni il progresso dal job_entry
        current_progress = job_entry.get("progress", {})
        
        with WeaviateSemanticEngine() as indexing_engine:
            for i, dir_name in enumerate(dir_list, start=1):
                dir_index = i - 1
                
                # Aggiorna stato URL a running
                update_url_progress(current_progress, dir_index, "running", "download")
                
                # Crea callback per progresso
                progress_callback = create_progress_callback(current_progress, dir_index, total)
                
                try:
                    # Usa dir_name invece di dir_list[i] per evitare errori di indicizzazione
                    metadata_path = os.path.join(BASE_FOLDER_RICETTE, dir_name, "media_original", f"metadata_{dir_name}.json")
                    
                    # Controlla se il file esiste prima di aprirlo
                    if not os.path.exists(metadata_path):
                        raise FileNotFoundError(f"File metadata non trovato: {metadata_path}")
                    
                    with open(metadata_path, "r") as f:
                        recipe_data = json.load(f)
                    
                    metadatas.append(recipe_data)
                    success += 1
                    
                    update_url_progress(current_progress, dir_index, "success", "done", 100.0)
                    current_progress["success"] = success
                    
                except Exception as e:
                    failed += 1
                    error_message = str(e)
                    #shortcode = extract_shortcode_from_url(url)
                    
                    error_details.append(f"URL {i} ({dir_name}): {error_message}")
                    update_url_progress(current_progress, dir_index, "failed", "error", error=error_message)
                    current_progress["failed"] = failed
                    
                    error_logger.log_exception("process_folder_job", e, {"dir_name": dir_name, "shortcode": dir_list[i]})
                    continue
                
                # Ricalcola percentuale totale
                current_progress["percentage"] = calculate_job_percentage(current_progress, total)
            #print("fine process_dir_list", metadatas)    
            logging.getLogger(__name__).info(f"Loaded metadata")

            # Indicizza ricette se disponibili
            if metadatas:
                current_progress["stage"] = "indexing"
                current_progress["percentage"] = max(float(current_progress.get("percentage") or 0.0), 95.0)
                
                logging.getLogger(__name__).info("call add_recipes_batch")
                if indexing_engine.add_recipes_batch(metadatas):
                    logging.getLogger(__name__).info("ricette inserite con successo")
                    _preprocess_collection(WCD_COLLECTION_NAME)
                else:
                    logging.getLogger(__name__).error("errore nell'inserimento delle ricette")
        
        # Aggiorna il job_entry con il progresso finale
        job_entry["progress"] = current_progress
        app.state.jobs[job_id] = job_entry
        
        # Completa job
        _finalize_job(job_entry, metadatas, total, success, failed, error_details)
        return job_entry["result"]

    def _finalize_job(job_entry, metadatas, total, success, failed, error_details):
        """Finalizza il job con risultati e stato."""
        job_entry["result"] = {
            "indexed": len(metadatas),
            "total_urls": total,
            "success": success,
            "failed": failed,
        }
        
        if len(metadatas) > 0:
            job_entry["status"] = "completed"
            if error_details:
                job_entry["detail"] = f"Completato con {len(metadatas)} ricette. Errori: {'; '.join(error_details)}"
        else:
            job_entry["status"] = "failed"
            if error_details:
                job_entry["detail"] = "; ".join(error_details)
            else:
                job_entry["detail"] = "Nessuna ricetta indicizzata"
        
        job_entry["progress"]["stage"] = "done"
        job_entry["progress"]["percentage"] = 100.0
        app.state.jobs[job_id] = job_entry

    # CORREZIONE: Esegui direttamente la funzione asincrona
    try:
        job_token = job_id_var.set(job_id)
        await _process_dir_list()
    except Exception as e:
        # Gestisci errore globale del job
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

    
# ===============================
# INIZIALIZZAZIONE APPLICAZIONE
# ===============================

app = FastAPI(
    title="Smart Recipe",
    version="0.7",
    description="API per gestione ricette con ricerca semantica basata su Weaviate/Elysia",
    lifespan=lifespan
)

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
    background_tasks.add_task(_ingest_urls_job, job_id, url_list)
    return JobStatus(job_id=job_id, status="queued", progress_percent=0.0, progress=app.state.jobs[job_id]["progress"])

@app.post("/recipes/importFromFolder", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
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
    background_tasks.add_task(_ingest_folder_job, job_id, dir_list)
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
     return search_recipes_elysia(query, limit)

@app.get("/recipes/delete/")
def delete_recipe(shortcode: str):
    """
    Elimina una ricetta specifica tramite shortcode.
    """
    with WeaviateSemanticEngine() as db_engine:
        db_engine.delete_recipe(shortcode)
    return {"message": "Ricetta eliminata con successo"}

@app.get("/recipes/{shortcode}")
def get_recipe_by_shortcode(shortcode: str):
    """
    Recupera una ricetta specifica tramite shortcode.
    
    TODO: Implementare ricerca per shortcode in Weaviate.
    
    Args:
        shortcode: Identificativo univoco della ricetta
        
    Returns:
        Metadati completi della ricetta
        
    Raises:
        HTTPException 501: Funzionalità non ancora implementata
    """
    try:
        # TODO: Implementare ricerca per shortcode specifico
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Ricerca per shortcode non ancora implementata"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_exception("get_recipe", e, {"shortcode": shortcode})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Errore interno: {str(e)}")

@app.get("/embeddings/preview3d")
def embeddings_preview3d(limit: int = 1000, with_meta: bool = True):
    """
    Visualizzazione 3D degli embeddings (DEPRECATO).
    
    Questa funzionalità non è attualmente supportata con Weaviate/Elysia.
    Mantenuta per compatibilità backward.
    
    Args:
        limit: Numero massimo di punti da visualizzare
        with_meta: Include metadati nei risultati
        
    Returns:
        Dict vuoto con messaggio di non supportato
    """
    # TODO: Implementare visualizzazione embeddings con Weaviate
    return {
        "status": "ok", 
        "n": 0, 
        "points": [], 
        "message": "Embeddings 3D view non supportata con Elysia"
    }

@app.get("/embeddings/3d", response_class=HTMLResponse)
def embeddings_3d_page():
    """
    Serve pagina HTML per visualizzazione embeddings 3D (DEPRECATO).
    
    Mantenuto per compatibilità backward.
    """
    html_path = os.path.join(BASE_DIR, "static", "embeddings_3d.html")
    if os.path.isfile(html_path):
        return FileResponse(html_path)
    # Fallback inline se il file non esiste
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Embeddings 3D Preview</title>
        <script src=\"https://cdn.plot.ly/plotly-2.30.0.min.js\"></script>
        <style>
          html, body { height: 100%; margin: 0; }
          #plot { width: 100%; height: 100%; }
        </style>
      </head>
      <body>
        <div id=\"plot\"></div>
        <script>
        async function loadAndPlot(){
          const res = await fetch('/embeddings/preview3d?limit=1000&with_meta=1');
          const data = await res.json();
          if(data.status !== 'ok' || !data.points || !data.points.length){
            document.getElementById('plot').innerHTML = 'Nessun dato disponibile';
            return;
          }
          const xs = data.points.map(p => p.x);
          const ys = data.points.map(p => p.y);
          const zs = data.points.map(p => p.z);
          const texts = data.points.map(p => (p.label || p.id));
          const trace = {
            type: 'scatter3d',
            mode: 'markers',
            x: xs, y: ys, z: zs,
            text: texts,
            marker: { size: 3, opacity: 0.8 }
          };
          const layout = {
            title: 'Embeddings (PCA 3D)',
            scene: {xaxis:{title:'PC1'}, yaxis:{title:'PC2'}, zaxis:{title:'PC3'}},
            margin: {l:0, r:0, t:40, b:0}
          };
          Plotly.newPlot('plot', [trace], layout, {responsive: true});
        }
        loadAndPlot();
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/embeddings/preview3d_with_query")
def embeddings_preview3d_with_query(q: str, limit: int = 1000, with_meta: bool = True):
    """
    Visualizzazione 3D embeddings con query (DEPRECATO).
    
    Non supportato con Weaviate/Elysia.
    
    Args:
        q: Query di ricerca
        limit: Numero massimo punti
        with_meta: Include metadati
        
    Returns:
        Dict vuoto con messaggio non supportato
    """
    # TODO: Implementare con Weaviate se necessario
    return {
        "status": "ok",
        "n": 0,
        "points": [],
        "query_point": None,
        "message": "Embeddings 3D view con query non supportata con Elysia"
    }
 
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
        #stats = elysia_recipe_db.get_stats()
        stats = {}
        return {
            "status": "ok",
            "system": "Smart Recipe API",
            "version": "0.7 - Ottimizzato",
            "embedding_model": EMBEDDING_MODEL,
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
