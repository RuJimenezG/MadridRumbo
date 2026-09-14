
from pathlib import Path

# --- Ingesta y chunking ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma"
QUERIES_DIR = BASE_DIR / "queries"

OUTPUT_DIR = BASE_DIR / "output"
CHUNKS_JSON = OUTPUT_DIR / "chunks.json"

MAX_FILAS_CSV = None #: int | None = 40
CSV_PARADAS = "Paradas CRTM.csv"

EXTENSIONES_TEXTO = {".txt", ".md"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_CSV = {".csv"}

# --- Embeddings OpenAI---
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")  # "local" | "tfidf" | "openai"
EMBEDDING_MODEL_LOCAL = os.getenv("EMBEDDING_MODEL_LOCAL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_MODEL_OPENAI = os.getenv("EMBEDDING_MODEL_OPENAI", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Embedding Gemini ---
EMBEDDING_MODEL = "gemini-embedding-2"
EMBED_BATCH_SIZE = 100
EMBEDDINGS_JSON = OUTPUT_DIR / "embeddings.json"
MAX_CHUNKS_EMBED: int | None = None # None = todos; 50 puede dejar fuera FAQ/PDF

EMBED_RPM_LIMIT = 2000 # La cuota gratuita de gemini-embedding-2 es de 100 RPM en free tier y 3000 RPM en Tier 1.

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", 4))
# CORREGIDO: con el corpus real, "Paradas CRTM.csv" (22.405 filas) genera ~9.700
# chunks por sí solo. Con MAX_CHUNKS=500 se truncaba el índice perdiendo el 100%
# de los FAQ/PDFs de tarifas (quedaban solo trozos del CSV). Subido a 12000 para
# cubrir el corpus actual (9.814 chunks) con margen.

MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 12000))

# --- Generación (Gemini) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENERATION_MODEL = "gemini-3.6-flash"
TEMPERATURE = 0.0