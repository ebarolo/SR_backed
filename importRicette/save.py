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
from utility.cloud_logging_config import get_error_logger, request_id_var, clear_error_chain
from utility.openai_errors import OpenAIError, QuotaExceededError

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
from utility.error_handler import ErrorHandler, ErrorSeverity, ErrorAction


# Inizializza logger e multiprocessing
error_logger = get_error_logger(__name__)
error_handler = ErrorHandler(__name__)
mp.set_start_method("spawn", force=True)

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _process_video_internal(
    recipeUrl: str,
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    force_redownload: bool = False
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
        force_redownload: Se True, forza il ri-download anche se già presente
        
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
                        import shutil
                        shutil.move(src, dst)
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
        raise  # Preserva stack trace originale

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

                # Verifica prima se il video ha una traccia audio usando ffprobe
                def _check_audio_stream():
                    """Verifica se il video ha una traccia audio."""
                    try:
                        result = subprocess.run(
                            [
                                "ffprobe", "-v", "error",
                                "-select_streams", "a:0",
                                "-show_entries", "stream=codec_type",
                                "-of", "default=noprint_wrappers=1:nokey=1",
                                video_path
                            ],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        return result.stdout.strip() == "audio"
                    except Exception:
                        # In caso di errore, assume che ci sia audio e prova comunque
                        return True

                has_audio = await asyncio.to_thread(_check_audio_stream)
                
                if has_audio:
                    # Estrae audio dal video usando FFmpeg
                    def _run_ffmpeg():
                        return subprocess.run(
                            [
                                "ffmpeg", "-y",  # Sovrascrivi file esistenti
                                "-i", video_path,
                                "-vn",  # Disabilita video
                                "-acodec", "libmp3lame",  # Codec MP3
                                "-q:a", "0",  # Qualità audio massima
                                "-ar", "44100",  # Frequenza campionamento
                                "-loglevel", "error",  # Solo errori
                                audio_path
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                    
                    try:
                        process = await error_handler.safe_execute_async(
                            lambda: asyncio.to_thread(_run_ffmpeg),
                            "ffmpeg_audio_extraction",
                            severity=ErrorSeverity.HIGH,
                            action=ErrorAction.RAISE,
                            context={
                                "shortcode": shortcode,
                                "video_path": video_path,
                                "audio_path": audio_path
                            }
                        )
                        _emit_progress("extract_audio", 50.0)
                        
                        # Verifica che il file audio sia stato effettivamente creato
                        if not os.path.exists(audio_path):
                            logging.getLogger(__name__).warning(
                                f"FFmpeg non ha creato il file audio per '{shortcode}', continuo senza audio"
                            )
                            ricetta_audio = ""
                        elif os.path.getsize(audio_path) == 0:
                            logging.getLogger(__name__).warning(
                                f"File audio vuoto per '{shortcode}', continuo senza audio"
                            )
                            ricetta_audio = ""
                        else:
                            # Trascrizione audio con Whisper
                            try:
                                ricetta_audio = await whisper_speech_recognition(audio_path, "it")
                                _emit_progress("stt", 85.0)
                            except OpenAIError as openai_err:
                                # Gestione specifica errori OpenAI con messaggio user-friendly
                                error_logger.log_error(
                                    "whisper_openai_error",
                                    f"OpenAI error in Whisper: {openai_err.user_message}",
                                    {
                                        "shortcode": shortcode,
                                        "error_type": openai_err.error_type.value,
                                        "should_retry": openai_err.should_retry,
                                        "context": openai_err.context
                                    }
                                )
                                _emit_progress("error", 50.0, message=openai_err.user_message)
                                raise
                            
                    except subprocess.CalledProcessError as e:
                        # FFmpeg fallito: continua senza audio invece di bloccare
                        error_logger.log_error(
                            "ffmpeg_extraction_failed",
                            f"FFmpeg fallito per '{shortcode}', continuo senza audio: {e.stderr if hasattr(e, 'stderr') else str(e)}",
                            {
                                "shortcode": shortcode,
                                "video_path": video_path,
                                "audio_path": audio_path
                            }
                        )
                        ricetta_audio = ""
                        _emit_progress("extract_audio", 50.0, message="Video senza audio, continuo con caption")
                    except Exception as e:
                        # Altri errori: logga ma continua
                        error_logger.log_exception(
                            "ffmpeg_extraction_error",
                            e,
                            {
                                "shortcode": shortcode,
                                "video_path": video_path,
                                "audio_path": audio_path
                            }
                        )
                        ricetta_audio = ""
                        _emit_progress("extract_audio", 50.0, message="Errore estrazione audio, continuo con caption")
                else:
                    # Video senza traccia audio
                    logging.getLogger(__name__).info(
                        f"Video '{shortcode}' non ha traccia audio, uso solo caption"
                    )
                    ricetta_audio = ""
                    _emit_progress("extract_audio", 50.0, message="Video senza audio")
                
                # Log lunghezza testi per debug
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Audio length: {len(ricetta_audio) if ricetta_audio else 0}, "
                    f"Caption length: {len(captionSanit) if captionSanit else 0}"
                )

            # Estrae informazioni ricetta usando GPT-4
            try:
                ricetta = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
                _emit_progress("parse_recipe", 100.0)
            except OpenAIError as openai_err:
                # Gestione specifica errori OpenAI con messaggio user-friendly
                error_logger.log_error(
                    "extract_recipe_openai_error",
                    f"OpenAI error in recipe extraction: {openai_err.user_message}",
                    {
                        "shortcode": shortcode,
                        "error_type": openai_err.error_type.value,
                        "should_retry": openai_err.should_retry,
                        "context": openai_err.context
                    }
                )
                _emit_progress("error", 85.0, message=openai_err.user_message)
                raise
            
            if ricetta:
                # Converti in dict se necessario
                ricetta_dict = (
                    ricetta if isinstance(ricetta, dict)
                    else (ricetta.model_dump() if ricetta else {})
                )
                
                # Genera immagini se abilitato
                if not NO_IMAGE:
                    try:
                        images_recipe = await generateRecipeImages(ricetta_dict, shortcode)
                    except OpenAIError as openai_err:
                        # Per immagini, logga ma continua (non bloccante)
                        error_logger.log_error(
                            "generate_images_openai_error",
                            f"OpenAI error in image generation: {openai_err.user_message}",
                            {
                                "shortcode": shortcode,
                                "error_type": openai_err.error_type.value,
                                "severity": "medium"  # Non critico
                            }
                        )
                        # Continua senza immagini generate
                        images_recipe = []
                        logging.getLogger(__name__).warning(
                            f"Generazione immagini fallita per '{shortcode}', continuo senza immagini: {openai_err.user_message}"
                        )
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
        except OpenAIError as openai_err:
            # Errore OpenAI già classificato e gestito
            # Propaga con messaggio user-friendly già impostato nel progress
            raise
        except Exception as e:
            # Log errore generico e rilancia
            error_logger.log_exception("process_video", e, {"shortcode": shortcode})
            
            # Estrai errore originale se wrapped in RetryError
            original_error = e
            if hasattr(e, 'last_attempt') and hasattr(e.last_attempt, 'exception'):
                original_error = e.last_attempt.exception()
            
            # Messaggio generico per utente
            error_message = str(original_error) if original_error else "Errore durante il processing"
            _emit_progress("error", 50.0, message=error_message)
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
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    force_redownload: bool = False
) -> RecipeDBSchema:
    """
    Processa un video ricetta e ne estrae i dati.
    
    Wrapper pubblico che gestisce retry e errori.
    
    Args:
        recipeUrl: URL del video o username Instagram
        progress_cb: Callback opzionale per aggiornamenti progresso
        force_redownload: Se True, forza il ri-download anche se già presente
        
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
            raise  # Preserva stack trace originale
