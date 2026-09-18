# MadridRumbo
> **Project Break · Sprints 08–10 | AI Engineering Bootcamp**
> **Grupo 3:** Rubén Jiménez Gutiérrez, Guzmán López Barceló, José Manuel Gil Ruiz.

Proyecto de sistema RAG para un asistente sobre tarifas, zonas, abonos y condiciones de viaje (p. ej. CRTM / Metro / Cercanías).


## Corpus
> Sección en construcción
Todas las fuentes se han descargado el día 07/09/2026:
- Paradas CRTM.csv
  - Fuente: https://datos.crtm.es/search?type=CSV%2520Collection
  - Seleccionado de cada colección de GTFS los archivos stops.txt y unificados en un solo csv tratado para eliminar filas innecesarias.
- crtm_billetes_tarifas.md
  - Fuente: https://www.crtm.es/billetes-y-tarifas/
  - Scrapeada la información relevante.
- crtm_faq.md
  - Fuente: https://www.crtm.es/billetes-y-tarifas/preguntas-frecuentes/
  - Scrapeada de la web.
- https://www.crtm.es/media/sjqj4ggj/bocm-20251231-tarifas_transporte.pdf
- https://www.crtm.es/media/s1qi0nmo/bocm-20251231-precios_transporte.pdf

---

## Proceso de carga e indexado:
- ORQUESTADOR           -> pipeline.py - ✅
- Cargar                -> load.py  - ✅
- Limpiar y normalizar  -> clean.py - ✅
- Chunk                 -> chunk.py - ✅
- Embed                 -> embed.py - ✅
- Index (ChromaDB)      -> index.py - Pendiente

### Instrucciones

Para generar los chunks y los embeddings:
- Instalar dependencias
```
pip install -r requirements.txt
```

- Ejecutar desde el directorio principal:
```
python main.py --prepare
```

Para descargar los embeddings entrar en el repo de Github, ir a Releases > Embeddings CRTM - desarrollo v1 > Assets, descargar embeddings.zip y descomprimirlo en la carpeta output/.

#### DevLog: al ejecutar el embeddind del corpus se obtiene un error 429
```
google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/embed_content_free_tier_requests, limit: 100, model: gemini-embedding-2\nPlease retry in 37.411097012s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/embed_content_free_tier_requests', 'quotaId': 'EmbedContentRequestsPerMinutePerUserPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-embedding-2'}, 'quotaValue': '100'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '37s'}]}}
```

Para seguir usando la capa gratuita (al menos en pruebas) sin tocar mucho los límites de chunks, filas del csv etc... se introduce un rate limiter en el código de la función de embeddear_texto() y se hacen algunas pruebas.

- Límites del modelo gemini-embedding-2 - Free Tier
  - RPM 100, TPM 30K, RPD 1K

El corpus genera en total 22.491 chunks. Conclusión: no es posible continuar con el free tier.

- Límites del modelo gemini-embedding-2 - Tier 1
  - RPM 3K, TPM 100K, RPD Ilimitado

El Tier 1 debería ser suficiente.

## utils.py
Este archivo contiene utilidades:
- contar_tokens_chunks(): función para contar los tokens que se van a consumir al embedear los chunks 
  - Se obtiene: 
´´´
Chunks analizados: 22491
Tokens totales: 2,836,469
Media tokens/chunk: 126.12
´´´
La facturación es de 0,20 $ por millon de tokens.

# Parte 2: Embeddings, ChromaDB, Retrieval y conexión de `main.py`

> **Persona 2 — MadridRumbo (Project Break RAG Engineering)**
> Pipeline: `Chunk → Embeddings → ChromaDB → Retrieval → (main.py) → Generación`

## Ficheros de los que soy responsable

| Fichero | Descripción |
|---|---|
| `src/embed.py` (función `embed_texts()`) | Embeddings con proveedor intercambiable: `openai` o `gemini`, misma interfaz. |
| `src/index.py` | Indexa los `Document` (de `chunk.py`) en ChromaDB persistente. `--recreate-index` para regenerar el índice. |
| `src/retrieve.py` | Recupera los top-k chunks más relevantes y los formatea como contexto. |
| `main.py` | CLI completa: `--prepare`, `--index`, `--query`, `--ask`. Conecta todo el pipeline, y reutiliza `output/chunks.json` en `--index` si ya existe (evita repetir la ingesta completa cada vez). |
| `config.py` (mi bloque) | `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL_OPENAI`, `EMBEDDING_MODEL_GEMINI`, `TOP_K`, `MAX_CHUNKS`, `COLLECTION_NAME`. |
| `eval_retrieval.py` + `queries/eval_preguntas.json` | Evaluación de retrieval comparando distintos valores de K. |

*(`src/embed.py` también contiene el pipeline de un compañero basado en `chunks.json`/`embeddings.json`; no es mío, no lo he tocado.)*

## Cómo funciona el pipeline completo ahora

```bash
python main.py --prepare              # ingesta (load→clean→chunk) + embeddings.json (Gemini)
python main.py --index                # (re)indexa el corpus en ChromaDB — offline
                                       # reutiliza output/chunks.json si ya existe
python main.py --index --recreate-index
python main.py --query "¿Qué es la Tarjeta Azul?"     # solo retrieval, sin LLM
python main.py --ask "¿Qué es la Tarjeta Azul?"        # RAG completo (ChromaDB + Gemini)
python main.py --ask "¿Qué es la Tarjeta Azul?" --k 6
```

```text
Documentos → load+clean+chunk (Persona 1) → embed_texts() (yo) → ChromaDB (yo)
                                                                       ↓
                                                          retrieve() top-k (yo)
                                                                       ↓
                                                  generate() con Gemini (Persona 3) → respuesta
```

## Proveedores de embeddings

Controlado por `EMBEDDING_PROVIDER` en `.env`:
- **`openai`**: `text-embedding-3-small`. Requiere `OPENAI_API_KEY`.
- **`gemini`**: `gemini-embedding-2`. Requiere `GEMINI_API_KEY`. En lotes de `EMBED_BATCH_SIZE`, con espera automática para no superar `EMBED_RPM_LIMIT`.

## Los 9 bugs reales que encontré y corregí (en tres rondas)

**Ronda 1 — embeddings/config:**
1. `config.py` no importaba `os` ni llamaba a `load_dotenv()` → `NameError` en cualquier `os.getenv(...)`.
2. Import roto `from .gemini_auth import configurar_gemini_api_key` en `embed.py` (el fichero no existía aún) → rompía la carga de *todo* el módulo. Corregido con `try/except`.
3. CSV real con delimitador `;` y encoding Latin-1, no `,`/UTF-8.

**Ronda 2 — integración de `main.py`:**
4. `src/index.py` importaba la clase `Chunk`, que ya no existe (el `chunk.py` real usa `Document` de LangChain) → rompía en cascada `retrieve.py` y `generate.py`. Reescrito para trabajar con `Document`.
5. `config.py` no tenía `COLLECTION_NAME`, que `index.py` necesita.
6. `MAX_CHUNKS` insuficiente dos veces: primero 500→12.000, y de nuevo 12.000→25.000 al confirmar que el pipeline real genera **22.491 chunks** (22.404 solo del CSV, una fila = un chunk).
7. `generate.py` creaba el cliente de Gemini al importar el módulo → bloqueaba `--prepare`/`--index`/`--query` sin `GEMINI_API_KEY`, aunque no se fuera a usar `--ask`. Solucionado con import perezoso en `main.py`.

**Ronda 3 — caché de embeddings e ingesta:**
8. `_cargar_embeddings_json()` (añadida por un compañero para reutilizar embeddings ya calculados) buscaba un fichero (`embeddings-{provider}.json`) que nunca se genera con ese nombre, y además solo comparaba la **cantidad** de chunks, no el **contenido** — riesgo de indexar pares (texto, vector) equivocados si el recuento coincidía por casualidad. Corregido: nombre real del fichero + validación texto a texto antes de reutilizar el caché.
9. `_cmd_index()` en `main.py` repetía toda la ingesta (incluida la lectura del CSV de 22.404 filas y los 2 PDFs) cada vez que se indexaba. Ahora reutiliza `output/chunks.json` si ya existe, reconstruyendo los `Document` con LangChain, y solo ejecuta la ingesta completa si el fichero no existe.

## Evaluación de retrieval

```bash
python eval_retrieval.py --k 1 3
```

| K | Aciertos in-corpus (de 11) | Proveedor |
|---|---|---|
| 1 | 3 | Real (`queries/eval_retrieval_resultados.json`) |
| 3 | 3 | Real (`queries/eval_retrieval_resultados.json`) |

**Confirmado con datos reales (no solo TF-IDF):** subir K de 1 a 3 **no mejora nada** — el resultado es idéntico. Diagnóstico: 7 de las 11 preguntas in-corpus recuperan **solo filas del CSV de paradas**, incluso preguntas de FAQ puras. El problema no es la calidad del embedding, es el volumen: el CSV es ~9.700-22.400 de los ~9.800-22.500 chunks totales del corpus (según la versión de `load.py`), y domina el espacio vectorial frente a las ~90 chunks de FAQ/PDFs que sí contienen las respuestas.

## Recomendación para el equipo sobre el CSV (con propuesta ya lista)

Indexar las paradas del CSV en tanto detalle es lo que está ahogando el retrieval. Tengo una propuesta probada que agrupa por zona tarifaria + tipo de transporte, guardando solo los nombres de las paradas (no el detalle completo de cada una):

- Filas originales: 22.404
- Chunks con 1 fila = 1 chunk: 22.404
- Chunks agrupando por zona con todo el detalle (aproximación de un compañero, en progreso): 9.927
- **Chunks agrupando por zona con solo nombres (mi propuesta, probada): 37**

Pendiente de decidir en equipo: si se adopta la versión compacta (37 chunks) para el RAG semántico, y se deja el CSV completo aparte como fuente de una futura *tool* de búsqueda exacta de paradas (Project Break de Agentes), en vez de intentar resolverlo todo con retrieval semántico.

## Cómo probar mi parte

```bash
pip install -r requirements.txt
cp .env.example .env      # rellena OPENAI_API_KEY o GEMINI_API_KEY
python main.py --index --recreate-index
python main.py --ask "¿Qué es la Tarjeta Azul?"
python eval_retrieval.py --k 1 3
```

## Estado

✅ Completo: embeddings, ChromaDB, retrieval, y `main.py` conectando todo el ciclo `--prepare → --index → --ask`. Probado con la ingesta real (22.491 chunks) usando embeddings simulados (sin gastar cuota de API); pendiente de que el equipo lo valide con `GEMINI_API_KEY`/`OPENAI_API_KEY` reales antes de la entrega final.

# Parte 3 y 4: Generación, evaluación, API interna y Streamlit

> **Persona 3 — MadridRumbo (Project Break RAG Engineering)**
> Pipeline: `Retrieval (ChromaDB) → Generación (Gemini) → responder()/rag_ask() → Evaluación → Streamlit`

## Ficheros de los que soy responsable

| Fichero | Descripción |
|---|---|
| `src/generate.py` | Generación con Gemini a partir del contexto recuperado. Prompt con abstención explícita si el contexto no contiene la respuesta. |
| `src/responder.py` | `responder(pregunta, k) -> dict` (API interna) y `rag_ask(consulta) -> str`. Une `retrieve()` + `generate()`, mide tiempo y hace el logging básico. |
| `eval_generacion.py` + `queries/eval_preguntas.json` | Evaluación de generación (15 preguntas, incluye casos fuera de corpus) con reintentos y guardado incremental de resultados. |
| `main.py` (`_cmd_ask`) | Corregido para que `--ask` pase por `responder()` en vez de llamar a `retrieve`/`generate` por separado. |
| `app.py` | Interfaz Streamlit: chat, contexto/fuentes recuperadas visibles y tabla de métricas. |
| `assets/icono.png` | Identidad visual de la app (diseño propio). |

## Cómo funciona mi parte del pipeline

```bash
python main.py --ask "¿Qué es un abono transporte?"      # RAG completo con logging
python eval_generacion.py                                  # evaluación de generación
python -m streamlit run app.py                              # interfaz
```

`responder()` centraliza retrieval + generación + logging, para que tanto el CLI como Streamlit usen exactamente el mismo camino y queden registrados igual en `rag.log` (pregunta, k, nº chunks, tiempo, modelo).

## Los bugs reales que encontré y corregí

**Evaluación de generación:**
1. `429 RESOURCE_EXHAUSTED` tratado solo como límite por minuto → resultó haber también un límite **diario** de generación (20/día) que ninguna espera soluciona; documentado y manejado por separado.
2. `503 UNAVAILABLE` (servidor saturado) no se capturaba, solo `ClientError` → ampliado a `APIError` con `code in (429, 503)`.
3. `eval_generacion.py` perdía todo el progreso si fallaba a mitad de las 15 preguntas → reescrito con guardado incremental tras cada pregunta.
4. Una pregunta válida sobre tarifas se respondía con abstención → diagnostiqué que las tablas de los PDFs pierden su estructura al extraerse como texto plano; no es un bug de mi código, se documenta como limitación conocida del corpus.
5. `_cmd_ask()` en `main.py` no pasaba por `responder()`, así que el logging que pide el enunciado (pregunta/k/chunks/tiempo/modelo) nunca se generaba con `--ask` → corregido.

**Soporte al equipo (bloqueaban mi evaluación):**
6. `SyntaxError: 'return' outside function` en `src/embed.py` por una indentación perdida al aplicar un parche de reintentos, detectado al validar una rama de un compañero antes de fusionarla.
7. Los reintentos de embeddings insistían aunque el error fuera de cuota **diaria** (no se recupera esperando) → añadida distinción entre error por minuto (reintentar) y por día (parar).

## Evaluación

- **Retrieval:** con `eval_retrieval.py` (K=1 y K=3) solo 3 de 11 preguntas in-corpus recuperan la fuente esperada. Diagnóstico con datos reales: el CSV de paradas es el 99,6% de los chunks del corpus y aparece en casi el 100% de las búsquedas, tapando a las FAQ/PDFs aunque no tengan relación con la pregunta.
- **Generación:** evaluación de las 15 preguntas de `eval_preguntas.json` en curso; aún no completa por el límite diario de generación (20 peticiones/día del free tier), que corta el proceso a mitad.


## Cómo probar mi parte

```bash
pip install -r requirements.txt
cp .env.example .env      # rellena GEMINI_API_KEY
python main.py --index --recreate-index
python main.py --ask "¿Qué es un abono transporte?"
python eval_generacion.py
python -m streamlit run app.py
```

## Estado

✅ Completo: generación con abstención, API interna (`responder`/`rag_ask`), CLI `--ask` con logging, interfaz Streamlit (chat + contexto + métricas).
⏳ Pendiente: terminar la evaluación de generación de las 15 preguntas (límite diario de cuota), decidir en equipo el filtro de `retrieve.py`, y el informe de decisiones final.
