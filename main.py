from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks, Request

from config import ( openAIclient, BASE_FOLDER_RICETTE, COLLECTION_NAME)

import uuid
import os
import uvicorn
import json

from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

from models import RecipeDBSchema, JobStatus, Ingredient
from typing import List
#from DB.langchain import get_langchain_recipe_db


from time import perf_counter
from importRicette.saveRecipe import process_video
from DB.elysia import ElysiaRecipeDatabase
import logging
from logging_config import setup_logging, get_error_logger, clear_error_chain
from logging_config import request_id_var, job_id_var
import asyncio as _asyncio

from DB.elysia import ingest_json_to_elysia, search_recipes_elysia, get_recipe_by_shortcode_elysia, elysia_recipe_db

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
            logging.getLogger(__name__).info(f"call get_langchain_recipe_db", extra={})

            #n, coll = ingest_json_to_chroma(metadatas, collection_name=COLLECTION_NAME)
            #db = get_langchain_recipe_db()
            #success_count, errors = db.add_recipes_batch(metadatas)
            success_count, errors = ingest_json_to_elysia(metadatas, collection_name=COLLECTION_NAME)

            print(f"Inseriti {success_count} record nella collection.")
            
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
    
    Usa il sistema Elysia/Weaviate per la ricerca semantica.
    """
    try:
        recipe_data = get_recipe_by_shortcode_elysia(shortcode)
        
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

@app.get("/embeddings/preview3d")
def embeddings_preview3d(limit: int = 1000, with_meta: bool = True):
    """
    Restituisce una proiezione 3D (PCA) degli embeddings per visualizzazione browser.

    - Usa ChromaDB per leggere `ids`, `embeddings` e opzionalmente `documents`/`metadatas`.
    - Proiezione PCA 3D implementata con NumPy (SVD).
    """
    try:
        # Verifica disponibilità collection 
        if not getattr(elysia_recipe_db, "collection", None):
            raise HTTPException(status_code=503, detail="Elysia/Weaviate non disponibile")

        # Import locale per non vincolare l'avvio se numpy manca
        try:
            import numpy as np  # type: ignore
        except Exception:
            raise HTTPException(status_code=500, detail="NumPy non installato: impossibile calcolare PCA 3D")

        # Funzionalità embeddings 3D temporaneamente non supportata con Elysia
        # TODO: Implementare visualizzazione embeddings con Weaviate
        return {"status": "ok", "n": 0, "points": [], "message": "Embeddings 3D view non supportata con Elysia"}

        embeddings = results.get("embeddings")
        if embeddings is None:
            embeddings = []
        ids = results.get("ids")
        if ids is None:
            ids = []
        documents = results.get("documents")
        if documents is None:
            documents = []
        metadatas = results.get("metadatas")
        if metadatas is None:
            metadatas = []

        if len(embeddings) == 0 or len(ids) == 0:
            return {"status": "ok", "n": 0, "points": []}

        # Costruisci matrice e PCA 3D
        X = np.asarray(embeddings, dtype=float)
        # Validazione forma dati
        if X.size == 0 or X.ndim != 2:
            return {"status": "ok", "n": 0, "points": []}
        # Allinea lunghezze con ids (difese su inconsistenze)
        n = min(len(ids), X.shape[0])
        if n == 0:
            return {"status": "ok", "n": 0, "points": []}
        X = X[:n]
        ids = ids[:n]
        if documents:
            documents = documents[:n]
        if metadatas:
            metadatas = metadatas[:n]
        # Centering
        Xc = X - X.mean(axis=0, keepdims=True)
        # SVD
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        # Proiezione sui primi 3 componenti
        comps = Vt[:3].T if Vt.shape[0] >= 3 else Vt.T  # gestione dimensioni < 3
        coords = Xc @ comps

        # Prepara etichette
        labels = []
        if documents:
            for doc in documents:
                # Estrai titolo se presente nel documento strutturato
                label = None
                try:
                    first_line = (doc.split("\n", 1)[0] or "").strip()
                    if first_line.lower().startswith("titolo:"):
                        label = first_line.split(":", 1)[1].strip()
                except Exception:
                    label = None
                labels.append(label)
        else:
            labels = [None] * len(ids)

        # Costruisci risposta compatta
        points = []
        for i, rid in enumerate(ids):
            x = float(coords[i, 0]) if coords.shape[1] >= 1 else 0.0
            y = float(coords[i, 1]) if coords.shape[1] >= 2 else 0.0
            z = float(coords[i, 2]) if coords.shape[1] >= 3 else 0.0
            pt = {"id": rid, "x": x, "y": y, "z": z}
            if with_meta:
                if labels:
                    pt["label"] = labels[i]
                if metadatas:
                    pt["meta"] = metadatas[i]
            points.append(pt)

        return {"status": "ok", "n": len(points), "points": points}
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_exception("embeddings_preview3d", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/embeddings/3d", response_class=HTMLResponse)
def embeddings_3d_page():
    """
    Pagina HTML semplice che visualizza gli embeddings 3D via Plotly.
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
    Come `preview3d`, ma aggiunge il punto della query proiettato negli stessi assi PCA.
    """
    try:
        if not getattr(elysia_recipe_db, "collection", None):
            raise HTTPException(status_code=503, detail="Elysia/Weaviate non disponibile")

        try:
            import numpy as np  # type: ignore
        except Exception:
            raise HTTPException(status_code=500, detail="NumPy non installato: impossibile calcolare PCA 3D")

        # Funzionalità embeddings 3D con query temporaneamente non supportata con Elysia
        # TODO: Implementare con Weaviate
        return {"status": "ok", "n": 0, "points": [], "query_point": None, "message": "Embeddings 3D view con query non supportata con Elysia"}

        embeddings = results.get("embeddings")
        if embeddings is None:
            embeddings = []
        ids = results.get("ids")
        if ids is None:
            ids = []
        documents = results.get("documents")
        if documents is None:
            documents = []
        metadatas = results.get("metadatas")
        if metadatas is None:
            metadatas = []

        X = np.asarray(embeddings, dtype=float)
        if X.size == 0 or X.ndim != 2:
            return {"status": "ok", "n": 0, "points": [], "query_point": None}

        n = min(len(ids), X.shape[0])
        if n == 0:
            return {"status": "ok", "n": 0, "points": [], "query_point": None}
        X = X[:n]
        ids = ids[:n]
        if documents:
            documents = documents[:n]
        if metadatas:
            metadatas = metadatas[:n]

        # PCA su dataset
        Xmean = X.mean(axis=0, keepdims=True)
        Xc = X - Xmean
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        comps = Vt[:3].T if Vt.shape[0] >= 3 else Vt.T
        coords = Xc @ comps

        # Embedding della query non supportato direttamente con Elysia
        # La gestione degli embeddings è interna a Weaviate
        return {"status": "ok", "n": 0, "points": [], "query_point": None, "message": "Embeddings query non supportata con Elysia"}
        qv = np.asarray(q_vec, dtype=float)
        if qv.ndim == 1:
            qv = qv.reshape(1, -1)
        # Match dimensioni: se la dimensione del modello differisce, taglia/riempie a zero
        d = X.shape[1]
        if qv.shape[1] != d:
            if qv.shape[1] > d:
                qv = qv[:, :d]
            else:
                pad = np.zeros((1, d - qv.shape[1]), dtype=float)
                qv = np.concatenate([qv, pad], axis=1)
        q_centered = qv - Xmean
        q_coords = (q_centered @ comps)[0]

        # Etichette
        labels = []
        if documents:
            for doc in documents:
                label = None
                try:
                    first_line = (doc.split("\n", 1)[0] or "").strip()
                    if first_line.lower().startswith("titolo:"):
                        label = first_line.split(":", 1)[1].strip()
                except Exception:
                    label = None
                labels.append(label)
        else:
            labels = [None] * len(ids)

        points = []
        for i, rid in enumerate(ids):
            x = float(coords[i, 0]) if coords.shape[1] >= 1 else 0.0
            y = float(coords[i, 1]) if coords.shape[1] >= 2 else 0.0
            z = float(coords[i, 2]) if coords.shape[1] >= 3 else 0.0
            pt = {"id": rid, "x": x, "y": y, "z": z}
            if with_meta:
                if labels:
                    pt["label"] = labels[i]
                if metadatas:
                    pt["meta"] = metadatas[i]
            points.append(pt)

        query_point = {
            "id": "__query__",
            "label": q,
            "x": float(q_coords[0]) if q_coords.shape[0] >= 1 else 0.0,
            "y": float(q_coords[1]) if q_coords.shape[0] >= 2 else 0.0,
            "z": float(q_coords[2]) if q_coords.shape[0] >= 3 else 0.0,
        }

        return {"status": "ok", "n": len(points), "points": points, "query_point": query_point}
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_exception("embeddings_preview3d_with_query", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/")
def search_recipes(query: str, limit: int = 12, max_time: Optional[int] = None, difficulty: Optional[str] = None, diet: Optional[str] = None, cuisine: Optional[str] = None):
    """
    Ricerca semantica con Elysia/Weaviate.
    
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
        
        # Usa il sistema Elysia/Weaviate
        results = search_recipes_elysia(query, limit, filters)
        
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
        
        #recipe_db = RecipeDatabase()
        #db = get_langchain_recipe_db()
         # Elenca tutte le entry nella directory
        for entry in os.listdir(BASE_FOLDER_RICETTE):
            entry_path = os.path.join(BASE_FOLDER_RICETTE, entry)
            # Controlla se è una directory
            if os.path.isdir(entry_path):
                recipe_folders.append(entry)
        
         # Ordina le cartelle alfabeticamente
        recipe_folders.sort()
        for recipe_folder in recipe_folders:

            #json_file = os.path.join(recipe_folder,"media_original", "metadata_{recipe_folder}.json")
            json_file = os.path.join(BASE_FOLDER_RICETTE, recipe_folder, "media_original", f"metadata_{recipe_folder}.json")
            logging.getLogger(__name__).info(f" {json_file}")

            if not os.path.isfile(json_file):
                error_logger.logger.warning(f"no recipe metadata json found in folder: {recipe_folder}")
                # Elimina la cartella se il file json non esiste
                try:
                    import shutil
                    shutil.rmtree(recipe_folder)
                    logging.getLogger(__name__).warning(f"Cartella eliminata: {recipe_folder} (mancava il metadata json)")
                except Exception as ex:
                    logging.getLogger(__name__).error(f"Errore nell'eliminazione della cartella {recipe_folder}: {ex}")
                continue
            else:
             with open(json_file, 'r', encoding='utf-8') as f:
                recipe_data_dict = json.load(f)
                
             # Converti dizionario in oggetto RecipeDBSchema
             try:
                recipe_data = RecipeDBSchema(**recipe_data_dict)
             except Exception as e:
                error_logger.log_exception("convert_recipe_data", e, {"shortcode": recipe_data_dict.get("shortcode", "unknown")})
                continue
                
             #recipe_db.add_recipe(recipe_data)
             logging.getLogger(__name__).info(f"recipe_data: {recipe_data}")

             #success = db.add_recipe(recipe_data_dict)
             success = ingest_json_to_elysia(recipe_data_dict, collection_name=COLLECTION_NAME)

             if success:
                 logging.getLogger(__name__).info(f"Ricetta {recipe_data.shortcode} inserita con successo nella collection.")
             else:
                 logging.getLogger(__name__).error(f"Errore nell'inserimento della ricetta {recipe_data.shortcode}")

    except Exception as e:
        error_logger.log_exception("recalc_info", e,{})
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
        stats = elysia_recipe_db.get_stats()
        
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
