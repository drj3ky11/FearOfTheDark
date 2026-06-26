#!/usr/bin/env python3
"""
Build PPTX for "Caso 1 — Hacking Forums: identidad y tiempo" (charla completa).

Run with:
    uv run python talks/04_caso1_hacking/build_slides_full.py
"""

import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pptx import Presentation
from pptx.util import Inches, Pt

from talks._shared.theme import (
    C_BG, C_BG_SEC, C_ACCENT, C_TITLE, C_BODY, C_MUTED, C_CODE_BG, C_BADGE,
    W, H,
    _set_bg, _add_rect, _add_txbox, _add_bullets,
    title_slide, section_slide, content_slide, two_col_slide,
    table_slide, code_slide, demo_slide,
)


# ─── Contenido de la presentación ─────────────────────────────────────────────

def build(prs: Presentation) -> None:

    # ── Portada ────────────────────────────────────────────────────────────────
    title_slide(prs,
        "Caso 1 — Hacking Forums: identidad y tiempo",
        "OGUsers · RaidForums · BreachForums — una identidad no muere, migra",
        "CSBC26  ·  OpHarvestSeason  ·  2019–2023",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: EL ECOSISTEMA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "El ecosistema",
                  "Qué son los hacking forums, qué se vende y por qué terminan leakeados")

    content_slide(prs, "Hacking forums: qué se vende aquí", [
        "Accesos iniciales a redes corporativas (Initial Access Brokers)",
        "Exploits, tools y RATs — mercado de herramientas de ataque",
        "Dumps de credenciales robadas: combos email:password, fullz, SSNs",
        "OG usernames — handles cortos y 'originales' en Instagram, Twitter, Snapchat",
        ("No es lo mismo que carding: aquí no se venden tarjetas sino acceso e información", 1),
        ("La moneda no es dinero fácil — es reputación técnica y notoriedad dentro del foro", 1),
    ], note="Diferencia central con carding: en hacking forums el producto es el acceso y la reputación")

    content_slide(prs, "OGUsers: el foro de los handles robados", [
        "Fundado ~2017, cerró definitivamente en 2022 — activo durante el boom de Instagram",
        "Especialización: robo y venta de usernames 'OG' (originales, cortos, valiosos)",
        "Un handle como @nike o @j podía valer miles de dólares en Bitcoin",
        "Técnicas usadas: SIM swapping, phishing, ingeniería social a empleados de telecoms",
        "Comunidad pequeña pero muy activa — varios cientos de vendedores regulares",
        ("4 brechas en 3 años: 2019, 2020, 2021, 2022 — un dataset único como serie temporal", 1),
    ])

    content_slide(prs, "RaidForums y BreachForums: el mercado de leaks", [
        "RaidForums (2015–2022): plataforma de redistribución de breaches — 'el mercado de datos'",
        "Cualquier brecha corporate terminaba ahí: Uber, LinkedIn, Facebook, miles más",
        "BreachForums surgió en 2022 tras el arresto del admin de RaidForums (Pompompurin)",
        "Mismo modelo: leak se publica gratis o se vende, reputación del vendedor es todo",
        "Ambos operaron en clearnet — no en dark web — lo que los hizo más accesibles y rastreables",
        ("El arresto de Pompompurin (FBI, 2023) terminó con BreachForums también", 1),
    ])

    content_slide(prs, "¿Por qué terminan leakeados?", [
        "Law enforcement: FBI y Europol toman servidores — datos quedan expuestos post-incautación",
        "Rival groups: competidores o hacktivistas publican la BD como golpe de imagen",
        "Disgruntled insiders: moderadores o admins publican datos como venganza o extorsión",
        "OpSec failures: backups en S3 público, bases de datos sin autenticación expuestas",
        "Exit scam: el admin vende o publica la BD antes de desaparecer",
        ("La ironía perfecta: los distribuidores de leaks ajenos terminan siendo leakeados ellos", 1),
        ("Y esto nos da el material de análisis más rico posible — la comunidad entera expuesta", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: LOS DATOS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "Los datos",
                  "Qué hay en los dumps, cómo están estructurados y qué hace a OGUsers especial")

    table_slide(prs, "Los datasets del Caso 1", [
        "Foro", "Leak", "Formato", "Usuarios aprox.", "Notas",
    ], [
        ["OGUsers",       "2019-08", "vBulletin SQL", "~50K",  "Primer snapshot — brecha por rival group"],
        ["OGUsers",       "2020-05", "vBulletin SQL", "~110K", "Segunda brecha — foro en crecimiento"],
        ["OGUsers",       "2021-09", "vBulletin SQL", "~200K", "Tercera brecha — mayor madurez"],
        ["OGUsers",       "2022-11", "vBulletin SQL", "~200K", "Cuarta brecha — meses antes del cierre"],
        ["RaidForums",    "2022-04", "vBulletin SQL", "~550K", "Incautación FBI — dataset completo"],
        ["BreachForums",  "2022-11", "vBulletin SQL", "~210K", "Primera versión — dump parcial"],
        ["BreachForums",  "2023-03", "vBulletin SQL", "~340K", "Segunda versión — dump más completo"],
    ], note="7 archivos en total · mismo schema vBulletin en todos · variantes mínimas de formato")

    content_slide(prs, "OGUsers como serie temporal única", [
        "4 snapshots del MISMO foro en 3 años — esto no existe en ningún otro dataset underground",
        "Cada snapshot es una 'foto' de la comunidad en un momento distinto",
        "Permite estudiar dinámica de comunidades: nacimiento, crecimiento, trauma, resiliencia",
        "Preguntas que solo se pueden responder con series temporales:",
        ("¿Cuántos usuarios sobreviven cada brecha? ¿Quiénes desaparecen? ¿Quiénes se quedan?", 1),
        ("¿La comunidad crece o se encoge tras cada exposición?", 1),
        ("¿Los que se van migran a RaidForums/BreachForums o abandonan definitivamente?", 1),
    ], note="Un dataset longitudinal de una comunidad criminal — excepcional para análisis forense")

    content_slide(prs, "Formato: vBulletin SQL — mismas tablas, distinto contenido", [
        "Mismo schema que los foros de carding — vBulletin era el estándar de la época",
        "user — userid, username, email, password hash, joindate, posts, IP, timezone",
        "post — userid, dateline, pagetext (el texto del post), threadid, parentid",
        "pmtext — mensajes privados (no siempre presentes — depende del dump)",
        "userfield — campos extra: bio libre, links de redes sociales, Telegram handle",
        ("El contenido es radicalmente distinto al de carding: técnicas de SIM swap, handles en venta, métodos", 1),
        ("Los posts revelan el lenguaje interno del grupo — invaluable para NER y estilometría", 1),
    ])

    code_slide(prs, "Schema de OGUsers — variantes entre snapshots", "El parser tiene que manejar diferencias entre las 4 versiones del mismo foro", [
        "-- Snapshot 2019: INSERT estándar, cp1251",
        "INSERT INTO user VALUES (1,'xXkillah420Xx','hash123','og@mail.ru',...);",
        "",
        "-- Snapshot 2021: columnas explícitas (vBulletin 5.x upgrade)",
        "INSERT INTO `user` (`userid`,`username`,`password`,`email`,...) VALUES (1,...);",
        "",
        "-- Snapshot 2022: encoding UTF-8, misma tabla",
        "-- (la mayoría de los campos son idénticos pero el encoding cambió)",
        "",
        "-- Estrategia: normalize_snapshots() detecta el schema en runtime",
        "-- y genera handle_norm + snapshot_year + joindate_epoch en todos",
    ], note="normalize_snapshots() — src/utils.py — maneja la heterogeneidad entre versiones")

    content_slide(prs, "Qué datos de valor hay en estos dumps", [
        "username / handle — identificador principal, frecuentemente reutilizado cross-foro",
        "email — throwaway pero si lo reusan es una señal fuerte",
        "password hash — misma contraseña en distintos foros = casi certeza del mismo actor",
        "joindate — cuándo se registró → correlaciona con eventos del ecosistema",
        "posts — el texto: técnicas, ventas, disputas — material para NER y estilometría",
        "IP address — raramente con VPN consistente antes de 2020",
        ("Los hacking forums tienen un campo extra valioso: referencias cruzadas a Discord, Telegram, Twitter", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: LA INFRAESTRUCTURA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "La infraestructura",
                  "El mismo stack que carding — con una diferencia crítica: 4 versiones del mismo schema")

    two_col_slide(prs, "El stack — idéntico al de carding forums", "Entorno base", [
        "uv — gestor de entornos Python (uv sync instala todo)",
        "Python 3.12 — type hints, estabilidad",
        "Jupyter Lab — análisis exploratorio + demo",
        "Ollama — inferencia local (NUNCA APIs externas con datos sensibles)",
        "nomic-embed-text (~300MB) — embeddings de 768D",
    ], "Librerías clave", [
        "pandas / numpy — manipulación de datos",
        "networkx — construcción y análisis de grafos",
        "difflib / SequenceMatcher — fuzzy matching de handles",
        "scikit-learn — clustering y métricas de similitud",
        "umap-learn — reducción dimensional 768D → 2D",
        "plotly — scatter interactivo para UMAP",
    ])

    content_slide(prs, "La diferencia crítica: 4 versiones del mismo schema", [
        "Para carding: 10 foros distintos → cada uno con su propio schema → un parser adaptable",
        "Para OGUsers: 4 snapshots del MISMO foro → el schema EVOLUCIONA entre versiones",
        "vBulletin 4.x → 5.x: columnas explícitas en lugar de implícitas, encoding cambia",
        "Solución: normalize_snapshots() — detecta el año del snapshot y normaliza la salida",
        "Columnas garantizadas después de normalización: handle_norm, snapshot_year, joindate_epoch",
        ("Sin esta normalización los joins cross-snapshot fallan silenciosamente — el peor tipo de bug", 1),
        ("El join cross-snapshot es el corazón del análisis — tiene que ser determinístico", 1),
    ], note="Ver src/utils.py → normalize_snapshots() y extract_snapshot_year()")

    code_slide(prs, "load_all_forums() con filtrado por categoría", "El punto de entrada para cargar el dataset de hacking forums", [
        "from src.utils import load_forum, list_forums",
        "",
        "# list_forums() filtra por categoría desde el directorio de datos",
        "hf_paths = list_forums('Hacking Forums')",
        "",
        "# Cargar y separar OGUsers del resto",
        "raw_forums = {}",
        "for path in hf_paths:",
        "    dfs = load_forum(path)   # auto-detect encoding + schema",
        "    raw_forums[path.stem] = dfs",
        "",
        "# normalize_snapshots() agrega handle_norm, snapshot_year, joindate_epoch",
        "normalized = normalize_snapshots(raw_forums)",
        "",
        "ogusers = {k: v for k, v in normalized.items() if 'ogusers' in k.lower()}",
        "others  = {k: v for k, v in normalized.items() if k not in ogusers}",
    ], note="load_forum() es el mismo parser del caso de carding — reutilización total del código")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: TÉCNICAS DE ANÁLISIS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "04", "Técnicas de análisis",
                  "Serie temporal · cross-foro pivoting · grafos · estilometría · embeddings")

    content_slide(prs, "Plan de análisis — 5 técnicas encadenadas", [
        "1. Análisis temporal de OGUsers — comparar los 4 snapshots",
        "2. Cross-foro identity pivoting — OGUsers → RaidForums / BreachForums",
        "3. Grafo de interacciones — evolución de la red tras cada brecha",
        "4. Estilometría — confirmar identidades cuando el handle cambia",
        "5. Embeddings + UMAP — clustering de comportamiento cross-foro",
        ("Cada técnica es una señal. La conclusión emerge cuando varias convergen.", 1),
        ("Una sola señal no construye un caso — la convergencia de 3+ sí lo hace.", 1),
    ])

    content_slide(prs, "1. Análisis temporal de OGUsers", [
        "Para cada par de snapshots consecutivos calculamos tres métricas:",
        ("Persisten: handles presentes en ambos snapshots — la comunidad estable", 1),
        ("Nuevos: handles que aparecen en el snapshot siguiente — crecimiento o rebranding", 1),
        ("Desaparecen: handles que no están en el siguiente — bajas reales o cambio de nombre", 1),
        "Visualización: bar chart apilado por transición (2019→2020, 2020→2021, 2021→2022)",
        "Pregunta clave: ¿el % de persistencia sube o baja tras cada brecha?",
        ("Una caída fuerte en persistencia tras una brecha indica pánico y abandono masivo", 1),
        ("Una persistencia alta indica que la comunidad se endureció — asumió el riesgo", 1),
    ], note="handles_per_snapshot[year] = set de handle_norm — operaciones de conjunto simples")

    content_slide(prs, "2. Cross-foro identity pivoting", [
        "Hipótesis: los actores activos de OGUsers migran a RaidForums o BreachForums",
        "Paso 1 — match exacto: og_handles ∩ other_handles → intersection de sets normalizados",
        "Paso 2 — fuzzy match: SequenceMatcher con threshold 0.85 para variaciones del handle",
        ("handle 'xXkillah420Xx' y 'killah420' son candidatos si similarity > 0.85", 1),
        "Paso 3 — match por email y password hash (cuando disponible) — señal más fuerte",
        "Resultado: lista de pares (handle_ogusers, handle_otro_foro, tipo_señal, confianza)",
        ("Falsos positivos son inevitables en handles cortos — revisar con estilometría", 1),
    ], note="Fuzzy matching limitado a muestras de 200×200 en demo — escala a full dataset offline")

    content_slide(prs, "3. Grafo de interacciones — evolución temporal", [
        "Cada reply entre usuarios es una arista dirigida: threadid → userid (responde)",
        "Construimos un grafo por snapshot de OGUsers y medimos:",
        ("Degree centrality: quién tiene más conexiones directas — el más activo socialmente", 1),
        ("Betweenness centrality: quién actúa de puente entre subgrupos — el conector", 1),
        ("Community detection (Louvain): subgrupos dentro del foro — vendors vs compradores", 1),
        "Comparamos la estructura del grafo entre snapshots: ¿quiénes son los nodos centrales?",
        "Si el mismo actor aparece como hub en dos snapshots distintos — es un referente estable",
    ], note="networkx.betweenness_centrality con k=500 para aproximación en datasets grandes")

    content_slide(prs, "4. Estilometría — el estilo no se puede suprimir", [
        "Cuando el handle cambia pero la persona sigue escribiendo — el estilo la delata",
        "Features manuales (src/stylometry.py) — sin GPU, sin Ollama:",
        ("Ratio puntuación/palabras, longitud promedio de palabras, uso de mayúsculas", 1),
        ("Palabras funcionales preferidas, errores tipográficos habituales, densidad de emojis", 1),
        "Aplicamos compare_users() sobre los posts de candidatos cross-foro",
        "Umbral: similitud > 0.90 = candidato fuerte para ser el mismo actor",
        ("Requiere mínimo ~50 posts por usuario para ser estadísticamente significativo", 1),
        ("Los usuarios con < 50 posts son ruido — no hay suficiente señal estilométrica", 1),
    ], note="src/stylometry.py — extract_features() + compare_users() — ver notebook sección 6")

    code_slide(prs, "Fuzzy matching + estilometría en pipeline", "Las dos técnicas encadenadas para cross-foro identity pivoting", [
        "from difflib import SequenceMatcher",
        "from src.stylometry import compare_users",
        "",
        "# Paso 1: fuzzy match de handles",
        "def fuzzy_match(handles_a, handles_b, threshold=0.85):",
        "    return [(a, b, SequenceMatcher(None, a, b).ratio())",
        "            for a in handles_a for b in handles_b",
        "            if a != b and SequenceMatcher(None, a, b).ratio() >= threshold]",
        "",
        "# Paso 2: estilometría sobre los candidatos",
        "candidates = fuzzy_match(og_handles[:200], rf_handles[:200])",
        "",
        "# Para cada par candidato, calcular similitud estilométrica",
        "sim_matrix = compare_users(posts_df, user_col='user', text_col='text')",
        "# sim > 0.90 + fuzzy > 0.85 → candidato fuerte para el mismo actor",
    ], note="El pipeline es bidireccional: fuzzy match filtra candidatos, estilometría los confirma")

    content_slide(prs, "5. Embeddings + UMAP — clustering de comportamiento", [
        "Problema: la estilometría manual captura features de superficie (puntuación, longitud)",
        "Los embeddings capturan SEMÁNTICA — de qué habla el usuario, no cómo lo escribe",
        "nomic-embed-text convierte los posts de cada usuario en un vector de 768 dimensiones",
        "UMAP reduce 768D a 2D preservando estructura local — puntos cercanos = usuarios similares",
        "Resultado: scatter interactivo (Plotly) — hover muestra username + foro de origen",
        ("Clusters que mezclan OGUsers + RaidForums + BreachForums = posible red de actores", 1),
        ("Outliers = estilo muy singular — candidatos a identificación específica", 1),
    ], note="Embeddings precomputados en results/hacking_forums/ — UMAP se corre en demo en vivo")

    content_slide(prs, "Embeddings en el idioma original — la regla crítica", [
        "Los posts de OGUsers están en inglés — no hay problema de idioma aquí",
        "Pero la regla vale para todos los casos: NUNCA traducir antes de embedear para atribución",
        "La traducción destruye la huella lingüística — las palabras funcionales, el ritmo, los tics",
        "nomic-embed-text es multilingüe: posts en inglés y en ruso quedan en el mismo espacio vectorial",
        ("Para NER y topic modeling con LLM → traducir ANTES si el modelo es predominantemente inglés", 1),
        ("Para embeddings, clustering y estilometría → idioma original siempre, sin excepción", 1),
    ], note="Regla del programa (Bloque 2): embeddings = original. NER/LLM = puede traducir.")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: DEMO EN VIVO
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "05", "Demo en vivo",
                  "Recorremos el notebook completo con los datos reales")

    demo_slide(prs, "02_hacking_forums.ipynb — recorrido completo", [
        "Cargar los 7 dumps y verificar volumen: normalize_snapshots()",
        "Análisis temporal OGUsers: persistencia entre los 4 snapshots, gráfico de barras",
        "Cross-foro pivoting: match exacto OGUsers ↔ RaidForums / BreachForums",
        "Fuzzy matching de handles con SequenceMatcher — demostrar falsos positivos",
        "Estilometría sobre candidatos cross-foro — compare_users() en vivo",
        "Embeddings precomputados + UMAP scatter — clusters de comportamiento interactivos",
    ], notebook_path="notebooks/cases/02_hacking_forums.ipynb")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 6: HALLAZGOS Y CONCLUSIÓN
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "06", "Hallazgos y conclusión",
                  "La hipótesis validada: las identidades no mueren, migran")

    content_slide(prs, "La hipótesis validada", [
        "Una identidad underground no muere con una brecha — migra",
        "Los actores más activos de OGUsers reaparecen en RaidForums y BreachForums",
        "Con el mismo handle (match exacto) o con variante (fuzzy match confirmado por estilo)",
        "La comunidad absorbe las brechas: tras cada una hay un período de contracción y recuperación",
        "Los nodos de alta centralidad en el grafo de OGUsers son los mismos cross-foro",
        ("Las brechas no destruyen la red social — la reorganizan alrededor de los mismos actores clave", 1),
    ])

    content_slide(prs, "Limitaciones del análisis", [
        "Fuzzy matching genera falsos positivos en handles cortos (2–4 caracteres) — colisión alta",
        "Los snapshots de OGUsers pueden tener diferencias de schema no detectadas automáticamente",
        "Estilometría requiere ≥ 50 posts por usuario — muchos candidatos no llegan a ese umbral",
        "Password hash matching: algunos dumps no incluyen hashes o usan formatos distintos (MD5, bcrypt)",
        "Embeddings sobre texto corto (un solo post) son ruidosos — se necesita agregar por usuario",
        ("Conclusión: el análisis identifica candidatos, no prueba identidad — eso requiere revisión manual", 1),
    ], note="Toda conclusión forense computacional es un candidato a investigar, no una prueba")

    content_slide(prs, "Lo que aprendimos de este caso", [
        "Las series temporales del mismo foro son más valiosas que múltiples foros en un solo momento",
        "El grafo de identidades cross-foro se construye incrementalmente — cada señal suma",
        "La combinación fuzzy matching + estilometría + embeddings es más robusta que cualquiera sola",
        "Los actores que sobreviven múltiples brechas son los más experimentados y los más peligrosos",
        "El análisis de redes sociales identifica a los brokers — quiénes conectan subgrupos distintos",
        ("Estos brokers son el target de mayor valor para investigación: son el puente entre comunidades", 1),
    ])

    # ── Cierre ────────────────────────────────────────────────────────────────
    title_slide(prs,
        "Preguntas",
        "github.com/csbc26  ·  notebooks/cases/02_hacking_forums.ipynb",
        "CSBC26  ·  OpHarvestSeason  ·  Caso 1",
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    template_path = sys.argv[1] if len(sys.argv) > 1 else None

    if template_path:
        prs = Presentation(template_path)
    else:
        prs = Presentation()
        prs.slide_width  = W
        prs.slide_height = H

    build(prs)

    out = Path(__file__).parent / "csbc26_caso1_hacking_forums.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
