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
| `main.py` | CLI completa: `--prepare`, `--index`, `--query`, `--ask`. Conecta todo el pipeline. |
| `config.py` (mi bloque) | `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL_OPENAI`, `EMBEDDING_MODEL_GEMINI`, `TOP_K`, `MAX_CHUNKS`, `COLLECTION_NAME`. |
| `eval_retrieval.py` + `queries/eval_preguntas.json` | Evaluación de retrieval comparando distintos valores de K. |

*(`src/embed.py` también contiene el pipeline de un compañero basado en `chunks.json`/`embeddings.json`; no es mío, no lo he tocado.)*

## Cómo funciona el pipeline completo ahora

```bash
python main.py --prepare              # ingesta (load→clean→chunk) + embeddings.json (Gemini)
python main.py --index                # (re)indexa el corpus en ChromaDB — offline
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

## Los 7 bugs reales que encontré y corregí (en dos rondas)

**Ronda 1 — embeddings/config:**
1. `config.py` no importaba `os` ni llamaba a `load_dotenv()` → `NameError` en cualquier `os.getenv(...)`.
2. Import roto `from .gemini_auth import configurar_gemini_api_key` en `embed.py` (el fichero no existía aún) → rompía la carga de *todo* el módulo. Corregido con `try/except`.
3. CSV real con delimitador `;` y encoding Latin-1, no `,`/UTF-8.

**Ronda 2 — integración de `main.py`:**
4. `src/index.py` importaba la clase `Chunk`, que ya no existe (el `chunk.py` real usa `Document` de LangChain) → rompía en cascada `retrieve.py` y `generate.py`. Reescrito para trabajar con `Document`.
5. `config.py` no tenía `COLLECTION_NAME`, que `index.py` necesita.
6. `MAX_CHUNKS` insuficiente dos veces: primero 500→12.000, y de nuevo 12.000→25.000 al confirmar que el pipeline real genera **22.491 chunks** (22.404 solo del CSV, una fila = un chunk).
7. `generate.py` creaba el cliente de Gemini al importar el módulo → bloqueaba `--prepare`/`--index`/`--query` sin `GEMINI_API_KEY`, aunque no se fuera a usar `--ask`. Solucionado con import en `main.py`.

## Evaluación de retrieval

```bash
python eval_retrieval.py --k 1 3
```

| K | Aciertos in-corpus (de 11) |
|---|---|
| 1 | 4 |
| 3 | 5 (con TF-IDF, solo como prueba de metodología) |

**Pendiente:** repetir esta evaluación con `EMBEDDING_PROVIDER=openai` o `gemini` (el código final ya no incluye TF-IDF) para tener el número definitivo antes de la entrega.

## Recomendación pendiente para el equipo

Indexar las 22.404 paradas del CSV fila a fila es mucho volumen para un asistente de tarifas/abonos, y sube el coste/tiempo de generar embeddings. Vale la pena discutir si conviene agregar el CSV (por zona o línea) antes de indexar, en vez de una fila = un chunk.

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