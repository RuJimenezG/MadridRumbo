"""Punto de entrada por línea de comandos de MadridRumbo.

Uso:
  python main.py --prepare -> carga, limpia y fragmenta el corpus documental.
"""

import argparse

from src.pipeline import ejecutar_ingesta

def _cmd_prepare() -> None:
    ejecutar_ingesta()
    print()


def main() -> None:
    """Ejecuta el comando solicitado desde la línea de comandos."""
    # Creamos el parser
    parser = argparse.ArgumentParser(
        prog="MadridRumbo",
        description="Asistente RAG sobre transporte público de Madrid.",
    )
    parser.add_argument("--prepare", action="store_true")
    
    # Procesamos los argumentos recibidos.
    args = parser.parse_args()

    # Ejecutamos la operación correspondiente al comando indicado.
    if args.prepare:
        _cmd_prepare()

if __name__ == "__main__":
    main()
