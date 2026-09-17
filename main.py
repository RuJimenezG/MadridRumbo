"""Punto de entrada por línea de comandos de MadridRumbo.

Uso:
  python main.py --prepare              -> carga, limpia y fragmenta el corpus (chunks.json)
  python main.py --index                -> (re)indexa el corpus en ChromaDB (offline)
  python main.py --index --recreate-index  -> borra y recrea la colección desde cero
  python main.py --query "..."          -> solo retrieval (sin LLM), muestra el contexto
  python main.py --ask "..."            -> RAG completo: retrieval + generación (Gemini)
  python main.py --ask "..." --k 6

CORREGIDO (Persona 2): antes solo existía --prepare, que ejecutaba la ingesta
y el pipeline de embeddings.json de Gemini, pero nunca llegaba a poblar
ChromaDB. Como generate.py espera chunks de retrieve.py (que lee de
ChromaDB), sin --index el sistema nunca podía responder a --ask. Añadidos
--index, --query y --ask para cerrar el ciclo completo.
"""
import argparse

from src.pipeline import ejecutar_ingesta
from src.embed import ejecutar_embeddings
from src.index import index_chunks
from src.retrieve import retrieve, format_context
# CORREGIDO (Persona 2): "from src.generate import generate" aquí arriba
# rompía --prepare, --index y --query sin GEMINI_API_KEY configurada, porque
# generate.py crea el cliente de Gemini al importar el módulo (no dentro de
# una función). Se importa solo dentro de _cmd_ask(),
# para que el resto de comandos funcionen sin esa clave.


def _cmd_prepare() -> None:
    """Ingesta (load->clean->chunk->chunks.json) + pipeline de embeddings.json de Gemini."""
    ejecutar_ingesta()
    print()
    ejecutar_embeddings()


def _cmd_index(recreate: bool) -> None:
    """Ingesta + indexación en ChromaDB (necesario antes de --query o --ask)."""
    chunks, _, _ = ejecutar_ingesta()
    print()
    n = index_chunks(chunks, recreate=recreate)
    print(f"[main] Indexados {n} chunks en ChromaDB.")


def _cmd_query(pregunta: str, k: int) -> None:
    """Solo retrieval: muestra el contexto recuperado, sin llamar al LLM."""
    chunks = retrieve(pregunta, k=k)
    print(f"\nPREGUNTA: {pregunta}")
    print(f"\n--- CONTEXTO RECUPERADO (top-{k}) ---\n")
    print(format_context(chunks))
    print("\nFUENTES:", sorted({c.source for c in chunks}))


def _cmd_ask(pregunta: str, k: int) -> None:
    """RAG completo: retrieval (ChromaDB) + generación (Gemini), con abstención si no hay evidencia."""
    from src.responder import responder
    resultado = responder(pregunta, k=k)
    print(f"\nPREGUNTA: {pregunta}\n")
    print(f"RESPUESTA:\n{resultado['respuesta']}\n")
    print("FUENTES:", resultado["fuentes"])


def main() -> None:
    """Ejecuta el comando solicitado desde la línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="MadridRumbo",
        description="Asistente RAG sobre transporte público de Madrid.",
    )
    parser.add_argument("--prepare", action="store_true", help="Ingesta + embeddings.json (Gemini)")
    parser.add_argument("--index", action="store_true", help="Indexa el corpus en ChromaDB (offline)")
    parser.add_argument("--recreate-index", action="store_true", help="Borra y recrea la colección al indexar")
    parser.add_argument("--query", type=str, help="Solo retrieval: muestra el contexto recuperado")
    parser.add_argument("--ask", type=str, help="RAG completo: retrieval + generación")
    parser.add_argument("--k", type=int, default=4, help="Número de chunks a recuperar (default=4)")

    args = parser.parse_args()

    if not any([args.prepare, args.index, args.query, args.ask]):
        parser.print_help()
        return

    if args.prepare:
        _cmd_prepare()

    if args.index:
        _cmd_index(recreate=args.recreate_index)

    if args.query:
        _cmd_query(args.query, k=args.k)

    if args.ask:
        _cmd_ask(args.ask, k=args.k)


if __name__ == "__main__":
    main()
