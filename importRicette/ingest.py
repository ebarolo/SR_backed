import os
import json
import logging
from typing import List

from fastapi import FastAPI
from colorgram import colorgram

from utility.logging_config import (
    setup_logging, 
    get_error_logger,
    job_id_var
)
from importRicette.save import process_video
from importRicette.analize import generateRecipeImages
from rag._weaviate import WeaviateSemanticEngine
from rag._elysia import _preprocess_collection

from config import BASE_FOLDER_RICETTE, WCD_COLLECTION_NAME, NO_IMAGE
from utility.utility import (
    extract_shortcode_from_url,
    calculate_job_percentage,
    create_progress_callback,
    update_url_progress,
    save_recipe_metadata,
    rgb_to_hex
)
from utility.path_utils import ensure_media_web_paths, ensure_media_web_path

# Setup logging
setup_logging()
error_logger = get_error_logger(__name__)


async def _ingest_urls_job(app: FastAPI, job_id: str, urls: List[str]):
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

                    if not NO_IMAGE and len(recipe_data.images) > 0:
                        palette_colors = colorgram.extract(recipe_data.images[0], 4)
                        palette_hex = [rgb_to_hex(color.rgb.r, color.rgb.g, color.rgb.b) for color in palette_colors]
                        recipe_data["palette_hex"] = palette_hex

                    recipe_data.images = ensure_media_web_paths(recipe_data.images)

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

async def _ingest_folder_job(app: FastAPI, job_id: str, dir_list: List[str]):
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

                    raw_images = recipe_data.get("images") or []
                    if not isinstance(raw_images, list):
                        raw_images = [raw_images]
                    images = ensure_media_web_paths(raw_images)

                    if not NO_IMAGE and len(images) == 0:
                        generated_images = await generateRecipeImages(recipe_data, recipe_data.get("shortcode", dir_name))
                        palette_colors = colorgram.extract(generated_images, 4)
                        palette_hex = [rgb_to_hex(color.rgb.r, color.rgb.g, color.rgb.b) for color in palette_colors]
                        recipe_data["palette_hex"] = palette_hex

                        generated_images = ensure_media_web_paths(generated_images)
                        recipe_data["images"] = generated_images or []
                        if generated_images and not recipe_data.get("image_url"):
                            recipe_data["image_url"] = generated_images[0]
                    else:
                        recipe_data["images"] = images

                    if recipe_data.get("image_url"):
                        recipe_data["image_url"] = ensure_media_web_path(recipe_data["image_url"])

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
                    
                    error_logger.log_exception("process_folder_job", e, {"dir_name": dir_name, "shortcode": dir_name})
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

    
