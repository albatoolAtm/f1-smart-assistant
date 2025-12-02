# app/agents/retriever_text.py

import os
import json
import numpy as np

# ---- Config ----
PASSAGES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "models", "passages.json"
)

# Global cache
_passages = None
_passage_texts = None
_passage_embs = None


def _local_embed_one(text: str, dim: int = 64):
    """
    Deterministic local 'embedding' used as a fallback.
    Same text -> same vector.
    """
    seed = abs(hash(text)) % (2**32)
    rng = np.random.RandomState(seed)
    return rng.normal(size=dim).astype("float32")


def _local_embed(texts):
    return np.stack([_local_embed_one(t) for t in texts], axis=0)


def load_passages():
    """
    Load small F1 knowledge base from JSON.
    Format: [{"text": "...", "source": "..."}, ...]
    """
    if not os.path.exists(PASSAGES_FILE):
        return []

    with open(PASSAGES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def google_embed(texts):
    """
    Previously called Gemini text-embedding-004.
    Now we ONLY use local embeddings (no external API).
    """
    if not texts:
        return np.zeros((0, 1), dtype="float32")

    # Just return local deterministic embeddings
    return _local_embed(texts)


def load_passage_embeddings():
    """
    Lazily load passages and compute embeddings once.
    """
    global _passages, _passage_texts, _passage_embs

    if _passages is None:
        _passages = load_passages()

        if _passages:
            _passage_texts = [p["text"] for p in _passages]
            _passage_embs = google_embed(_passage_texts)
        else:
            _passage_texts = []
            _passage_embs = np.zeros((0, 1), dtype="float32")

    return _passage_texts, _passage_embs, _passages


def text_retriever(query: str, top_k: int = 3):
    """
    Retrieve the top_k passages most similar to the query
    using cosine similarity on embeddings.
    """
    passage_texts, passage_embs, passages = load_passage_embeddings()

    if passage_embs.shape[0] == 0:
        return []

    # Embed query
    q_emb = google_embed([query])[0]

    # Cosine similarity
    passage_norms = np.linalg.norm(passage_embs, axis=1, keepdims=True) + 1e-8
    q_norm = np.linalg.norm(q_emb) + 1e-8

    passage_unit = passage_embs / passage_norms
    q_unit = q_emb / q_norm

    sims = np.dot(passage_unit, q_unit)

    # Indices of top_k highest similarity
    idx = np.argsort(-sims)[:top_k]

    results = [
        {
            "text": passage_texts[i],
            "score": float(sims[i]),
            "source": passages[i].get("source"),
        }
        for i in idx
    ]

    return results
