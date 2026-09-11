"""
index.py — Indexación de chunks en ChromaDB persistente.

ChromaDB guarda embeddings + metadatos (`source`, `chunk_id`) para poder
mostrar la procedencia de cada chunk recuperado y, si hace falta, regenerar
el índice desde cero (--recreate-index) tras cambiar de modelo de embeddings
o de MAX_CHUNKS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chromadb
from config import CHROMA_DIR, COLLECTION_NAME, MAX_CHUNKS
from src.chunk import Chunk
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


def index_chunks(chunks: list[Chunk], recreate: bool = False) -> int:
    """Indexa una lista de chunks en ChromaDB. Devuelve el número de chunks indexados."""
    if len(chunks) > MAX_CHUNKS:
        from collections import Counter
        perdidos = Counter(c.source for c in chunks[MAX_CHUNKS:])
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

    ids = [f"{c.source}::{c.chunk_id}" for c in chunks]
    texts = [c.text for c in chunks]
    metadatas = [{"source": c.source, "chunk_id": c.chunk_id} for c in chunks]

    # Chroma requiere embeddings explícitos si no se configura un embedding_function propio.
    # fit_tfidf=True: si el proveedor es "tfidf", ajusta el vectorizador sobre todo el corpus aquí.
    embeddings = embed_texts(texts, fit_tfidf=True)

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
    from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
    from src.load import load_documents
    from src.chunk import chunk_documents

    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate-index", action="store_true", help="Borra y recrea la colección desde cero")
    args = parser.parse_args()

    docs = load_documents(DATA_DIR)
    chunks = chunk_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    n = index_chunks(chunks, recreate=args.recreate_index)
    print(f"[index] Indexados {n} chunks de {len(docs)} documentos en la colección '{COLLECTION_NAME}'.")
