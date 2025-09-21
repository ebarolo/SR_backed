"""
Modulo per il processing di video ricette.

Gestisce il download, l'estrazione audio, la trascrizione
e l'analisi di ricette da video di social media.

Author: Smart Recipe Team
"""

import os
import re
import subprocess
import asyncio
import multiprocessing as mp
import uuid
import logging
from typing import Dict, Any, Optional, Callable

# Import librerie esterne
from tenacity import retry, stop_after_attempt, wait_exponential

# Import modelli e configurazione
from utility.models import RecipeDBSchema
from config import BASE_FOLDER_RICETTE, NO_IMAGE

# Import utility
from utility.utility import sanitize_text, sanitize_filename
from utility.logging_config import get_error_logger, request_id_var, clear_error_chain

# Import moduli interni
from importRicette.analize import (
    extract_recipe_info,
    whisper_speech_recognition,
    generateRecipeImages
)
from importRicette.scrape.instaLoader import (
    scarica_contenuto_reel,
    scarica_contenuti_account
)
from importRicette.scrape.yt_dlp import yt_dlp_video


# Inizializza logger e multiprocessing
error_logger = get_error_logger(__name__)
mp.set_start_method("spawn", force=True)

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _process_video_internal(
    recipeUrl: str,
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None
) -> RecipeDBSchema:
    """
    Processa internamente un video ricetta.
    
    Gestisce diversi tipi di input:
    - Username Instagram (senza http/https): scarica tutti i reel dell'account
    - URL Instagram: usa instaloader per download
    - Altri URL: usa yt-dlp per download
    
    Args:
        recipeUrl: URL del video o username Instagram
        progress_cb: Callback per aggiornamenti progresso
        
    Returns:
        RecipeDBSchema con i dati estratti
        
    Raises:
        RuntimeError: Errore durante il processing
        ValueError: Dati non validi o mancanti
    """
    # Pulisce catena errori e imposta tracking
    clear_error_chain()
    operation_id = str(uuid.uuid4())[:8]
    request_id_var.set(f"process_video_{operation_id}")

    # Pattern per validazione URL
    urlPattern = r'^(ftp|http|https):\/\/[^ \"]+$'

    def _emit_progress(stage: str, local_percent: float, message: Optional[str] = None):
        """Helper per emettere aggiornamenti progresso."""
        if progress_cb is None:
            return
        try:
            payload: Dict[str, Any] = {
                "stage": stage,
                "local_percent": float(local_percent)
            }
            if message is not None:
                payload["message"] = message
            progress_cb(payload)
        except Exception:
            # Non interrompe il flusso se callback fallisce
            pass

    # Download video basato sul tipo di input
    try:
        if not re.match(urlPattern, recipeUrl):
            # Input è username Instagram
            dws = await scarica_contenuti_account(recipeUrl)
            _emit_progress("download", 25.0)
        else:
            url_lower = recipeUrl.lower()
            if any(host in url_lower for host in ["instagram.com"]):
                # URL Instagram: usa instaloader
                dws = await scarica_contenuto_reel(recipeUrl)
                _emit_progress("download", 25.0)
            else:
                # Altri URL: usa yt-dlp
                info = await yt_dlp_video(recipeUrl)
                
                # Crea struttura directory compatibile
                shortcode = sanitize_filename(info["video_title"]) or "video"
                downloadFolder = os.path.join(
                    BASE_FOLDER_RICETTE, shortcode, "media_original"
                )
                os.makedirs(downloadFolder, exist_ok=True)
                
                # Sposta file scaricato nella posizione corretta
                src = info["video_filename"]
                dst = os.path.join(downloadFolder, os.path.basename(info["video_filename"]))
                try:
                    if os.path.abspath(src) != os.path.abspath(dst):
                        os.replace(src, dst)
                except Exception as e:
                    error_logger.log_error(
                        "file_move",
                        f"Failed to move downloaded file: {e}",
                        {"src": src, "dst": dst}
                    )
                
                # Crea struttura dati compatibile
                dws = [{
                    "error": "",
                    "shortcode": shortcode,
                    "caption": "",
                    "url_video": recipeUrl,
                }]
                _emit_progress("download", 25.0)
    except Exception as e:
        error_logger.log_exception("download_error", e, {"recipeUrl": recipeUrl})
        _emit_progress("error", 0.0, message=str(e))
        raise e

    # Processa ogni video scaricato
    for dw in dws:
        shortcode = dw.get("shortcode", "SHORTCODE_NON_TROVATO")
        try:
            ricetta_audio = ""
            captionSanit = sanitize_text(dw.get("caption", ""))

            # Path della cartella contenente i media
            video_folder_post = os.path.join(
                BASE_FOLDER_RICETTE, shortcode, "media_original"
            )

            # Cerca file video MP4 nella cartella
            video_files = [
                f for f in os.listdir(video_folder_post) if f.endswith(".mp4")
            ]
            
            if video_files:
                # Usa il primo video trovato
                video_path = os.path.join(video_folder_post, video_files[0])
                
                # Path per file audio estratto
                audio_filename = f"{os.path.splitext(shortcode)[0]}.mp3"
                audio_path = os.path.join(video_folder_post, audio_filename)

                # Estrae audio dal video usando FFmpeg
                try:
                    process = await asyncio.to_thread(
                        subprocess.run,
                        [
                            "ffmpeg", "-i", video_path,
                            "-q:a", "0",  # Qualità audio massima
                            "-map", "a",   # Estrai solo audio
                            audio_path
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    _emit_progress("extract_audio", 50.0)
                except subprocess.CalledProcessError as e:
                    extra_info = {
                        "shortcode": shortcode,
                        "return_code": e.returncode,
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                        "command": str(e.cmd)
                    }
                    error_logger.log_exception("ffmpeg_audio_extraction", e, extra_info)
                    _emit_progress("error", 25.0, message=str(e))
                    raise RuntimeError(f"Errore durante l'estrazione dell'audio per shortcode '{shortcode}': {e.stderr}") from e

                # Trascrizione audio con Whisper
                ricetta_audio = await whisper_speech_recognition(audio_path, "it")
                _emit_progress("stt", 85.0)
                
                # Log lunghezza testi per debug
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Audio length: {len(ricetta_audio) if ricetta_audio else 0}, "
                    f"Caption length: {len(captionSanit) if captionSanit else 0}"
                )

            # Estrae informazioni ricetta usando GPT-4
            ricetta = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
            _emit_progress("parse_recipe", 100.0)
            
            if ricetta:
                # Converti in dict se necessario
                ricetta_dict = (
                    ricetta if isinstance(ricetta, dict)
                    else (ricetta.model_dump() if ricetta else {})
                )
                
                # Genera immagini se abilitato
                if not NO_IMAGE:
                    images_recipe = await generateRecipeImages(ricetta_dict, shortcode)
                else:
                    images_recipe = []
                
                # Aggiungi immagini generate (o lista vuota)
                ricetta_dict["images"] = images_recipe or []
                
                # Assicura che tutti i campi lista siano inizializzati
                ricetta_dict["ingredients"] = ricetta_dict.get("ingredients", [])
                ricetta_dict["recipe_step"] = ricetta_dict.get("recipe_step", [])
                ricetta_dict["category"] = ricetta_dict.get("category", [])
                ricetta_dict["tags"] = ricetta_dict.get("tags", [])
                ricetta_dict["nutritional_info"] = ricetta_dict.get("nutritional_info", [])
                
                # Aggiungi campi richiesti
                ricetta_dict["ricetta_audio"] = ricetta_audio
                ricetta_dict["ricetta_caption"] = captionSanit
                ricetta_dict["shortcode"] = shortcode
                
                # Imposta URL immagine principale se presente
                if images_recipe and not ricetta_dict.get("image_url"):
                    ricetta_dict["image_url"] = images_recipe[0]

                # Processing completato con successo
                logging.getLogger(__name__).info(
                    f"Processing completato per '{shortcode}'. "
                    f"Titolo: '{ricetta_dict.get('title', 'N/A')}'",
                    extra={
                        "shortcode": shortcode,
                        "title": ricetta_dict.get('title', 'N/A')
                    }
                )
                return RecipeDBSchema(**ricetta_dict)
            else:
                # Nessuna ricetta estratta
                error_logger.log_error(
                    "recipe_extraction",
                    f"Nessuna ricetta estratta per '{shortcode}'",
                    {"shortcode": shortcode}
                )
                raise ValueError(
                    f"Nessuna ricetta estratta per shortcode '{shortcode}'"
                )
        except Exception as e:
            # Log errore e rilancia
            error_logger.log_exception("process_video", e, {"shortcode": shortcode})
            
            # Estrai errore originale se wrapped in RetryError
            original_error = e
            if hasattr(e, 'last_attempt') and hasattr(e.last_attempt, 'exception'):
                original_error = e.last_attempt.exception()
            
            _emit_progress("error", 50.0, message=str(original_error))
            raise original_error
            

    # Gestione caso dati vuoti
    if not dws:
        error_logger.log_error(
            "process_video_no_data",
            "Nessun dato video fornito",
            {"recipe_input": recipeUrl}
        )
        raise ValueError("Nessun dato video fornito")
    else:
        # Caso anomalo: loop completato senza return/raise
        error_logger.log_error(
            "process_video_logic_error",
            "Loop completato senza risultato",
            {"dws_count": len(dws), "recipe_input": recipeUrl}
        )
        raise RuntimeError("Errore logico nel processing")

async def process_video(
    recipeUrl: str,
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None
) -> RecipeDBSchema:
    """
    Processa un video ricetta e ne estrae i dati.
    
    Wrapper pubblico che gestisce retry e errori.
    
    Args:
        recipeUrl: URL del video o username Instagram
        progress_cb: Callback opzionale per aggiornamenti progresso
        
    Returns:
        RecipeDBSchema con i dati estratti dalla ricetta
        
    Raises:
        Exception: Errore durante il processing
    """
    try:
        return await _process_video_internal(recipeUrl, progress_cb)
    except Exception as e:
        # Estrai errore originale da RetryError se presente
        if hasattr(e, 'last_attempt') and hasattr(e.last_attempt, 'exception'):
            original_error = e.last_attempt.exception()
            raise original_error
        else:
            raise e
