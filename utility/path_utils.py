"""Utility helpers for mapping media file paths to web-accessible URLs."""

from __future__ import annotations

import os
from typing import Iterable, List, Optional

from config import STATIC_DIR, MEDIA_RICETTE_WEB_PREFIX

_STATIC_ROOT = os.path.normpath(STATIC_DIR)


def ensure_static_web_path(file_path: Optional[str]) -> Optional[str]:
    """Return a path that can be served from FastAPI's static mount."""
    if not file_path:
        return file_path

    path_str = str(file_path).replace("\\", "/")

    if path_str.startswith(("http://", "https://")):
        return path_str

    if path_str.startswith("/static/"):
        return path_str

    if path_str.startswith("static/"):
        return f"/{path_str}"

    if path_str.startswith("mediaRicette/"):
        return f"/static/{path_str}"

    try:
        rel_path = os.path.relpath(os.path.normpath(file_path), _STATIC_ROOT)
    except ValueError:
        return path_str

    rel_path = rel_path.replace("\\", "/")
    if rel_path.startswith("../"):
        return path_str

    return f"/static/{rel_path}"


def ensure_static_web_paths(paths: Optional[Iterable[str]]) -> List[str]:
    """Vector version of ``ensure_static_web_path`` for iterables."""
    if not paths:
        return []
    return [ensure_static_web_path(path) for path in paths if path]


def ensure_media_web_path(file_path: Optional[str]) -> Optional[str]:
    """Map a media file inside ``mediaRicette`` to its web URL."""
    web_path = ensure_static_web_path(file_path)
    if not web_path:
        return web_path
    if web_path.startswith(MEDIA_RICETTE_WEB_PREFIX):
        return web_path
    if "mediaRicette/" in web_path:
        return web_path
    if isinstance(file_path, str) and "mediaRicette" in file_path:
        adjusted = file_path.replace("\\", "/")
        if adjusted.startswith("/static/"):
            return adjusted
        if adjusted.startswith("static/"):
            return f"/{adjusted}"
        idx = adjusted.find("mediaRicette")
        if idx >= 0:
            suffix = adjusted[idx:]
            return f"/static/{suffix}" if not suffix.startswith("/static/") else suffix
    return web_path


def ensure_media_web_paths(paths: Optional[Iterable[str]]) -> List[str]:
    """Apply ``ensure_media_web_path`` to each element of ``paths``."""
    if not paths:
        return []
    return [ensure_media_web_path(path) for path in paths if path]


def web_path_to_filesystem_path(web_path: Optional[str]) -> Optional[str]:
    """Converte un percorso web (/static/...) in percorso filesystem assoluto."""
    if not web_path:
        return web_path
    
    path_str = str(web_path).replace("\\", "/")
    
    # Se inizia con /static/, rimuovi /static/ e aggiungi STATIC_DIR
    if path_str.startswith("/static/"):
        relative_path = path_str[8:]  # Rimuove "/static/"
        return os.path.join(_STATIC_ROOT, relative_path)
    
    # Se è già un percorso assoluto, restituiscilo così com'è
    if os.path.isabs(path_str):
        return path_str
        
    return web_path
