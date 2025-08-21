import os
import re
import subprocess
import asyncio
import multiprocessing as mp
import yt_dlp

from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from models import RecipeDBSchema

from utility import sanitize_text, sanitize_filename, get_error_context, logger 
from importRicette.analizeRecipe import extract_recipe_info, whisper_speech_recognition, generateRecipeImages
from importRicette.instaloader import scarica_contenuto_reel, scarica_contenuti_account

from config import BASE_FOLDER_RICETTE

mp.set_start_method("spawn", force=True)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def yt_dlp_video(url: str) -> Dict[str, Any]:
    opzioni = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(BASE_FOLDER_RICETTE, "%(title)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(opzioni) as ydl:
            logger.info(f"Inizio download del video: {url}")
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            logger.info(f"Download completato con successo: {url}")
            video_title = sanitize_filename(info["title"])
            video_filename = ydl.prepare_filename(info)
        return {"video_title": video_title, "video_filename": video_filename}
    except yt_dlp.utils.DownloadError as e:
        error_context = get_error_context()
        logger.error(f"Errore nel download del video {url}: {e} - {error_context}", exc_info=True)
        raise
    except KeyError as ke:
        error_context = get_error_context()
        if "config" in str(ke):
            logger.error(
                f"Errore di configurazione durante l'estrazione: {ke} - {error_context}"
            )
        raise
    except Exception as e:
        error_context = get_error_context()
        logger.error(
            f"Errore imprevisto durante il download del video {url}: {e} - {error_context}", exc_info=True
        )
        raise

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
async def process_video(recipe: str):

    urlPattern = r'^(ftp|http|https):\/\/[^ "]+$'

    if not re.match(urlPattern, recipe):
        dws = await scarica_contenuti_account(recipe)
    else:
        dws = await scarica_contenuto_reel(recipe)

    for dw in dws:
        shortcode = dw.get("shortcode", "SHORTCODE_NON_TROVATO") # Default per logging
        try:
            logger.info(f"Inizio elaborazione per shortcode: {shortcode}, URL video: {dw.get('url_video', 'URL_NON_TROVATO')}")
            captionSanit = sanitize_text(dw["caption"])

            video_folder_post = os.path.join(BASE_FOLDER_RICETTE, shortcode)
            logger.info(f"Cartella video per shortcode '{shortcode}': {video_folder_post}")

            # Cerca il file video nella cartella
            video_files = [
                f for f in os.listdir(video_folder_post) if f.endswith(".mp4")
            ]
            if not video_files:
                raise FileNotFoundError(
                    f"Nessun file video .mp4 trovato in {video_folder_post} per shortcode '{shortcode}'. File presenti: {os.listdir(video_folder_post) if os.path.exists(video_folder_post) else 'cartella non esistente'}"
                )

            video_path = os.path.join(
                video_folder_post, video_files[0]
            )  # Percorso completo al file video

            audio_filename = f"{os.path.splitext(shortcode)[0]}.mp3"
            audio_path = os.path.join(video_folder_post, audio_filename)

            logger.info(f"estrazione audio da video: {video_path}")
            try:
                process = await asyncio.to_thread(
                    subprocess.run,
                    ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info(f"Audio extraction successful: {audio_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg command failed with exit code {e.returncode}")
                logger.error(f"ffmpeg stdout: {e.stdout}")
                logger.error(f"ffmpeg stderr: {e.stderr}")
                logger.error(f"Command was: {e.cmd}")
                raise RuntimeError(f"Errore durante l'estrazione dell'audio per shortcode '{shortcode}': {e.stderr}") from e

            logger.info(f"Inizio speech_to_text per shortcode '{shortcode}', audio: {audio_path}")
            ricetta_audio = await whisper_speech_recognition(audio_path, "it")
            logger.info(f"Fine speech_to_text per shortcode '{shortcode}'. Lunghezza testo: {len(ricetta_audio) if ricetta_audio else 0}")

            # Estrai informazioni dalla ricetta
            logger.info(f"Inizio estrazione informazioni ricetta dal testo trascritto per shortcode '{shortcode}'. Lunghezza testo: {len(ricetta_audio) if ricetta_audio else 0}")
            ricetta = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
            if ricetta:
                titolo_estratto = ricetta.get('title', 'N/A') if isinstance(ricetta, dict) else getattr(ricetta, 'title', 'N/A')
                logger.info(f"Informazioni ricetta estratte con successo per shortcode '{shortcode}': titolo='{titolo_estratto}'")
            else:
                logger.warning(f"Nessuna informazione ricetta estratta per shortcode '{shortcode}' dal testo analizzato.")
                pass
            
            images_recipe = await generateRecipeImages(ricetta, video_folder_post)
            
            # Convert the RecipeAIResponse object to a RecipeDBSchema object
            ricetta_dict = ricetta if isinstance(ricetta, dict) else (ricetta.model_dump() if ricetta else {})

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

            logger.info(f"process_video completato per shortcode '{shortcode}'. Titolo: '{ricetta_dict.get('title', 'N/A')}'")
            return RecipeDBSchema(**ricetta_dict)
        except Exception as e:
            logger.error(f"Errore durante process_video per shortcode '{shortcode}': {e}", exc_info=True)
            raise # Rilancia l'eccezione per interrompere l'elaborazione
    

    if not dws:
        logger.warning("Nessun dato video fornito a process_video.")
        return None # O sollevare un errore se un risultato è sempre atteso
    else:
        # Questo caso (dws non vuoto, ma nessun return/raise nel loop) dovrebbe essere raro
        # se ogni iterazione del loop gestisce tutti i percorsi (successo con return, fallimento con raise).
        logger.error("process_video ha completato il loop senza restituire o sollevare un errore per nessun elemento.")
        return None # O sollevare un errore indicando un problema logico
