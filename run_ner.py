#!/usr/bin/env python3
"""Pre-generates NER cache for the IronMarch notebook.
Run this once; the notebook will load from cache on next execution."""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import ollama
from tqdm.auto import tqdm

from src.utils import load_forum, RESULTS_DIR, DATA_DIR

IM_RESULTS = RESULTS_DIR / 'ironmarch'
IM_RESULTS.mkdir(parents=True, exist_ok=True)
NER_CACHE = IM_RESULTS / 'ner_comparison.parquet'

if NER_CACHE.exists():
    df = pd.read_parquet(NER_CACHE)
    print(f"Cache ya existe: {len(df):,} entidades. Borralo manualmente para regenerar.")
    sys.exit(0)

# --- Load data ---
far_right_dir = DATA_DIR / 'Far Right Forum'
candidates = [p for p in (list(far_right_dir.glob('*IronMarch*.zip')) +
                           list(far_right_dir.glob('*iron*.zip')))
              if not p.name.startswith('._')]
if not candidates:
    print("ERROR: No se encontró el dataset de IronMarch.")
    sys.exit(1)

ironmarch_path = candidates[0]
print(f"Dataset: {ironmarch_path.name}")

raw = load_forum(ironmarch_path)
posts = raw.get('post', pd.DataFrame())

for col in ['userid']:
    if col in posts.columns:
        posts[col] = pd.to_numeric(posts[col], errors='coerce')
        posts.dropna(subset=[col], inplace=True)
        posts[col] = posts[col].astype(int).astype(str)

text_col = 'pagetext' if 'pagetext' in posts.columns else 'message'
print(f"Posts totales: {len(posts):,}, col texto: {text_col}")

# --- Build samples ---
SAMPLE_SIZE = 500
posts_text = posts.dropna(subset=[text_col]).copy()
posts_text = posts_text[posts_text[text_col].astype(str).str.len() > 100]

sample_random = posts_text.sample(min(SAMPLE_SIZE, len(posts_text)), random_state=42)

if 'forumid' in posts_text.columns:
    forum_sizes = posts_text['forumid'].value_counts(normalize=True)
    stratified = []
    for fid, prop in forum_sizes.items():
        n = max(1, int(SAMPLE_SIZE * prop))
        sub = posts_text[posts_text['forumid'] == fid]
        stratified.append(sub.sample(min(n, len(sub)), random_state=42))
    sample_stratified = pd.concat(stratified).head(SAMPLE_SIZE)
else:
    sample_stratified = sample_random

top_user_ids = posts_text.groupby('userid').size().nlargest(25).index
sample_top_users = (
    posts_text[posts_text['userid'].isin(top_user_ids)]
    .groupby('userid').head(20).reset_index(drop=True)
)

print(f"Muestras: random={len(sample_random)}, strat={len(sample_stratified)}, top={len(sample_top_users)}")
total = len(sample_random) + len(sample_stratified) + len(sample_top_users)
print(f"Total posts a procesar: {total:,}")

# --- NER ---
NER_SYSTEM = """You are a threat intelligence analyst. Extract named entities from forum posts.
Reply ONLY with valid JSON object: {"entities": [{"entity": "...", "type": "..."}]}
Allowed types: PERSON, ORGANIZATION, LOCATION, EVENT, IDEOLOGY
If no entities found, reply: {"entities": []}"""

def extract_entities(text: str, model: str = 'qwen2.5:14b') -> list[dict]:
    try:
        response = ollama.generate(
            model=model,
            system=NER_SYSTEM,
            prompt=str(text)[:1500],
            format='json',
            options={'temperature': 0},
        )
        result = json.loads(response['response'])
        entities = result.get('entities', result) if isinstance(result, dict) else result
        return entities if isinstance(entities, list) else []
    except Exception:
        return []

def run_ner_on_sample(sample_df, label):
    records = []
    for _, row in tqdm(sample_df.iterrows(), total=len(sample_df), desc=label):
        for ent in extract_entities(row[text_col]):
            records.append({
                'sample': label,
                'entity': ent.get('entity', '').strip(),
                'type': ent.get('type', 'UNKNOWN'),
                'userid': row.get('userid', ''),
            })
    return pd.DataFrame(records)

ner_parts = []
for sample_df, label in [
    (sample_random,     'aleatoria'),
    (sample_stratified, 'estratificada'),
    (sample_top_users,  'top_usuarios'),
]:
    ner_parts.append(run_ner_on_sample(sample_df, label))

ner_all = pd.concat(ner_parts, ignore_index=True)

if len(ner_all) > 0 and 'entity' in ner_all.columns:
    ner_all = ner_all[ner_all['entity'].str.len() > 1]
    ner_all.to_parquet(NER_CACHE, index=False)
    print(f"\nNER guardado: {len(ner_all):,} entidades → {NER_CACHE}")
    print(ner_all['type'].value_counts().head())
else:
    print("\n⚠️ Sin resultados NER — modelo no disponible.")
    ner_all = pd.DataFrame(columns=['sample', 'entity', 'type', 'userid'])
    ner_all.to_parquet(NER_CACHE, index=False)
