# Guión de Taller — FearOfTheDark
### Análisis de leaks de ransomware con LLMs locales

**Nivel**: Máster / Investigación en Ciberseguridad  
**Duración estimada**: 4–5 horas (con ejecuciones)  
**Requisitos**: Python 3.10+, Ollama, 16 GB RAM, ~12 GB disco

---
Hay que extraer data_Vruto en en la raiz de bloque5_ransomware. No hay que tocar las carpetas para no estropear las rutas.

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

# Modelo de embeddings (4.7 GB) — para clustering semántico (4096 dims)
ollama pull qwen3-embedding
```

> **Nota para el taller**: arrancar la descarga de modelos antes de empezar.  
> `qwen2.5:14b` tarda ~15 min con buena conexión.  
> `qwen3-embedding` es el modelo de embeddings de todos los módulos — **no sustituir por nomic-embed-text-v2-moe**, los vectores deben vivir en el mismo espacio para el análisis comparativo.

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
├── LockBit/
│   ├── data/{raw,processed}/
│   ├── notebooks/00–04
│   └── src/loaders.py
├── ExploitIn/
│   ├── data/{raw,processed}/
│   ├── notebooks/00–03
│   └── src/loaders.py
├── comparative/
│   └── 01_cross_group_similarity.ipynb
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
**Modelo**: `qwen3-embedding` (4096 dims, vía `ollama.embed()`)  
**Output**: `message_embeddings.npy` + `actor_embeddings.parquet`

#### Por qué dos modelos distintos

| Tarea | Modelo correcto | Por qué |
|---|---|---|
| Clasificar / razonar | `qwen2.5:14b` (generativo) | Entiende instrucciones, produce texto |
| Generar embeddings | `qwen3-embedding` (embedding) | Optimizado para similitud semántica, API `embed()`, 4096 dims |

> **Error común**: intentar usar el modelo de embeddings con `ollama.chat()` — no funciona.  
> La API correcta es `ollama.embed(model=..., input=[lista_de_textos])`.
>
> **Por qué `qwen3-embedding` y no `nomic-embed-text-v2-moe`**: todos los módulos deben usar  
> el mismo modelo para que la comparativa cruzada tenga sentido matemático. `qwen3-embedding`  
> produce vectores de 4096 dims vs 768 de nomic, con mejor cobertura del ruso y mayor capacidad de contexto (40k tokens).

#### Pipeline de embeddings

```
mensajes ──► ollama.embed() en batches de 32 ──► matriz (N, 4096)
                                                        │
                                              media L2-normalizada por actor
                                                        │
                                              UMAP (4096D → 2D, métrica coseno)
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

> **Tiempo estimado**: ~8–10 min para embeddings de 1,500 mensajes (mayor coste por 4096 dims vs 768).

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

## Comparativa Conti ↔ Black Basta (módulos 1 y 2)

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

## Módulo 4 — Exploit.in

### Contexto del dataset

| Campo | Valor |
|---|---|
| Tipo de dato | Dump SQL de foro underground (Invision Power Board) |
| Período | ~2005–2008 |
| Posts públicos | 80.891 |
| Mensajes privados | 14.318 |
| Hilos del foro | 13.925 |
| Usuarios registrados | 9.647 |
| Votos de reputación | 4.785 |
| Secciones del foro | 41 (17 activas) |
| Idioma principal | Ruso |
| Fuente | Leak público (documentado en Have I Been Pwned) |

**Diferencia fundamental con los módulos anteriores:**

| | ContiLeaks / BlackBasta | LockBit | Exploit.in |
|---|---|---|---|
| Tipo | Comunicaciones internas de grupo criminal | Panel operacional | Foro público underground |
| Actores | Operadores de ransomware (cerrado) | Afiliados y víctimas | Comunidad underground rusa (abierto) |
| Perspectiva | Organización interna | Operaciones externas | Ecosistema de formación |
| Temporal | 2020–2025 | 2024–2025 | **2005–2008** (precede a todo lo anterior) |

> **Punto de discusión clave**: Exploit.in precede históricamente a Conti y BlackBasta por más de 12 años.  
> Es el tipo de foro donde se forman los futuros operadores de ransomware: aprenden técnicas,  
> venden sus primeros dumps, construyen reputación. Los módulos anteriores muestran el producto final;  
> Exploit.in muestra el **ecosistema de origen**.

---

### 00 — Extracción y exploración

**Notebook**: `ExploitIn/notebooks/00_extract_and_explore.ipynb`

El dump SQL (~190 MB descomprimido) es un volcado MySQL estándar de IPB.  
Se parsea con el mismo patrón de dos pasadas que LockBit:

```python
tables = load_exploitin(zip_path)
# dict: posts, topics, forums, members, message_text, message_topics, reputation
```

**Particularidades del parser:**
- Posts contienen HTML (BBCode + `<br />`) — se limpia con `html.parser`
- Timestamps Unix → UTC datetime
- Mensajes privados: `message_topics` contiene remitente/destinatario; `message_text` contiene el contenido

**Secciones de mayor interés para TI:**

| Sección | Posts | Hilos |
|---|---|---|
| Покупка/Продажа/Обмен/Работа | 7.750 | 2.627 |
| Флейм (off-topic) | 6.176 | 596 |
| Безопасность и взлом | 6.396 | 828 |
| 1st Access Level (premium) | 5.121 | 415 |
| Деньги (carding) | 2.978 | 377 |

---

### 01 — Análisis del foro

**Notebook**: `ExploitIn/notebooks/01_forum_analysis.ipynb`

Análisis estructurado **sin LLM**:

#### Jerarquía de usuarios (grupos IPB)

| ID | Nombre (ruso) | Significado | Usuarios |
|---|---|---|---|
| 4 | Админ | Administrador | 3 |
| 6 | Супермодератор | Supermod | 1 |
| 7 | Модератор | Moderador | 9 |
| 100 | Доверенный | Usuario de confianza | 8 |
| 3 | Пользователь | Usuario regular | 9.400 |
| 8 | Забанен | Baneado | 219 |

> **Punto de discusión**: el 2,3% de usuarios baneados (219/9.647) tiene más posts previos  
> que la media. Los foros underground purgan a los estafadores, pero tarde.

#### Sistema de reputación — red de confianza

- 4.785 votos (positivos + negativos) con comentarios en texto libre
- El sistema de reputación es la moneda de confianza para transacciones en el marketplace
- La tabla `ibf_reputation.message` contiene los comentarios → fuente de inteligencia sobre quién confía en quién

#### Marketplace — lo que se compraba/vendía en 2005–2008

Categorías principales (búsqueda por palabras clave en ruso):
```
shells / accesos RDP     ~800 posts
carding / dumps CVV      ~600 posts
spam / mailing           ~500 posts
passwords / accounts     ~450 posts
malware / crypters       ~350 posts
```

#### Black List & White List

Sección donde la comunidad documenta estafadores internos:
- 73 hilos, 554 posts — registro de fraudes entre miembros
- Formato: `[nick] кинул [cantidad] на [método]` ("X estafó Y en Z")

---

### 02 — Clasificación LLM de posts

**Notebook**: `ExploitIn/notebooks/02_llm_posts.ipynb`  
**Modelo**: `qwen2.5:14b`

#### Selección de muestra

Con 80.891 posts no se clasifican todos. Estrategia: ~5.000 posts de las 9 secciones más relevantes, con cuotas proporcionales:

| Sección | Cuota |
|---|---|
| Безопасность и взлом | 800 |
| Покупка/Продажа/Обмен/Работа | 900 |
| Деньги | 600 |
| 1st Access Level | 800 |
| Вирусология | todos (~597) |
| Программирование | 400 |
| Спам, рассылки | 400 |
| Криптография | 300 |
| Black List | todos (~492) |

#### Categorías de clasificación (adaptadas a foro público)

| Categoría | Descripción |
|---|---|
| `hacking` | Intrusión, vulnerabilidades, exploits, pentesting |
| `carding` | Fraude con tarjetas, dumps, CVV, e-money |
| `malware` | Troyanos, bots, crypters, exploits, ransomware |
| `spam` | Spam masivo, mailing, scrapers, bases de correos |
| `marketplace` | Compraventa general de servicios, credenciales, accesos |
| `programming` | Código, scripts, desarrollo, automatización |
| `community` | Discusión técnica, preguntas, debate off-topic |
| `unknown` | No clasificable |

**Resultados de clasificación** (5.289 posts):
```
community      1.568  (29,6%)
hacking          784  (14,8%)
marketplace      775  (14,7%)
programming      694  (13,1%)
malware          658  (12,4%)
spam             404   (7,6%)
carding          291   (5,5%)
unknown          115   (2,2%)
```

#### Perfilado de usuarios

156 usuarios con ≥8 posts en la muestra son perfilados con JSON estructurado:
```json
{
  "specialty": "hacking | carding | malware | spam | marketplace | programming | community",
  "role": "seller | buyer | teacher | developer | moderator | community_member | scammer",
  "confidence": "high | medium | low",
  "summary": "...",
  "evidence": [...]
}
```

> **Tiempo estimado**: ~60 min clasificación + ~20 min perfilado con `qwen2.5:14b`.

---

### 03 — Embeddings y clustering

**Notebook**: `ExploitIn/notebooks/03_embeddings.ipynb`  
**Modelo**: `qwen3-embedding` (4096 dims) — mismo espacio que Conti, BB y LockBit

5.289 posts embebidos en batches de 16. UMAP + HDBSCAN aplicados sobre mensajes y sobre centroides de actores.

> **Tiempo estimado**: ~25–30 min para embeddings.

---

## Comparativa entre los cuatro grupos

| | Conti | Black Basta | LockBit | Exploit.in |
|---|---|---|---|---|
| Tipo de dato | Chats internos | Chats internos | Panel operacional | Foro público |
| Período | 2020–2022 | 2023–2024 | dic 2024 – abr 2025 | 2005–2008 |
| Actores/Usuarios | 485 | 49 | 75 | 9.647 (156 perfilados) |
| Mensajes analizados | ~216.000 | ~195.400 | 4.423 negociaciones | 5.289 (muestra) |
| LLM target | Mensajes internos (ruso) | Mensajes internos (ruso) | Negociaciones con víctimas | Posts de foro (ruso) |
| Dato financiero | No | No | 7 pagos, funnel completo | Marketplace precios 2005 |
| Notebooks | 00–03 | 00–03 | 00–04 | 00–03 |

---

## Análisis comparativo de 4 grupos

**Notebook**: `comparative/01_cross_group_similarity.ipynb`

### Fundamento matemático

Todos los módulos usan `qwen3-embedding` (4096D) → los vectores viven en el **mismo espacio**.  
El centroide de un actor es la media L2-normalizada de todos sus embeddings de mensaje.  
La similitud coseno entre centroides de actores de distintos grupos es directamente comparable.

```python
def compute_centroids(msgs_df, embeddings, actor_col='username', min_posts=5):
    centroids = {}
    for actor, group in msgs_df.groupby(actor_col):
        if len(group) >= min_posts:
            vecs = embeddings[group.index.tolist()]
            c = vecs.mean(axis=0)
            c /= np.linalg.norm(c)   # L2-normalización
            centroids[actor] = c
    return centroids
```

### Matriz de cohesión 4×4 (resultados reales)

Similitud coseno media entre grupos (diagonal = intra-grupo):

|  | Conti | Black Basta | LockBit | Exploit.in |
|---|---|---|---|---|
| **Conti** | **0.914** | 0.921 | 0.841 | 0.801 |
| **Black Basta** | 0.921 | **0.945** | 0.869 | 0.791 |
| **LockBit** | 0.841 | 0.869 | **0.905** | 0.723 |
| **Exploit.in** | 0.801 | 0.791 | 0.723 | **0.930** |

**Interpretación de la tabla:**

- **Conti ↔ BlackBasta (0.921) > intra-Conti (0.914)**: la similitud entre grupos es mayor que la cohesión interna de Conti. Confirma empíricamente que BlackBasta es una evolución directa de Conti — cultura operacional prácticamente idéntica.
- **LockBit más cercano a BlackBasta (0.869) que a Conti (0.841)**: los operadores de LockBit comparten más estilo con la generación BlackBasta. Coherente con la cronología (LockBit 3.0 es contemporáneo de BB).
- **Exploit.in claramente separado (0.72–0.80)**: lógico — es un foro público de 2005, no comunicaciones internas cifradas de un grupo criminal. La barrera semántica refleja la diferencia de contexto, no necesariamente de personas.
- **Exploit.in más cohesivo internamente (0.930)**: paradójico a primera vista. Refleja que el foro tiene un vocabulario y estilo muy característico del underground ruso de los 2000s.

> **Punto de discusión**: Conti y BlackBasta son semánticamente **más similares entre sí que internamente**.  
> ¿Qué implica esto? Que los operadores de ambos grupos usan el mismo argot, las mismas herramientas,  
> el mismo estilo de comunicación. La hipótesis de sucesión directa (ex-miembros de Conti fundaron BB)  
> tiene soporte semántico.

### Exploit.in como ecosistema fuente

El análisis de "bridge" busca usuarios de Exploit.in (2005–2008) con el mayor parecido semántico a los operadores de ransomware (2020–2025).

**Top usuarios de Exploit.in más similares a operadores de ransomware:**

| Usuario EI | Especialidad | Mejor Conti | sim | Mejor BB | sim |
|---|---|---|---|---|---|
| slrz | unknown | tl2 | 0.924 | cob_crypt_ward | 0.920 |
| abashkin | unknown | strix | 0.904 | nickolas | 0.897 |
| USD | malware | tl2 | 0.901 | usernamenn1 | 0.901 |
| Mescalin | malware | tl2 | 0.899 | cob_crypt_ward | 0.898 |
| Маринка | hacking | tl2 | 0.893 | cob_crypt_ward | 0.880 |

> **Punto de discusión (importante — matiz metodológico)**:  
> Similitud alta NO prueba que sean la misma persona. Prueba que usan un estilo de escritura y vocabulario similar.  
> Puede deberse a: (1) misma persona con 15 años de diferencia, (2) personas formadas en el mismo ecosistema cultural,  
> (3) uso del mismo argot underground ruso. Las tres hipótesis son igualmente plausibles con solo embeddings.  
> Para atribución real se necesitaría correlación de IPs, patrones horarios, o información externa.

### UMAP conjunto

El notebook proyecta los centroides de los 4 grupos en 2D:
- Conti (🔴) y BlackBasta (🔵) tienden a mezclarse → confirma alta similitud
- LockBit (🟡) forma un cluster parcialmente solapado → estilo diferente (inglés con víctimas, no ruso interno)
- Exploit.in (🟢) ocupa su propio espacio → separación contextual clara

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
| `qwen3-embedding` | Embeddings semánticos (4096D) | `bge-m3` (menor tamaño, 768D), `nomic-embed-text-v2-moe` (768D, incompatible con este proyecto) |

> **Por qué `qwen3-embedding` y no `nomic-embed-text-v2-moe`**: con 7.6B params, 40k tokens de contexto  
> y 4096 dims, qwen3-embedding produce representaciones más ricas y tiene mejor cobertura del ruso.  
> La clave es la **consistencia**: todos los módulos deben usar el mismo modelo para que la comparativa  
> cruzada sea matemáticamente válida. Cambiar de modelo en un módulo rompe el espacio vectorial compartido.

> **Sobre los modelos de razonamiento (qwen3, deepseek-r1)**:  
> Los modelos con thinking mode generan un bloque `<think>...</think>` antes de responder.  
> Con `num_predict` bajo, el presupuesto se agota en el bloque de razonamiento → respuesta vacía → todo `unknown`.  
> Para clasificación masiva: usar `qwen2.5:14b` (sin thinking).  
> Para el analista conversacional (notebook 04): `qwen3` con `think=False` en options es viable.

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
