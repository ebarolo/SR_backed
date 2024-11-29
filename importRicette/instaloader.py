import os
import instaloader
import logging
import re

from typing import Dict, Any

BASE_FOLDER = os.path.join(os.getcwd(), "static/preprocess_video")

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='backend.log'
)
logger = logging.getLogger(__name__)


ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

logger.info(f"ISTA_USERNAME {ISTA_USERNAME} ISTA_PASSWORD {ISTA_PASSWORD} ")

if not ISTA_USERNAME:
    logger.error(f"ISTA_USERNAME non è stata impostata {ISTA_USERNAME} ISTA_PASSWORD {ISTA_PASSWORD} ")

    raise ValueError("ISTA_USERNAME non è stata impostata. Imposta la variabile d'ambiente ISTA_USERNAME")

def sanitize_folder_name(folder_name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', folder_name)

def create_safe_folder_name(title):
    short_title = title.split('\r')[0]
    safe_title = re.sub(r'[^\w\s-]', '', short_title)
    safe_title = safe_title.strip()[:50]
    safe_title = safe_title.replace(' ', '_')
    return safe_title

async def scarica_contenuto_reel(url: str) -> Dict[str, Any]:
    result = []
    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=True,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            compress_json=False
        )
        
        # Login (opzionale ma consigliato per evitare limitazioni)
        # L.login(ISTA_USERNAME, ISTA_PASSWORD)
        
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        account_name = create_safe_folder_name(post.owner_username)
        folder_path = os.path.join("", f"{account_name}")

        os.makedirs(folder_path, exist_ok=True)
        L.download_post(post, folder_path)
            
        res = {
            "error": "",
            "titolo": create_safe_folder_name(post.caption.split('\n')[0] if post.caption else str(post.mediaid)),
            "percorso_video": folder_path,
            "caption": post.caption if post.caption else ""
        }
        
        logger.info(f"Download completato per {url}")
        logger.info(f" {str(res)}")
        result.append(res)
        return  result
    except instaloader.exceptions.InstaloaderException as e:
        logger.error(f"Errore specifico di scarica_contenuto_reel: {str(e)}")
        result.append({
            "error": str(e),
            "titolo": "",
            "percorso_video": "",
            "caption": ""
        })
        raise result

async def scarica_contenuti_account(username: str):
  result = []
     # Scarica i post dell'account
  try:
    L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=True,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            compress_json=False
     )

    # Login (opzionale, ma consigliato per evitare limitazioni)
    L.login(ISTA_USERNAME, ISTA_PASSWORD)
    
    profile = instaloader.Profile.from_username(L.context, username)
       
    account_name = create_safe_folder_name(profile.username)
    folder_path = os.path.join("", f"{account_name}")
    os.makedirs(folder_path, exist_ok=True)
        
    for post in profile.get_posts():
        if post.is_video:
         L.download_post(post, target=folder_path)

         res = {
          "error": "",
          "titolo": create_safe_folder_name(post.caption.split('\n')[0] if post.caption else str(post.mediaid)),
          "percorso_video": folder_path,
          "caption": post.caption if post.caption else ""
         }
                
         result.append(res)
    return result
  
  except instaloader.exceptions.InstaloaderException as e:
   logger.error(f"Errore specifico di scarica_contenuti_account: {str(e)}")
  raise result.append({
            "error": str(e),
            "titolo": "",
            "percorso_video": "",
            "caption": ""
        })

