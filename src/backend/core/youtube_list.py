"""Simple management for a text-based list of YouTube URLs."""
from __future__ import annotations

from pathlib import Path
from typing import List


ARCHIVO_YT = Path("data/youtube.txt")

# Cache para evitar lecturas repetidas
_cache: List[str] | None = None


def _invalidate_cache() -> None:
    """Invalida el cache cuando se modifican los datos."""
    global _cache
    _cache = None


def obtener_lista_youtube() -> List[str]:
    """Return stored YouTube URLs from the text file."""
    global _cache
    
    # Usar cache si está disponible
    if _cache is not None:
        return _cache.copy()
    
    if not ARCHIVO_YT.exists():
        _cache = []
        return []
    
    urls = [line.strip() for line in ARCHIVO_YT.read_text().splitlines() if line.strip()]
    _cache = urls
    return urls.copy()


def agregar_youtube(url: str) -> None:
    """Append a new YouTube URL to the text file."""
    ARCHIVO_YT.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVO_YT.open("a", encoding="utf-8") as fh:
        fh.write(url + "\n")
    _invalidate_cache()


def compactar_lista_youtube() -> List[str]:
    """Remove blank lines and rewrite the YouTube list.

    Returns the cleaned list so clients can keep their state in sync.
    """
    urls = obtener_lista_youtube()
    if not urls:
        _invalidate_cache()
        return []
    ARCHIVO_YT.write_text("\n".join(urls) + "\n", encoding="utf-8")
    _invalidate_cache()
    return urls
