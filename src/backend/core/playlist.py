"""Gestión de playlists en disco usando modelos de Pydantic."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import UUID

from . import metadata

PLAYLIST_PATH = Path("data/playlist.json")


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
    if not PLAYLIST_PATH.exists():
        return []
    datos = json.loads(PLAYLIST_PATH.read_text(encoding="utf-8"))
    return [_parse_track(item) for item in datos]


def _save_tracks(tracks: Iterable[metadata.Track]) -> None:
    _ensure_parent()
    serializado = [_serialize_track(track) for track in tracks]
    PLAYLIST_PATH.write_text(
        json.dumps(serializado, indent=2, ensure_ascii=False), encoding="utf-8"
    )


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

    buscado = str(track_id)
    for pista in _load_tracks():
        if str(pista.id) == buscado:
            return pista
    return None


def actualizar(track_id: UUID | str, **updates) -> metadata.Track:
    """Actualiza campos de una pista existente."""

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
