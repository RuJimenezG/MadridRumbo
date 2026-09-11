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
- Embed                 -> embed.py - Pendiente
- Index (ChromaDB)      -> index.py - Pendiente

### Instrucciones

Para generar los chunks:
- Instalar dependencias
```
pip install -r requirements.txt
```

- Ejecutar desde el directorio principal:
```
python main.py --prepare
```


