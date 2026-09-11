"""Parámetros y rutas del pipeline RAG (S8 + S9 + S10). Live Review calidad del aire."""

from pathlib import Path

# --- Ingesta y chunking ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
CHUNKS_JSON = OUTPUT_DIR / "chunks.json"

MAX_FILAS_CSV: int | None = 40
CSV_PARADAS = "Paradas CRTM.csv"

EXTENSIONES_TEXTO = {".txt", ".md"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_CSV = {".csv"}