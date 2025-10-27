"""Gestión de playlists en disco usando modelos de Pydantic."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from . import metadata

PLAYLIST_PATH = Path("data/playlist.json")

# Cache simple para evitar lecturas repetidas
_cache: Optional[Dict[str, metadata.Track]] = None
_cache_dirty = False


def _ensure_parent() -> None:
    PLAYLIST_PATH.parent.mkdir(parents=True, exist_ok=True)


def _serialize_track(track: metadata.Track) -> dict:
    """Convierte una pista en un diccionario serializable."""

    if hasattr(track, "model_dump_json"):
        return json.loads(track.model_dump_json())  # type: ignore[attr-defined]
    return json.loads(track.json())


def _parse_track(data: dict) -> metadata.Track:
    """Crea un objeto :class:`metadata.Track` a partir de un diccionario."""

    if hasattr(metadata.Track, "model_validate"):
        return metadata.Track.model_validate(data)  # type: ignore[attr-defined]
    return metadata.Track.parse_obj(data)  # type: ignore[attr-defined]


def _copy_track(track: metadata.Track, **updates) -> metadata.Track:
    """Compatibilidad entre Pydantic v1 y v2 para copiar modelos."""

    updates.setdefault("actualizado", datetime.utcnow())
    if hasattr(track, "model_copy"):
        return track.model_copy(update=updates)  # type: ignore[attr-defined]
    return track.copy(update=updates)  # type: ignore[attr-defined]


def _load_tracks() -> List[metadata.Track]:
    global _cache
    
    # Usar cache si está disponible y no está sucio
    if _cache is not None:
        return list(_cache.values())
    
    if not PLAYLIST_PATH.exists():
        _cache = {}
        return []
    
    datos = json.loads(PLAYLIST_PATH.read_text(encoding="utf-8"))
    tracks = [_parse_track(item) for item in datos]
    
    # Actualizar cache indexado por ID
    _cache = {str(track.id): track for track in tracks}
    return tracks


def _save_tracks(tracks: Iterable[metadata.Track]) -> None:
    global _cache, _cache_dirty
    
    _ensure_parent()
    serializado = [_serialize_track(track) for track in tracks]
    PLAYLIST_PATH.write_text(
        json.dumps(serializado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    
    # Actualizar cache
    _cache = {str(track.id): track for track in tracks}
    _cache_dirty = False


def listar() -> List[metadata.Track]:
    """Devuelve todas las pistas almacenadas."""

    return _load_tracks()


def agregar(track: metadata.Track) -> metadata.Track:
    """Añade una nueva pista a la playlist."""

    pistas = _load_tracks()
    pista = _copy_track(track)
    pistas.append(pista)
    _save_tracks(pistas)
    return pista


def obtener(track_id: UUID | str) -> Optional[metadata.Track]:
    """Recupera una pista por su identificador."""

    global _cache
    
    buscado = str(track_id)
    
    # Intentar obtener del cache primero
    if _cache is not None and buscado in _cache:
        return _cache[buscado]
    
    # Si no está en cache, cargar desde disco
    _load_tracks()
    return _cache.get(buscado) if _cache else None


def actualizar(track_id: UUID | str, **updates) -> metadata.Track:
    """Actualiza campos de una pista existente."""

    global _cache
    
    buscado = str(track_id)
    pistas = _load_tracks()

    for indice, pista in enumerate(pistas):
        if str(pista.id) != buscado:
            continue
        pistas[indice] = _copy_track(pista, **updates)
        _save_tracks(pistas)
        return pistas[indice]

    raise KeyError(f"No existe la pista con id {track_id}")


def eliminar(track_id: UUID | str) -> bool:
    """Elimina una pista. Devuelve ``True`` si se borró."""

    buscado = str(track_id)
    pistas = _load_tracks()
    nuevas = [p for p in pistas if str(p.id) != buscado]
    if len(nuevas) == len(pistas):
        return False
    _save_tracks(nuevas)
    return True
