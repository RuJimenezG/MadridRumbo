
from functools import lru_cache
import sys
import pickle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import EMBEDDING_PROVIDER, EMBEDDING_MODEL_LOCAL, EMBEDDING_MODEL_OPENAI, OPENAI_API_KEY, CHROMA_DIR

_TFIDF_VECTORIZER_PATH = CHROMA_DIR / "tfidf_vectorizer.pkl"


@lru_cache(maxsize=1)
def _get_local_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_LOCAL)


def _tfidf_fit_and_save(texts: list[str]):
    """Ajusta el vectorizador TF-IDF sobre el corpus completo y lo persiste en disco
    para que las consultas posteriores (retrieve) usen el mismo espacio vectorial."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    vectorizer = TfidfVectorizer(max_features=512)
    vectorizer.fit(texts)
    with open(_TFIDF_VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    return vectorizer


def _tfidf_load():
    if not _TFIDF_VECTORIZER_PATH.exists():
        raise RuntimeError(
            "No existe un vectorizador TF-IDF ajustado. Ejecuta primero: python main.py --index"
        )
    with open(_TFIDF_VECTORIZER_PATH, "rb") as f:
        return pickle.load(f)


def embed_texts(texts: list[str], fit_tfidf: bool = False) -> list[list[float]]:
    """Devuelve una lista de vectores de embedding, uno por texto de entrada.

    `fit_tfidf`: si True y el proveedor es "tfidf", ajusta el vectorizador sobre
    `texts` (se usa únicamente durante la indexación, con el corpus completo).
    """
    if EMBEDDING_PROVIDER == "openai":
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.embeddings.create(model=EMBEDDING_MODEL_OPENAI, input=texts)
        return [d.embedding for d in resp.data]
    elif EMBEDDING_PROVIDER == "tfidf":
        vectorizer = _tfidf_fit_and_save(texts) if fit_tfidf else _tfidf_load()
        return vectorizer.transform(texts).toarray().tolist()
    else:
        model = _get_local_model()
        return model.encode(texts, show_progress_bar=False).tolist()


if __name__ == "__main__":
    vecs = embed_texts(["¿Cuánto cuesta el Abono Joven?", "Zonas tarifarias de Madrid"])
    print(f"Generados {len(vecs)} vectores de dimensión {len(vecs[0])}")
