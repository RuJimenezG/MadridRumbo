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

### Estrategia adoptada

Como solución intermedia, la implementación actual agrupa las paradas por **tipo de transporte y zona tarifaria**, generando bloques de hasta seis paradas.

Cada bloque conserva información de las paradas y metadatos sobre su tipo de transporte y zona. Estos bloques se consideran unidades semánticas completas y no vuelven a fragmentarse posteriormente.

Para el resto de documentos se utiliza `RecursiveCharacterTextSplitter`, con los valores de `CHUNK_SIZE` y `CHUNK_OVERLAP` definidos en `config.py`.

Esta estrategia busca mantener suficiente información de cada parada reduciendo al mismo tiempo la fragmentación excesiva que producía la estrategia inicial.

**Resultado final del corpus tras aplicar la estrategia actual:**

> **PENDIENTE:** actualizar tras ejecutar de nuevo `python main.py --prepare` con la versión definitiva.

| Métrica                                | Resultado final |
| -------------------------------------- | --------------: |
| Documentos cargados                    |       PENDIENTE |
| Chunks totales                         |       PENDIENTE |
| Chunks procedentes del CSV             |       PENDIENTE |
| Chunks procedentes de FAQ/Markdown/PDF |       PENDIENTE |

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

Los resultados anteriores corresponden a una versión anterior del pipeline y no deben utilizarse para valorar la implementación final.

Una vez regenerados los chunks, embeddings e índice con la estrategia actual, debe repetirse:

```bash
python eval_retrieval.py --k 1 3 5
```

**Resultados finales:**

|  K | Aciertos in-corpus | Observación |
| -: | -----------------: | ----------- |
|  1 |          PENDIENTE | PENDIENTE   |
|  3 |          PENDIENTE | PENDIENTE   |
|  5 |          PENDIENTE | PENDIENTE   |

**Conclusión final sobre K:**

> **PENDIENTE:** completar después de ejecutar la evaluación definitiva. Debe indicarse si aumentar K mejora la recuperación de la fuente correcta o si únicamente introduce más ruido.

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

> **PENDIENTE DE COMPLETAR CON UN RESULTADO REAL DE `eval_generacion_resultados.json`.**

**Pregunta:**
`[insertar pregunta evaluada]`

**Respuesta:**
`[insertar respuesta obtenida]`

**Fuentes recuperadas:**
`[insertar fuentes]`

**Valoración:**
La respuesta se considera correcta porque está respaldada por el corpus y contiene la evidencia esperada definida en `eval_preguntas.json`.

### Ejemplo de abstención correcta

> **PENDIENTE DE COMPLETAR CON UN RESULTADO REAL DE `eval_generacion_resultados.json`.**

**Pregunta fuera de corpus:**
`[insertar pregunta evaluada, por ejemplo una consulta ajena al transporte madrileño]`

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

### 6.2. Pérdida de estructura en tablas PDF

**Problema**

Algunos documentos oficiales contienen precios y condiciones organizados mediante tablas. La extracción de los PDF como texto plano puede perder filas, columnas o relaciones espaciales entre valores.

Como consecuencia, determinada información puede existir visualmente en el PDF pero resultar difícil de recuperar correctamente desde el texto extraído.

**Siguiente paso**

Preprocesar las tablas mediante herramientas específicas de extracción estructurada y convertirlas a formatos más adecuados para retrieval, por ejemplo Markdown, CSV o JSON.

Otra posibilidad sería mantener el PDF como fuente original pero generar previamente una representación textual estructurada de sus tablas.

---

### 6.3. Dependencia de cuotas y disponibilidad de APIs externas

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

Los experimentos realizados llevaron a modificar la estrategia de chunking y a separar mejor los distintos tipos de información.

También se han identificado limitaciones relacionadas con la extracción de tablas PDF y con la dependencia de APIs externas.

Las siguientes iteraciones deberían centrarse principalmente en:

* Repetir y analizar la evaluación sobre el corpus definitivo.
* Separar las búsquedas estructuradas de paradas del retrieval semántico general.
* Mejorar la extracción de tablas y documentos estructurados.
* Incorporar monitorización, métricas y gestión robusta de proveedores durante la futura fase de MLOps.

MadridRumbo queda diseñado como un componente modular que puede evolucionar desde un RAG independiente hacia una herramienta reutilizable dentro de un sistema de agentes.
