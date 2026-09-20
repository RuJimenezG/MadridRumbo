# Informe de decisiones — MadridRumbo

## 1. Objetivo

Este documento recoge las principales decisiones técnicas, experimentos y limitaciones observadas durante el desarrollo de MadridRumbo, un sistema RAG especializado en información sobre transporte público de la Comunidad de Madrid.

El objetivo no es documentar cada incidencia encontrada durante el desarrollo, sino justificar las decisiones que han afectado al diseño final del sistema y analizar sus resultados.

---

## 2. Decisiones sobre el corpus y el chunking

Una de las principales dificultades del proyecto ha sido combinar fuentes documentales de naturaleza muy diferente.

El corpus contiene documentos textuales y PDF con información sobre tarifas, títulos y condiciones de uso, junto con un CSV de gran tamaño que contiene miles de paradas de transporte.

### Primera estrategia: una parada por chunk

La primera implementación convertía cada fila válida de `Paradas CRTM.csv` en un chunk independiente.

El resultado aproximado fue:

| Elemento                    | Resultado |
| --------------------------- | --------: |
| Filas/paradas del CSV       |    22.404 |
| Chunks generados por el CSV |    22.404 |
| Chunks totales del corpus   |    22.491 |
| Tokens totales              | 2.836.469 |
| Media de tokens por chunk   |    126,12 |

Esta estrategia conservaba todo el detalle de cada parada, pero introducía un fuerte desequilibrio en el corpus: prácticamente todos los vectores correspondían al CSV, mientras que los documentos de tarifas, FAQ y normativa estaban representados por un número muy reducido de chunks.

### Experimentos de reducción del CSV

Durante el desarrollo se estudiaron varias estrategias para reducir esta desproporción:

| Estrategia                                              | Chunks aproximados |
| ------------------------------------------------------- | -----------------: |
| Una fila = un chunk                                     |             22.404 |
| Agrupación conservando mayor detalle                    |              9.927 |
| Agrupación por zona/tipo conservando únicamente nombres |                 37 |

La alternativa más agresiva reducía enormemente el tamaño del índice, pero sacrificaba información potencialmente útil sobre cada parada.

### Estrategia específica para el CSV

Como solución intermedia, la implementación actual agrupa las paradas por **tipo de transporte y zona tarifaria**, generando bloques de hasta seis paradas.

Cada bloque conserva información de las paradas y metadatos sobre su tipo de transporte y zona. Estos bloques se consideran unidades semánticas completas y no vuelven a fragmentarse posteriormente.

Para el resto de documentos se utiliza `RecursiveCharacterTextSplitter`, con los valores de `CHUNK_SIZE` y `CHUNK_OVERLAP` definidos en `config.py`.

Esta estrategia busca mantener suficiente información de cada parada reduciendo al mismo tiempo la fragmentación excesiva que producía la estrategia inicial.

### Experimento de `CHUNK_SIZE` y `CHUNK_OVERLAP`

Para determinar la configuración de fragmentación de las fuentes documentales se compararon tres combinaciones de `CHUNK_SIZE` y `CHUNK_OVERLAP`.

Durante el experimento se mantuvieron constantes el corpus, el modelo de embeddings (`gemini-embedding-2`), la base vectorial y `K = 3`.

La estrategia específica de `Paradas CRTM.csv` también se mantuvo constante, por lo que los cambios de configuración afectaron principalmente a los documentos Markdown y PDF.

| Métrica | 400 / 50 | 800 / 100 | 1200 / 150 |
|---|---:|---:|---:|
| Chunks totales | 3933 | 3835 | 3807 |
| Chunks documentales | 185 | 87 | 59 |
| Source hit @3 | 7/7 | 7/7 | 6/7 |
| Evidence hit @3 | 6/7 | 6/7 | 6/7 |
| Fuente esperada en Top-1 | 6/7 | 4/7 | 5/7 |
| Posición media de la fuente esperada | 1,29 | 1,71 | 1,33 |

Las tres configuraciones obtuvieron el mismo resultado global de `Evidence hit @3`: 6 aciertos sobre 7 preguntas. Sin embargo, presentaron diferencias importantes en el ranking y en el tipo de errores cometidos.

La configuración 400 / 50 obtuvo el comportamiento más consistente. La fuente esperada apareció dentro del Top-3 en las siete preguntas y en primera posición en seis de ellas, obteniendo además la mejor posición media.

Su principal desventaja es el incremento de la fragmentación documental: se generan 185 chunks documentales frente a 87 con 800 / 100. Sin embargo, el número total de vectores únicamente aumenta de 3835 a 3933, aproximadamente un 2,6 %, debido al peso de los bloques procedentes del CSV.

La configuración 1200 / 150 mostró una ventaja diferente: los chunks de mayor tamaño permitieron resolver correctamente q10, cuya respuesta necesita conservar varios datos relacionados dentro del contexto. A cambio, q01 dejó de aparecer dentro del Top-3 y q08 empeoró su posición.

La configuración 800 / 100 presentó un comportamiento intermedio. En q10 la fuente esperada era recuperada, pero el fragmento no contenía toda la evidencia necesaria. Una prueba adicional ampliando el retrieval a K=4 y K=5 tampoco permitió recuperar el fragmento correcto.

Por tanto, se selecciona como configuración definitiva:

```python
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
```

Esta elección no pretende establecer una configuración universalmente óptima, sino seleccionar el mejor compromiso observado para el corpus y el conjunto de evaluación de MadridRumbo.

### Resultado final del corpus

Con la configuración seleccionada, el corpus queda formado por:

| Métrica                                  | Resultado final |
| ---------------------------------------- | --------------: |
| Documentos cargados                      |            3758 |
| Documentos tras limpieza                 |            3758 |
| Chunks totales                           |            3933 |
| Chunks procedentes de `Paradas CRTM.csv` |            3748 |
| Chunks procedentes de FAQ/Markdown/PDF   |             185 |


---

## 3. Generación de embeddings y límites de proveedor

Durante las primeras pruebas se utilizó `gemini-embedding-2` para generar los embeddings.

Al procesar el corpus completo apareció un error `429 RESOURCE_EXHAUSTED` provocado por los límites de peticiones del proveedor.

Como primera medida se añadió control de rate limiting y procesamiento por lotes. También se desarrolló la utilidad `contar_tokens_chunks()` para poder conocer de antemano el volumen aproximado que debía procesarse.

Con la estrategia inicial se contabilizaron aproximadamente 2,84 millones de tokens para los 22.491 chunks.

El volumen del corpus hizo necesario utilizar una cuota superior a la disponible inicialmente para completar la generación de embeddings.

Esta experiencia llevó a incorporar al pipeline:

* Procesamiento de embeddings por lotes.
* Control de la frecuencia de peticiones.
* Tratamiento diferenciado de errores temporales y límites de cuota.
* Posibilidad de utilizar Gemini u OpenAI como proveedores de embeddings.
* Reutilización de embeddings previamente calculados cuando sea posible.

La principal conclusión es que el tamaño y la estrategia de chunking no afectan únicamente a la calidad del retrieval: también tienen un impacto directo sobre el tiempo de procesamiento y el coste de generación de embeddings.

---

## 4. Evaluación del retrieval

La evaluación de retrieval utiliza las preguntas de `queries/eval_preguntas.json`.

Para cada pregunta in-corpus se comprueba si la fuente esperada aparece entre los `K` chunks recuperados.

### Primera evaluación

Sobre la versión inicial del corpus se obtuvieron los siguientes resultados:

|  K | Preguntas in-corpus con fuente esperada |
| -: | --------------------------------------: |
|  1 |                                  3 / 11 |
|  3 |                                  3 / 11 |

Aumentar `K` de 1 a 3 no produjo ninguna mejora.

Al analizar los resultados se observó que gran parte de las consultas recuperaban fragmentos de `Paradas CRTM.csv` incluso cuando la pregunta estaba relacionada exclusivamente con tarifas o preguntas frecuentes.

La causa principal identificada fue el fuerte desequilibrio del índice: el CSV aportaba decenas de miles de vectores frente a unas pocas decenas procedentes de FAQ y documentos de tarifas.

Este resultado fue uno de los motivos principales para modificar la estrategia de construcción de los chunks del CSV.

### Evaluación con el corpus definitivo

Una vez seleccionada como definitiva la configuración de chunking `CHUNK_SIZE = 400` y `CHUNK_OVERLAP = 50`, se regeneraron los chunks, embeddings y el índice ChromaDB.
 Sobre este índice se realizó un experimento específico para determinar el
valor de `K` utilizado por el retriever.

Se compararon:

- `K = 3`
- `K = 4`

Durante la comparación se mantuvieron constantes el corpus, la estrategia de chunking, el modelo de embeddings y el índice vectorial. La única variable modificada fue el número de chunks recuperados.

#### Evaluación automática de Source hit

El script `eval_retrieval.py` se ejecutó sobre las 11 preguntas in-corpus de `queries/eval_preguntas.json`.

Para cada pregunta se comprobó si la fuente esperada aparecía entre los `K` resultados recuperados.

| K | Fuente esperada recuperada |
|---:|---:|
| 3 | 11 / 11 (100 %) |
| 4 | 11 / 11 (100 %) |

Aumentar K de 3 a 4 no mejora el `Source hit`, ya que con K=3 la fuente esperada ya aparece en el 100 % de las preguntas.

Sin embargo, recuperar el documento correcto no garantiza que los chunks recuperados contengan toda la evidencia necesaria para responder.

Por este motivo se realizó también una evaluación cualitativa sobre siete preguntas representativas del conjunto de evaluación.

#### Evaluación de Evidence hit

Se comprobó manualmente si los chunks recuperados contenían la evidencia definida en `criterio_evidencia` para cada pregunta.

| Métrica | K=3 | K=4 |
|---|---:|---:|
| Source hit | 7 / 7 (100 %) | 7 / 7 (100 %) |
| Evidence hit | 6 / 7 (85,7 %) | 7 / 7 (100 %) |
| Evidencia suficiente en primera posición | 6 / 7 | 6 / 7 |

La diferencia entre ambas configuraciones aparece en q10:

> ¿Qué incremento se aplica a las tarifas del transporte público en 2026 y qué excepciones hay?

El criterio de evaluación exige recuperar el incremento del 3 % y las excepciones correspondientes al abono joven y al título de 10 viajes de Castilla y León.

Con `K = 3`, la fuente correcta se recupera, pero ninguno de los tres chunks contiene toda la evidencia necesaria.

Con `K = 4`, el cuarto fragmento contiene la información que faltaba y la pregunta pasa a obtener `Evidence hit = Sí`.

Esto demuestra que `Source hit` y `Evidence hit` miden aspectos distintos: el sistema puede recuperar el documento correcto sin haber recuperado todavía el fragmento adecuado para responder.

#### Ruido introducido por K=4

También se analizó la utilidad del cuarto fragmento recuperado en las siete preguntas:

| Utilidad del cuarto chunk | Casos |
|---|---:|
| Necesario | 1 |
| Útil | 0 |
| Redundante | 2 |
| Irrelevante | 4 |

En seis de las siete preguntas el cuarto chunk no era necesario para responder.

Por tanto, aumentar K introduce contexto adicional que en la mayoría de los casos resulta redundante o irrelevante. Sin embargo, en q10 ese fragmento adicional permite corregir un fallo real del retrieval.

El coste adicional se considera limitado: no requiere regenerar embeddings ni el índice, y únicamente supone recuperar un fragmento más y aumentar ligeramente el contexto enviado posteriormente al modelo generador.

### Decisión final sobre K

Se selecciona:

```python
TOP_K = 4
```

Ambas configuraciones obtienen un `Source hit` del 100 % sobre las 11 preguntasin-corpus, pero K=4 mejora el `Evidence hit` del subconjunto analizado de 6/7 (85,7 %) a 7/7 (100 %).

Aunque el cuarto chunk introduce información redundante o irrelevante en varias consultas, el incremento de contexto se considera asumible frente a la mejora de cobertura observada en q10.

Por tanto, la configuración definitiva del retrieval de MadridRumbo queda establecida en `K = 4`.

Esta decisión es específica para el corpus, la estrategia de chunking 400 / 50 y el conjunto de evaluación utilizados en el proyecto.

---

## 5. Evaluación de generación

La evaluación de generación utiliza el mismo conjunto de 15 preguntas.

El objetivo es comprobar dos comportamientos:

1. Para preguntas **in-corpus**, el sistema debe generar una respuesta apoyada en la información recuperada.
2. Para preguntas **fuera de corpus**, el sistema debe abstenerse y evitar generar información no respaldada por los documentos.

El prompt de generación obliga al modelo a utilizar únicamente el contexto recuperado. Cuando no existe evidencia suficiente, debe responder:

> `No lo sé, no está en los documentos.`

El script de evaluación guarda los resultados después de cada pregunta. Esta decisión se incorporó después de comprobar que una interrupción por cuotas o errores del proveedor podía hacer perder una evaluación parcialmente completada.

### Ejemplo de acierto in-corpus

**Pregunta:**
`¿Puedo cambiar la zona del título ya cargado en mi tarjeta?`

**Respuesta:**
`Sí, a lo largo de los 30 días del periodo de validez de una carga, si necesitas cambiar de zona puedes hacerlo en cualquiera de las Oficinas de Gestión, en los estancos y en las máquinas de metro.`

**Fuentes recuperadas:**
`crtm_faq.md`

**Valoración:**
La respuesta se considera correcta porque está respaldada por el corpus y contiene la evidencia esperada definida en `eval_preguntas.json`.

### Ejemplo de abstención correcta

**Pregunta fuera de corpus:**
`¿Qué requisitos pide la beca MEC para estudiantes universitarios?`

**Respuesta:**
`No lo sé, no está en los documentos.`

**Valoración:**
El sistema se abstiene correctamente al no disponer de evidencia suficiente en el contexto recuperado, evitando utilizar conocimiento externo al corpus.

---

## 6. Fallos y limitaciones observadas

### 6.1. Desequilibrio del corpus

**Problema**

La primera versión generaba un chunk por cada parada del CSV. Como consecuencia, el índice contenía decenas de miles de chunks de paradas frente a muy pocos chunks de FAQ, tarifas y normativa.

Esto provocaba que el retrieval recuperase frecuentemente información sobre paradas para preguntas que no tenían ninguna relación con ellas.

**Decisión tomada**

Se modificó la representación del CSV para agrupar las paradas por tipo de transporte y zona tarifaria en bloques de varias paradas.

**Siguiente paso**

En una evolución basada en agentes, las consultas exactas sobre paradas podrían resolverse mediante una herramienta específica sobre los datos estructurados, reservando el retrieval vectorial para información documental y semántica.

---

### 6.2. Limitación del retrieval en consultas composicionales

**Problema**

Durante las pruebas se detectó una limitación en las consultas que requieren combinar información procedente de distintas partes del corpus.

Un ejemplo representativo es la consulta:

> ¿Cuál es el precio del billete para ir desde Hospital de Móstoles hasta Príncipe Pío?

Para responder correctamente no basta con recuperar un único fragmento. El sistema debe localizar, al menos:

1. La estación de origen y su información tarifaria.
2. La estación de destino y su información tarifaria.
3. Las reglas o precios aplicables al trayecto correspondiente.

La implementación actual realiza una única búsqueda vectorial utilizando el embedding de la pregunta completa y recupera los `K` chunks semánticamente más próximos.

Al ejecutar la consulta anterior con valores de `K` comprendidos entre 4 y 12, los resultados recuperados correspondían únicamente a información sobre paradas y estaciones. No se recuperaron chunks procedentes de los documentos de tarifas.

Aumentar el valor de `K` no solucionó el problema, ya que los nuevos resultados continuaban perteneciendo al mismo tipo de información.

**Experimento de diagnóstico**

Para comprobar si la información tarifaria estaba correctamente indexada se realizó una consulta más específica:

```bash
python main.py --query "precio billete sencillo MetroSur Metro Zona A Combinado Metro 2026" --k 5
```
En este caso, los cinco primeros resultados recuperados procedieron de los documentos:

- bocm-20251231-precios_transporte.pdf
- bocm-20251231-tarifas_transporte.pdf

Entre los fragmentos recuperados aparecieron explícitamente conceptos como:

- BILLETES SENCILLOS: PRECIOS VIGENTES 2026
- Metro Zona A y ML1
- MetroEste, MetroNorte y MetroSur
- Combinado Metro

Este experimento permite concluir que la información tarifaria sí está presente e indexada correctamente, pero la consulta original no consigue recuperarla debido a la forma en la que se realiza actualmente el retrieval.

Los nombres concretos de las estaciones tienen un peso semántico elevado en la consulta y hacen que los chunks de paradas dominen los primeros resultados, mientras que los documentos de tarifas quedan fuera del Top-K.

**Conclusión**

Este caso muestra una limitación del retrieval vectorial basado en una única consulta para preguntas composicionales o multi-hop. El sistema recupera correctamente información cuando la consulta está centrada en un único concepto, pero presenta dificultades cuando la respuesta requiere combinar diferentes tipos de evidencia.

Aumentar únicamente el valor de K no constituye una solución adecuada, ya que puede incrementar el ruido del contexto sin garantizar que se recuperen las distintas clases de información necesarias.

**Siguiente paso**

Como posible mejora se plantea implementar una estrategia de query decomposition o multi-query retrieval.

Una consulta de origen-destino podría descomponerse conceptualmente en varias búsquedas independientes:

1. Recuperar información sobre la parada de origen.
2. Recuperar información sobre la parada de destino.
3. Recuperar las reglas tarifarias relevantes.
4. Combinar los fragmentos recuperados antes de enviarlos al modelo generativo.

De esta forma, el LLM recibiría conjuntamente la evidencia necesaria para realizar la deducción final.

También se mantiene como línea de mejora el preprocesamiento de las tablas tarifarias de los PDF a un formato estructurado, como Markdown, CSV o JSON, ya que la extracción actual a texto plano pierde parcialmente la relación entre encabezados, categorías y precios.

---

### 6.3. Pérdida de estructura en tablas PDF

**Problema**

Algunos documentos oficiales contienen precios y condiciones organizados mediante tablas. La extracción de los PDF como texto plano puede perder filas, columnas o relaciones espaciales entre valores.

Como consecuencia, determinada información puede existir visualmente en el PDF pero resultar difícil de recuperar correctamente desde el texto extraído.

**Siguiente paso**

Preprocesar las tablas mediante herramientas específicas de extracción estructurada y convertirlas a formatos más adecuados para retrieval, por ejemplo Markdown, CSV o JSON.

Otra posibilidad sería mantener el PDF como fuente original pero generar previamente una representación textual estructurada de sus tablas.

---

### 6.4. Dependencia de cuotas y disponibilidad de APIs externas

**Problema**

Durante la generación de embeddings y durante la evaluación de generación se encontraron errores relacionados con límites de peticiones (`429`) y disponibilidad temporal del proveedor (`503`).

Estos errores pueden interrumpir procesos largos y dificultar evaluaciones reproducibles.

**Decisiones tomadas**

Se añadieron procesamiento por lotes, esperas entre peticiones, reintentos ante errores temporales y guardado incremental de los resultados de evaluación.

**Siguiente paso**

En una etapa de MLOps sería conveniente incorporar observabilidad sobre las llamadas externas, métricas de consumo, caché, políticas de reintento más completas y, cuando sea necesario, mecanismos de fallback entre proveedores.

---

## 7. Otras decisiones de ingeniería

### Separación entre pipeline offline y consultas online

La preparación del corpus, generación de embeddings e indexación se realizan separadamente de las consultas del usuario.

Esto evita repetir operaciones costosas cada vez que se realiza una pregunta y permite reutilizar el índice persistente de ChromaDB.

### Reutilización de artefactos

El sistema puede reutilizar `output/chunks.json` durante la indexación en lugar de volver a ejecutar toda la ingesta.

También se ha trabajado en reutilizar embeddings ya calculados, verificando que correspondan con el corpus y modelo utilizados antes de incorporarlos al índice.

### API interna independiente de la interfaz

La función `responder()` centraliza retrieval, generación, fuentes y métricas.

De esta forma, tanto la CLI como Streamlit utilizan el mismo flujo interno y el componente podrá reutilizarse posteriormente como herramienta dentro del Project Break de Agentes.

---

## 8. Conclusiones

El desarrollo de MadridRumbo ha mostrado que en un sistema RAG la calidad final no depende únicamente del modelo de embeddings o del LLM.

La representación del corpus tiene un impacto especialmente importante. El primer diseño conservaba un nivel muy alto de detalle para las paradas, pero el gran desequilibrio resultante perjudicaba el retrieval global.

El experimento de chunking comparó las configuraciones 400 / 50, 800 / 100 y 1200 / 150. Aunque las tres obtuvieron 6/7 en `Evidence hit @3`, 400 / 50 presentó el comportamiento más consistente en retrieval, con 7/7 en `Source hit @3`, 6/7 fuentes esperadas en primera posición y una posición media de 1,29. Por ello se adoptó como configuración definitiva para las fuentes documentales.

También se han identificado limitaciones relacionadas con la extracción de tablas PDF y con la dependencia de APIs externas.

Las siguientes iteraciones deberían centrarse principalmente en:

* Repetir y analizar la evaluación sobre el corpus definitivo.
* Separar las búsquedas estructuradas de paradas del retrieval semántico general.
* Mejorar la extracción de tablas y documentos estructurados.
* Incorporar monitorización, métricas y gestión robusta de proveedores durante la futura fase de MLOps.

MadridRumbo queda diseñado como un componente modular que puede evolucionar desde un RAG independiente hacia una herramienta reutilizable dentro de un sistema de agentes.