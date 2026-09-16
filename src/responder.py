"""
responder.py — Une retrieve() + generate() en una única función reutilizable,
sin depender de si la usa el CLI o Streamlit.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TOP_K
from src.retrieve import retrieve
from src.generate import generate


def responder(pregunta: str, k: int = TOP_K) -> dict:
    """Responde una pregunta usando el corpus. Devuelve texto + fuentes usadas."""
    chunks = retrieve(pregunta, k=k)
    respuesta = generate(pregunta, chunks)
    fuentes = sorted(set(c.source for c in chunks))
    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "fuentes": fuentes,
        "k": k,
        "num_chunks": len(chunks),
    }


def rag_ask(consulta: str) -> str:
    """Versión simplificada para el futuro proyecto de Agentes: solo el texto."""
    return responder(consulta)["respuesta"]