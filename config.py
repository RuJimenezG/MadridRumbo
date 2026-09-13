# =====================================================================
# =====================================================================
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma"
QUERIES_DIR = BASE_DIR / "queries"

COLLECTION_NAME = "transporte_madrid"

# --- Embeddings ---
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")  # "local" | "tfidf" | "openai"
EMBEDDING_MODEL_LOCAL = os.getenv("EMBEDDING_MODEL_LOCAL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_MODEL_OPENAI = os.getenv("EMBEDDING_MODEL_OPENAI", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Chunking (coordinar el valor final con quien haga chunk.py) ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", 4))
# CORREGIDO: con el corpus real, "Paradas CRTM.csv" (22.405 filas) genera ~9.700
# chunks por sí solo. Con MAX_CHUNKS=500 se truncaba el índice perdiendo el 100%
# de los FAQ/PDFs de tarifas (quedaban solo trozos del CSV). Subido a 12000 para
# cubrir el corpus actual (9.814 chunks) con margen.
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 12000))
