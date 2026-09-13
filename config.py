"""Parámetros y rutas del pipeline RAG (S8 + S9 + S10). Live Review calidad del aire."""

from pathlib import Path

# --- Ingesta y chunking ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
CHUNKS_JSON = OUTPUT_DIR / "chunks.json"

MAX_FILAS_CSV = None #: int | None = 40
CSV_PARADAS = "Paradas CRTM.csv"

EXTENSIONES_TEXTO = {".txt", ".md"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_CSV = {".csv"}

# --- Embedding ---
EMBEDDING_MODEL = "gemini-embedding-2"
EMBED_BATCH_SIZE = 100
EMBEDDINGS_JSON = OUTPUT_DIR / "embeddings.json"
MAX_CHUNKS_EMBED: int | None = None # None = todos; 50 puede dejar fuera FAQ/PDF

EMBED_RPM_LIMIT = 2000 # La cuota gratuita de gemini-embedding-2 es de 100 RPM en free tier y 3000 RPM en Tier 1.