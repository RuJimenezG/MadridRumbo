# Experimento de retrieval — Comparación K=3 vs K=4

## 1. Objetivo

Este experimento evalúa el efecto de aumentar el número de chunks recuperados por el retriever de `K = 3` a `K = 4`.

La comparación se realiza sobre la configuración de chunking seleccionada como definitiva para MadridRumbo:

```python
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
```

Antes de iniciar el experimento se han regenerado los chunks, embeddings e índice ChromaDB con esta configuración.

Durante todo el experimento se mantendrán constantes:

- el corpus;
- la estrategia específica de bloques de `Paradas CRTM.csv`;
- `CHUNK_SIZE = 400`;
- `CHUNK_OVERLAP = 50`;
- el modelo de embeddings `gemini-embedding-2`;
- los embeddings ya generados;
- el índice ChromaDB.

La única variable experimental será el número de resultados recuperados:

- `K = 3`;
- `K = 4`.

---

## 2. Motivación

En el experimento de chunking 400 / 50 se observó que la pregunta q10 no contenía toda la evidencia necesaria dentro del Top-3.

Sin embargo, una prueba exploratoria mostró que el cuarto resultado sí contenía la evidencia necesaria.

Esto plantea una cuestión relevante para el diseño final del retrieval:

> ¿Aumentar K de 3 a 4 mejora de forma útil la recuperación de evidencia o
> simplemente introduce más contexto y ruido?

El experimento no pretende únicamente comprobar si aparecen más fuentes correctas al aumentar K. Dado que un valor mayor de K recupera necesariamente más fragmentos, también se analizará la calidad del contexto adicional.

---

## 3. Hipótesis

La hipótesis de partida es que `K = 4` puede mejorar la cobertura del retrieval en consultas donde la evidencia relevante queda inmediatamente fuera del Top-3.

En particular, se espera que q10 pase de `Evidence hit = No` con K=3 a `Evidence hit = Sí` con K=4.

A cambio, el cuarto fragmento puede introducir información irrelevante o redundante en preguntas que ya estaban correctamente resueltas con K=3.

Por tanto, la decisión final no se basará únicamente en el número de aciertos, sino en el compromiso entre:

- cobertura de fuentes;
- recuperación de evidencia;
- posición de la evidencia relevante;
- cantidad de contexto adicional útil;
- ruido añadido al contexto.

---

## 4. Configuración del experimento

| Parámetro | Valor |
|---|---|
| `CHUNK_SIZE` | 400 caracteres |
| `CHUNK_OVERLAP` | 50 caracteres |
| Modelo de embeddings | `gemini-embedding-2` |
| Base vectorial | ChromaDB |
| Corpus | Definitivo |
| Valores de K | 3 y 4 |
| Índice | Mismo índice para ambos valores |
| Evaluación automática | 11 preguntas in-corpus |
| Evaluación cualitativa | 7 preguntas representativas |

No se regenerarán chunks, embeddings ni ChromaDB entre K=3 y K=4.

---

## 5. Métricas

### 5.1. Source hit

Se considera `Source hit` cuando la fuente esperada aparece entre los K resultados recuperados.

El script `eval_retrieval.py` calcula automáticamente esta métrica sobre todas las preguntas in-corpus de `eval_preguntas.json`.

### 5.2. Evidence hit

Se considera `Evidence hit` cuando el contexto recuperado contiene la evidencia necesaria para responder correctamente según `criterio_evidencia`.

Esta métrica se comprobará manualmente sobre siete preguntas representativas.

### 5.3. Posición de la evidencia

Se anotará la mejor posición en la que aparece el fragmento que contiene la evidencia suficiente para responder.

Si ninguno de los K resultados contiene evidencia suficiente se indicará `-`.

### 5.4. Utilidad del cuarto fragmento

Para K=4 se clasificará el cuarto fragmento en una de estas categorías:

- **Necesario**: introduce evidencia imprescindible que no estaba en el Top-3.
- **Útil**: aporta información relevante adicional, aunque el Top-3 ya era suficiente.
- **Redundante**: repite información ya presente sin aportar evidencia nueva.
- **Irrelevante**: no aporta información útil para responder a la consulta.

Esta métrica permite analizar el coste cualitativo de aumentar K.

### 5.5. Ganancia al aumentar K

Se observarán especialmente:

- preguntas que pasan de `Source hit = No` a `Sí`;
- preguntas que pasan de `Evidence hit = No` a `Sí`;
- número de cuartos fragmentos necesarios o útiles;
- número de cuartos fragmentos redundantes o irrelevantes.

---

## 6. Evaluación automática de Source hit

El evaluador automático se ejecutará sobre todas las preguntas de `eval_preguntas.json`.

Las preguntas fuera de corpus no se contabilizan en esta evaluación de retrieval porque no tienen una fuente esperada. Su abstención se evaluará posteriormente en la capa de generación.

### Resultados

| Métrica | K=3 | K=4 | Diferencia |
|---|---:|---:|---:|
| Preguntas in-corpus evaluadas | 11 | 11 | — |
| Source hit | 11/11 | 11/11 | 0 |
| Source hit (%) | 100 % | 100 % | 0 pp |

### Preguntas que mejoran al pasar de K=3 a K=4

No se observaron mejoras de `Source hit` al aumentar K de 3 a 4.

Con ambos valores, la fuente esperada fue recuperada en las 11 preguntas in-corpus.

Por tanto, desde el punto de vista exclusivo de recuperación de fuente, K=4 no aporta una mejora frente a K=3.

La comparación deberá centrarse ahora en si el cuarto fragmento permite recuperar evidencia que no estaba disponible en el Top-3 y en el posible ruido adicional introducido.

---

## 7. Evaluación cualitativa de Evidence hit

Se reutiliza el mismo subconjunto representativo empleado en los experimentos de chunking.

| ID | Fuente esperada | Criterio de evidencia |
|---|---|---|
| q01 | `crtm_faq.md` | Debe mencionar que la Tarjeta Azul es para empadronados en Madrid y válida en Metro de Madrid y EMT. |
| q03 | `crtm_billetes_tarifas.md` | Debe responder 8 zonas: 6 en Comunidad de Madrid y 2 en Castilla-La Mancha. |
| q05 | `crtm_faq.md` | Debe indicar que se puede terminar la carga sin suplemento y que el perfil se actualiza en la siguiente recarga. |
| q08 | `crtm_billetes_tarifas.md` | Debe citar el 40 % para 26-64 años y Tarjeta Azul, y el 50 % para el Abono 30 días Joven. |
| q09 | `bocm-20251231-precios_transporte.pdf` | Debe confirmar que se mantienen los precios del segundo semestre de 2025. |
| q10 | `bocm-20251231-tarifas_transporte.pdf` | Debe citar el incremento del 3 %, excepto en el abono joven y el título 10 viajes de Castilla y León. |
| q11 | `Paradas CRTM.csv` | Debe responder zona A para Plaza de Castilla. |

### 7.1. Resultados con K=3

| ID | Source hit | Evidence hit | Posición evidencia suficiente | Observación |
|---|:---:|:---:|---:|---|
| q01 | Si | Si | 1 | En todos los fragmentos hay información que permite responder, aunque el mejor es el 1. |
| q03 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q05 | Si | Si | 1 | Los otros dos fragmentos no ofrecen información relevante. |
| q08 | Si | Si | 1 | El fragmento 3 contiene información relevante aunque no permitiría responder la pregunta con precisión. El 2 no es relevante. |
| q09 | Si | Si | 1 | Los otros dos fragmentos contienen información relevante pero incompleta. |
| q10 | Si | No | - | No cumple el criterio de evidencia dentro del Top-3. |
| q11 | Si | Si | 1 | Los 3 fragmentos contienen información relevante. |

### 7.2. Resultados con K=4

| ID | Source hit | Evidence hit | Posición evidencia suficiente | Utilidad del 4.º chunk | Observación |
|---|:---:|:---:|---:|---|---|
| q01 | Si | Si | 1 | Redundante | En todos los fragmentos hay información que permite responder, aunque el mejor es el 1. |
| q03 | Si | Si | 1 | Irrelevante | Los otros tres fragmentos no ofrecen información relevante. |
| q05 | Si | Si | 1 | Irrelevante | Los otros tres fragmentos no ofrecen información relevante. |
| q08 | Si | Si | 1 | Irrelevante | El fragmento 3 contiene información relevante aunque no permitiría responder la pregunta con precisión. 2 y 4 no son relevantes. |
| q09 | Si | Si | 1 | Irrelevante | Los otros tres fragmentos contienen información relevante pero incompleta. |
| q10 | Si | Si | 4 | Necesario | Los otros tres fragmentos no ofrecen información relevante. |
| q11 | Si | Si | 1 | Redundante | Los 4 fragmentos contienen información relevante. |

---

## 8. Comparación directa K=3 vs K=4

| ID | Evidence hit K=3 | Evidence hit K=4 | Cambio | Utilidad del 4.º chunk |
|---|:---:|:---:|---|---|
| q01 | Sí | Sí | Sin cambio | Redundante |
| q03 | Sí | Sí | Sin cambio | Irrelevante |
| q05 | Sí | Sí | Sin cambio | Irrelevante |
| q08 | Sí | Sí | Sin cambio | Irrelevante |
| q09 | Sí | Sí | Sin cambio | Irrelevante |
| q10 | No | Sí | Mejora | Necesario |
| q11 | Sí | Sí | Sin cambio | Redundante |

### Resumen cualitativo

| Métrica | K=3 | K=4 |
|---|---:|---:|
| Source hit sobre las 7 preguntas | 7/7 (100 %) | 7/7 (100 %) |
| Evidence hit sobre las 7 preguntas | 6/7 (85,7 %) | 7/7 (100 %) |
| Evidencia suficiente en posición 1 | 6/7 | 6/7 |
| Preguntas mejoradas al aumentar K | — | 1/7 |

### Calidad del cuarto fragmento

| Clasificación del 4.º chunk | Número de preguntas |
|---|---:|
| Necesario | 1 |
| Útil | 0 |
| Redundante | 2 |
| Irrelevante | 4 |
| **Total** | **7** |

---

## 9. Análisis de q10

q10 constituye el caso más relevante de la comparación.

**Pregunta**

> ¿Qué incremento se aplica a las tarifas del transporte público en 2026 y qué excepciones hay?

**Criterio de evidencia**

La evidencia recuperada debe incluir:

- el incremento del 3 %;
- la excepción correspondiente al abono joven;
- la excepción correspondiente al título de 10 viajes de Castilla y León.

### K=3

**Source hit:** Sí

**Evidence hit:** No

**Posición de evidencia suficiente:** -

Aunque la fuente esperada aparece dentro del Top-3, ninguno de los tres fragmentos contiene toda la información necesaria para cumplir el criterio de evidencia.

Por tanto, recuperar la fuente correcta no es suficiente para responder correctamente a la consulta.

### K=4

**Source hit:** Sí

**Evidence hit:** Sí

**Posición de evidencia suficiente:** 4

El cuarto fragmento contiene la información que faltaba para cumplir completamente el criterio de evidencia.

Por este motivo se clasifica el cuarto resultado como **Necesario**.

### Interpretación

Aumentar K de 3 a 4 corrige un fallo real del retrieval.

La mejora no consiste en recuperar una fuente nueva, ya que la fuente correcta ya estaba presente con K=3, sino en ampliar el contexto hasta incluir el fragmento que contiene la evidencia completa.

Este resultado muestra nuevamente que `Source hit` y `Evidence hit` miden aspectos diferentes del sistema y que evaluar únicamente la presencia del documento esperado puede ocultar fallos relevantes.

---

## 10. Análisis del ruido añadido

Aumentar K de 3 a 4 introduce un fragmento adicional en todas las consultas.

La evaluación cualitativa muestra que este fragmento adicional no resulta útil en la mayoría de las preguntas:

| Tipo de cuarto fragmento | Casos | Porcentaje |
|---|---:|---:|
| Necesario | 1 | 14,3 % |
| Útil | 0 | 0 % |
| Redundante | 2 | 28,6 % |
| Irrelevante | 4 | 57,1 % |

En seis de las siete preguntas el cuarto fragmento no es necesario para responder correctamente.

En q01 y q11 aporta información relacionada, pero redundante respecto a la ya recuperada.

En q03, q05, q08 y q09 el cuarto fragmento no aporta información útil para responder a la consulta.

Sin embargo, en q10 el cuarto fragmento resulta imprescindible y permite pasar de `Evidence hit = No` a `Evidence hit = Sí`.

Por tanto, K=4 introduce una cantidad apreciable de información redundante o irrelevante, pero a cambio corrige un fallo real que no podía resolverse con K=3.

---

## 11. Coste relativo

El cambio de K=3 a K=4 no requiere regenerar chunks, embeddings ni el índice vectorial.

El coste adicional se limita a recuperar un fragmento más por consulta y, posteriormente, incluirlo en el contexto enviado al modelo generador.

Esto supone aproximadamente un 33 % más de fragmentos recuperados por consulta, aunque el incremento real de tokens dependerá del tamaño de cada chunk.

En la evaluación realizada, seis de los siete cuartos fragmentos no eran necesarios para cumplir el criterio de evidencia.

Por tanto, K=4 presenta un coste adicional de contexto y puede introducir más ruido. Sin embargo, este incremento permite resolver correctamente q10, que falla con K=3.

Dado el reducido tamaño absoluto del contexto recuperado y la mejora observada en Evidence hit, el coste adicional se considera asumible para MadridRumbo.

---

## 12. Criterio de decisión

La evaluación automática obtiene el mismo `Source hit` con ambos valores:

- K=3: 11/11 preguntas in-corpus.
- K=4: 11/11 preguntas in-corpus.

Por tanto, aumentar K no mejora la capacidad de recuperar la fuente esperada.

La diferencia aparece al evaluar el contenido real de los fragmentos.

Sobre las siete preguntas analizadas cualitativamente:

- K=3 obtiene `Evidence hit` en 6/7 preguntas.
- K=4 obtiene `Evidence hit` en 7/7 preguntas.

La mejora procede de q10, donde el cuarto fragmento contiene evidencia imprescindible que no aparece dentro del Top-3.

El principal inconveniente es el ruido añadido: en seis de las siete preguntas el cuarto fragmento es redundante o irrelevante.

Sin embargo, el incremento de contexto se considera asumible frente a la mejora obtenida en cobertura de evidencia.

Por ello se selecciona K=4 como valor definitivo para el retrieval.

---

## 13. Decisión final

**Configuración seleccionada: `K = 4`**

La elección se basa en que ambos valores recuperan la fuente esperada en el 100 % de las 11 preguntas in-corpus, pero K=4 mejora la recuperación efectiva de evidencia en el análisis cualitativo.

Con K=3 se obtiene evidencia suficiente en 6 de las 7 preguntas evaluadas (85,7 %), mientras que con K=4 se obtiene en las 7 (100 %).

La mejora se concentra en q10, cuyo cuarto fragmento contiene información necesaria que no estaba disponible en el Top-3.

Aunque K=4 introduce información redundante o irrelevante en otras consultas, el coste adicional de recuperar un único chunk se considera aceptable para MadridRumbo.

La configuración definitiva de retrieval queda por tanto establecida en:

```python
TOP_K = 4
```

Esta decisión es específica para el corpus, la estrategia de chunking 400 / 50 y el conjunto de evaluación utilizados en MadridRumbo.