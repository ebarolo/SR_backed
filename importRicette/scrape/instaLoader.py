import os
import instaloader
import logging
from typing import Dict, Any

from utility.utility import sanitize_folder_name
from utility.logging_config import get_error_logger, clear_error_chain
from config import ISTA_USERNAME, ISTA_PASSWORD, BASE_FOLDER_RICETTE

# Initialize error logger
error_logger = get_error_logger(__name__)

def get_instaloader():
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=True,
        download_geotags=False,
        download_comments=False,
        save_metadata=True,
        compress_json=False,
        sanitize_paths=True,
        post_metadata_txt_pattern="",  # Disable metadata txt files
        dirname_pattern=os.path.join(
            BASE_FOLDER_RICETTE, "{shortcode}"
        ),
        filename_pattern="{shortcode}",
    )

    # Try to login if credentials are available
    if ISTA_USERNAME and ISTA_PASSWORD:
        try:
            logging.getLogger(__name__).info(f"Attempting to login with username: {ISTA_USERNAME}")
            L.login(ISTA_USERNAME, ISTA_PASSWORD)
            logging.getLogger(__name__).info("Login successful")
        except Exception as login_error:
            error_logger.log_exception("instagram_login", login_error, {"username": ISTA_USERNAME})
            error_logger.log_error("instagram_login_warning", "Proceeding without authentication - some operations may be rate limited", {"username": ISTA_USERNAME})
    else:
        logging.getLogger(__name__).info("No Instagram credentials available, proceeding without authentication")

    return L

async def scarica_contenuto_reel(url: str) -> Dict[str, Any]:
    # Clear error chain at start of new operation
    clear_error_chain()
    
    result = []
    try:
        L = get_instaloader()

        # Extract shortcode from URL with improved handling for different URL formats
        # Handle URLs like:
        # - https://www.instagram.com/p/ABC123/
        # - https://www.instagram.com/reel/ABC123/
        # - https://www.instagram.com/tv/ABC123/
        # - https://instagram.com/p/ABC123/

        logging.getLogger(__name__).info(f"Processing URL: {url}")

        # Clean URL by removing query parameters and trailing slashes
        clean_url = url.split("?")[0].rstrip("/")

        # Extract shortcode from URL path segments
        url_parts = clean_url.split("/")
        shortcode = None

        # Look for the shortcode after /p/, /reel/, or /tv/
        for i, part in enumerate(url_parts):
            if part in ["p", "reel", "tv"] and i + 1 < len(url_parts):
                shortcode = url_parts[i + 1]
                break

        if not shortcode:
            raise ValueError(f"Could not extract shortcode from URL: {url}")

        logging.getLogger(__name__).info(f"Extracted shortcode: {shortcode}")
        # Create a folder named after the shortcode inside static/mediaRicette
        shortcode_folder = os.path.join(
            BASE_FOLDER_RICETTE, shortcode
        )
        
        # Check if the folder already exists and contains files
        if os.path.exists(shortcode_folder) and os.listdir(shortcode_folder):
            error_logger.log_error("content_already_exists", f"Folder {shortcode_folder} already exists and contains files", {"shortcode": shortcode, "url": url})

            raise ValueError(f"Content for shortcode {shortcode} already downloaded")

        else:
            downloadFolder = os.path.join(shortcode_folder, "media_original")
            os.makedirs(downloadFolder, exist_ok=True)

            # Set the dirname_pattern to the shortcode folder for this download
            L.dirname_pattern = downloadFolder

            logging.getLogger(__name__).info(f"Created folder for download: {downloadFolder}")
            try:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
            except instaloader.exceptions.InstaloaderException as e:
                error_logger.log_exception("instaloader_fetch_post", e, {"shortcode": shortcode, "url": url})
                raise ValueError(f"Errore durante il recupero del post con shortcode {shortcode}: {str(e)}") from e
            except Exception as e: # Cattura generica per altri possibili errori non di Instaloader
                error_logger.log_exception("unexpected_fetch_post", e, {"shortcode": shortcode, "url": url})
                raise ValueError(f"Errore inaspettato durante il recupero del post con shortcode {shortcode}: {str(e)}") from e

            # Dump all available post attributes
            post_attributes = {}
            for attr in dir(post):
                # Skip private attributes and methods
                if not attr.startswith("_") and not callable(getattr(post, attr)):
                    try:
                        value = getattr(post, attr)
                        # Convert complex objects to string representation to avoid serialization issues
                        if not isinstance(value, (str, int, float, bool, type(None))):
                            value = str(value)
                        post_attributes[attr] = value
                    except Exception as e:
                        post_attributes[attr] = f"Error accessing attribute: {str(e)}"

            logging.getLogger(__name__).info(f"Post attributes extracted", extra={"shortcode": shortcode, "attributes_count": len(post_attributes)})
            
            # Download the post
            L.download_post(post, downloadFolder)

            res = {
                "error": "",
                "shortcode": shortcode,
                "caption": post.caption if post.caption else "",
            }

            result.append(res)
            return result

    except instaloader.exceptions.InstaloaderException as e:
        error_logger.log_exception("scarica_contenuto_reel", e, {"url": url})
        raise ValueError(f"Errore scarica_contenuto_reel: {str(e)}") from e

async def scarica_contenuti_account(username: str):
    # Clear error chain at start of new operation
    clear_error_chain()
    
    result = []
    try:
        L = get_instaloader()
        # Scarica i post dell'account
        logging.getLogger(__name__).info(f"Attempting to fetch profile: {username}")
        profile = instaloader.Profile.from_username(L.context, username)

        account_name = sanitize_folder_name(profile.username)
        folder_path = os.path.join("", f"{account_name}")
        os.makedirs(folder_path, exist_ok=True)

        post_count = 0
        logging.getLogger(__name__).info(f"Starting to fetch posts for profile: {username}")
        downloadFolder = os.path.join(folder_path, "media_original")
        for post in profile.get_posts():
            if post.is_video:
                L.download_post(post, target=downloadFolder)
                post_count += 1

                res = {
                    "error": "",
                    "titolo": sanitize_folder_name(
                        post.caption.split("\n")[0]
                        if post.caption
                        else str(post.mediaid)
                    ),
                    "percorso_video": downloadFolder,
                    "caption": post.caption if post.caption else "",
                }

                result.append(res)
                logging.getLogger(__name__).info(f"Downloaded post {post_count} for {username}")

        logging.getLogger(__name__).info(f"Completed fetching {post_count} posts for profile: {username}")
        return result
    except instaloader.exceptions.InstaloaderException as e:
        error_logger.log_exception("scarica_contenuti_account", e, {"username": username})
        raise ValueError(f"Errore scarica_contenuti_account: {str(e)}") from e