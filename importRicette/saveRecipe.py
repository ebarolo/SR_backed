import os
import logging
import shutil
import re
import subprocess
import asyncio
import yt_dlp
from typing import Dict, Any
from datetime import datetime
from functools import wraps
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import multiprocessing as mp

from importRicette.utility import sanitize_text, sanitize_filename, sanitize_folder_name
from importRicette.analizeRecipe import Recipe, extract_recipe_info
from importRicette.instaLoader import scarica_contenuto_reel, scarica_contenuti_account
from RAG.dbQdrant import vectorEngine

mp.set_start_method('spawn', force=True)
os.environ["OPENAI_API_KEY"] = "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"

BASE_FOLDER = os.path.join(os.getcwd(), "static/ricette")
OPENAI_API_KEY ='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'
enableRag = True
collectionName = 'smart_Recipe'

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

def is_number(value):
    """Verifica se il valore è un numero."""
    try:
        float(str(value))
        return True
    except (ValueError, TypeError):
        return False
    
def create_date_folder() -> str:
    """Crea una cartella con la data odierna se non esiste già."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(BASE_FOLDER, today)
    os.makedirs(date_folder, exist_ok=True)
    return date_folder

def rename_file(video_folder,file_name:str):
     # Rinominare tutti i file nella cartella video_folder_new mantenendo l'estensione originale
    for filename in os.listdir(video_folder):
        old_file_path = os.path.join(video_folder, filename)
        name, ext = os.path.splitext(filename)  # Separare nome ed estensione
        new_file_path = os.path.join(video_folder, f"{file_name}{ext}")
        os.rename(old_file_path, new_file_path)
    return ""

def timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Timeout dopo {seconds} secondi nella funzione {func.__name__}")
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
        logger.error(f"Errore: Il file audio '{audio_file_path}' non è stato trovato.")
        raise
    except Exception as e:
        logger.error(f"Errore durante il riconoscimento vocale: {str(e)}")
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
        logger.error(f"Errore nel download del video {url}: {e}")
        raise
    except KeyError as ke:
        if 'config' in str(ke):
            logger.error(f"Errore di configurazione durante l'estrazione: {ke}")
        raise
    except Exception as e:
        logger.error(f"Errore imprevisto durante il download del video {url}: {e}")
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
        rename_file(dw['percorso_video'], titleSanit)

        video_folder_pre = os.path.join(os.getcwd(), dw['percorso_video'])
        video_folder_post = os.path.join(BASE_FOLDER, titleSanit)
                
        if os.path.exists(video_folder_pre):
           shutil.copytree(video_folder_pre, video_folder_post, dirs_exist_ok=True) 
           shutil.rmtree(video_folder_pre)

        audio_filename = f"{os.path.splitext(os.path.basename(video_folder_post))[0]}.mp3"
        audio_path = os.path.join(video_folder_post, audio_filename)
                
        video = f"{os.path.splitext(os.path.basename(video_folder_post))[0]}.mp4"
        v_path = os.path.join(video_folder_post, video)

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
        ricetta:Recipe = await extract_recipe_info(ricetta_audio, captionSanit, [], [])
        logger.info(f"recipe_info : {ricetta.title}")
        
        folderName_new = sanitize_folder_name(ricetta.title)

        text_filename = f"{ricetta.title}_originale.txt"
        text_path = os.path.join(video_folder_post, text_filename)

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(ricetta_audio)
            f.write("\n\n")
            f.write(captionSanit)

        ricetta.ricetta_audio = ricetta_audio
        ricetta.ricetta_caption = captionSanit
        ricetta.video = os.path.join(BASE_FOLDER, folderName_new, f"{recipe.title}.mp4")
        
        
        recipe_filename = f"{ricetta.title}_elaborata.tx"
        recipe_info_path = os.path.join(video_folder_post, recipe_filename)

        with open(recipe_info_path, 'w', encoding='utf-8') as f:
            for key in ricetta.__dict__:
                value = getattr(ricetta, key)
                f.write(f'{key}: {value}')
                f.write('\n')
        
        '''
        recipe_filename = f"{ricetta.title}.json"
        recipe_info_path = os.path.join(video_folder_post, recipe_filename)
        json_txt = "{"
        with open(recipe_info_path, 'w', encoding='utf-8') as f:
          
          for key in ricetta.__dict__:
            value = getattr(ricetta, key)
            json_txt += f'"{key}": "{value}"'
            json_txt += f",\n"
          json_txt.rstrip(json_txt[-2])
          json_txt += "}"
          json_t = json_txt.replace('"[', '[')
          json_t = json_txt.replace(']"', ']')
          json_t = json_txt.replace('\'', '"')
          
          jsontxt = str(ricetta.model_dump())
          jsontxt =jsontxt.replace("'", "\"")
          f.write(jsontxt)   
        '''

        recipe_filename = f"{ricetta.title}_embedding.txt"
        recipe_info_path = os.path.join(video_folder_post, recipe_filename)

        with open(recipe_info_path, 'w', encoding='utf-8') as f:
         
         if hasattr(ricetta, 'ingredients'):
        
          ingredients_text = ' '.join([f' {str(ing.qt)} {ing.um} {ing.name},' if ing.qt > 0 else f' {ing.um} {ing.name},' for ing in ricetta.ingredients])
         else:
          ingredients_text = ''
         # Poi compongo il testo finale
         text_for_embedding = f"{ricetta.title}\n{' '.join(ricetta.prepration_step)}\n{ingredients_text}"
         
         f.write(text_for_embedding)   

        ricetta.error = ""
        recipesImported.append(ricetta.model_dump())
        logger.info(f"process_video completato per: {ricetta}")
      except Exception as e:
       logger.error(f"Errore durante process_video : {e}")
       ricetta.error = e
       raise e
      try:
       if(enableRag):

         logger.info(f"enableRag for {ricetta.model_dump()}")

         qdrant = vectorEngine(collectionName)
         ricetta.recipe_id = abs(hash(ricetta.title))
         logger.info("ricetta id "+str(ricetta.recipe_id))

         if hasattr(ricetta, 'ingredients'):
            ingredients_text = ' '.join([f'{str(ing.qt)} {ing.um} {ing.name}' if ing.qt > 0 else f'{ing.um} {ing.name}' for ing in ricetta.ingredients]) # Fixed: Access dictionary elements using keys
            # Removing trailing comma and adding space
            ingredients_text = ingredients_text.replace(',', '').strip() + ' '
         else:
            ingredients_text = ''
            # Poi compongo il testo finale
            text_for_embedding = f"{ricetta.title}\n{ingredients_text}\n{' '.join(ricetta.prepration_step)}"
         logger.info("text_for_embedding \n\n")
         logger.info(text_for_embedding)

         qdrant = vectorEngine(collectionName)

         resqd = qdrant.add_documents(text_for_embedding=text_for_embedding, meta=ricetta.model_dump())
         logger.info("resp qdrant "+str(resqd))       
         
         recipesImported.append(ricetta.model_dump())
         logger.info(f"added ricetta")

        # responseRabitHole = saveRecipeInRabitHole(recipeJSON, recipeTXT)
        # logger.info(f"ricetta memorizza nella memoria dichiarativa del Cheshire Cat {type(responseRabitHole.content)}")
        # importedJSON.append(recipeJSON) 
        
      except Exception as e:
        logger.error (f"Rag err {e}")
        ricetta.error = e
        recipesImported.append(ricetta.model_dump())

        raise
    
    return recipesImported
