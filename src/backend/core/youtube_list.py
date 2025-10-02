"""Simple management for a text-based list of YouTube URLs."""
from __future__ import annotations

from pathlib import Path
from typing import List


ARCHIVO_YT = Path("data/youtube.txt")


def obtener_lista_youtube() -> List[str]:
    """Return stored YouTube URLs from the text file."""
    if not ARCHIVO_YT.exists():
        return []
    return [line.strip() for line in ARCHIVO_YT.read_text().splitlines() if line.strip()]


def agregar_youtube(url: str) -> None:
    """Append a new YouTube URL to the text file."""
    ARCHIVO_YT.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVO_YT.open("a", encoding="utf-8") as fh:
        fh.write(url + "\n")


def compactar_lista_youtube() -> List[str]:
    """Remove blank lines and rewrite the YouTube list.

    Returns the cleaned list so clients can keep their state in sync.
    """
    urls = obtener_lista_youtube()
    if not urls:
        return []
    ARCHIVO_YT.write_text("\n".join(urls) + "\n", encoding="utf-8")
    return urls
