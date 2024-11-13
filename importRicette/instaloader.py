import os
import instaloader
import logging
from typing import Dict, Any
import re

BASE_FOLDER = os.path.join(os.getcwd(), "static/preprocess_video")

# Configurazione del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

def sanitize_folder_name(folder_name: str) -> str:
    # Sostituisce i caratteri non validi con un carattere di sottolineatura
    return re.sub(r'[<>:"/\\|?*]', '_', folder_name)

def create_safe_folder_name(title):
    # Prendi solo la prima parte del titolo fino al primo carattere di nuova riga
    short_title = title.split('\r')[0]
    
    # Rimuovi caratteri speciali e emoji
    safe_title = re.sub(r'[^\w\s-]', '', short_title)
    
    # Limita la lunghezza e rimuovi spazi iniziali/finali
    safe_title = safe_title.strip()[:50]
    
    # Sostituisci spazi con underscore
    safe_title = safe_title.replace(' ', '_')
    
    return safe_title

async def scarica_contenuti_instagram(url: str) -> Dict[str, Any]:
    try:
        # Inizializza instaloader
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            compress_json=False
        )
        
        # Login (opzionale ma consigliato per evitare limitazioni)
        #L.login("e.barolo", "meqxid-mesdeg-hUpti5")
        
        # Estrai l'ID del post dall'URL
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Crea il nome della cartella
        account_name = create_safe_folder_name(post.owner_username)
        folder_path = os.path.join("", f"{account_name}")

        os.makedirs(folder_path, exist_ok=True)
        L.download_post(post,folder_path)
            
        # Prepara il dizionario di risposta
        result = {
            "titolo": create_safe_folder_name(post.caption.split('\n')[0] if post.caption else str(post.mediaid)),
            "percorso_video": folder_path,
            "caption": post.caption if post.caption else ""
        }
        
        logger.info(f"Download completato per {url}")
        logger.info(f"Download completato per {str(result)}")
        return result
        
    except Exception as e:
        logger.error(f"Errore durante il download da Instagram: {str(e)}")
        raise
