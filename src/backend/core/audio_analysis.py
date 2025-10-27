"""Herramientas de análisis de audio basadas en librosa."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import librosa

from . import metadata

DEFAULT_MAX_MUESTRAS_CUE = 2048


def _downsample(segmento: np.ndarray, max_muestras: int) -> List[float]:
    """Reduce el tamaño de un segmento preservando su forma general."""

    if segmento.size == 0:
        return []
    if max_muestras <= 0 or segmento.size <= max_muestras:
        return segmento.astype(float).tolist()
    indices = np.linspace(0, segmento.size - 1, num=max_muestras, dtype=int)
    return segmento[indices].astype(float).tolist()


def _intervalos_desde_beats(
    beat_frames: Sequence[int], sr: int, duracion: float, beats_por_cue: int
) -> List[Tuple[float, float]]:
    """Genera intervalos aproximados agrupando beats consecutivos."""

    if not beat_frames:
        return [(0.0, float(duracion))]

    tiempos = librosa.frames_to_time(np.asarray(beat_frames), sr=sr)
    paso = max(1, int(beats_por_cue))
    intervalos: List[Tuple[float, float]] = []

    for indice in range(0, len(tiempos) - 1, paso):
        inicio = float(tiempos[indice])
        fin_indice = min(indice + paso, len(tiempos) - 1)
        fin = float(tiempos[fin_indice])
        if fin - inicio <= 1e-3:
            continue
        intervalos.append((inicio, fin))

    if not intervalos:
        intervalos.append((0.0, float(duracion)))
    else:
        ultimo_inicio, ultimo_fin = intervalos[-1]
        if ultimo_fin < duracion:
            intervalos[-1] = (ultimo_inicio, float(duracion))

    return intervalos


def _extraer_cues(
    y: np.ndarray,
    sr: int,
    intervalos: Iterable[Tuple[float, float]],
    max_muestras: int,
) -> List[metadata.Cue]:
    """Construye objetos :class:`metadata.Cue` a partir de intervalos."""

    cues: List[metadata.Cue] = []
    duracion_total = float(len(y) / sr) if sr else 0.0

    for indice, (inicio, fin) in enumerate(intervalos):
        inicio_seg = max(0.0, float(inicio))
        fin_seg = min(float(fin), duracion_total)
        if fin_seg <= inicio_seg:
            continue

        inicio_muestra = int(inicio_seg * sr)
        fin_muestra = int(fin_seg * sr)
        segmento = y[inicio_muestra:fin_muestra]
        if segmento.size == 0:
            continue

        forma = _downsample(segmento, max_muestras)
        cues.append(
            metadata.Cue(
                nombre=f"cue_{indice}",
                inicio=inicio_seg,
                fin=fin_seg,
                forma=forma,
            )
        )

    return cues


def analizar_audio(
    ruta_audio: str | Path,
    intervalos: Iterable[Tuple[float, float]] | None = None,
    auto_cues: bool = True,
    beats_por_cue: int = 4,
    max_muestras_cue: int = DEFAULT_MAX_MUESTRAS_CUE,
) -> metadata.AnalysisResult:
    """Realiza un análisis completo: BPM + cues (opcionales)."""

    ruta = Path(ruta_audio)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo de audio: {ruta}")

    # Optimización: si no se necesitan cues, cargar solo para BPM
    need_full_audio = bool(intervalos) or auto_cues
    
    if need_full_audio:
        y, sr = librosa.load(str(ruta))
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        duracion = librosa.get_duration(y=y, sr=sr)
    else:
        # Cargar con menor calidad para solo BPM (más rápido)
        y, sr = librosa.load(str(ruta), sr=22050, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        duracion = librosa.get_duration(y=y, sr=sr)

    if intervalos:
        intervalos_limpios = [
            (max(0.0, float(inicio)), min(float(fin), float(duracion)))
            for inicio, fin in intervalos
            if fin > inicio
        ]
    elif auto_cues:
        intervalos_limpios = _intervalos_desde_beats(beat_frames, sr, float(duracion), beats_por_cue)
    else:
        intervalos_limpios = []

    cues = _extraer_cues(y, sr, intervalos_limpios, max_muestras_cue) if intervalos_limpios else []

    return metadata.AnalysisResult(
        bpm=float(tempo),
        duracion=float(duracion),
        sample_rate=int(sr),
        cues=cues,
    )


def extraer_bpm(ruta_audio: str | Path) -> float:
    """Devuelve solo el BPM estimado."""

    return analizar_audio(ruta_audio, auto_cues=False).bpm


def calcular_cues(
    ruta_audio: str | Path,
    intervalos: Iterable[Tuple[float, float]],
    max_muestras_cue: int = DEFAULT_MAX_MUESTRAS_CUE,
) -> List[metadata.Cue]:
    """Calcula los cues para los intervalos proporcionados."""

    resultado = analizar_audio(
        ruta_audio,
        intervalos=intervalos,
        auto_cues=False,
        max_muestras_cue=max_muestras_cue,
    )
    return resultado.cues
