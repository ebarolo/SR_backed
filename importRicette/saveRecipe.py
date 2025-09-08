import os
import re
import subprocess
import asyncio
import multiprocessing as mp

import uuid
import logging

from typing import Dict, Any, Optional, Callable
from tenacity import retry, stop_after_attempt, wait_exponential

from models import RecipeDBSchema
from config import BASE_FOLDER_RICETTE, NO_IMAGE

from utility import sanitize_text, sanitize_filename, get_error_context
from logging_config import get_error_logger, request_id_var, clear_error_chain 
from importRicette.analizeRecipe import extract_recipe_info, whisper_speech_recognition, generateRecipeImages
from importRicette.scrape.instaLoader import scarica_contenuto_reel, scarica_contenuti_account
from importRicette.scrape.yt_dlp import yt_dlp_video


# Initialize error logger
error_logger = get_error_logger(__name__)

mp.set_start_method("spawn", force=True)

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
async def process_video(recipeUrl: str, progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None):
    """
    Accetta un input che può essere:
    - username Instagram (no scheme http/https) → scarica tutti i reel video dell'account
    - URL: se Instagram → usa instaloader; per altri domini prova yt-dlp per scaricare e creare struttura coerente
    """
    # Clear error chain at start of new operation
    clear_error_chain()
    
    # Set context variables for tracking
    operation_id = str(uuid.uuid4())[:8]
    request_id_var.set(f"process_video_{operation_id}")

    urlPattern = r'^(ftp|http|https):\/\/[^ \"]+$'

    def _emit_progress(stage: str, local_percent: float, message: Optional[str] = None):
        if progress_cb is None:
            return
        try:
            payload: Dict[str, Any] = {"stage": stage, "local_percent": float(local_percent)}
            if message is not None:
                payload["message"] = message
            progress_cb(payload)
        except Exception:
            # Non interrompere il flusso in caso di errore nella callback
            pass

    if not re.match(urlPattern, recipeUrl):
        dws = await scarica_contenuti_account(recipeUrl)
        _emit_progress("download", 25.0)
    else:
        url_lower = recipeUrl.lower()
        if any(host in url_lower for host in ["instagram.com"]):
            dws = await scarica_contenuto_reel(recipeUrl)
            _emit_progress("download", 25.0)
        else:
            # usa yt-dlp per scaricare il singolo video in una cartella stile shortcode generico
            info = await yt_dlp_video(recipeUrl)
            # crea struttura compatibile
            shortcode = sanitize_filename(info["video_title"]) or "video"
            downloadFolder = os.path.join(BASE_FOLDER_RICETTE, shortcode, "media_original")
            os.makedirs(downloadFolder, exist_ok=True)
            # sposta/normalizza il file nella cartella target
            src = info["video_filename"]
            dst = os.path.join(downloadFolder, os.path.basename(info["video_filename"]))
            try:
                if os.path.abspath(src) != os.path.abspath(dst):
                    os.replace(src, dst)
            except Exception as e:
                error_logger.log_error("file_move", f"Failed to move downloaded file: {e}", {"src": src, "dst": dst})
            dws = [{
                "error": "",
                "shortcode": shortcode,
                "caption": "",
                "url_video": recipeUrl,
            }]
            _emit_progress("download", 25.0)

    for dw in dws:
        #print(f"dw: {dw}")
        shortcode = dw.get("shortcode", "SHORTCODE_NON_TROVATO") # Default per logging
        try:
            #logger.info(f"Inizio elaborazione per shortcode: {shortcode}")
            ricetta_audio = ""
            captionSanit = sanitize_text(dw.get("caption", "caption NON_TROVATO")) # Default per logging

            video_folder_post = os.path.join(BASE_FOLDER_RICETTE, shortcode, "media_original")
            #logger.info(f"Cartella video per shortcode '{shortcode}': {video_folder_post}")

            # Cerca il file video nella cartella
            video_files = [
                f for f in os.listdir(video_folder_post) if f.endswith(".mp4")
            ]
            
            if video_files:
    
             video_path = os.path.join(
                video_folder_post, video_files[0]
             )  # Percorso completo al file video

             audio_filename = f"{os.path.splitext(shortcode)[0]}.mp3"
             audio_path = os.path.join(video_folder_post, audio_filename)

             try:
                process = await asyncio.to_thread(
                    subprocess.run,
                    ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path],
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

             ricetta_audio = await whisper_speech_recognition(audio_path, "it")
             _emit_progress("stt", 85.0)
            
             # Log per verificare che il testo non sia troncato
             logger = logging.getLogger(__name__)
             logger.info(f"Ricetta audio length: {len(ricetta_audio) if ricetta_audio else 0}, Caption length: {len(captionSanit) if captionSanit else 0}")

            # Estrai informazioni dalla ricetta
            ricetta = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
            _emit_progress("parse_recipe", 100.0)
            if ricetta:              
                       
             # Normalizza la ricetta in un dict per uso successivo
             ricetta_dict = ricetta if isinstance(ricetta, dict) else (ricetta.model_dump() if ricetta else {})
             if not NO_IMAGE:
                images_recipe = await generateRecipeImages(ricetta_dict, shortcode)
             else:
                images_recipe = []
            
             if images_recipe:
                ricetta_dict["images"] = images_recipe
                if not ricetta_dict.get("image_url"):
                    ricetta_dict["image_url"] = images_recipe[0]            

             # Keep ingredients and recipe_step as lists
             ricetta_dict["ingredients"] = ricetta_dict.get("ingredients", [])
             ricetta_dict["recipe_step"] = ricetta_dict.get("recipe_step", [])

             # Keep category, tags, and nutritional_info as lists
             ricetta_dict["category"] = ricetta_dict.get("category", [])
             ricetta_dict["tags"] = ricetta_dict.get("tags", [])
             ricetta_dict["nutritional_info"] = ricetta_dict.get("nutritional_info", [])

             # Add required fields
             ricetta_dict["ricetta_audio"] = ricetta_audio
             ricetta_dict["ricetta_caption"] = captionSanit
             ricetta_dict["shortcode"] = shortcode
             
             # Persist generated images into metadata for frontend retrieval
             if images_recipe:
                ricetta_dict["images"] = images_recipe
                if not ricetta_dict.get("image_url"):
                    ricetta_dict["image_url"] = images_recipe[0]

             # Successfully completed processing - using standard logger for info level
             logging.getLogger(__name__).info(f"process_video completato per shortcode '{shortcode}'. Titolo: '{ricetta_dict.get('title', 'N/A')}'", extra={"shortcode": shortcode, "title": ricetta_dict.get('title', 'N/A')})
             return RecipeDBSchema(**ricetta_dict)
            else:
             error_logger.log_error("recipe_extraction", f"Nessuna informazione ricetta estratta per shortcode '{shortcode}' dal testo analizzato.", {"shortcode": shortcode})
             return None
        except Exception as e:
            error_logger.log_exception("process_video", e, {"shortcode": shortcode})
            _emit_progress("error", 50.0, message=str(e))
            raise # Rilancia l'eccezione per interrompere l'elaborazione
            

    if not dws:
        error_logger.log_error("process_video_no_data", "Nessun dato video fornito a process_video.", {"recipe_input": recipeUrl})
        return None # O sollevare un errore se un risultato è sempre atteso
    else:
        # Questo caso (dws non vuoto, ma nessun return/raise nel loop) dovrebbe essere raro
        # se ogni iterazione del loop gestisce tutti i percorsi (successo con return, fallimento con raise).
        error_logger.log_error("process_video_logic_error", "process_video ha completato il loop senza restituire o sollevare un errore per nessun elemento.", {"dws_count": len(dws), "recipe_input": recipeUrl})
        return None # O sollevare un errore indicando un problema logico
