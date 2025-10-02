"""Pydantic models that describen pistas, cues y resultados de análisis."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class Cue(BaseModel):
    """Segmento de la onda con un nombre y posiciones en segundos."""

    nombre: str = Field(..., description="Identificador único del cue dentro de la pista")
    inicio: float = Field(..., ge=0, description="Tiempo de inicio del cue en segundos")
    fin: float = Field(..., gt=0, description="Tiempo de fin del cue en segundos")
    forma: List[float] = Field(
        default_factory=list,
        description="Muestra reducida de la onda asociada al cue",
    )

    @validator("fin")
    def validar_fin(cls, fin: float, values: Dict[str, float]) -> float:
        inicio = values.get("inicio", 0.0)
        if fin <= inicio:
            raise ValueError("El fin del cue debe ser mayor que el inicio")
        return float(fin)


class Track(BaseModel):
    """Representa una pista con metadatos enriquecidos."""

    id: UUID = Field(default_factory=uuid4, description="Identificador único de la pista")
    titulo: str = Field(..., description="Nombre de la pista")
    artista: str = Field(..., description="Artista principal")
    bpm: Optional[float] = Field(
        default=None,
        description="Tempo en beats por minuto, si fue calculado o asignado",
        gt=0,
    )
    generos: List[str] = Field(default_factory=list, description="Etiquetas de género")
    cues: List[Cue] = Field(default_factory=list, description="Segmentos relevantes de la onda")
    fuentes: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapeo servicio→URL para ubicar la pista en plataformas externas",
    )
    notas: Optional[str] = Field(default=None, description="Notas libres del usuario")
    creado: datetime = Field(
        default_factory=datetime.utcnow, description="Fecha de creación del registro"
    )
    actualizado: datetime = Field(
        default_factory=datetime.utcnow, description="Última fecha de modificación"
    )

    class Config:
        allow_population_by_field_name = True


class AnalysisResult(BaseModel):
    """Resumen del análisis automático de audio."""

    bpm: float = Field(..., gt=0, description="Tempo estimado en beats por minuto")
    duracion: float = Field(..., gt=0, description="Duración total de la pista en segundos")
    sample_rate: int = Field(..., gt=0, description="Frecuencia de muestreo utilizada")
    cues: List[Cue] = Field(default_factory=list, description="Cues generados a partir del audio")
