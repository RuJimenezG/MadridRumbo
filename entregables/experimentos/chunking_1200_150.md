# Experimento de chunking — Configuración 400 / 50

## 1. Objetivo

Este experimento forma parte de la evaluación de la estrategia de chunking utilizada en MadridRumbo.

El objetivo es observar el comportamiento del corpus y del retrieval utilizando una configuración con chunks de mayor tamaño que el baseline:

- `CHUNK_SIZE = 1200`
- `CHUNK_OVERLAP = 150`

Los resultados se compararán con las configuraciones previamente evaluadas:

- 800 / 100 — baseline.
- 400 / 50 — mayor granularidad.
- 1200 / 150 — mayor cantidad de contexto por chunk.

El experimento pretende analizar:

1. El efecto de aumentar el tamaño de los chunks sobre la fragmentación del corpus.
2. Si disponer de más contexto dentro de cada fragmento mejora la recuperación de evidencias formadas por varios datos relacionados.
3. Si chunks mayores introducen más ruido o perjudican la precisión del ranking.

---

## 2. Configuración del experimento

| Parámetro | Valor |
|---|---:|
| `CHUNK_SIZE` | 1200 caracteres |
| `CHUNK_OVERLAP` | 150 caracteres |
| Porcentaje aproximado de solapamiento | 12,5 % |
| Splitter | `RecursiveCharacterTextSplitter` |
| `TOP_K` utilizado en el experimento | 3 |
| Modelo de embeddings | `gemini-embedding-2` |
| Base vectorial | ChromaDB |

Se mantienen constantes el corpus, el modelo de embeddings, el valor de `K` y el resto de parámetros del pipeline.

La principal variable experimental es, por tanto, el tamaño de los chunks.

### Tratamiento especial del CSV

`Paradas CRTM.csv` utiliza una estrategia independiente del splitter.

Las paradas se agrupan por tipo de transporte y zona tarifaria en bloques de hasta seis paradas. Estos bloques se consideran unidades semánticas completas y no vuelven a pasar por `RecursiveCharacterTextSplitter`.

Por ello, `CHUNK_SIZE` y `CHUNK_OVERLAP` afectan únicamente a las fuentes documentales sometidas al splitter.

La estrategia del CSV se mantiene constante durante todos los experimentos.

---

## 3. Hipótesis

Al aumentar `CHUNK_SIZE` de 800 a 1200 caracteres se espera reducir el número de chunks generados para las fuentes documentales.

Los chunks mayores pueden conservar dentro del mismo fragmento información relacionada que una configuración más granular podría separar.

Esto podría beneficiar especialmente a consultas cuya evidencia requiere varios datos relacionados, condiciones o excepciones.

Sin embargo, disponer de más contenido dentro de cada chunk también puede introducir información irrelevante y reducir la precisión semántica del retrieval.

El caso q10 será especialmente relevante, ya que con las configuraciones 800 / 100 y 400 / 50 la fuente correcta fue recuperada, pero el Top-3 no contenía toda la evidencia necesaria.

---

## 4. Efecto sobre el corpus

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3807 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks `crtm_faq.md` | 21 |
| Chunks `crtm_billetes_tarifas.md` | 14 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 13 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 11 |
| Tamaño medio de los chunks | 553,76 caracteres |
| Tamaño mínimo | 119 caracteres |
| Tamaño máximo | 1197 caracteres |
| Tamaño mediano | 597 caracteres |

### Tamaño de los chunks documentales

| Métrica | 800 / 100 | 400 / 50 | 1200 / 150 |
|---|---:|---:|---:|
| Chunks documentales | 87 | 185 | 59 |
| Tamaño medio | 649,68 | 297,24 | 959,81 |
| Mediana | 709 | 334 | 1109 |
| Mínimo | 119 | 22 | 119 |
| Máximo | 798 | 400 | 1197 |

### Comparación con baseline 800 / 100

| Métrica | 800 / 100 | 1200 / 150 | Variación |
|---|---:|---:|---:|
| Chunks totales | 3835 | 3807 | -28 (-0,7 %) |
| Chunks CSV | 3748 | 3748 | 0 (0 %) |
| Chunks documentales | 87 | 59 | -28 (-32,2 %) |
| Tamaño medio global | 549,69 | 553,76 | +4,07 (+0,7 %) |
| Mediana global | 597 | 597 | 0 |

### Comparación del número de chunks

| Métrica | 800 / 100 | 400 / 50 | 1200 / 150 |
|---|---:|---:|---:|
| Chunks totales | 3835 | 3933 | 3807 |
| Chunks CSV | 3748 | 3748 | 3748 |
| Chunks documentales | 87 | 185 | 59 |

### Comparación de fragmentación documental

| Configuración | Chunks documentales | Variación vs baseline |
|---|---:|---:|
| 400 / 50 | 185 | +112,6 % |
| 800 / 100 | 87 | referencia |
| 1200 / 150 | 59 | -32,2 % |

### Observación

La configuración `CHUNK_SIZE = 1200` y `CHUNK_OVERLAP = 150` reduce el número total de chunks de 3.835 a 3.807 respecto al baseline 800 / 100.

Esta reducción global es pequeña, aproximadamente un 0,7 %, debido al peso de `Paradas CRTM.csv`, que mantiene exactamente los mismos 3.748 bloques en todos los experimentos.

Si se consideran únicamente las fuentes documentales afectadas por `RecursiveCharacterTextSplitter`, el efecto es mucho más evidente.

El número de chunks documentales disminuye de 87 a 59, una reducción aproximada del 32,2 % respecto al baseline.

Respecto a la configuración 400 / 50, la diferencia es todavía mayor: se pasa de 185 a 59 chunks documentales, lo que supone una reducción aproximada del 68,1 %.

La reducción se observa en todas las fuentes documentales:

- `crtm_faq.md`: de 36 chunks en 800 / 100 a 12.
- `crtm_billetes_tarifas.md`: de 20 a 14.
- `bocm-20251231-precios_transporte.pdf`: de 17 a 13.
- `bocm-20251231-tarifas_transporte.pdf`: de 14 a 11.

Los chunks documentales presentan ahora un tamaño medio de 959,81 caracteres y una mediana de 1.109 caracteres. El tamaño máximo observado, 1.197 caracteres, es coherente con el límite configurado de 1.200.

Estos resultados confirman que la configuración 1200 / 150 conserva una cantidad significativamente mayor de contexto dentro de cada unidad documental y reduce el número de fragmentos que deben indexarse.

La siguiente fase del experimento permitirá comprobar si esta reducción de granularidad mejora la recuperación de evidencias compuestas por varios datos relacionados o si, por el contrario, introduce demasiado contenido irrelevante dentro de cada chunk.

---

## 5. Evaluación del retrieval

Para hacer comparable este experimento con el baseline se mantiene `K = 3`.

Se utilizan exactamente las mismas preguntas:

| ID | Fuente esperada | Objetivo |
|---|---|---|
| q01 | `crtm_faq.md` | Información localizada en FAQ |
| q03 | `crtm_billetes_tarifas.md` | Información concreta sobre zonas |
| q05 | `crtm_faq.md` | Respuesta explicativa en FAQ |
| q08 | `crtm_billetes_tarifas.md` | Evidencia con varios porcentajes |
| q09 | `bocm-20251231-precios_transporte.pdf` | Recuperación desde PDF |
| q10 | `bocm-20251231-tarifas_transporte.pdf` | Recuperación desde PDF |
| q11 | `Paradas CRTM.csv` | Caso de control sobre el CSV |

Para cada pregunta se observan dos criterios:

**Source hit @3**

La fuente esperada aparece entre los tres chunks recuperados.

**Evidence hit @3**

El contenido recuperado contiene realmente la información necesaria para responder a la pregunta según el criterio definido en `queries/eval_preguntas.json`.

---

## 6. Resultados de retrieval

| ID | Source hit @3 | Evidence hit @3 | Posición fuente esperada | Observación |
|---|:---:|:---:|---:|---|
| q01 | No | No | - | En el fragmento 1 hay información relevante pero de otra fuente que no responde completamente la pregunta. Si se incrementa K a 4, acierta en el cuarto fragmento. |
| q03 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q05 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q08 | Si | Si | 3 | Los otros dos fragmentos no ofrecen información relevante. |
| q09 | Si | Si | 1 | El fragmento 3 contiene información relevante que también permite responder. |
| q10 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q11 | Si | Si | 1 | Los 3 fragmentos contienen información relevante |

### Resumen

| Métrica | 800 / 100 | 400 / 50 | 1200 / 150 |
|---|---:|---:|---:|
| Source hit @3 | 7/7 (100 %) | 7/7 (100 %) | 6/7 (85,7 %) |
| Evidence hit @3 | 6/7 (85,7 %) | 6/7 (85,7 %) | 6/7 (85,7 %) |
| Fuente esperada en Top-1 | 4/7 (57,1 %) | 6/7 (85,7 %) | 5/7 (71,4 %) |
| Posición media de la fuente esperada cuando aparece | 1,71 | 1,29 | 1,33 |

---

## 7. Análisis cualitativo

### FAQ

El comportamiento sobre las preguntas procedentes de las FAQ es desigual.

q05 mantiene un resultado estable respecto a las configuraciones anteriores: la fuente esperada aparece en primera posición y contiene evidencia suficiente.

Sin embargo, q01 empeora de forma clara.

Con 800 / 100 la fuente esperada aparecía en tercera posición y con 400 / 50 había mejorado hasta la primera. Con 1200 / 150 no aparece dentro del Top-3.

El primer fragmento recuperado contiene información relacionada procedente de otra fuente, pero no permite responder completamente a la pregunta.

Al aumentar de forma exploratoria K a 4, la fuente esperada aparece en cuarta posición y sí contiene la evidencia necesaria.

Este resultado no se contabiliza como acierto, ya que el experimento mantiene K=3 constante.

El comportamiento sugiere que chunks más grandes pueden contener más información y perder cierta especificidad semántica, haciendo que fragmentos relacionados pero menos precisos desplacen al resultado más adecuado.

### Billetes y tarifas

q03 mantiene un comportamiento estable y recupera la fuente esperada en primera posición con evidencia suficiente.

q08 también conserva el `Evidence hit @3`, aunque la fuente esperada aparece ahora en tercera posición.

Esto supone un empeoramiento en ranking respecto a 400 / 50, donde aparecía en primera posición, y también respecto a 800 / 100, donde aparecía en segunda.

Los dos primeros fragmentos de q08 no resultan relevantes para responder a la consulta.

Por tanto, aunque el mayor tamaño de chunk no impide recuperar la evidencia, sí parece reducir la precisión del ranking en esta pregunta concreta.

### PDF

La configuración 1200 / 150 mejora el comportamiento observado en los documentos PDF, especialmente en q10.

En q09 la fuente esperada aparece en primera posición y contiene evidencia suficiente. Además, el tercer fragmento también contiene información relevante que permitiría responder a la pregunta.

El resultado más significativo corresponde a q10.

Con las configuraciones 800 / 100 y 400 / 50 se recuperaba la fuente correcta, pero el Top-3 no contenía toda la evidencia necesaria para cumplir el criterio establecido.

Con 1200 / 150, la fuente esperada aparece en primera posición y el fragmento recuperado contiene tanto el incremento del 3 % como las excepciones necesarias, por lo que q10 pasa finalmente a obtener `Evidence hit @3 = Sí`.

Este resultado apoya la hipótesis de que chunks de mayor tamaño pueden resultar beneficiosos cuando la respuesta depende de varios datos relacionados que conviene conservar dentro de una misma unidad semántica.

Sin embargo, esta mejora no es general para todo el corpus, ya que otras preguntas, como q01 y q08, empeoran en el ranking.

Se prestará especial atención a q10, ya que con la configuración 800 / 100 se recuperó la fuente correcta en primera posición pero el fragmento no contenía toda la evidencia necesaria.

Esta pregunta permitirá comprobar si una mayor granularidad mejora la selección del fragmento relevante o, por el contrario, separa todavía más la información necesaria.

### CSV de paradas

q11 mantiene exactamente el comportamiento esperado.

La fuente aparece en primera posición, existe evidencia suficiente y los tres fragmentos recuperados resultan relevantes.

El  resultado permanece estable respecto a las otras configuraciones, lo querefuerza el uso de q11 como caso de control.

Esto es coherente con el diseño del pipeline, ya que `Paradas CRTM.csv` utiliza una estrategia específica de bloques que no depende de `CHUNK_SIZE` ni de `CHUNK_OVERLAP`.

---

## 8. Conclusión provisional

La configuración 1200 / 150 reduce significativamente la fragmentación documental respecto a las otras alternativas.

Se generan 59 chunks documentales, frente a 87 con 800 / 100 y 185 con 400 / 50. Los fragmentos contienen además mucha más información, con una media de 959,81 caracteres.

En retrieval, esta configuración obtiene un `Source hit @3` de 6/7 y un `Evidence hit @3` de 6/7.

Por tanto, el número total de preguntas con evidencia suficiente permanece idéntico al de las configuraciones anteriores: 6 de 7.

Sin embargo, cambia la naturaleza de los errores.

La configuración 1200 / 150 resuelve correctamente q10, que había fallado con 800 / 100 y 400 / 50. Esto sugiere que el mayor tamaño del chunk permite conservar conjuntamente información relacionada que las configuraciones más pequeñas separaban entre distintos fragmentos.

A cambio, q01 deja de recuperar la fuente y evidencia necesarias dentro del Top-3. La respuesta correcta aparece al ampliar de forma exploratoria K a 4, lo que indica que la información existe en el índice pero queda desplazada por otros fragmentos semánticamente relacionados.

También se observa un empeoramiento en la posición de q08, cuya fuente esperada pasa a tercera posición.

Los resultados muestran por tanto un compromiso entre granularidad y cantidad de contexto:

- Los chunks pequeños favorecen la precisión del ranking.
- Los chunks grandes pueden conservar mejor evidencias compuestas por varios
  datos relacionados.
- Ninguna de las configuraciones probadas mejora el `Evidence hit @3` global
  respecto a las demás.

Por ello, 1200 / 150 no puede considerarse globalmente superior, aunque muestra una ventaja clara para determinados tipos de preguntas sobre documentos estructuralmente complejos como los PDF.

---

## 9. Comparación acumulada

| Experimento | Chunks documentales | Source hit @3 | Evidence hit @3 | Top-1 esperado | Posición media* |
|---|---:|---:|---:|---:|---:|
| 800 / 100 | 87 | 7/7 | 6/7 | 4/7 | 1,71 |
| 400 / 50 | 185 | 7/7 | 6/7 | 6/7 | 1,29 |
| 1200 / 150 | 59 | 6/7 | 6/7 | 5/7 | 1,33 |

\* Posición media calculada únicamente cuando la fuente esperada aparece dentro del Top-3.

### Comportamiento de las preguntas más sensibles al chunking

| Pregunta | 800 / 100 | 400 / 50 | 1200 / 150 |
|---|---|---|---|
| q01 | Evidence hit @3 | Evidence hit @3 | **Fallo** |
| q08 | Evidence hit @3 (#2) | Evidence hit @3 (#1) | Evidence hit @3 (#3) |
| q09 | Evidence hit @3 (#3) | Evidence hit @3 (#1) | Evidence hit @3 (#1) |
| q10 | **Fallo** | **Fallo** | Evidence hit @3 (#1) |