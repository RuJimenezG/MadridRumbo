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