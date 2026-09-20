# Experimento de chunking — Configuración 800 / 100

## 1. Objetivo

Este experimento forma parte de la evaluación de la estrategia de chunking utilizada en MadridRumbo.

El objetivo es observar el comportamiento del corpus y del retrieval utilizando la siguiente configuración:

- `CHUNK_SIZE = 800`
- `CHUNK_OVERLAP = 100`

Esta configuración corresponde al baseline utilizado durante el desarrollo del
proyecto y servirá como referencia para compararla posteriormente con otras
configuraciones de chunking.

El experimento pretende analizar dos aspectos:

1. El efecto de la configuración sobre la fragmentación del corpus.
2. La capacidad del sistema para recuperar la evidencia necesaria para responder a un conjunto representativo de preguntas.

---

## 2. Configuración del experimento

| Parámetro | Valor |
|---|---:|
| `CHUNK_SIZE` | 800 caracteres |
| `CHUNK_OVERLAP` | 100 caracteres |
| Porcentaje aproximado de solapamiento | 12,5 % |
| Splitter | `RecursiveCharacterTextSplitter` |
| `TOP_K` utilizado en el experimento | 3 |
| Modelo de embeddings | `gemini-embedding-2` |
| Base vectorial | ChromaDB |

Durante la comparación con las siguientes configuraciones se mantendrán
constantes el corpus, el modelo de embeddings, el valor de `K` y el resto de
parámetros del pipeline. De esta forma, la principal variable modificada será
la estrategia de chunking.

### Tratamiento especial del CSV

`Paradas CRTM.csv` utiliza una estrategia específica.

Las paradas se agrupan previamente por tipo de transporte y zona tarifaria en bloques de hasta seis paradas. Estos bloques se consideran unidades semánticas completas y no vuelven a pasar por `RecursiveCharacterTextSplitter`.

Por tanto, los parámetros `CHUNK_SIZE` y `CHUNK_OVERLAP` afectan principalmente a las fuentes documentales textuales y PDF del corpus.

La estrategia del CSV se mantendrá constante durante todos los experimentos para evitar introducir una segunda variable en la comparación.

---

## 3. Hipótesis

La configuración 800 / 100 representa una estrategia intermedia de fragmentación.

Se parte de la hipótesis de que un tamaño de 800 caracteres puede proporcionar suficiente contexto para conservar juntas ideas relacionadas sin generar chunks excesivamente grandes.

El solapamiento de 100 caracteres busca reducir el riesgo de perder información situada en los límites entre dos chunks consecutivos.

Esta configuración se utilizará como baseline frente a configuraciones con chunks más pequeños y más grandes.

No se presupone que sea la configuración óptima: la decisión final se realizará a partir de los resultados observados durante los experimentos.

---

## 4. Efecto sobre el corpus

Tras ejecutar el pipeline con la configuración 800 / 100 se obtienen las
siguientes estadísticas:

| Métrica | Resultado |
|---|---:|
| Documentos cargados | 3758 |
| Documentos tras limpieza | 3758 |
| Chunks totales | 3835 |
| Chunks `Paradas CRTM.csv` | 3748 |
| Chunks `crtm_faq.md` | 36 |
| Chunks `crtm_billetes_tarifas.md` | 20 |
| Chunks `bocm-20251231-precios_transporte.pdf` | 17 |
| Chunks `bocm-20251231-tarifas_transporte.pdf` | 14 |
| Tamaño medio de los chunks | 549,69 caracteres |
| Tamaño mínimo | 119 caracteres |
| Tamaño máximo | 801 caracteres |
| Tamaño mediano | 597 caracteres |

### Tamaño de los chunks documentales

| Métrica | 800 / 100 |
|---|---:|
| Chunks documentales | 87 | 
| Tamaño medio | 649,68 |
| Mediana | 709 |
| Mínimo | 119 |
| Máximo | 798 |

### Observación

Con la configuración `CHUNK_SIZE = 800` y `CHUNK_OVERLAP = 100`
se generan 3.835 chunks a partir de 3.758 documentos.

La mayor parte del índice corresponde a `Paradas CRTM.csv`, con
3.748 chunks. Esto supone aproximadamente el 97,7 % del total.

Sin embargo, este resultado no depende directamente de los parámetros
`CHUNK_SIZE` y `CHUNK_OVERLAP`, ya que las paradas utilizan una
estrategia específica de agrupación en bloques y no pasan por
`RecursiveCharacterTextSplitter`.

Las fuentes documentales sometidas al splitter generan en conjunto
87 chunks:

- `crtm_faq.md`: 36
- `crtm_billetes_tarifas.md`: 20
- `bocm-20251231-precios_transporte.pdf`: 17
- `bocm-20251231-tarifas_transporte.pdf`: 14

El tamaño medio de los chunks es de 549,69 caracteres y la mediana
de 597 caracteres, ambos claramente inferiores al máximo configurado
de 800 caracteres.

Esto es esperable porque `CHUNK_SIZE` establece un tamaño máximo y no
obliga a que todos los fragmentos alcancen dicho tamaño. El splitter
intenta respetar separaciones naturales del texto cuando es posible.

La proximidad entre media y mediana indica que, globalmente, no existe
una diferencia extrema entre ambas medidas, aunque el tamaño mínimo
de 119 caracteres confirma la existencia de algunos fragmentos
considerablemente menores que el límite configurado.

---

## 5. Evaluación del retrieval

Para comparar las distintas configuraciones de chunking se utiliza `K = 3`
en todos los experimentos.

Se selecciona un subconjunto representativo del conjunto de evaluación del
proyecto.

| ID | Fuente esperada | Objetivo |
|---|---|---|
| q01 | `crtm_faq.md` | Información localizada en FAQ |
| q05 | `crtm_faq.md` | Respuesta explicativa en FAQ |
| q03 | `crtm_billetes_tarifas.md` | Información concreta sobre zonas |
| q08 | `crtm_billetes_tarifas.md` | Evidencia con varios porcentajes |
| q09 | `bocm-20251231-precios_transporte.pdf` | Recuperación desde PDF |
| q10 | `bocm-20251231-tarifas_transporte.pdf` | Recuperación desde PDF |
| q11 | `Paradas CRTM.csv` | Caso de control sobre el CSV |

Para cada pregunta se observan dos criterios:

**Source hit @3**

La fuente esperada aparece entre los tres chunks recuperados.

**Evidence hit @3**

El contenido recuperado contiene realmente la información necesaria para
responder a la pregunta de acuerdo con el criterio de evidencia definido en
`queries/eval_preguntas.json`.

---

## 6. Resultados de retrieval

| ID | Source hit @3 | Evidence hit @3 | Posición fuente esperada | Observación |
|---|:---:|:---:|---:|---|
| q01 | Si | Si | 3 | En todas las fuentes hay información que permite responder, aunque la mejor es la tercera. |
| q03 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante |
| q05 | Si | Si | 1 | - |
| q08 | Si | Si | 2 | El fragmento 1 contiene información relevante aunque no permitiría responder la pregunta con precisión. El 3 no es relevante.|
| q09 | Si | Si | 3 | Los otros dos fragmentos contienen información relevante pero incompleta |
| q10 | Si | No | 3 | No cumple el criterio de evidencia. Ni siquiera subiendo top k a 5. |
| q11 | Si | Si | 1 | Los 3 fragmentos contienen información relevante |

### Resumen

| Métrica | 800 / 100 | 400 / 50 | 1200 / 150 |
|---|---:|---:|---:|
| Source hit @3 @3 | 7/7 (100 %) | 7/7 (100 %) | 6/7 (85,7 %) |
| Evidence hit @3 | 6/7 (85,7 %) | 6/7 (85,7 %) | 6/7 (85,7 %) |
| Fuente esperada en Top-1 | 4/7 (57,1 %) | 6/7 (85,7 %) | 5/7 (71,4 %) |
| Posición media de la fuente esperada cuando aparece | 1,71 | 1,29 | 1,33 |

---

## 7. Análisis cualitativo

### FAQ

Las preguntas q01 y q05 recuperan correctamente la evidencia necesaria.

En q05 la fuente esperada aparece como primer resultado, lo que muestra
una recuperación directa y precisa.

En q01 la fuente esperada aparece en tercera posición. Sin embargo,
los otros fragmentos recuperados también contienen información suficiente
para responder a la pregunta.

Esto indica que determinada información sobre títulos de transporte puede
estar repetida o explicada desde distintos puntos del corpus. En este caso,
la posición de la fuente esperada no implica necesariamente una peor
capacidad de respuesta, ya que el contexto recuperado sigue conteniendo
evidencia válida.

### Billetes y tarifas

Las preguntas q03 y q08 recuperan la fuente y la evidencia necesarias.

En q03 la información relevante aparece directamente en primera posición
y los otros dos fragmentos no aportan información útil para la consulta.

En q08 la fuente esperada aparece en segunda posición. El primer fragmento
contiene información relacionada con la pregunta, pero por sí solo no
permitiría responderla con la precisión requerida por el criterio de
evidencia. El tercer resultado no resulta relevante.

Este comportamiento muestra la utilidad de recuperar varios fragmentos:
con `K = 1`, q08 podría disponer de contexto relacionado pero insuficiente,
mientras que con `K = 3` aparece la evidencia necesaria.

### PDF

Los documentos PDF presentan resultados más variables.

En q09 la evidencia necesaria se encuentra en la fuente esperada, pero esta
aparece en tercera posición. Los dos primeros fragmentos contienen información
relacionada con la consulta, aunque de forma incompleta.

El caso q10 resulta especialmente relevante. La fuente esperada se recupera
en primera posición, por lo que se obtiene un `Source hit @3`, pero el fragmento
recuperado no contiene toda la información exigida por el criterio de evidencia.

Por tanto, q10 obtiene `Source hit @3 = Sí` pero `Evidence hit @3 = No`.

Este resultado demuestra que recuperar el documento correcto no garantiza
haber recuperado el fragmento adecuado del documento. En fuentes como los PDF
oficiales, donde la información procede en parte de tablas y estructuras
complejas, el tamaño y los límites de los chunks pueden afectar a que una
evidencia completa quede contenida en un único fragmento.

Este caso será especialmente útil para comparar las siguientes configuraciones
de chunking.

### CSV de paradas

q11 recupera correctamente información sobre la parada consultada y la fuente
esperada aparece en primera posición.

Además, los tres fragmentos recuperados contienen información relevante.

Este caso funciona como control del experimento, ya que la fragmentación de
`Paradas CRTM.csv` no depende de `CHUNK_SIZE` ni de `CHUNK_OVERLAP`.

Por ello, se espera que su comportamiento permanezca relativamente estable
en los siguientes experimentos. Una variación importante en q11 debería
analizarse con cautela, ya que no podría atribuirse directamente al splitter
utilizado para las fuentes documentales.

---

## 8. Conclusión provisional

La configuración 800 / 100 proporciona un baseline sólido para la comparación
con las siguientes estrategias.

En las siete preguntas seleccionadas, la fuente esperada aparece dentro del
Top-3 en todos los casos, obteniéndose un `Source hit @3` de 7/7 (100 %).

Sin embargo, la recuperación de la fuente correcta no garantiza por sí sola
que el contexto contenga toda la información necesaria. El criterio
`Evidence hit @3` se cumple en 6 de las 7 preguntas (85,7 %).

El caso q10 es especialmente significativo: el sistema recupera la fuente
esperada en primera posición, pero el fragmento obtenido no contiene toda la
evidencia necesaria para responder correctamente. Esto pone de manifiesto la
necesidad de evaluar los chunks recuperados y no únicamente el fichero del que
proceden.

También se observa que en varias preguntas la evidencia suficiente no coincide
necesariamente con la primera aparición de la fuente esperada. En q08 y q09,
por ejemplo, es necesario disponer de varios resultados para alcanzar el
contexto adecuado.

Por otra parte, el corpus generado continúa estando dominado numéricamente por
los bloques de `Paradas CRTM.csv`, que representan aproximadamente el 97,7 %
de los chunks. No obstante, estos bloques utilizan una estrategia propia y no
están afectados directamente por los parámetros 800 / 100.

Por tanto, esta primera ejecución no permite todavía afirmar que 800 / 100 sea
la configuración óptima. Sus resultados servirán como referencia para observar
si configuraciones con chunks más pequeños o más grandes mejoran la recuperación
de evidencia, especialmente en los documentos PDF.

---

## 9. Comparación con otras configuraciones

Los resultados de este experimento se compararán posteriormente con:

| Experimento | `CHUNK_SIZE` | `CHUNK_OVERLAP` |
|---|---:|---:|
| Baseline | **800** | **100** |
| Chunks pequeños | 400 | 50 |
| Chunks grandes | 1200 | 150 |

La comparación final tendrá en cuenta:

- número de chunks generados;
- distribución de chunks entre fuentes;
- tamaño de los chunks;
- recuperación de la fuente correcta;
- recuperación de la evidencia necesaria;
- ruido introducido en el contexto;
- coste computacional asociado al número de embeddings.