# Resumen de experimentos de chunking — MadridRumbo

## 1. Objetivo

El objetivo de estos experimentos es evaluar el efecto de distintas configuraciones de `CHUNK_SIZE` y `CHUNK_OVERLAP` sobre la fragmentación del corpus y la calidad del retrieval de MadridRumbo.

Se compararon tres configuraciones:

- `800 / 100`: configuración baseline.
- `400 / 50`: chunks más pequeños y mayor granularidad.
- `1200 / 150`: chunks más grandes y mayor cantidad de contexto.

En los tres casos se mantuvo aproximadamente el mismo porcentaje de solapamiento, un 12,5 %.

Para hacer comparables los resultados se mantuvieron constantes el corpus, el modelo de embeddings (`gemini-embedding-2`), la base vectorial ChromaDB y `K = 3` durante la evaluación principal.

`Paradas CRTM.csv` utiliza una estrategia específica: las paradas se agrupan por tipo de transporte y zona tarifaria en bloques de hasta seis paradas. Estos bloques no pasan por `RecursiveCharacterTextSplitter`, por lo que los cambios de `CHUNK_SIZE` y `CHUNK_OVERLAP` afectan principalmente a las fuentes documentales Markdown y PDF.

---

## 2. Preguntas utilizadas en la comparación

Se seleccionó el mismo subconjunto de siete preguntas en los tres experimentos:

| ID | Fuente esperada | Objetivo |
|---|---|---|
| q01 | `crtm_faq.md` | Información localizada en FAQ |
| q03 | `crtm_billetes_tarifas.md` | Información concreta sobre zonas |
| q05 | `crtm_faq.md` | Respuesta explicativa en FAQ |
| q08 | `crtm_billetes_tarifas.md` | Evidencia con varios porcentajes |
| q09 | `bocm-20251231-precios_transporte.pdf` | Recuperación desde PDF |
| q10 | `bocm-20251231-tarifas_transporte.pdf` | Evidencia formada por varios datos relacionados |
| q11 | `Paradas CRTM.csv` | Caso de control sobre el CSV |

Se midieron los siguientes indicadores:

- **Source hit @3**: la fuente esperada aparece entre los tres primeros resultados.
- **Evidence hit @3**: los tres primeros resultados contienen la evidencia necesaria para responder según el criterio de evaluación.
- **Top-1 esperado**: la fuente esperada aparece en primera posición.
- **Posición media**: posición media de la fuente esperada cuando aparece dentro del Top-3.

---

## 3. Experimento 800 / 100

### Efecto sobre el corpus

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3835 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks documentales | 87 |
| Chunks `crtm_faq.md` | 36 |
| Chunks `crtm_billetes_tarifas.md` | 20 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 17 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 14 |
| Tamaño medio global | 549,69 caracteres |
| Mediana global | 597 caracteres |
| Tamaño mínimo global | 119 caracteres |
| Tamaño máximo global | 801 caracteres |
| Tamaño medio documental | 549,69 caracteres |
| Mediana documental | 597 caracteres |
| Tamaño mínimo documental | 119 caracteres |
| Tamaño máximo documental | 801 caracteres |

### Retrieval

| ID | Source hit | Evidence hit | Posición fuente esperada |
|---|:---:|:---:|---:|
| q01 | Sí | Sí | 3 |
| q03 | Sí | Sí | 1 |
| q05 | Sí | Sí | 1 |
| q08 | Sí | Sí | 2 |
| q09 | Sí | Sí | 3 |
| q10 | Sí | No | 1 |
| q11 | Sí | Sí | 1 |

### Resumen

| Métrica | Resultado |
|---|---:|
| Source hit @3 | 7/7 (100 %) |
| Evidence hit @3 | 6/7 (85,7 %) |
| Top-1 esperado | 4/7 (57,1 %) |
| Posición media | 1,71 |

El principal fallo es q10. Aunque se recupera la fuente esperada en primera posición, el fragmento no contiene toda la evidencia necesaria.

Como prueba adicional se aumentó el retrieval a `K = 4` y `K = 5`. La evidencia correcta de q10 siguió sin recuperarse, por lo que el problema no se resuelve simplemente ampliando el número de resultados.

---

## 4. Experimento 400 / 50

### Efecto sobre el corpus

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3933 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks documentales | 185 |
| Chunks `crtm_faq.md` | 79 |
| Chunks `crtm_billetes_tarifas.md` | 44 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 33 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 29 |
| Tamaño medio global | 535,60 caracteres |
| Mediana global | 592 caracteres |
| Tamaño mínimo global | 22 caracteres |
| Tamaño máximo global | 801 caracteres |
| Tamaño medio documental | 297,24 caracteres |
| Mediana documental | 334 caracteres |
| Tamaño mínimo documental | 22 caracteres |
| Tamaño máximo documental | 400 caracteres |

La reducción del tamaño de chunk provoca que los chunks documentales pasen de 87 a 185, un incremento aproximado del 112,6 % respecto al baseline.

### Retrieval

| ID | Source hit | Evidence hit | Posición fuente esperada |
|---|:---:|:---:|---:|
| q01 | Sí | Sí | 1 |
| q03 | Sí | Sí | 1 |
| q05 | Sí | Sí | 1 |
| q08 | Sí | Sí | 1 |
| q09 | Sí | Sí | 1 |
| q10 | Sí | No | 3 |
| q11 | Sí | Sí | 1 |

### Resumen

| Métrica | Resultado |
|---|---:|
| Source hit @3 | 7/7 (100 %) |
| Evidence hit @3 | 6/7 (85,7 %) |
| Top-1 esperado | 6/7 (85,7 %) |
| Posición media | 1,29 |

Esta configuración no aumenta el número total de `Evidence hit`, pero mejora claramente la posición de las fuentes esperadas.

En q10 la evidencia completa no aparece dentro del Top-3, pero una prueba exploratoria con `K = 4` recupera el fragmento adecuado en cuarta posición. Esto indica que la evidencia existe y se encuentra semánticamente próxima a la consulta, aunque queda fuera del límite fijado para la comparación principal.

---

## 5. Experimento 1200 / 150

### Efecto sobre el corpus

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3807 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks documentales calculados como total - CSV | 59 |
| Chunks `crtm_faq.md` | 21 |
| Chunks `crtm_billetes_tarifas.md` | 14 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 13 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 11 |
| Tamaño medio global | 553,76 caracteres |
| Mediana global | 597 caracteres |
| Tamaño mínimo global | 119 caracteres |
| Tamaño máximo global | 1197 caracteres |
| Tamaño medio documental | 959,81 caracteres |
| Mediana documental | 1109 caracteres |
| Tamaño mínimo documental | 119 caracteres |
| Tamaño máximo documental | 1197 caracteres |

### Retrieval

| ID | Source hit | Evidence hit | Posición fuente esperada |
|---|:---:|:---:|---:|
| q01 | No | No | - |
| q03 | Sí | Sí | 1 |
| q05 | Sí | Sí | 1 |
| q08 | Sí | Sí | 3 |
| q09 | Sí | Sí | 1 |
| q10 | Sí | Sí | 1 |
| q11 | Sí | Sí | 1 |

### Resumen

| Métrica | Resultado |
|---|---:|
| Source hit @3 | 6/7 (85,7 %) |
| Evidence hit @3 | 6/7 (85,7 %) |
| Top-1 esperado | 5/7 (71,4 %) |
| Posición media cuando aparece en Top-3 | 1,33 |

El resultado más destacable es q10: al aumentar el tamaño de los chunks, la fuente esperada aparece en primera posición y contiene toda la evidencia necesaria.

A cambio, q01 deja de aparecer dentro del Top-3. Una prueba exploratoria con `K = 4` sí recupera la evidencia adecuada en cuarta posición.

---

## 6. Comparación final

| Métrica | 400 / 50 | 800 / 100 | 1200 / 150 |
|---|---:|---:|---:|
| Chunks documentales | 185 | 87 | 59 |
| Chunks totales | 3933 | 3835 | 3807 |
| Source hit @3 | 7/7 | 7/7 | 6/7 |
| Evidence hit @3 | 6/7 | 6/7 | 6/7 |
| Top-1 esperado | 6/7 | 4/7 | 5/7 |
| Posición media | 1,29 | 1,71 | 1,33 |
| Fallo principal | q10 | q10 | q01 |

### Preguntas más sensibles al chunking

| Pregunta | 400 / 50 | 800 / 100 | 1200 / 150 |
|---|---|---|---|
| q01 | Evidence hit, posición 1 | Evidence hit, posición 3 | **Fallo @3; acierto con K=4** |
| q08 | Evidence hit, posición 1 | Evidence hit, posición 2 | Evidence hit, posición 3 |
| q09 | Evidence hit, posición 1 | Evidence hit, posición 3 | Evidence hit, posición 1 |
| q10 | **Fallo @3; acierto con K=4** | **Fallo incluso con K=4 y K=5** | Evidence hit, posición 1 |

---

## 7. Interpretación

Los tres experimentos obtienen el mismo `Evidence hit @3`: 6 aciertos de 7 preguntas. Por tanto, ninguna configuración demuestra ser superior si se considera únicamente esta métrica.

Sin embargo, aparecen diferencias relevantes en el comportamiento del retrieval.

`400 / 50` ofrece el mejor ranking general. Recupera la fuente esperada en primera posición en 6 de las 7 preguntas y obtiene la mejor posición media, 1,29. Su principal desventaja es que duplica ampliamente el número de chunks documentales.

`1200 / 150` conserva más contexto en cada fragmento y resuelve q10, una pregunta cuya evidencia depende de varios datos relacionados. Sin embargo, pierde q01 dentro del Top-3 y empeora la posición de q08. Esto sugiere que chunks mayores pueden conservar mejor evidencias compuestas, pero también reducir la especificidad semántica.

`800 / 100` presenta un comportamiento intermedio, pero ofrece un ranking inferior al de `400 / 50`. Además, el fallo de q10 no se corrige ampliando el retrieval a K=4 ni K=5.

Los resultados muestran un compromiso entre granularidad y contexto: los chunks pequeños favorecen la precisión del ranking, mientras que los chunks grandes pueden conservar mejor información relacionada dentro de una misma unidad.

---

## 8. Configuración seleccionada

Se selecciona como configuración definitiva:

```python
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
```

La elección se basa en que esta configuración presenta el comportamiento más consistente en el conjunto evaluado:

- `Source hit @3`: 7/7.
- `Evidence hit @3`: 6/7.
- Fuente esperada en Top-1: 6/7.
- Posición media: 1,29.

Aunque genera más chunks documentales, el índice completo aumenta únicamente de 3835 a 3933 chunks respecto al baseline, aproximadamente un 2,6 %, debido al peso de los bloques del CSV.

La decisión no implica que `400 / 50` sea una configuración universalmente óptima. Es la alternativa que ofrece el mejor compromiso observado entre granularidad, precisión del ranking, estabilidad y coste para el corpus y el conjunto de evaluación utilizados en MadridRumbo.
