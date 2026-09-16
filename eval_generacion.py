"""
eval_generacion.py — Evaluación de la capa de generación con las preguntas
de queries/eval_preguntas.json.

Para cada pregunta, llama a responder() y comprueba:
  - si es "in-corpus": ¿ha respondido con contenido (no se ha abstenido)?
  - si es "fuera-de-corpus": ¿se ha abstenido correctamente?

Requiere que el índice ya esté construido con datos reales (python main.py --index).

Uso:
    python eval_generacion.py
"""
import json
import time

from config import QUERIES_DIR
from src.responder import responder
from google.genai.errors import ClientError

FRASE_ABSTENCION = "no lo sé, no está en los documentos"

# El tier gratuito de gemini-3.6-flash limita a 5 peticiones/minuto para
# generate_content. Usamos 4 (con margen) y esperamos ese tiempo entre
# preguntas; si aun así se agota la cuota, se espera 60s y se reintenta.
GENERATION_RPM_LIMIT = 4


def cargar_preguntas() -> list[dict]:
    path = QUERIES_DIR / "eval_preguntas.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def se_abstuvo(respuesta: str) -> bool:
    return FRASE_ABSTENCION in respuesta.lower()


def _responder_con_reintento(pregunta, intentos=3):
    for intento in range(intentos):
        try:
            return responder(pregunta)
        except ClientError as e:
            if getattr(e, "code", None) == 429 and intento < intentos - 1:
                print("   (límite de cuota, esperando 60s...)")
                time.sleep(60)
            else:
                raise


def evaluar() -> list[dict]:
    preguntas = cargar_preguntas()
    resultados = []

    for i, q in enumerate(preguntas):
        r = _responder_con_reintento(q["pregunta"])
        abstuvo = se_abstuvo(r["respuesta"])

        if q["tipo"] == "fuera-de-corpus":
            correcto = abstuvo  # debería abstenerse
        else:
            correcto = not abstuvo  # debería responder con contenido

        resultados.append({
            "id": q["id"],
            "tipo": q["tipo"],
            "pregunta": q["pregunta"],
            "respuesta": r["respuesta"],
            "fuentes": r["fuentes"],
            "se_abstuvo": abstuvo,
            "correcto": correcto,
        })

        estado = "✔" if correcto else "✘"
        print(f"{estado}  {q['id']:5} [{q['tipo']:15}] {q['pregunta'][:60]}")

        # Espera antes de la siguiente llamada a generate() (no hace falta
        # esperar después de la última pregunta).
        if i < len(preguntas) - 1:
            time.sleep(60 / GENERATION_RPM_LIMIT)

    return resultados


def resumen(resultados: list[dict]):
    total = len(resultados)
    aciertos = sum(1 for r in resultados if r["correcto"])
    print(f"\n===== RESUMEN =====")
    print(f"{aciertos}/{total} preguntas correctas (abstención/respuesta según correspondía)")


if __name__ == "__main__":
    resultados = evaluar()
    resumen(resultados)

    out_path = QUERIES_DIR / "eval_generacion_resultados.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en {out_path}")