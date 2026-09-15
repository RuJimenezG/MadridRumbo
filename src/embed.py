"""Generación de embeddings con OpenAI o Gemini.

Lee output/chunks.json, convierte cada chunk en un vector y guarda
output/embeddings.json. Expone embeddear_consulta() para el retriever.
"""

import json
import time
from pathlib import Path
# SKU de Google Gemini
from google import genai
from google.genai import types
from config import (
    CHUNKS_JSON,
    EMBED_BATCH_SIZE,
    EMBEDDING_MODEL,
    EMBEDDINGS_JSON,
    MAX_CHUNKS_EMBED,
    EMBED_RPM_LIMIT,
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL_OPENAI,
    OPENAI_API_KEY,
    EMBEDDING_MODEL_GEMINI,
    GEMINI_API_KEY,
)

# CORREGIDO (Persona 2): este import rompía TODO el fichero para cualquier
# proveedor, no solo Gemini, porque falla al cargar el módulo (antes de llamar
# a ninguna función). src/gemini_auth.py aún no existe en el repo. Lo hacemos
# robusto con try/except para no bloquear al resto del equipo mientras se
# termina ese fichero — @quien-lo-escribió: sustituye este bloque en cuanto
# subas gemini_auth.py, o dime y lo integro.
try:
    from .gemini_auth import configurar_gemini_api_key
except ImportError:
    def configurar_gemini_api_key():
        """Fallback temporal: no hace nada especial, genai.Client() ya puede
        recibir la api_key directamente. Sustituir por la versión real de
        gemini_auth.py en cuanto exista."""
        pass

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# =====================================================================
# Funciones de Gemini (pipeline chunks.json -> embeddings.json)
# — código del compañero, sin tocar —
# =====================================================================

def _extraer_vector(embedding_obj) -> list[float]:
    # Dependiendo de cómo devuelva el SDK el embedding el vector puede venir almacenado en un atributo llamado "values". Si existe ese atributo, extraemos sus valores y los convertimos explícitamente en una lista de números float.
    if hasattr(embedding_obj, "values"):
        return list(embedding_obj.values)
    # Si el objeto ya es iterable directamente, lo convertimos igualmente en una lista. Esta segunda posibilidad hace que la función sea compatible con distintas representaciones del resultado.
    return list(embedding_obj)


# Carga desde disco los chunks generados previamente por el pipeline de ingesta.
def cargar_chunks_json() -> list[dict]:
    # Antes de intentar leer el archivo, comprobamos que exista.
    if not CHUNKS_JSON.exists():
        raise FileNotFoundError(
            f"No existe {CHUNKS_JSON}. Ejecuta antes: python main.py --prepare"
        )

    # Leemos todo el contenido de chunks.json como texto UTF-8 y json.loads() lo convierte a estructuras normales de Python (diccionarios, listas, strings, etc.).
    data = json.loads(CHUNKS_JSON.read_text(encoding="utf-8"))
    # El pipeline guarda los chunks dentro de la clave "chunks". get("chunks", []) devuelve: la lista de chunks si existe o una lista vacía si la clave no está presente.
    return data.get("chunks", [])


def embeddear_textos(client: genai.Client, textos: list[str]) -> list[list[float]]:
    """Envía textos a Gemini en lotes y devuelve vectores en el mismo orden."""
    # Si no recibimos ningún texto, no es necesario llamar a Gemini.
    if not textos:
        return []
    # Aquí acumularemos todos los vectores generados. Cada elemento será una lista de float.
    vectores: list[list[float]] = []
    # Recorremos los textos por lotes.
    for inicio in range(0, len(textos), EMBED_BATCH_SIZE):
        # Extraemos el lote correspondiente.
        lote = textos[inicio: inicio + EMBED_BATCH_SIZE]
        # Lista de contenidos preparada para enviarse a la API.
        contents = [types.Content(parts=[types.Part(text=t)]) for t in lote]
        # Solicitamos a Gemini los embeddings del lote.
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=contents,
        )
        # result.embeddings contiene un embedding por cada texto enviado.
        # _extraer_vector() convierte cada embedding devuelto por el SDK en una lista normal de float.
        lote_vectores = [_extraer_vector(emb) for emb in result.embeddings]
        # Añadimos los vectores de este lote a la lista global, conservando el mismo orden que tenían los textos originales.
        vectores.extend(lote_vectores)
        # Se configura un tiempo de espera para no superar el límite de RPM del tier gratuito de Gemini
        if inicio + EMBED_BATCH_SIZE < len(textos):
            espera = 60 * len(lote) / EMBED_RPM_LIMIT
            time.sleep(espera)
    # Devolvemos todos los vectores generados.
    return vectores


def ejecutar_embeddings() -> tuple[list[dict], Path]:
    """chunks.json → vectores → embeddings.json."""
    # Configuramos primero la API key de Gemini.
    configurar_gemini_api_key()
    # Creamos el cliente que realizará las peticiones a la API.
    client = genai.Client()
    # Cargamos los chunks generados previamente durante la fase de preparación del corpus.
    chunks = cargar_chunks_json()
    # Guardamos el número total de chunks disponibles antes de aplicar cualquier límite.
    total_disponibles = len(chunks)
    # Si MAX_CHUNKS_EMBED tiene un valor configurado, reducimos el conjunto de chunks a procesar. Si es None, se procesan todos.
    if MAX_CHUNKS_EMBED is not None:
        chunks = chunks[:MAX_CHUNKS_EMBED]
    # Extraemos únicamente el texto de cada chunk.
    textos = [c["text"] for c in chunks]
    # Guardamos el instante justo antes de empezar la generación para poder medir cuánto tarda la operación completa.
    inicio = time.perf_counter()
    # Enviamos los textos a Gemini y obtenemos sus vectores.
    vectores = embeddear_textos(client, textos)
    # Calculamos el tiempo transcurrido. perf_counter() devuelve segundos, por eso multiplicamos por 1000 para expresarlo en milisegundos.
    latencia_ms = (time.perf_counter() - inicio) * 1000
    # Mostramos en consola:
    # - número de chunks procesados;
    # - tiempo empleado;
    # - modelo utilizado.
    print(
        f"Embeddings: {len(textos)} chunks en {latencia_ms:.0f} ms ({EMBEDDING_MODEL})"
    )
    # Si hemos procesado menos chunks de los que había originalmente, informamos de ello. Esto permite detectar fácilmente que MAX_CHUNKS_EMBED está limitando el procesamiento.
    if len(textos) < total_disponibles:
        print(f"  (de {total_disponibles} en {CHUNKS_JSON.name}; ver MAX_CHUNKS_EMBED)")
    # Construiremos una lista que relacione cada chunk original con su embedding correspondiente.
    items = []
    # zip() empareja cada chunk con su vector. Esto funciona correctamente porque embeddear_textos() conserva el orden de entrada.
    for chunk, vector in zip(chunks, vectores):
        # Para cada elemento conservamos:
        # - el texto original;
        # - su embedding;
        # - los metadatos del chunk.
        items.append(
            {
                "text": chunk["text"],
                "vector": vector,
                "metadata": chunk.get("metadata", {}),
            }
        )

    # Construimos la estructura completa que se guardará en embeddings.json.
    payload = {
        "embedding_model": EMBEDDING_MODEL,
        "total": len(items),
        "total_chunks_en_origen": total_disponibles,
        "dimensions": len(vectores[0]) if vectores else 0,
        # Lista con los textos, vectores y metadatos.
        "items": items,
    }

    # Nos aseguramos de que exista el directorio donde debe guardarse embeddings.json.
    # parents=True: crea también los directorios superiores necesarios.
    # exist_ok=True: no produce error si el directorio ya existe.
    EMBEDDINGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    # Serializamos el payload como JSON y lo escribimos en disco.
    EMBEDDINGS_JSON.write_text(
        json.dumps(
            # Estructura Python que queremos convertir a JSON.
            payload,
            # Conserva directamente caracteres como ñ, á, é, etc. en lugar de convertirlos a secuencias Unicode.
            ensure_ascii=False,
            # Añade sangría para que el archivo resulte legible.
            indent=2,
        ),
        # Guardamos el fichero utilizando codificación UTF-8.
        encoding="utf-8",
    )

    # Informamos por consola de:
    # - dónde se ha guardado el archivo;
    # - cuántas dimensiones tiene cada embedding.
    print(f"  Guardado: {EMBEDDINGS_JSON} ({payload['dimensions']} dimensiones)")
    # Devolvemos:
    # 1. La lista de elementos con texto, embedding y metadata.
    # 2. La ruta del archivo embeddings.json generado.
    return items, EMBEDDINGS_JSON


# =====================================================================
# Mi parte (Persona 2): embed_texts() — interfaz usada por index.py/retrieve.py
# Arquitectura ChromaDB, independiente del pipeline chunks.json de arriba.
# Solo dos proveedores soportados: "openai" y "gemini".
# =====================================================================

def _embed_gemini_directo(texts: list[str]) -> list[list[float]]:
    """
    Gemini para embed_texts() (arquitectura ChromaDB), en lotes, respetando
    EMBED_RPM_LIMIT. Usa GEMINI_API_KEY/EMBEDDING_MODEL_GEMINI directamente,
    sin depender de gemini_auth.py, para no acoplarme al pipeline de arriba.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    client = genai.Client(api_key=GEMINI_API_KEY)
    vectores: list[list[float]] = []

    for inicio in range(0, len(texts), EMBED_BATCH_SIZE):
        lote = texts[inicio: inicio + EMBED_BATCH_SIZE]
        result = client.models.embed_content(model=EMBEDDING_MODEL_GEMINI, contents=lote)
        vectores.extend(_extraer_vector(emb) for emb in result.embeddings)
        if inicio + EMBED_BATCH_SIZE < len(texts):
            time.sleep(60 * len(lote) / EMBED_RPM_LIMIT)

    return vectores


def _embed_openai(texts: list[str]) -> list[list[float]]:
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY en el .env")
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model=EMBEDDING_MODEL_OPENAI, input=texts)
    return [d.embedding for d in resp.data]


def embed_texts(texts: list[str], fit_tfidf: bool = False) -> list[list[float]]:
    """Devuelve una lista de vectores de embedding, uno por texto de entrada.

    Proveedores soportados: "openai" y "gemini" (EMBEDDING_PROVIDER en .env).
    `fit_tfidf` se mantiene en la firma por compatibilidad con index.py, pero
    no se usa (no hay proveedor tfidf en esta versión).
    """
    if EMBEDDING_PROVIDER == "gemini":
        return _embed_gemini_directo(texts)
    elif EMBEDDING_PROVIDER == "openai":
        return _embed_openai(texts)
    else:
        raise ValueError(
            f"EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r} no soportado. "
            f"Usa 'openai' o 'gemini' en tu .env."
        )


if __name__ == "__main__":
    vecs = embed_texts(["¿Cuánto cuesta el Abono Joven?", "Zonas tarifarias de Madrid"])
    print(f"Generados {len(vecs)} vectores de dimensión {len(vecs[0])}")
