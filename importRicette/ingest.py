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
from utility.error_handler import ErrorHandler, ErrorSeverity, ErrorAction, BatchErrorHandler
from utility.openai_errors import OpenAIError
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
from utility.path_utils import ensure_media_web_paths, ensure_media_web_path, web_path_to_filesystem_path

# Setup logging
setup_logging()
error_logger = get_error_logger(__name__)
error_handler = ErrorHandler(__name__)


async def _process_single_url(url: str, progress_callback, shortcode: str, force_redownload: bool = False):
    """
    Processa un singolo URL con gestione errori standardizzata.
    
    Args:
        url: URL da processare
        progress_callback: Callback per aggiornamenti progresso
        shortcode: Shortcode estratto dall'URL
        force_redownload: Se True, forza il ri-download anche se già presente
        
    Returns:
        RecipeDBSchema o None se errore
        
    Raises:
        OpenAIError: Se si verifica un errore OpenAI (quota, rate limit, ecc.)
        Exception: Per altri tipi di errore
    """
    try:
        # Processa video
        recipe_data = await process_video(url, progress_cb=progress_callback, force_redownload=force_redownload)
        
        if not recipe_data:
            raise ValueError("Recipe data is empty")

        if not NO_IMAGE and len(recipe_data.images) > 0:
            # Converti percorso web in percorso filesystem per colorgram
            image_path = web_path_to_filesystem_path(recipe_data.images[0])
            palette_colors = colorgram.extract(image_path, 4)
            palette_hex = [rgb_to_hex(color.rgb.r, color.rgb.g, color.rgb.b) for color in palette_colors]
            recipe_data.palette_hex = palette_hex

        recipe_data.images = ensure_media_web_paths(recipe_data.images)

        # Salva metadati
        if not save_recipe_metadata(recipe_data, BASE_FOLDER_RICETTE):
            raise ValueError("Failed to save recipe metadata")
        
        return recipe_data
    
    except OpenAIError:
        # Rilancia errori OpenAI per gestione speciale
        raise
    except Exception as e:
        # Altri errori vengono rilanciati
        raise


async def _ingest_urls_job(app: FastAPI, job_id: str, urls: List[str], force_redownload: bool = False):
    """
    Job principale per l'importazione di ricette da URL video.
    
    Processa una lista di URL video, estrae le informazioni delle ricette,
    genera i metadati e li indicizza nel database vettoriale Elysia/Weaviate.
    
    Args:
        job_id: ID univoco del job per tracking
        urls: Lista di URL video da processare
        force_redownload: Se True, forza il ri-download anche se già presente
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
        batch_error_handler = BatchErrorHandler(__name__)
        
        with WeaviateSemanticEngine() as indexing_engine:
            for i, url in enumerate(urls, start=1):
                url_index = i - 1
                shortcode = extract_shortcode_from_url(url)
                
                # Aggiorna stato URL a running
                update_url_progress(progress, url_index, "running", "download")
                
                # Crea callback per progresso
                progress_callback = create_progress_callback(progress, url_index, total)
                
                # Gestione con cattura specifica errori OpenAI
                recipe_data = None
                error_message = None
                
                try:
                    recipe_data = await _process_single_url(
                        url, progress_callback, shortcode, force_redownload
                    )
                except OpenAIError as openai_err:
                    # Errore OpenAI: usa messaggio user-friendly
                    error_message = openai_err.user_message
                    error_logger.log_error(
                        f"openai_error_url_{i}",
                        f"OpenAI error processing URL: {openai_err.message}",
                        {
                            "url": url,
                            "shortcode": shortcode,
                            "error_type": openai_err.error_type.value,
                            "should_retry": openai_err.should_retry
                        }
                    )
                    batch_error_handler.add_error(
                        openai_err, shortcode, f"process_url_{i}", ErrorSeverity.HIGH
                    )
                except Exception as e:
                    # Errore generico
                    error_message = str(e)
                    error_logger.log_exception(
                        f"error_url_{i}", e,
                        {"url": url, "shortcode": shortcode, "url_index": i}
                    )
                    batch_error_handler.add_error(
                        e, shortcode, f"process_url_{i}", ErrorSeverity.MEDIUM
                    )
                
                if recipe_data:
                    metadatas.append(recipe_data)
                    batch_error_handler.add_success(shortcode, recipe_data)
                    update_url_progress(progress, url_index, "success", "done", 100.0)
                else:
                    # Imposta errore con messaggio appropriato
                    final_error_msg = error_message or "Processing failed"
                    update_url_progress(progress, url_index, "failed", "error", 
                                      error=final_error_msg)
                
                # Aggiorna progresso
                summary = batch_error_handler.get_summary()
                progress["success"] = summary["successes"]
                progress["failed"] = summary["errors"]
                progress["percentage"] = calculate_job_percentage(progress, total)
                
                # Controllo soglia errori (opzionale)
                if batch_error_handler.should_abort(error_threshold=0.8):
                    logging.getLogger(__name__).warning(
                        f"Troppi errori nel batch ({summary['errors']}/{summary['total']}), "
                        "ma continuiamo lo stesso"
                    )

            # Indicizza ricette se disponibili
            if metadatas:
                progress["stage"] = "indexing"
                progress["percentage"] = max(float(progress.get("percentage") or 0.0), 95.0)
                
                logging.getLogger(__name__).info("call add_recipes_batch")
                if indexing_engine.add_recipes_batch(metadatas):
                    logging.getLogger(__name__).info("ricette inserite con successo")
                else:
                    logging.getLogger(__name__).error("errore nell'inserimento delle ricette")
        
        # Usa summary del batch error handler
        summary = batch_error_handler.get_summary()
        error_details = [f"URL {err['item_id']}: {str(err['error'])}" for err in summary['error_details']]
        
        # Completa job con dati dal batch handler
        _finalize_job(job_entry, metadatas, total, summary['successes'], summary['errors'], error_details)
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
                    try:
                        generated_images = await generateRecipeImages(recipe_data, recipe_data.get("shortcode", dir_name))
                        # Converti percorso web in percorso filesystem per colorgram (usa prima immagine se è lista)
                        first_image = generated_images[0] if isinstance(generated_images, list) and generated_images else generated_images
                        image_path = web_path_to_filesystem_path(first_image)
                        palette_colors = colorgram.extract(image_path, 4)
                        palette_hex = [rgb_to_hex(color.rgb.r, color.rgb.g, color.rgb.b) for color in palette_colors]
                        recipe_data["palette_hex"] = palette_hex

                        generated_images = ensure_media_web_paths(generated_images)
                        recipe_data["images"] = generated_images or []
                        if generated_images and not recipe_data.get("image_url"):
                            recipe_data["image_url"] = generated_images[0]
                    except OpenAIError as openai_err:
                        # Per errori OpenAI in generazione immagini, logga ma continua
                        error_logger.log_error(
                            "generate_images_openai_error_folder",
                            f"OpenAI error generating images: {openai_err.user_message}",
                            {
                                "dir_name": dir_name,
                                "error_type": openai_err.error_type.value,
                                "severity": "medium"
                            }
                        )
                        # Continua senza immagini
                        recipe_data["images"] = []
                        logging.getLogger(__name__).warning(
                            f"Image generation failed for '{dir_name}': {openai_err.user_message}"
                        )
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
             with WeaviateSemanticEngine() as indexing_engine:

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

    
