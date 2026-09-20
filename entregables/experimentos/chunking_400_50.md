# Experimento de chunking — Configuración 400 / 50

## 1. Objetivo

Este experimento forma parte de la evaluación de la estrategia de chunking utilizada en MadridRumbo.

El objetivo es observar el comportamiento del corpus y del retrieval utilizando una configuración con mayor granularidad que el baseline:

- `CHUNK_SIZE = 400`
- `CHUNK_OVERLAP = 50`

Los resultados se compararán con la configuración baseline 800 / 100.

El experimento pretende analizar dos aspectos:

1. El efecto de reducir el tamaño de los chunks sobre la fragmentación del corpus.
2. La capacidad del sistema para recuperar la evidencia necesaria para responder al mismo conjunto de preguntas utilizado en el baseline.

---

## 2. Configuración del experimento

| Parámetro | Valor |
|---|---:|
| `CHUNK_SIZE` | 400 caracteres |
| `CHUNK_OVERLAP` | 50 caracteres |
| Porcentaje aproximado de solapamiento | 12,5 % |
| Splitter | `RecursiveCharacterTextSplitter` |
| `TOP_K` utilizado en el experimento | 3 |
| Modelo de embeddings | `gemini-embedding-2` |
| Base vectorial | ChromaDB |

Respecto al experimento baseline 800 / 100, se mantienen constantes el corpus,
el modelo de embeddings, el valor de `K` y el resto de parámetros del pipeline.

De esta forma, la variable experimental principal es el tamaño de los chunks.

### Tratamiento especial del CSV

`Paradas CRTM.csv` utiliza una estrategia específica.

Las paradas se agrupan previamente por tipo de transporte y zona tarifaria en bloques de hasta seis paradas. Estos bloques se consideran unidades semánticas completas y no vuelven a pasar por `RecursiveCharacterTextSplitter`.

Por tanto, los parámetros `CHUNK_SIZE` y `CHUNK_OVERLAP` afectan principalmente a las fuentes documentales textuales y PDF del corpus.

La estrategia del CSV se mantendrá constante durante todos los experimentos para evitar introducir una segunda variable en la comparación.

---

## 3. Hipótesis

Al reducir `CHUNK_SIZE` de 800 a 400 caracteres se espera generar un mayor
número de chunks en las fuentes documentales.

Los fragmentos más pequeños podrían mejorar la precisión del retrieval al contener menos información no relacionada con cada consulta.

Sin embargo, también existe el riesgo de fragmentar información que necesita aparecer conjuntamente para responder correctamente a una pregunta.

Este posible efecto será especialmente relevante en preguntas cuya evidencia esté compuesta por varios datos relacionados, como porcentajes, condiciones o excepciones.

El solapamiento se reduce proporcionalmente de 100 a 50 caracteres, manteniendo aproximadamente el mismo porcentaje de solapamiento del baseline: 12,5 %.

---

## 4. Efecto sobre el corpus

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3933 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks `crtm_faq.md` | 79 |
| Chunks `crtm_billetes_tarifas.md` | 44 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 33 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 29 |
| Tamaño medio de los chunks | 535,6 caracteres |
| Tamaño mínimo | 22 caracteres |
| Tamaño máximo | 801 caracteres |
| Tamaño mediano | 592 caracteres |

### Tamaño de los chunks documentales

| Métrica | 800 / 100 | 400 / 50 |
|---|---:|---:|
| Chunks documentales | 87 | 185 |
| Tamaño medio | 649,68 | 297,24 |
| Mediana | 709 | 334 |
| Mínimo | 119 | 22 |
| Máximo | 798 | 400 |

### Comparación con baseline 800 / 100

| Métrica | 800 / 100 | 400 / 50 | Variación |
|---|---:|---:|---:|
| Chunks totales | 3835 | 3933 | +98 (+2,6 %) |
| Chunks CSV | 3748 | 3748 | 0 (0 %) |
| Chunks documentales | 87 | 185 | +98 (+112,6 %) |
| Tamaño medio | 549,69 | 535,60 | -14,09 (-2,6 %) |
| Mediana | 597 | 592 | -5 (-0,8 %) |

### Observación

La reducción de `CHUNK_SIZE` de 800 a 400 caracteres y de `CHUNK_OVERLAP` de 100 a 50 produce un aumento de 3.835 a 3.933 chunks totales, lo que representa únicamente un incremento aproximado del 2,6 %.

Sin embargo, esta cifra global resulta poco representativa del efecto real del cambio de configuración, ya que `Paradas CRTM.csv` mantiene exactamente los mismos 3.748 chunks en ambos experimentos. Estos bloques utilizan una estrategia específica y no pasan por `RecursiveCharacterTextSplitter`.

Si se consideran únicamente las fuentes documentales afectadas por el splitter, el número de chunks pasa de 87 a 185, un incremento aproximado del 112,6 %.

El efecto se observa en todas las fuentes documentales:

- `crtm_faq.md`: de 36 a 79 chunks.
- `crtm_billetes_tarifas.md`: de 20 a 44 chunks.
- `bocm-20251231-precios_transporte.pdf`: de 17 a 33 chunks.
- `bocm-20251231-tarifas_transporte.pdf`: de 14 a 29 chunks.

Por tanto, reducir a la mitad el tamaño máximo del chunk provoca aproximadamente una duplicación del número de fragmentos documentales.

Las métricas globales de tamaño muestran una reducción mucho menor: la media pasa de 549,69 a 535,60 caracteres y la mediana de 597 a 592.
Este resultado está condicionado por el peso de los bloques del CSV, que representan la mayor parte del corpus y cuyo tamaño no cambia entre ambos experimentos.

El tamaño máximo global observado es de 801 caracteres. Este valor no contradice el `CHUNK_SIZE = 400`, ya que los bloques procedentes del CSV no son procesados por el splitter y pueden superar ese límite.

Será necesario analizar ahora el retrieval para determinar si el aumento de granularidad proporciona una recuperación más precisa o si, por el contrario, fragmenta información que necesita permanecer unida para responder correctamente a determinadas consultas.

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

El contenido recuperado contiene realmente la información necesaria para
responder a la pregunta según el criterio definido en
`queries/eval_preguntas.json`.

---

## 6. Resultados de retrieval

| ID | Source hit @3 | Evidence hit @3 | Posición fuente esperada | Observación |
|---|:---:|:---:|---:|---|
| q01 | SI | Si | 1 | En todos los fragmentos hay información que permite responder, aunque el mejor es el 1. |
| q03 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q05 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q08 | Si | Si | 1 | El fragmento 3 contiene información relevante aunque no permitiría responder la pregunta con precisión. El 2 no es relevante. |
| q09 | Si | Si | 1 | Los otros dos fragmentos contienen información relevante pero incompleta. |
| q10 | Si | No | 3 | No cumple el criterio de evidencia. Si se incrementa K a 4, acierta en el cuarto fragmento. |
| q11 | Si | Si | 1 | Los 3 fragmentos contienen información relevante |

### Resumen

| Métrica | 800 / 100 | 400 / 50 |
|---|---:|---:|
| Source hit @3 @3 | 7 / 7 (100 %) | 7 / 7 (100 %) |
| Evidence hit @3 | 6 / 7 (85,7 %) | 6 / 7 (85,7 %) |
| Fuente esperada en Top-1 | 4 / 7 (57,1 %) | 6 / 7 (85,7 %) |
| Posición media de la fuente esperada cuando aparece | 1,71 | 1,29 |

---

## 7. Análisis cualitativo

### FAQ

La configuración 400 / 50 ofrece buenos resultados en las preguntas
procedentes de las FAQ.

En q01 y q05 la fuente esperada aparece en primera posición y el contexto
recuperado contiene evidencia suficiente para responder.

En q01 los tres fragmentos contienen información útil, aunque el primero
es el que proporciona la respuesta de forma más directa.

Respecto al baseline 800 / 100, q01 mejora la posición de la fuente esperada
desde la tercera hasta la primera posición.

Esto sugiere que una mayor granularidad puede facilitar que el embedding de
la consulta se aproxime a fragmentos más específicos del documento.

### Billetes y tarifas

q03 y q08 obtienen tanto `Source hit @3` como `Evidence hit @3`.

En ambos casos la fuente esperada aparece en primera posición.

En q03 los dos fragmentos restantes no contienen información relevante.

En q08 el tercer fragmento contiene información relacionada, aunque no sería
suficiente por sí solo para responder con la precisión exigida. El segundo
resultado no resulta relevante.

Comparado con 800 / 100, q08 mejora la posición de la fuente esperada desde
la segunda hasta la primera posición.

Por tanto, en estas consultas la reducción del tamaño del chunk parece
favorecer una recuperación más precisa sin perder la evidencia necesaria.

### PDF

El comportamiento sobre los PDF muestra tanto mejoras como una posible
limitación de utilizar chunks más pequeños.

En q09 la fuente esperada pasa de la tercera posición obtenida con 800 / 100
a la primera posición con 400 / 50.

Los otros dos fragmentos contienen información relacionada pero incompleta,
por lo que el primer resultado es suficiente para responder correctamente.

El comportamiento de q10 es diferente.

Con 800 / 100 la fuente esperada aparecía en primera posición pero el
fragmento recuperado no contenía toda la evidencia necesaria.

Con 400 / 50 la fuente esperada sigue apareciendo dentro del Top-3, pero pasa
a la tercera posición y ninguno de los tres fragmentos recuperados contiene
toda la evidencia exigida.

Al aumentar de forma exploratoria el retrieval a K=4, el cuarto fragmento sí
contiene la evidencia necesaria.

Este resultado no se contabiliza como acierto del experimento, ya que la
comparación se realiza manteniendo K=3 constante, pero resulta útil para
diagnosticar el comportamiento del sistema.

El resultado sugiere que la reducción del tamaño de los chunks puede haber
fragmentado información que necesita mantenerse próxima. El retriever localiza
el documento correcto, pero la evidencia completa queda situada en un
fragmento que no alcanza las tres primeras posiciones.

### CSV de paradas

q11 mantiene el mismo comportamiento observado en el baseline.

La fuente esperada aparece en primera posición, existe evidencia suficiente
y los tres fragmentos recuperados contienen información relevante.

Este comportamiento estable era esperable, ya que los bloques procedentes
de `Paradas CRTM.csv` no utilizan `RecursiveCharacterTextSplitter` y por
tanto no se ven afectados directamente por el cambio de 800 / 100 a 400 / 50.

El resultado refuerza su utilidad como caso de control del experimento.

---

## 8. Conclusión provisional

La configuración 400 / 50 modifica de forma importante la fragmentación de
las fuentes documentales.

El número de chunks documentales aumenta de 87 a 185, lo que supone un
incremento aproximado del 112,6 %. El tamaño medio de estos nuevos fragmentos
es de 297,24 caracteres, con una mediana de 334 y un máximo de 400 caracteres.

En retrieval, esta mayor granularidad mejora claramente la posición de las
fuentes esperadas.

La fuente esperada aparece en primera posición en 6 de las 7 preguntas
evaluadas, frente a 4 de 7 con la configuración 800 / 100. La posición media
también mejora de 1,71 a 1,29.

Sin embargo, esta mejora en el ranking no se traduce en un aumento de la
recuperación efectiva de evidencia.

Ambas configuraciones obtienen:

- `Source hit @3`: 7/7.
- `Evidence hit @3`: 6/7.

Por tanto, la configuración 400 / 50 produce fragmentos más específicos y
parece mejorar la precisión del ranking, pero no aumenta el número de
preguntas que pueden responderse con la evidencia disponible en Top-3.

El caso q10 muestra además una posible desventaja de los chunks pequeños.
La evidencia completa aparece al ampliar experimentalmente la búsqueda a
K=4, pero queda fuera del Top-3 utilizado en la comparación.

Esto sugiere que una fragmentación más fina puede mejorar la correspondencia
semántica entre consulta y fragmento, pero también separar información
relacionada que sería útil conservar conjuntamente.

Por el momento, no existe evidencia suficiente para considerar 400 / 50
superior a 800 / 100. Será necesario comparar estos resultados con una
configuración de chunks más grandes.

---

### 9. Comparación acumulada

| Experimento | Chunk size | Overlap | Chunks documentales | Source hit @3 | Evidence hit @3 | Top-1 esperado | Posición media |
|---|---:|---:|---:|---:|---:|---:|---:|
| 800 / 100 | 800 | 100 | 87 | 7/7 | 6/7 | 4/7 | 1,71 |
| 400 / 50 | 400 | 50 | 185 | 7/7 | 6/7 | 6/7 | 1,29 |