"""FastAPI backend para análisis, playlists y búsquedas musicales."""
from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator

from .core import audio_analysis, metadata, playlist, services, youtube_list


class Intervalo(BaseModel):
    """Representa un tramo en segundos dentro de un audio."""

    inicio: float = Field(..., ge=0)
    fin: float = Field(..., gt=0)

    @validator("fin")
    def validar_fin(cls, fin: float, values: Dict[str, float]) -> float:
        inicio = values.get("inicio", 0.0)
        if fin <= inicio:
            raise ValueError("El final debe ser mayor que el inicio")
        return fin


class AnalisisPayload(BaseModel):
    ruta: str = Field(..., description="Ruta local del archivo a analizar")
    intervalos: List[Intervalo] = Field(default_factory=list)
    auto_cues: bool = Field(
        default=True,
        description="Si no hay intervalos definidos, generar cues automáticamente",
    )
    beats_por_cue: int = Field(
        default=4, ge=1, description="Número de beats agrupados para cada cue"
    )
    max_muestras_cue: int = Field(
        default=audio_analysis.DEFAULT_MAX_MUESTRAS_CUE,
        ge=128,
        le=16384,
        description="Cantidad máxima de puntos en la forma de onda almacenada",
    )


class CrearTrackPayload(BaseModel):
    titulo: str
    artista: str
    ruta_audio: Optional[str] = Field(
        default=None, description="Ruta para analizar y completar metadatos"
    )
    intervalos: List[Intervalo] = Field(default_factory=list)
    auto_cues: bool = Field(default=True)
    beats_por_cue: int = Field(default=4, ge=1)
    generos: List[str] = Field(default_factory=list)
    fuentes: Dict[str, str] = Field(default_factory=dict)
    notas: Optional[str] = None
    bpm: Optional[float] = Field(default=None, gt=0)
    cues: List[metadata.Cue] = Field(default_factory=list)


class ActualizarTrackPayload(BaseModel):
    titulo: Optional[str] = None
    artista: Optional[str] = None
    bpm: Optional[float] = Field(default=None, gt=0)
    generos: Optional[List[str]] = None
    fuentes: Optional[Dict[str, str]] = None
    notas: Optional[str] = None
    cues: Optional[List[metadata.Cue]] = None


class BuscarPayload(BaseModel):
    query: str
    soundcloud_client_id: Optional[str] = None
    youtube_api_key: Optional[str] = None
    include_itunes: bool = True
    include_suno: bool = False
    suno_token: Optional[str] = None


app = FastAPI(title="QuantumLive Backend")


@app.post("/analizar", response_model=metadata.AnalysisResult)
def analizar_pista(payload: AnalisisPayload) -> metadata.AnalysisResult:
    """Analiza un archivo de audio devolviendo BPM y cues opcionales."""

    intervalos = [(i.inicio, i.fin) for i in payload.intervalos]

    try:
        return audio_analysis.analizar_audio(
            ruta_audio=payload.ruta,
            intervalos=intervalos or None,
            auto_cues=payload.auto_cues,
            beats_por_cue=payload.beats_por_cue,
            max_muestras_cue=payload.max_muestras_cue,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:  # pragma: no cover - errores específicos de análisis
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.get("/playlist", response_model=List[metadata.Track])
def obtener_playlist() -> List[metadata.Track]:
    """Devuelve todas las pistas almacenadas en la playlist local."""

    return playlist.listar()


@app.post("/playlist", response_model=metadata.Track, status_code=status.HTTP_201_CREATED)
def crear_track(payload: CrearTrackPayload) -> metadata.Track:
    """Crea una pista en la playlist, analizando audio si se proporciona."""

    analisis: Optional[metadata.AnalysisResult] = None
    intervalos = [(i.inicio, i.fin) for i in payload.intervalos]

    if payload.ruta_audio:
        try:
            analisis = audio_analysis.analizar_audio(
                ruta_audio=payload.ruta_audio,
                intervalos=intervalos or None,
                auto_cues=payload.auto_cues,
                beats_por_cue=payload.beats_por_cue,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    data = {
        "titulo": payload.titulo,
        "artista": payload.artista,
        "generos": payload.generos,
        "fuentes": payload.fuentes,
        "notas": payload.notas,
        "bpm": payload.bpm,
        "cues": payload.cues,
    }

    if analisis:
        data.update({"bpm": analisis.bpm, "cues": analisis.cues})

    pista = metadata.Track(**data)
    return playlist.agregar(pista)


@app.get("/playlist/{track_id}", response_model=metadata.Track)
def obtener_track(track_id: UUID) -> metadata.Track:
    pista = playlist.obtener(track_id)
    if pista is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pista no encontrada")
    return pista


@app.patch("/playlist/{track_id}", response_model=metadata.Track)
def actualizar_track(track_id: UUID, payload: ActualizarTrackPayload) -> metadata.Track:
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar",
        )

    try:
        return playlist.actualizar(track_id, **updates)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pista no encontrada")


@app.delete("/playlist/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_track(track_id: UUID) -> None:
    if not playlist.eliminar(track_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pista no encontrada")


@app.post("/buscar")
def buscar_en_servicios(payload: BuscarPayload) -> Dict[str, object]:
    """Realiza búsquedas paralelas en los servicios configurados."""

    return services.buscar_en_todos(
        payload.query,
        soundcloud_client_id=payload.soundcloud_client_id,
        youtube_api_key=payload.youtube_api_key,
        include_itunes=payload.include_itunes,
        include_suno=payload.include_suno,
        suno_token=payload.suno_token,
    )


@app.get("/youtube")
def lista_youtube() -> List[str]:
    """Devuelve la lista de URLs de YouTube almacenadas en texto plano."""

    return youtube_list.obtener_lista_youtube()


@app.post("/youtube")
def agregar_youtube(url: str) -> None:
    """Agrega una nueva URL de YouTube a la lista local."""

    youtube_list.agregar_youtube(url)


@app.post("/youtube/ordenar", response_model=List[str])
def ordenar_youtube() -> List[str]:
    """Limpia la lista eliminando líneas vacías y devuelve el resultado."""

    return youtube_list.compactar_lista_youtube()
