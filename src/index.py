"""
index.py — Indexación de chunks en ChromaDB persistente.

CORREGIDO (Persona 2): este fichero importaba "from src.chunk import Chunk",
una clase que ya no existe — el chunk.py real del equipo usa Document de
LangChain (fragmentar_documentos() -> list[Document]), no mi dataclass Chunk
original. Esto rompía el import de index.py (y en cascada, el de retrieve.py
y generate.py). Ahora index_chunks() trabaja directamente con Document:
  - doc.page_content -> texto del chunk
  - doc.metadata["source"]        -> fuente (rellenada por src/load.py)
  - doc.metadata["chunk_index"]   -> índice (rellenado por src/chunk.py)

ChromaDB guarda embeddings + metadatos (`source`, `chunk_id`) para poder
mostrar la procedencia de cada chunk recuperado y, si hace falta, regenerar
el índice desde cero (--recreate-index) tras cambiar de modelo de embeddings
o de MAX_CHUNKS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chromadb
from langchain_core.documents import Document
from config import CHROMA_DIR, COLLECTION_NAME, MAX_CHUNKS
from src.embed import embed_texts


def get_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_or_create_collection(client, recreate: bool = False):
    if recreate:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(COLLECTION_NAME)


def _nombre_fuente(metadata: dict) -> str:
    """Extrae solo el nombre de fichero de metadata['source'] (puede venir con ruta completa)."""
    source = metadata.get("source", "desconocido")
    return Path(str(source)).name


def index_chunks(chunks: list[Document], recreate: bool = False) -> int:
    """Indexa una lista de Document (de src/chunk.py) en ChromaDB. Devuelve el número de chunks indexados."""
    if len(chunks) > MAX_CHUNKS:
        from collections import Counter
        perdidos = Counter(_nombre_fuente(c.metadata) for c in chunks[MAX_CHUNKS:])
        print(
            f"[index] AVISO: {len(chunks)} chunks superan MAX_CHUNKS={MAX_CHUNKS}. "
            f"Se van a DESCARTAR {len(chunks) - MAX_CHUNKS} chunks, de estas fuentes: "
            f"{dict(perdidos)}. Sube MAX_CHUNKS en config.py/.env si no quieres perder "
            f"contenido de estos documentos, o revisa con el equipo si ese corpus (p. ej. "
            f"un CSV muy grande) necesita filtrarse/agregarse antes de indexar."
        )
        chunks = chunks[:MAX_CHUNKS]

    client = get_client()
    collection = get_or_create_collection(client, recreate=recreate)

    ids = [f"{_nombre_fuente(c.metadata)}::{c.metadata.get('chunk_index', i)}" for i, c in enumerate(chunks)]
    texts = [c.page_content for c in chunks]
    metadatas = [
        {"source": _nombre_fuente(c.metadata), "chunk_id": c.metadata.get("chunk_index", i)}
        for i, c in enumerate(chunks)
    ]

    # Chroma requiere embeddings explícitos si no se configura un embedding_function propio.
    embeddings = embed_texts(texts)

    # Indexar por lotes para evitar problemas de memoria en corpus grandes.
    batch_size = 64
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            documents=texts[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
        )
    return len(ids)


if __name__ == "__main__":
    import argparse
    from src.pipeline import ejecutar_ingesta

    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate-index", action="store_true", help="Borra y recrea la colección desde cero")
    args = parser.parse_args()

    chunks, _, _ = ejecutar_ingesta()
    n = index_chunks(chunks, recreate=args.recreate_index)
    print(f"[index] Indexados {n} chunks en la colección '{COLLECTION_NAME}'.")
