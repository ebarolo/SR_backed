import yt_dlp
import asyncio
import os
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from utility.utility import sanitize_filename
from utility.cloud_logging_config import get_error_logger, clear_error_chain
from config import BASE_FOLDER_RICETTE

error_logger = get_error_logger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def yt_dlp_video(url: str) -> Dict[str, Any]:
    # Clear error chain at start of new operation
    clear_error_chain()
    
    opzioni = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(BASE_FOLDER_RICETTE, "%(title)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(opzioni) as ydl:
            #logger.info(f"Inizio download del video: {url}")
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            #logger.info(f"Download completato con successo: {url}")
            video_title = sanitize_filename(info["title"])
            video_filename = ydl.prepare_filename(info)
        return {"video_title": video_title, "video_filename": video_filename}
    except yt_dlp.utils.DownloadError as e:
        error_logger.log_exception("yt_dlp_download", e, {"url": url})
        raise
    except KeyError as ke:
        if "config" in str(ke):
            error_logger.log_exception("yt_dlp_config", ke, {"url": url, "key_error": str(ke)})
        else:
            error_logger.log_exception("yt_dlp_key_error", ke, {"url": url})
        raise
    except Exception as e:
        error_logger.log_exception("yt_dlp_unexpected", e, {"url": url})
        raise
