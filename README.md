# QuantumLive
Laboratorio musical modular – magia, caos, colaboración y evolución sonora

## Backend

El directorio `src/backend` contiene un servidor **FastAPI** pensado para DJs y productores que desean centralizar análisis de audio, playlists y búsquedas en catálogos externos.

### 1. Análisis musical automático

- `POST /analizar` recibe la ruta de un archivo de audio y devuelve BPM, duración y una lista de *cues*.  
- Los cues se generan automáticamente agrupando beats; también puedes forzar tus propios intervalos.  
- Cada cue guarda una versión reducida de la forma de onda para visualizarla en clientes ligeros.

Ejemplo:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "ruta": "samples/track.wav",
    "auto_cues": true,
    "beats_por_cue": 8
  }' \
  http://localhost:8000/analizar
```

### 2. Playlist inteligente multiplataforma

- Las pistas se almacenan como JSON en `data/playlist.json` con el modelo `metadata.Track` (título, artista, BPM, géneros, cues, notas y fuentes externas).  
- Endpoints disponibles:
  - `GET /playlist` lista todo el catálogo.
  - `POST /playlist` crea una pista y, si se proporciona `ruta_audio`, calcula BPM/cues automáticamente.
  - `GET /playlist/{id}` recupera una pista por identificador.
  - `PATCH /playlist/{id}` actualiza metadatos (BPM, géneros, notas, cues…).
  - `DELETE /playlist/{id}` elimina una pista.

```bash
curl -X POST http://localhost:8000/playlist \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Live Session",
    "artista": "Quantum Crew",
    "ruta_audio": "samples/live_session.wav",
    "generos": ["house", "latin"],
    "fuentes": {"youtube": "https://youtu.be/demo"}
  }'
```

### 3. Búsqueda en SoundCloud, iTunes y YouTube (Suno opcional)

- `POST /buscar` agrega resultados de todos los servicios configurados en una sola respuesta JSON.
- Acepta claves/ID por servicio para respetar los límites de cada API.
- La integración de Suno queda como “stub”: el backend devuelve un error amigable hasta que se configure el token y la lógica específica.

```bash
curl -X POST http://localhost:8000/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "afrohouse",
    "soundcloud_client_id": "TU_CLIENT_ID",
    "youtube_api_key": "TU_API_KEY"
  }'
```

### 4. Lista personal de YouTube en texto plano

- `data/youtube.txt` mantiene enlaces simples, ideales para listas rápidas o uso offline.
- Endpoints:
  - `GET /youtube` devuelve la lista depurada.
  - `POST /youtube` agrega un enlace nuevo.
  - `POST /youtube/ordenar` reescribe el archivo eliminando líneas vacías y repite la lista resultante.

### Ejecutar el servidor

```bash
uvicorn backend.main:app --reload
```
