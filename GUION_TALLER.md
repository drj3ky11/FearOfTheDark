# Guión de Taller — FearOfTheDark
### Análisis de leaks de ransomware con LLMs locales

**Nivel**: Máster / Investigación en Ciberseguridad  
**Duración estimada**: 4–5 horas (con ejecuciones)  
**Requisitos**: Python 3.10+, Ollama, 16 GB RAM, ~12 GB disco

---

## Contexto y motivación

En febrero de 2022, un investigador ucraniano filtró las comunicaciones internas del grupo de ransomware **Conti** tras su declaración de apoyo a la invasión rusa. Dos años después, en 2024, los chats internos de **Black Basta** sufrieron una filtración similar. Ambos datasets son hoy referencia en threat intelligence.

Este taller usa esos datos públicos para practicar un pipeline de análisis con LLMs en local: sin enviar datos a APIs externas, reproducible en cualquier máquina con Ollama.

**Lo que aprenderemos:**
- Parsear datos en formatos no estándar del mundo real
- Clasificar texto en ruso con un LLM local
- Generar embeddings semánticos y aplicar clustering
- Inferir estructura organizativa de un grupo criminal a partir de sus comunicaciones

**Lo que NO haremos:**
- Identificar personas reales
- Usar infraestructura identificada (C2, wallets BTC)
- Redistribuir los datos originales

---

## Setup inicial

### Instalación de dependencias del sistema

```bash
sudo apt install p7zip-full
```

### Modelos Ollama

```bash
# Modelo de chat/razonamiento (9 GB) — para clasificación y perfilado
ollama pull qwen2.5:14b

# Modelo de embeddings (957 MB) — para clustering semántico
ollama pull nomic-embed-text-v2-moe
```

> **Nota para el taller**: arrancar la descarga de modelos antes de empezar.  
> `qwen2.5:14b` tarda ~15 min con buena conexión.

### Paquetes Python

```bash
pip install pandas pyarrow matplotlib langdetect tqdm ollama umap-learn hdbscan scikit-learn
```

### Estructura del proyecto

```
FearOfTheDark/
├── ContiLeaks/
│   ├── data/{raw,processed}/
│   ├── notebooks/00–03
│   └── src/loaders.py
├── BlackBasta/
│   ├── data/{raw,processed}/
│   ├── notebooks/00–03
│   └── src/loaders.py
└── GUION_TALLER.md  ← estás aquí
```

---

## Módulo 1 — ContiLeaks

### Contexto del dataset

| Campo | Valor |
|---|---|
| Período | Junio 2020 – Febrero 2022 |
| Plataformas | Jabber (XMPP) + Rocket.Chat |
| Mensajes totales (brutos) | 254,884 |
| Mensajes tras limpieza | 216,303 |
| Actores únicos | 485 |
| Canales/conversaciones | 635 |
| Idioma principal | Ruso (~62%), búlgaro/macedonio (~21%), ucraniano (~4%) |
| Fuente | PRODAFT / VXUnderground |

**Los top actores por volumen de mensajes:**

```
target     26,770   bentley    17,440   tl1       12,157
stern      11,948   defender    9,666   hof        5,041
user8       4,914   mango       4,158   driver     4,038
```

> **Punto de discusión**: ¿Qué indica el volumen de mensajes sobre el rol de un actor?  
> `target` lidera con diferencia — ¿coordinador central o bot?

---

### 00 — Extracción y exploración

**Notebook**: `ContiLeaks/notebooks/00_extract_and_explore.ipynb`

Los datos llegan comprimidos en `.zip`/`.7z`. Este notebook:
1. Descomprime con `p7zip`
2. Identifica los tres formatos de fichero presentes
3. Muestra ejemplos de cada fuente

**Formatos encontrados:**

| Fuente | Formato | Ficheros |
|---|---|---|
| Jabber 2020 | JSON concatenado (objetos sin array wrapper) | ~1 fichero por IP/día |
| Jabber 2021–2022 | Ídem | ~1 fichero por IP/día |
| Rocket.Chat | JSON con clave `"messages": [...]` | 1 fichero por canal/día |

> **Formato Jabber — detalle importante**:  
> Los ficheros son NDJSON "roto": objetos JSON concatenados directamente, sin comas ni array wrapper.  
> Hay que iterar con `JSONDecoder.raw_decode()` en lugar de `json.loads()`.

---

### 01 — Carga unificada y limpieza

**Notebook**: `ContiLeaks/notebooks/01_load_and_clean.ipynb`  
**Output**: `data/processed/conti_unified.parquet`

#### Pipeline

```
Jabber 2020  ──┐
Jabber 2021  ──┼──► normalize_schema() ──► concat ──► clean ──► detect_lang ──► parquet
Rocket.Chat  ──┘
```

**Schema unificado:**

```python
{
  'timestamp': datetime64[ns, UTC],   # normalizado a UTC
  'username':  str,                    # sin dominio (@xxx → xxx)
  'to_user':   str,                    # destinatario o sala
  'message':   str,
  'source':    str,                    # 'jabber_2020' | 'jabber_2021' | 'rocketchat'
  'channel':   str,                    # nombre de fichero origen
  'lang':      str,                    # código ISO detectado por langdetect
}
```

**Limpieza aplicada:**
- Eliminar mensajes vacíos o solo whitespace → **−12,407 filas**
- Eliminar duplicados exactos (timestamp + username + message) → **−26,174 filas**
- Normalizar username a lowercase

**Detección de idioma** (`langdetect` sobre primeros 200 chars):

```
ru    134,020   bg    23,929   mk    22,581
uk     8,176   und    8,093   en     6,687
```

> **Punto de discusión**: `bg` (búlgaro) y `mk` (macedonio) son lingüísticamente muy similares al ruso  
> y `langdetect` los confunde con frecuencia. El ruso real es mayor del 62% que aparece.

---

### 02 — Análisis con LLM

**Notebook**: `ContiLeaks/notebooks/02_llm_analysis.ipynb`  
**Modelo**: `qwen2.5:14b` (local, sin API externa)  
**Output**: `data/processed/conti_sample_classified.parquet` + `actor_profiles.json`

#### Estrategia de muestreo

Con 216k mensajes no podemos clasificar todo (tomaría días).  
**Solución**: top 30 actores × 50 mensajes distribuidos uniformemente en el tiempo = ~1,500 mensajes.

```python
def sample_actor(actor_df, n):
    # Muestra 1 mensaje cada len/n posiciones → cubre todo el rango temporal
    indices = [int(i * len(actor_df) / n) for i in range(n)]
    return actor_df.iloc[indices]
```

> **Por qué distribución uniforme y no aleatoria**: evita sesgo hacia periodos de alta actividad.

#### Categorías de clasificación

| Categoría | Descripción |
|---|---|
| `technical` | Desarrollo de malware, builds, código, infraestructura |
| `operational` | Ataques, targets, accesos, despliegue |
| `financial` | Pagos, bitcoin, ransom, negociaciones |
| `organizational` | Gestión, tareas, RRHH |
| `comms` | Comunicación general, saludos, off-topic |
| `unknown` | Demasiado corto o ambiguo |

**Prompt de clasificación** (temperature=0 para reproducibilidad):

```
You are a threat intelligence analyst classifying messages from the leaked Conti
ransomware group chats. Messages are mostly in Russian. Classify each message
into exactly one category: technical / operational / financial / organizational /
comms / unknown.
Reply with ONLY the category name, nothing else.
```

> **Detalles de implementación importantes**:
> - `temperature: 0` — resultados deterministas
> - `num_predict: 10` — forzamos respuesta corta, sin texto extra
> - Checkpoint cada 50 mensajes — si se interrumpe, retoma donde lo dejó
> - Fallback: si el modelo responde algo no esperado → `unknown`

#### Perfilado de actores

Para cada actor, enviamos una muestra de sus mensajes y pedimos al LLM que infiera su rol:

```
{
  "role": "leader | developer | operator | negotiator | affiliate | support | unknown",
  "confidence": "high | medium | low",
  "summary": "2-3 sentences describing responsibilities",
  "evidence": ["quotes from messages"]
}
```

> **Tiempo estimado**: ~25–30 min para 1,500 mensajes + 30 perfiles con `qwen2.5:14b`.

---

### 03 — Embeddings y clustering

**Notebook**: `ContiLeaks/notebooks/03_embeddings_profiling.ipynb`  
**Modelo**: `nomic-embed-text-v2-moe` (768 dims, vía `ollama.embed()`)  
**Output**: `bb_message_embeddings.npy` + `actor_embeddings.parquet`

#### Por qué dos modelos distintos

| Tarea | Modelo correcto | Por qué |
|---|---|---|
| Clasificar / razonar | `qwen2.5:14b` (generativo) | Entiende instrucciones, produce texto |
| Generar embeddings | `nomic-embed-text-v2-moe` (embedding) | Optimizado para similitud semántica, API `embed()` |

> **Error común**: intentar usar el modelo de embeddings con `ollama.chat()` — no funciona.  
> La API correcta es `ollama.embed(model=..., input=[lista_de_textos])`.

#### Pipeline de embeddings

```
mensajes ──► ollama.embed() en batches de 32 ──► matriz (N, 768)
                                                        │
                                              media por actor
                                                        │
                                              UMAP (768D → 2D, métrica coseno)
                                                        │
                                              HDBSCAN (clustering)
```

**Parámetros UMAP:**
```python
umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
```

**Parámetros HDBSCAN:**
```python
hdbscan.HDBSCAN(min_cluster_size=3, min_samples=2)
# Cluster -1 = "ruido" (actores sin patrón comunicativo claro)
```

> **Punto de discusión**: ¿Qué significa que dos actores tengan embeddings similares?  
> No que hablen de lo mismo, sino que su *estilo y vocabulario habitual* es similar.  
> Actores con el mismo rol tienden a agruparse.

**Visualizaciones generadas:**
1. Scatter UMAP de mensajes coloreado por categoría
2. Scatter UMAP de actores coloreado por cluster HDBSCAN
3. Heatmap cluster × rol LLM (validación cruzada)
4. Top 3 actores más similares por similitud coseno

> **Tiempo estimado**: ~3–4 min para embeddings de 1,500 mensajes en batches de 32.

---

## Módulo 2 — Black Basta

### Contexto del dataset

| Campo | Valor |
|---|---|
| Período | Septiembre 2023 – Septiembre 2024 |
| Plataforma | Matrix (matrix.bestflowers247.online) |
| Mensajes totales (tras limpieza) | ~195,400 |
| Actores únicos | 49 |
| Canales (rooms) | 79 |
| Idioma principal | Ruso |
| Fuente | PRODAFT / VXUnderground |

**Diferencias clave con Conti:**

| | Conti | Black Basta |
|---|---|---|
| Plataforma | Jabber + Rocket.Chat | Matrix |
| Actores | 485 | 49 (grupo más pequeño) |
| Formato datos | JSON multi-fuente | Un solo pseudo-JSON |
| Periodo | 2020–2022 | 2023–2024 |
| Extracción | Archivos comprimidos | No necesaria |

---

### 00 — Exploración del formato

**Notebook**: `BlackBasta/notebooks/00_explore.ipynb`

El fichero `blackbasta_chats.json` **no es JSON válido**:

```
{                                                    ← sin comillas en claves
    timestamp: 2023-09-18 13:35:07,                 ← valor sin comillas
    chat_id: !VdvDXHFZwWDpIAtpCj:matrix.org,
    sender_alias: @usernamenn:matrix.org,
    message: texto del mensaje                       ← puede ser multilínea
}
{                                                    ← siguiente objeto concatenado
    ...
}
```

> **Punto de discusión**: datos del mundo real raramente vienen en formatos limpios.  
> Antes de escribir código, siempre explorar manualmente: `head`, `wc -l`, búsquedas con `grep`.

---

### 01 — Carga y limpieza

**Notebook**: `BlackBasta/notebooks/01_load_and_clean.ipynb`  
**Output**: `data/processed/blackbasta_unified.parquet`

#### Parser custom con regex

```python
_RE_BLOCK = re.compile(r'\{([^{}]*?)\}', re.DOTALL)  # extrae cada objeto
_RE_TS    = re.compile(r'timestamp:\s*(.+?),\s*\n')
_RE_CHAT  = re.compile(r'chat_id:\s*(.+?),\s*\n')
_RE_ALIAS = re.compile(r'sender_alias:\s*(.+?),\s*\n')
_RE_MSG   = re.compile(r'message:\s*(.*)', re.DOTALL)
```

**Normalización de IDs Matrix:**
```
@usernamenn:matrix.bestflowers247.online  →  usernamenn   (username)
!VdvDXHFZwWDpIAtpCj:matrix.org           →  VdvDXHFZwWDpIAtpCj  (channel)
```

**Schema de salida** (mismo que Conti excepto `to_user` — Matrix no tiene mensajes directos):

```python
{ 'timestamp', 'username', 'channel', 'message', 'source': 'blackbasta', 'lang' }
```

---

### 02 — Análisis con LLM

**Notebook**: `BlackBasta/notebooks/02_llm_analysis.ipynb`

**Diferencia vs Conti**: con solo 49 actores, muestreamos **todos** (no solo top 30)  
y tomamos **80 mensajes/actor** en lugar de 50 → ~3,900 mensajes totales.

Las categorías y el prompt son idénticos para poder comparar resultados entre grupos.

> **Tiempo estimado**: ~55–70 min para ~3,900 mensajes con `qwen2.5:14b`.

---

### 03 — Embeddings y clustering

**Notebook**: `BlackBasta/notebooks/03_embeddings_profiling.ipynb`

**Diferencia vs Conti**: con 49 actores (vs 485), añadimos un **heatmap de similitud coseno**  
entre todos los actores — con 485 sería ilegible, con 49 es informativo.

**Parámetros UMAP ajustados** para dataset más pequeño:
```python
umap.UMAP(n_neighbors=10, ...)  # reducido de 15 porque hay menos puntos
```

**Visualización extra**: scatter de actores con etiqueta `nombre (rol)` simultáneamente —  
posible porque hay pocos actores y las etiquetas no se solapan tanto.

---

## Comparativa entre grupos

### Diferencias estructurales

| | Conti | Black Basta |
|---|---|---|
| Tamaño del grupo | Grande (485 actores) | Pequeño (49 actores) |
| Jerarquía | Compleja, múltiples capas | Más plana |
| Plataforma | Jabber (P2P) + Rocket.Chat | Matrix (centralizado) |
| Período operativo | ~20 meses | ~12 meses |
| Mensajes/actor (media) | ~446 | ~3,988 |

> **Punto de discusión**: Conti era una organización grande con estructura empresarial documentada.  
> Black Basta es más pequeño y concentrado — mayor cohesión, menor compartimentación.

### Lo que el análisis LLM permite detectar

1. **Roles funcionales** sin conocimiento previo del grupo — el LLM infiere desde el texto
2. **Pares de actores con comunicación similar** — posible colaboración estrecha o mismo rol
3. **Evolución temporal** — ¿cambia la categoría dominante de mensajes antes/después de eventos?
4. **Canales especializados** — ¿hay rooms dedicados a finance, técnico, etc.?

### Limitaciones del análisis

- **Muestra, no universo**: clasificamos ~1,500 / ~3,900 mensajes de ~216k / ~195k
- **Sesgos de langdetect**: ruso → búlgaro/macedonio en mensajes cortos
- **nomic-embed-text-v2-moe**: mejor en inglés que en ruso — embeddings son aproximados
- **Alias anonimizados en BlackBasta**: los usernames reales fueron sustituidos por `@usernameXX`
- **El LLM puede alucinar roles**: validar siempre con evidencias que el propio modelo cita

---

## Módulo 3 — LockBit

### Contexto del dataset

| Campo | Valor |
|---|---|
| Tipo de dato | Volcado SQL del panel de administración (MySQL 8.0) |
| Período | Diciembre 2024 – Abril 2025 (~4,5 meses) |
| Operadores registrados | 75 |
| Víctimas comprometidas | 246 |
| Víctimas que pagaron | 7 (~2,8% tasa de conversión) |
| Builds de malware | 1.183 |
| Mensajes de negociación | 4.423 |
| Invites de afiliación | 3.693 |
| Fuente | Filtración pública (abril 2025) |

**Diferencia fundamental con Conti y BlackBasta:**

| | ContiLeaks / BlackBasta | LockBit |
|---|---|---|
| Tipo | Chats internos del grupo | Base de datos operacional del panel |
| Datos | Comunicaciones entre miembros | Víctimas, builds, negociaciones con víctimas |
| Formato | JSON / pseudo-JSON | SQL dump (MySQL) |
| Perspectiva | Organización interna | Operaciones externas (víctimas) |
| Parser | Regex / JSON decoder | State machine sobre INSERT statements |

> **Punto de discusión**: ContiLeaks y BlackBasta muestran _cómo se organizan internamente_.  
> LockBit muestra _cómo operan hacia el exterior_: víctimas, builds, negociaciones, pagos.  
> Son perspectivas complementarias del mismo tipo de amenaza.

---

### 00 — Extracción y exploración

**Notebook**: `LockBit/notebooks/00_extract_and_explore.ipynb`

El archivo `paneldb_dump.sql` (27 MB descomprimido, ~114.000 líneas) es un dump MySQL estándar.  
Se parsea en **dos pasadas** sin necesidad de un servidor MySQL:

```python
# Paso 1: extraer esquemas (CREATE TABLE → nombres de columnas)
# Paso 2: extraer datos (INSERT INTO → filas por tabla)
tables = load_lockbit(zip_path)  # dict[str, pd.DataFrame]
```

**Tablas extraídas** (de las 20 disponibles, guardamos 6):
- `users` — operadores y afiliados (75 registros)
- `clients` — víctimas comprometidas (246 registros)
- `chats` — negociaciones de rescate (4.423 mensajes)
- `builds` — compilaciones de malware (1.183 registros)
- `btc_addresses` — wallets de pago (~60.000 registros)
| `invites` — códigos de afiliación (3.693 registros)

> La tabla `pkeys` (30.000 registros) contiene claves criptográficas y se excluye  
> deliberadamente del análisis para no facilitar ningún uso indebido.

---

### 01 — Análisis operacional

**Notebook**: `LockBit/notebooks/01_operational_analysis.ipynb`

Análisis de datos estructurados **sin LLM**:

#### Jerarquía de operadores
- El campo `permissions` (JSON array) indica módulos habilitados por afiliado
- `level=4` → admin, `level=1` → afiliado estándar
- `tag=newbie/verified` → estado de cada afiliado

#### Funnel de conversión (dato clave del taller)

```
246 víctimas en panel
 ↓ 208 iniciaron chat  (84,6%)
 ↓   7 pagaron         ( 2,8%)
 ↓   0 descifrado done ( 0,0%)
```

> **Punto de discusión**: El 0% de descifrado completado a pesar de 7 pagos levanta preguntas.  
> ¿Falló el proceso técnico? ¿Modelo de "exit" antes de entregar las claves? ¿Panel capturado antes?

#### Builds de malware
- 1.183 builds creados por 54 operadores distintos
- Variantes: tipo 25 (LB 2.5), 30 (LB 3.0), 40, 46, 50
- Cada build puede tener `company_website` y `revenue` range ($1k – $999k)

#### Estructura de afiliación
- 3.693 invites — evidencia de reclutamiento masivo
- Dos criptomonedas: BTC y XMR para pago de la cuota de afiliación

---

### 02 — Análisis LLM de negociaciones

**Notebook**: `LockBit/notebooks/02_llm_chats.ipynb`

**Diferencia clave vs notebooks 02 anteriores**: aquí los chats son entre operadores LockBit  
(extorsionadores) y víctimas (empresas comprometidas), **no comunicación interna del grupo**.

#### Fases de negociación clasificadas

| Fase | Descripción |
|---|---|
| `opening` | Primer contacto, instrucciones iniciales |
| `technical_proof` | Petición de ficheros de prueba, test de descifrado |
| `price_negotiation` | Importe del rescate, descuentos, presión temporal |
| `payment_instructions` | Dirección Bitcoin, confirmación de pago |
| `closing` | Entrega de clave, amenazas si no se paga |
| `unknown` | Irrelevante, corto o ambiguo |

#### Perfilado de operadores (estilo de negociación)
- El LLM infiere: `aggressive / professional / patient / scripted / technical`
- 35 operadores activos en chats, se perfilan los que tienen ≥5 mensajes

> **Punto de discusión**: ¿Se puede distinguir un operador profesional de un "newbie"  
> solo por cómo escribe en inglés a sus víctimas? ¿Qué implica eso sobre la organización?

> **Tiempo estimado**: ~15–20 min (4.423 mensajes × ~0.25 s/msg con `qwen2.5:14b`).

---

### 03 — Embeddings y clustering de negociaciones

**Notebook**: `LockBit/notebooks/03_embeddings.ipynb`

Con 4.423 mensajes (vs 195k en BlackBasta) se pueden embeber **todos** sin muestreo.

**Parámetros UMAP/HDBSCAN:**
```python
umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine')
hdbscan.HDBSCAN(min_cluster_size=20, min_samples=5)
```

**Visualizaciones:**
1. Scatter coloreado por fase de negociación — ¿están semánticamente separadas?
2. Scatter coloreado por rol (operador / víctima)
3. Heatmap de similitud coseno operador×operador (máx 35×35, legible)

> **Punto de discusión**: Si dos operadores tienen similitud coseno muy alta,  
> ¿podrían ser el mismo individuo con cuentas distintas? ¿O seguir el mismo script?

---

### 04 — Analista conversacional (bonus)

**Notebook**: `LockBit/notebooks/04_chat_analyst.ipynb`

Interfaz de consulta en lenguaje natural sobre la base de datos. El LLM recibe el esquema  
completo de los DataFrames como contexto, genera código pandas para responder y el notebook  
lo ejecuta mostrando **código generado + resultado**.

#### Patrón: text-to-pandas

```python
# El alumno edita esta celda y ejecuta:
ask("¿Qué operador tiene más víctimas asignadas?")

# El LLM genera:
result = (clients.groupby('advid')
          .size()
          .reset_index(name='n_victims')
          .merge(users[['id','login']], left_on='advid', right_on='id')
          .sort_values('n_victims', ascending=False)
          .head(5))

# El notebook ejecuta el código y muestra la tabla
```

#### Historial de sesión (preguntas encadenadas)

```python
ask("¿Qué operador tiene más víctimas?")
ask("¿Cuántos de sus builds son de tipo 30?")  # el LLM recuerda el operador anterior
reset_memory()  # para empezar un hilo nuevo
```

#### Parámetros

| Parámetro | Descripción |
|---|---|
| `show_code=True` | Muestra el código generado (útil en clase) |
| `show_code=False` | Solo muestra el resultado (más limpio) |
| `memory=True` | Acumula historial para preguntas de seguimiento |
| `memory=False` | Consulta aislada sin contexto previo |

> **Para el taller**: este notebook funciona bien como actividad libre al final.  
> Los alumnos proponen preguntas y debaten si el código generado es correcto.  
> Es también una demostración de las capacidades y limitaciones del LLM como analista.

> **Punto de discusión**: ¿Por qué deepseek-r1 clasifica todo como `unknown` aquí  
> pero qwen2.5 no? Los modelos de razonamiento (R1, o1) generan un bloque `<think>`  
> que agota el presupuesto de tokens antes de producir la respuesta real.

---

## Comparativa entre los tres grupos

| | Conti | Black Basta | LockBit |
|---|---|---|---|
| Tipo de dato | Chats internos | Chats internos | Panel operacional |
| Período | 2020–2022 | 2023–2024 | dic 2024 – abr 2025 |
| Actores/Operadores | 485 | 49 | 75 |
| Mensajes analizados | ~216.000 | ~195.400 | 4.423 (negociaciones) |
| LLM target | Mensajes internos | Mensajes internos | Negociaciones con víctimas |
| Dato financiero | No | No | 7 pagos, funnel completo |
| Notebooks | 00–03 | 00–03 | 00–04 (+ analista conversacional) |

---

## Apéndice técnico

### Por qué LLMs locales (Ollama) en lugar de API

- **Privacidad**: datos sensibles no salen del equipo
- **Coste**: sin coste por token para miles de clasificaciones
- **Reproducibilidad**: mismo modelo, mismos resultados
- **Autonomía**: funciona offline, sin dependencia de terceros

### Elección de modelos

| Modelo | Tarea | Alternativas |
|---|---|---|
| `qwen2.5:14b` | Clasificación y razonamiento en ruso | `llama3.1:8b` (más rápido, menos preciso), `llama3.3:70b` (más lento, más preciso) |
| `nomic-embed-text-v2-moe` | Embeddings semánticos | `bge-m3` (mejor soporte multilingüe/ruso), `mxbai-embed-large` |

> Para mejor calidad en ruso: `bge-m3` supera a nomic en benchmarks multilingües,  
> pero el modelo es más grande (~567M params vs ~137M).

### Checkpoint pattern

Patrón usado para clasificaciones largas:

```python
# Guardar progreso cada N mensajes
if (i + 1) % CHECKPOINT_EVERY == 0:
    partial.to_parquet(CHECKPOINT_PATH)

# Al inicio: retomar si existe
if CHECKPOINT_PATH.exists():
    done = pd.read_parquet(CHECKPOINT_PATH)
    todo = sample[~sample.index.isin(done.index)]
```

> Imprescindible cuando un proceso tarda >30 min: un kernel crash lo pierde todo.

### Batch embeddings

```python
# CORRECTO — una llamada, N embeddings
resp = ollama.embed(model='nomic-embed-text-v2-moe', input=['texto1', 'texto2', ...])
embeddings = resp.embeddings  # lista de listas de floats

# INCORRECTO — no usar para embeddings
ollama.chat(model='nomic-embed-text-v2-moe', ...)  # falla, no es modelo de chat
```

### Patrón text-to-pandas (analista conversacional)

El LLM recibe como contexto el esquema de los DataFrames y genera código pandas ejecutable.  
El notebook ejecuta el código con `exec()` en un namespace controlado:

```python
SYSTEM_PROMPT = f"""
Available DataFrames: users ({len(users)} rows), clients, chats, builds, ...
[esquema de columnas y ejemplo de valores]

Rules:
- Store your answer in a variable called `result`
- Do NOT import anything — pd and all DataFrames are already in scope
"""

namespace = {**DATAFRAMES, 'pd': pd, 'result': None}
exec(generated_code, namespace)
display(namespace['result'])
```

**Por qué modelos de razonamiento (deepseek-r1, o1) no funcionan bien aquí:**  
Generan un bloque `<think>...</think>` antes de la respuesta. Con `num_predict` bajo,  
el modelo agota el presupuesto en el bloque de pensamiento y nunca llega a producir  
la respuesta real → devuelve vacío o categoría inválida → `unknown`. La solución es  
usar modelos de instrucción estándar (`qwen2.5:14b`) para tareas de clasificación masiva.

---

*Material para uso académico — FearOfTheDark Project*
