"""
Smart Recipe API - Sistema di gestione ricette con ricerca semantica.

Questo modulo implementa il backend FastAPI per Smart Recipe, un sistema
di gestione ricette che utilizza Weaviate/Elysia per la ricerca semantica
e OpenAI GPT-5 per l'elaborazione intelligente delle ricette.

Author: Smart Recipe Team
Version: 0.7
"""

# Import FastAPI e middleware
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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
from config import BASE_FOLDER_RICETTE, EMBEDDING_MODEL
from models import RecipeDBSchema, JobStatus, Ingredient
from RAG.elysia_ import add_recipes_elysia, search_recipes_elysia
from importRicette.saveRecipe import process_video
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

def _reimport_shortcodes_job(job_id: str, shortcodes: List[str]):
    """
    Job in background per reimportare ricette da shortcode esistenti.
    
    TODO: Implementare la logica effettiva di reimport.
    Attualmente è solo un placeholder.
    
    Args:
        job_id: ID univoco del job
        shortcodes: Lista di shortcode da reimportare
    """
    try:
        # Imposta il job ID per il logging
        job_id_var.set(job_id)
        
        # TODO: Implementare la logica di reimport
        # Per ora simuliamo il processo
        import time
        time.sleep(2)  # Simula elaborazione
        
        error_logger.info(f"Reimport completato per shortcode: {shortcodes}")
        
    except Exception as e:
        error_logger.log_exception("reimport_shortcodes", e, {"shortcodes": shortcodes})

def _ingest_urls_job(job_id: str, urls: List[str]):
    """
    Job principale per l'importazione di ricette da URL video.
    
    Processa una lista di URL video, estrae le informazioni delle ricette,
    genera i metadati e li indicizza nel database vettoriale Elysia/Weaviate.
    
    Args:
        job_id: ID univoco del job per tracking
        urls: Lista di URL video da processare
    """
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
        error_details = []  # Raccoglie i dettagli degli errori

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
                    raise ValueError("Recipe data is empty")
                
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
            except Exception as e:
                failed += 1
                error_message = str(e)
                
                # Estrai shortcode dall'URL per messaggi più informativi
                shortcode = "unknown"
                try:
                    if "instagram.com" in url.lower():
                        # Estrai shortcode da URL Instagram
                        url_parts = url.split("/")
                        for i_part, part in enumerate(url_parts):
                            if part in ["p", "reel", "tv"] and i_part + 1 < len(url_parts):
                                shortcode = url_parts[i_part + 1]
                                break
                    elif "youtube.com" in url.lower() or "youtu.be" in url.lower():
                        # Estrai video ID da URL YouTube
                        if "v=" in url:
                            shortcode = url.split("v=")[1].split("&")[0]
                        elif "youtu.be/" in url:
                            shortcode = url.split("youtu.be/")[1].split("?")[0]
                    else:
                        # Per altri URL, usa l'ultima parte del path
                        shortcode = url.split("/")[-1].split("?")[0]
                except Exception:
                    shortcode = "unknown"
                
                # Raccoglie i dettagli dell'errore con shortcode specifico
                error_details.append(f"URL {i} ({shortcode}): {error_message}")
                
                if 0 <= idx0 < len(progress.get("urls", [])):
                    ue = progress["urls"][idx0]
                    if ue.get("stage") != "error":
                        ue["stage"] = "error"
                    ue["status"] = "failed"
                    ue["error"] = error_message
                progress["failed"] = failed
                progress["percentage"] = _recalc_job_percentage()
                # Log dell'errore specifico con shortcode estratto
                error_logger.log_exception("process_video_job", e, {"url": url, "shortcode": shortcode})
                continue

        if metadatas:
            
            progress["stage"] = "indexing"
            progress["percentage"] = max(float(progress.get("percentage") or 0.0), 95.0)
            logging.getLogger(__name__).info(f"call ingest_json_to_elysia", extra={})
 
            #for metadata in metadatas:
            if add_recipes_elysia(metadatas):
                logging.getLogger(__name__).info(f"ricette inserite con successo")
            else:
                logging.getLogger(__name__).error(f"errore nell'inserimento delle ricette")
            
            
        # Completa job
        job_entry["result"] = {
            "indexed": len(metadatas),
            "total_urls": total,
            "success": success,
            "failed": failed,
        }
        if len(metadatas) > 0:
            job_entry["status"] = "completed"
            # Aggiungi dettagli degli errori se ci sono stati fallimenti
            if error_details:
                job_entry["detail"] = f"Completato con {len(metadatas)} ricette. Errori: {'; '.join(error_details)}"
        else:
            job_entry["status"] = "failed"
            # Usa i dettagli degli errori raccolti o un messaggio di default
            if error_details:
                job_entry["detail"] = "; ".join(error_details)
            else:
                job_entry["detail"] = "Nessuna ricetta indicizzata"
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

# ===============================
# INIZIALIZZAZIONE APPLICAZIONE
# ===============================

app = FastAPI(
    title="Smart Recipe",
    version="0.7",
    description="API per gestione ricette con ricerca semantica basata su Weaviate/Elysia",
    lifespan=lifespan
)

# Configurazione CORS per permettere richieste cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# ENDPOINTS API
# ===============================

@app.get("/shortcodes/list")
async def get_shortcodes_list():
    """
    Recupera la lista di tutti gli shortcode disponibili.
    
    Scansiona la directory MediaRicette e restituisce informazioni
    su tutte le ricette salvate localmente.
    
    Returns:
        Dict con lista shortcode e conteggio totale
    """
    try:
        media_dir = os.path.join(BASE_DIR, "static", "MediaRicette")
        
        if not os.path.exists(media_dir):
            return {"shortcodes": [], "total": 0}
        
        # Ottieni tutte le directory (shortcode)
        shortcodes = []
        for item in os.listdir(media_dir):
            item_path = os.path.join(media_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Conta i file di ricetta (inclusi quelli nelle sottocartelle)
                recipe_files = []
                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        if file.endswith(('.json', '.mp3', '.jpg', '.jpeg', '.png')) and not file.startswith('.'):
                            recipe_files.append(os.path.join(root, file))
                
                if recipe_files:
                    shortcodes.append({
                        "shortcode": item,
                        "path": item_path,
                        "files_count": len(recipe_files)
                    })
        
        # Ordina per nome
        shortcodes.sort(key=lambda x: x["shortcode"])
        
        return {
            "shortcodes": shortcodes,
            "total": len(shortcodes)
        }
        
    except Exception as e:
        error_logger.error(f"Errore nel recupero shortcode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero shortcode: {str(e)}"
        )

@app.post("/shortcodes/reimport")
async def reimport_selected_shortcodes(shortcodes: List[str], background_tasks: BackgroundTasks):
    """
    Avvia il reimport di ricette selezionate.
    
    TODO: Implementazione completa del reimport.
    
    Args:
        shortcodes: Lista di shortcode da reimportare
        background_tasks: Gestore task in background FastAPI
        
    Returns:
        Dict con job_id e stato del task
    """
    try:
        if not shortcodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessun shortcode fornito"
            )
        
        # Genera un job ID per il reimport
        job_id = str(uuid.uuid4())
        
        # Avvia il reimport in background
        background_tasks.add_task(_reimport_shortcodes_job, job_id, shortcodes)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Reimport avviato per {len(shortcodes)} shortcode",
            "shortcodes": shortcodes
        }
        
    except Exception as e:
        error_logger.error(f"Errore nell'avvio reimport shortcode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nell'avvio reimport: {str(e)}"
        )

# Configurazione mount directory statiche
app.mount("/mediaRicette", StaticFiles(directory=os.path.join(BASE_DIR, "static", "mediaRicette")), name="mediaRicette")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/frontend", StaticFiles(directory=os.path.join(BASE_DIR, "frontend")), name="frontend")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Middleware per aggiungere Request ID a tutte le richieste HTTP.
    
    Aggiunge un ID univoco ad ogni richiesta per tracciamento e logging.
    Logga solo errori (>=400) e warning per ridurre verbosità.
    """
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

@app.get("/", include_in_schema=False)
async def index():
    """
    Serve la pagina index.html del frontend.
    
    Cerca prima in frontend/, poi in static/ come fallback.
    """
    dist_index = os.path.join(DIST_DIR, "index.html")
    static_index = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.isfile(dist_index):
        return FileResponse(dist_index)
    if os.path.isfile(static_index):
        return FileResponse(static_index)
    return JSONResponse({"detail": "index.html non trovato"}, status_code=404)

@app.post("/ingest/recipes", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
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

@app.get("/ingest/status")
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

@app.get("/ingest/status/{job_id}", response_model=JobStatus)
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

@app.get("/recipe/{shortcode}")
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

@app.get("/search/")
def search_recipes(
    query: str,
    limit: int = 12,
    max_time: Optional[int] = None,
    difficulty: Optional[str] = None,
    diet: Optional[str] = None,
    cuisine: Optional[str] = None
):
    """
    Endpoint principale per ricerca semantica ricette.
    
    Utilizza Weaviate/Elysia per ricerca vettoriale semantica
    con supporto per filtri multipli.
    
    Args:
        query: Testo di ricerca
        limit: Numero massimo risultati (default 12)
        max_time: Tempo massimo preparazione in minuti
        difficulty: Livello difficoltà ricetta
        diet: Tipo di dieta (vegan, vegetarian, etc.)
        cuisine: Tipo di cucina
        
    Returns:
        Lista ricette ordinate per rilevanza
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
        
        # Usa il sistema Elysia/Weaviate
        results, oggetti = search_recipes_elysia(query, limit)
        logging.info(f"✅ Ricerca semantica con Elysia/Weaviate completata con successo {results} {oggetti}")
        return oggetti
        
    except Exception as e:
        error_logger.log_exception("search", e, {"query": query[:50]})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Errore in ricerca semantica")
  
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
