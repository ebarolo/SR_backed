import os
import logging
import shutil
import re
import subprocess
import asyncio
import multiprocessing as mp
import traceback
from typing import Dict, Any
from functools import wraps
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import yt_dlp
import json

from utility import sanitize_text, sanitize_filename, sanitize_folder_name, rename_files, rename_folder
from importRicette.analizeRecipe import extract_recipe_info
from importRicette.instaloader import scarica_contenuto_reel, scarica_contenuti_account
from models import RecipeDBSchema


mp.set_start_method('spawn', force=True)
os.environ["OPENAI_API_KEY"] = "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"

BASE_FOLDER = os.path.join(os.getcwd(), "static/ricette")
OPENAI_API_KEY ='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'

enableRag = False

if not OPENAI_API_KEY:
 raise ValueError("La chiave API di OpenAI non è stata impostata. Imposta la variabile d'ambiente OPENAI_API_KEY.")

clientOpenAI = OpenAI(api_key=OPENAI_API_KEY)

# Configurazione del logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
  filename='backend.log'
)

logger = logging.getLogger(__name__)

def get_error_context():
    """Get the current file, line number and function name where the error occurred"""
    stack = traceback.extract_stack()
    if len(stack) > 1:
        frame = stack[-2]
        return f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}"
    return ""

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                error_context = get_error_context()
                logger.error(f"Timeout dopo {seconds} secondi nella funzione {func.__name__} - {error_context}")
                raise
        return wrapper
    return decorator

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(300)  # 5 minuti di timeout
async def whisper_speech_recognition(audio_file_path: str, language: str) -> str:
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Usiamo asyncio.to_thread per eseguire la chiamata bloccante in un thread separato
            transcription = await asyncio.to_thread(
                clientOpenAI.audio.transcriptions.create,
                model="whisper-1", 
                file=audio_file
            )
        return transcription.text
    except FileNotFoundError:
        error_context = get_error_context()
        logger.error(f"Errore: Il file audio '{audio_file_path}' non è stato trovato. - {error_context}")
        raise
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore durante il riconoscimento vocale: {str(e)} - {error_context}")
        raise
   
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@timeout(600) 
async def download_video(url: str) -> Dict[str, Any]:
    opzioni = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(BASE_FOLDER, '%(title)s.%(ext)s')
    }

    try:
        with yt_dlp.YoutubeDL(opzioni) as ydl:
            logger.info(f"Inizio download del video: {url}")
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            logger.info(f"Download completato con successo: {url}")
            video_title = sanitize_filename(info['title'])
            video_filename = ydl.prepare_filename(info)
        return {"video_title": video_title, "video_filename": video_filename}
    except yt_dlp.utils.DownloadError as e:
        error_context = get_error_context()
        logger.error(f"Errore nel download del video {url}: {e} - {error_context}")
        raise
    except KeyError as ke:
        error_context = get_error_context()
        if 'config' in str(ke):
            logger.error(f"Errore di configurazione durante l'estrazione: {ke} - {error_context}")
        raise
    except Exception as e:
        error_context = get_error_context()
        logger.error(f"Errore imprevisto durante il download del video {url}: {e} - {error_context}")
        raise

async def process_video(recipe: str):
    recipesImported = []
    urlPattern = r'^(ftp|http|https):\/\/[^ "]+$'

    if not re.match(urlPattern, recipe):
      dws = await scarica_contenuti_account(recipe)
    else:
      dws = await scarica_contenuto_reel(recipe)

    for dw in dws:
     if len(dw['error']) == 0:
      try:
        logger.info(f"video scaricato: {str(dw)}")
        captionSanit = sanitize_text(dw['caption'])
        titleSanit = sanitize_text(dw['titolo'])
        rename_files(dw['percorso_video'], titleSanit)

        video_folder_pre = os.path.join(os.getcwd(), dw['percorso_video'])
        video_folder_post = os.path.join(BASE_FOLDER, titleSanit)
                
        if os.path.exists(video_folder_pre):
           shutil.copytree(video_folder_pre, video_folder_post, dirs_exist_ok=True) 
           shutil.rmtree(video_folder_pre)

        # Cerca il file video nella cartella
        video_files = [f for f in os.listdir(video_folder_post) if f.endswith('.mp4')]
        if not video_files:
            raise FileNotFoundError(f"Nessun file video trovato in {video_folder_post}")
            
        video = video_files[0]  # Prendi il primo file video trovato
        v_path = os.path.join(video_folder_post, video)
        
        audio_filename = f"{os.path.splitext(video)[0]}.mp3"
        audio_path = os.path.join(video_folder_post, audio_filename)

        logger.info(f"estrazione audio da video: {v_path}")
        await asyncio.to_thread(subprocess.run, [
          'ffmpeg', '-i', v_path, 
          '-q:a', '0', '-map', 'a', audio_path
        ], check=True)
                
        logger.info(f"start speech_to_text: {audio_path}")
        ricetta_audio = await whisper_speech_recognition(audio_path, "it")
        logger.info(f"end speech_to_text")
                
        # Estrai informazioni dalla ricetta
        logger.info(f"start extract_recipe_info: {ricetta_audio}")
        ricetta = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
        logger.info(f"recipe_info : {ricetta}")
        
        recipeNameSanit = sanitize_folder_name(ricetta.title)
        recipe_folder = os.path.join(BASE_FOLDER, recipeNameSanit)
        re_folder = rename_folder(video_folder_post, recipe_folder)

        '''
        text_filename = f"{recipeNameSanit}_originale.txt"
        text_path = os.path.join(re_folder, text_filename)

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(ricetta_audio)
            f.write("\n\n")
            f.write(captionSanit)
        '''
        # Convert the RecipeAIResponse object to a RecipeDBSchema object
        ricetta_dict = ricetta.model_dump()
        
        # Keep ingredients and recipe_step as lists
        ricetta_dict['ingredients'] = ricetta_dict['ingredients']
        ricetta_dict['recipe_step'] = ricetta_dict['recipe_step']
        
        # Keep category, tags, and nutritional_info as lists
        ricetta_dict['category'] = ricetta_dict['category']
        ricetta_dict['tags'] = ricetta_dict.get('tags', [])
        ricetta_dict['nutritional_info'] = ricetta_dict.get('nutritional_info', [])
        
        # Add required fields
        ricetta_dict['ricetta_audio'] = ricetta_audio
        ricetta_dict['ricetta_caption'] = captionSanit
        ricetta_dict['video_path'] = os.path.join(re_folder, f"{ricetta.title}.mp4")
        
        logger.info(f"process_video completato per: {ricetta}")
        return RecipeDBSchema(**ricetta_dict)
      except Exception as e:
       logger.error(f"Errore durante process_video : {e}")
       raise e

    
