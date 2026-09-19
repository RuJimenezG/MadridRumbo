"""Funciones auxiliares del proyecto MadridRumbo."""

import json

from google import genai
from google.genai import types

from config import CHUNKS_JSON, EMBEDDING_MODEL
from .model_auth import configurar_gemini_api_key


def contar_tokens_chunks() -> int:
    """Cuenta los tokens de todos los textos almacenados en chunks.json."""

    # Comprobamos que exista el archivo generado durante la ingesta.
    if not CHUNKS_JSON.exists():
        raise FileNotFoundError(
            f"No existe {CHUNKS_JSON}. Ejecuta antes: python main.py --prepare"
        )

    # Cargamos el contenido de chunks.json.
    data = json.loads(CHUNKS_JSON.read_text(encoding="utf-8"))

    # Extraemos únicamente el texto de cada chunk.
    textos = [chunk["text"] for chunk in data.get("chunks", [])]

    if not textos:
        return 0

    # Configuramos la API key y creamos el cliente de Gemini.
    configurar_gemini_api_key()
    client = genai.Client()

    total_tokens = 0

    # Contamos en lotes pequeños para no enviar todo el corpus
    # en una única petición.
    batch_size = 20

    for inicio in range(0, len(textos), batch_size):
        lote = textos[inicio : inicio + batch_size]

        # Cada texto se representa como un Content independiente,
        # de la misma forma conceptual que durante el embedding.
        contents = [
            types.Content(parts=[types.Part(text=texto)])
            for texto in lote
        ]

        # Gemini ejecuta únicamente su tokenizador y devuelve
        # el número total de tokens del lote.
        resultado = client.models.count_tokens(
            model=EMBEDDING_MODEL,
            contents=contents,
        )

        total_tokens += resultado.total_tokens

    print(f"Chunks analizados: {len(textos)}")
    print(f"Tokens totales: {total_tokens:,}")
    print(f"Media tokens/chunk: {total_tokens / len(textos):.2f}")

    return total_tokens