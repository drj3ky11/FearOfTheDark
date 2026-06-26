"""
Estilometría: extracción de features y comparación de usuarios.

La estilometría analiza características del estilo de escritura que son
estables en el tiempo y difíciles de suprimir conscientemente. Permite
atribuir textos anónimos a autores conocidos y confirmar identidades
cruzadas entre foros con distintos nombres de usuario.

No requiere GPU ni modelos de lenguaje — opera puramente sobre features
estadísticas del texto.
"""

import re
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity as _cosine_similarity

# ─── Lista de palabras funcionales bilingüe (ES/EN) ──────────────────────────
# Las palabras funcionales (artículos, preposiciones, conjunciones, pronombres)
# son muy estables en el estilo de escritura individual y poco afectadas por
# el tema tratado.
_FUNCTION_WORDS = frozenset([
    # Español
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se",
    "las", "un", "por", "con", "no", "una", "su", "para", "es", "al",
    "lo", "como", "más", "o", "pero", "sus", "le", "ya", "fue", "este",
    "ha", "sí", "porque", "esta", "entre", "cuando", "muy", "sin",
    "sobre", "también", "me", "hasta", "hay", "donde", "quien", "desde",
    "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra",
    "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí", "antes",
    "algunos", "qué", "unos", "yo", "otro", "otras", "otra", "él",
    "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos",
    "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros",
    # Inglés
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us",
])


def extract_features(text: str) -> dict:
    """
    Extrae features estilométricas de un texto.

    Las features capturan propiedades del estilo de escritura que son
    estables en el tiempo y características del individuo:
    - Longitud media y desviación estándar de oraciones
    - Ratios de puntuación (punto, coma, exclamación, pregunta)
    - Ratio de palabras funcionales (bilingüe ES/EN)
    - Ratio de capitalización

    Parámetros:
        text: texto a analizar (puede ser vacío o solo espacios)

    Retorna:
        dict con claves: mean_sentence_len, std_sentence_len,
        punct_period_ratio, punct_comma_ratio, punct_excl_ratio,
        punct_quest_ratio, function_word_ratio, capitalization_ratio.
        Si el texto está vacío, todos los valores son 0.0.
    """
    _empty = {
        "mean_sentence_len": 0.0,
        "std_sentence_len": 0.0,
        "punct_period_ratio": 0.0,
        "punct_comma_ratio": 0.0,
        "punct_excl_ratio": 0.0,
        "punct_quest_ratio": 0.0,
        "function_word_ratio": 0.0,
        "capitalization_ratio": 0.0,
    }

    if not text or not text.strip():
        return _empty

    # Tokenizar en oraciones (separador: . ! ?)
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return _empty

    # Longitudes de oraciones en palabras
    sent_lengths = [len(s.split()) for s in sentences]
    mean_sent = float(np.mean(sent_lengths))
    std_sent = float(np.std(sent_lengths)) if len(sent_lengths) > 1 else 0.0

    # Total de caracteres para ratios de puntuación
    total_chars = len(text)
    if total_chars == 0:
        return _empty

    punct_period = text.count(".") / total_chars
    punct_comma  = text.count(",") / total_chars
    punct_excl   = text.count("!") / total_chars
    punct_quest  = text.count("?") / total_chars

    # Tokenizar en palabras para ratios de función y capitalización
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return _empty

    total_words = len(words)
    func_count = sum(1 for w in words if w.lower() in _FUNCTION_WORDS)
    cap_count  = sum(1 for w in words if w[0].isupper()) if words else 0

    return {
        "mean_sentence_len":    mean_sent,
        "std_sentence_len":     std_sent,
        "punct_period_ratio":   punct_period,
        "punct_comma_ratio":    punct_comma,
        "punct_excl_ratio":     punct_excl,
        "punct_quest_ratio":    punct_quest,
        "function_word_ratio":  func_count / total_words,
        "capitalization_ratio": cap_count  / total_words,
    }


def compare_users(
    df: pd.DataFrame,
    user_col: str = "user",
    text_col: str = "text",
) -> pd.DataFrame:
    """
    Calcula la similitud estilométrica entre todos los pares de usuarios.

    Agrega todos los posts de cada usuario, extrae un vector de features
    y calcula la similitud coseno entre cada par. La diagonal siempre vale 1.0.

    Parámetros:
        df:        DataFrame con al menos las columnas user_col y text_col.
        user_col:  nombre de la columna que identifica al usuario (default: "user").
        text_col:  nombre de la columna con el texto (default: "text").

    Retorna:
        pd.DataFrame cuadrado indexado y columneado por nombre de usuario,
        donde result.loc[u, v] == result.loc[v, u] y la diagonal es 1.0.
    """
    # Agregar todos los posts por usuario
    grouped = (
        df.dropna(subset=[user_col, text_col])
        .groupby(user_col)[text_col]
        .apply(lambda texts: " ".join(str(t) for t in texts if t))
    )

    users = grouped.index.tolist()
    if not users:
        return pd.DataFrame()

    # Extraer features para cada usuario
    feature_matrix = np.array([
        list(extract_features(grouped[u]).values()) for u in users
    ], dtype=np.float64)

    # Normalizar a norma unitaria antes de calcular similitud coseno
    norms = np.linalg.norm(feature_matrix, axis=1, keepdims=True)
    # Evitar división por cero para usuarios con texto vacío
    norms = np.where(norms == 0, 1.0, norms)
    normalized = feature_matrix / norms

    sim_matrix = _cosine_similarity(normalized)

    return pd.DataFrame(sim_matrix, index=users, columns=users)
