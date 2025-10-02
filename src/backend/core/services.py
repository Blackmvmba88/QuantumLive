"""Integraciones con servicios externos para búsqueda musical."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests


def buscar_en_soundcloud(query: str, client_id: str) -> dict:
    """Busca pistas en SoundCloud usando un *client_id* público."""

    url = "https://api-v2.soundcloud.com/search/tracks"
    params = {"q": query, "client_id": client_id}
    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def buscar_en_itunes(query: str) -> dict:
    """Busca contenido musical en la API pública de iTunes."""

    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "music"}
    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def buscar_en_youtube(query: str, api_key: str) -> dict:
    """Realiza una búsqueda de videos musicales en YouTube Data API v3."""

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "key": api_key,
    }
    respuesta = requests.get(url, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def buscar_en_suno(query: str, token: str) -> dict:
    """Plantilla básica para integrar el API de Suno cuando esté disponible."""

    raise NotImplementedError(
        "La API pública de Suno no está documentada; se requiere implementación personalizada"
    )


def buscar_en_todos(
    query: str,
    *,
    soundcloud_client_id: Optional[str] = None,
    youtube_api_key: Optional[str] = None,
    include_itunes: bool = True,
    include_suno: bool = False,
    suno_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Coordina búsquedas en múltiples plataformas y gestiona errores comunes."""

    resultados: Dict[str, Any] = {}

    if soundcloud_client_id:
        try:
            resultados["soundcloud"] = buscar_en_soundcloud(query, soundcloud_client_id)
        except requests.RequestException as exc:  # pragma: no cover - solo errores HTTP
            resultados["soundcloud"] = {"error": str(exc)}
    else:
        resultados["soundcloud"] = {"error": "client_id no proporcionado"}

    if include_itunes:
        try:
            resultados["itunes"] = buscar_en_itunes(query)
        except requests.RequestException as exc:  # pragma: no cover - solo errores HTTP
            resultados["itunes"] = {"error": str(exc)}

    if youtube_api_key:
        try:
            resultados["youtube"] = buscar_en_youtube(query, youtube_api_key)
        except requests.RequestException as exc:  # pragma: no cover
            resultados["youtube"] = {"error": str(exc)}
    else:
        resultados["youtube"] = {"error": "api_key no proporcionada"}

    if include_suno:
        if suno_token:
            try:
                resultados["suno"] = buscar_en_suno(query, suno_token)
            except NotImplementedError as exc:
                resultados["suno"] = {"error": str(exc)}
            except requests.RequestException as exc:  # pragma: no cover
                resultados["suno"] = {"error": str(exc)}
        else:
            resultados["suno"] = {"error": "token de Suno no proporcionado"}

    return resultados
