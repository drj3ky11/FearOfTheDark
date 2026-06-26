"""
Embeddings via Ollama
======================
An embedding is a dense numeric vector that captures the semantic meaning of a text.
Two texts that are similar in meaning will have vectors that are close together
(high cosine similarity). Two unrelated texts will be far apart.

We use this in two ways:

1. STYLOMETRIC ANALYSIS: embed all posts by the same user concatenated together.
   Users who write in a similar style (same vocabulary, same sentence patterns,
   same topics) will have similar vectors. This lets us cluster users by writing
   style and, crucially, link the same person across different forums even if
   they use different usernames.

2. SEMANTIC SEARCH: embed a query and find the most similar posts in a forum.
   Useful for finding all posts related to a specific topic (e.g. "cashout methods")
   without relying on exact keyword matches.

Why local models (Ollama) instead of OpenAI/Cohere?
- The data is sensitive. We cannot send it to external APIs.
- We have a GPU. Local inference is fast enough.
- qwen3-embedding is multilingual (strong Russian/Chinese support) and trained for retrieval and clustering tasks.
"""

import ollama
import numpy as np
import pandas as pd
from tqdm import tqdm


DEFAULT_MODEL = "qwen3-embedding"
EMBED_DIMS = 4096

# How many texts to send to Ollama in a single request.
# Too large → OOM on the GPU. Too small → too many round trips.
# 32 is safe for qwen3-embedding (4096 dims) on an RTX A2000 12GB.
_BATCH_SIZE = 32


def embed_texts(
    texts: list[str],
    model: str = DEFAULT_MODEL,
    batch_size: int = _BATCH_SIZE,
    show_progress: bool = True,
) -> np.ndarray:
    """
    Embed a list of texts using a local Ollama model.

    Texts are sent in batches to avoid overwhelming the GPU.
    Empty/None texts are replaced with empty strings (Ollama handles them gracefully).

    Returns:
        float32 numpy array of shape (len(texts), embedding_dim).
        For qwen3-embedding, dim=4096.
    """
    results: list[list[float]] = []

    batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
    iterator = tqdm(batches, desc=f"Embedding [{model}]") if show_progress else batches

    for batch in iterator:
        clean = [t if t else "" for t in batch]
        response = ollama.embed(model=model, input=clean)
        results.extend(response.embeddings)

    if not results:
        return np.empty((0, 0), dtype=np.float32)

    return np.array(results, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity between two sets of vectors.

    cosine_similarity(a, b)[i, j] = similarity between a[i] and b[j].
    Values range from -1 (opposite) to 1 (identical).

    We use this to find the most similar user profiles across forums.
    """
    # Normalize to unit vectors so dot product == cosine similarity
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def compute_actor_centroids(
    posts_df: pd.DataFrame,
    model: str = DEFAULT_MODEL,
    min_posts: int = 5,
    batch_size: int = _BATCH_SIZE,
) -> tuple[list, np.ndarray]:
    """
    Build one L2-normalized centroid per actor by embedding individual messages.

    Unlike embed_users (which concatenates), this embeds each message separately
    and averages the resulting vectors. Better for large corpora where concatenation
    would exceed the model's context window, and more robust against outlier messages.

    Returns:
        actor_ids: list of userids
        centroids: np.ndarray of shape (n_actors, dim), L2-normalized
    """
    df = posts_df.dropna(subset=["userid", "pagetext"]).copy()
    df["pagetext"] = df["pagetext"].astype(str).str.strip()
    df = df[df["pagetext"].str.len() > 0]

    post_counts = df.groupby("userid").size()
    valid = post_counts[post_counts >= min_posts].index
    df = df[df["userid"].isin(valid)].reset_index(drop=True)

    all_texts = df["pagetext"].tolist()
    all_embeddings = embed_texts(all_texts, model=model, batch_size=batch_size)

    actor_ids = []
    centroids = []
    for uid, group in df.groupby("userid"):
        vecs = all_embeddings[group.index.tolist()]
        c = vecs.mean(axis=0)
        norm = np.linalg.norm(c)
        if norm > 0:
            c /= norm
        actor_ids.append(uid)
        centroids.append(c)

    return actor_ids, np.array(centroids, dtype=np.float32)


def embed_users(
    posts_df: pd.DataFrame,
    model: str = DEFAULT_MODEL,
    min_posts: int = 3,
) -> tuple[list, np.ndarray]:
    """
    Build one embedding per user by concatenating all their posts.

    Why concatenate instead of averaging individual post embeddings?
    Concatenating gives the model more context about the user's overall
    writing style. Averaging can dilute distinctive patterns.

    Users with fewer than min_posts are excluded — too little text
    produces unreliable embeddings that cluster for the wrong reasons.

    Returns:
        user_ids: list of userids (same order as rows in embeddings)
        embeddings: np.ndarray of shape (n_users, dim)
    """
    # Group posts by user, concatenate text
    grouped = (
        posts_df.dropna(subset=["userid", "pagetext"])
        .groupby("userid")["pagetext"]
        .apply(lambda texts: " ".join(str(t) for t in texts if t))
    )

    # Filter out users with too few posts or empty text
    post_counts = posts_df.groupby("userid").size()
    grouped = grouped[grouped.str.len() > 0]
    grouped = grouped[grouped.index.isin(post_counts[post_counts >= min_posts].index)]

    user_ids = grouped.index.tolist()
    combined_texts = grouped.tolist()

    embeddings = embed_texts(combined_texts, model=model)
    return user_ids, embeddings
