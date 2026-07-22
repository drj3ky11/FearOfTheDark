# Bloque 6 — Transcripción de audio con Whisper

Módulo introductorio al pipeline **audio → texto** usando modelos locales.

## Requisito previo (sistema)

```bash
sudo apt install -y ffmpeg
```

`ffmpeg` es necesario para que Whisper decodifique ficheros de audio (mp3, m4a, wav, etc.).

## Notebooks

| Notebook | Contenido |
|---|---|
| `00_transcripcion_whisper.ipynb` | Whisper local desde cero: generar audio de demo, transcribir, comparar modelos, exportar con timestamps |

## Dependencias Python

Ya incluidas en `pyproject.toml` (raíz del repo):

```
faster-whisper>=1.1
gtts>=2.5
```

Instalar con:

```bash
uv sync
```

## Modelos Whisper

`faster-whisper` descarga los pesos de HuggingFace la primera vez y los cachea en `~/.cache/huggingface/`.

| Modelo | Tamaño | Calidad |
|---|---|---|
| `tiny` | 39 MB | baja |
| `base` | 74 MB | media-baja |
| `small` | 244 MB | **buena — recomendado** |
| `medium` | 769 MB | excelente (mejor con GPU) |
