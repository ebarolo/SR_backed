import os
import instaloader
import logging
from typing import Dict, Any

from utility import sanitize_folder_name

BASE_FOLDER = os.path.join(os.getcwd(), "static/preprocess_video")

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    filename='backend.log'
)

logger = logging.getLogger(__name__)

# Uncomment these lines and set environment variables for authentication
ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

#logger.info(f"Instagram credentials status: Username defined: {ISTA_USERNAME is not None}, Password defined: {ISTA_PASSWORD is not None}")

if not ISTA_USERNAME or not ISTA_PASSWORD:
    logger.warning("Instagram credentials not set. Some operations may fail due to rate limiting or access restrictions.")

def get_instaloader():
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=True,
        download_geotags=False,
        download_comments=False,
        save_metadata=True,
        compress_json=False,
        sanitize_paths=True
        )
    
    # Try to login if credentials are available
    if ISTA_USERNAME and ISTA_PASSWORD:
        try:
            logger.info(f"Attempting to login with username: {ISTA_USERNAME}")
            L.login(ISTA_USERNAME, ISTA_PASSWORD)
            logger.info("Login successful")
        except Exception as login_error:
            logger.error(f"Login failed: {str(login_error)}")
            logger.warning("Proceeding without authentication - some operations may be rate limited")
    else:
        logger.warning("No Instagram credentials available, proceeding without authentication")
    
    return L

async def scarica_contenuto_reel(url: str) -> Dict[str, Any]:
    result = []
    try:
        L = get_instaloader()
        
        # Extract shortcode from URL with improved handling for different URL formats
        # Handle URLs like:
        # - https://www.instagram.com/p/ABC123/
        # - https://www.instagram.com/reel/ABC123/
        # - https://www.instagram.com/tv/ABC123/
        # - https://instagram.com/p/ABC123/
        
        logger.info(f"Processing URL: {url}")
        
        # Clean URL by removing query parameters and trailing slashes
        clean_url = url.split('?')[0].rstrip('/')
        
        # Extract shortcode from URL path segments
        url_parts = clean_url.split('/')
        shortcode = None
        
        # Look for the shortcode after /p/, /reel/, or /tv/
        for i, part in enumerate(url_parts):
            if part in ['p', 'reel', 'tv'] and i+1 < len(url_parts):
                shortcode = url_parts[i+1]
                break
        
        if not shortcode:
            raise ValueError(f"Could not extract shortcode from URL: {url}")
            
        logger.info(f"Extracted shortcode: {shortcode}")
        
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        account_name = sanitize_folder_name(post.owner_username)
        folder_path = os.path.join("", f"{account_name}")

        os.makedirs(folder_path, exist_ok=True)
        L.download_post(post, folder_path)
            
        res = {
            "error": "",
            "titolo": sanitize_folder_name(post.caption.split('\n')[0] if post.caption else str(post.mediaid)),
            "percorso_video": folder_path,
            "caption": post.caption if post.caption else ""
        }
        
        logger.info(f"Download completato per {url}")
        logger.info(f" {str(res)}")
        result.append(res)
        return result
    except instaloader.exceptions.InstaloaderException as e:
        logger.error(f"Errore specifico di scarica_contenuto_reel: {str(e)}")
        result.append({
            "error": str(e),
            "titolo": "",
            "percorso_video": "",
            "caption": ""
        })
        return result

async def scarica_contenuti_account(username: str):
    result = []
    try:
        L = get_instaloader()
        # Scarica i post dell'account
        logger.info(f"Attempting to fetch profile: {username}")
        profile = instaloader.Profile.from_username(L.context, username)
       
        account_name = sanitize_folder_name(profile.username)
        folder_path = os.path.join("", f"{account_name}")
        os.makedirs(folder_path, exist_ok=True)
        
        post_count = 0
        logger.info(f"Starting to fetch posts for profile: {username}")
        for post in profile.get_posts():
            if post.is_video:
                L.download_post(post, target=folder_path)
                post_count += 1

                res = {
                    "error": "",
                    "titolo": sanitize_folder_name(post.caption.split('\n')[0] if post.caption else str(post.mediaid)),
                    "percorso_video": folder_path,
                    "caption": post.caption if post.caption else ""
                }
                
                result.append(res)
                logger.info(f"Downloaded post {post_count} for {username}")
        
        logger.info(f"Completed fetching {post_count} posts for profile: {username}")
        return result
    except instaloader.exceptions.InstaloaderException as e:
        logger.error(f"Errore specifico di scarica_contenuti_account: {str(e)}")
        result.append({
            "error": str(e),
            "titolo": "",
            "percorso_video": "",
            "caption": ""
        })
        return result

