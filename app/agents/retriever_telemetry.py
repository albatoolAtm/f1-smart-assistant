# app/agents/retriever_telemetry.py
import os
import json

TELEMETRY_EMB_FILE = os.path.join(
    os.path.dirname(__file__), "..", "models", "telemetry_embeddings.json"
)


def load_telemetry_embeddings():
    """
    Load precomputed telemetry 'embeddings' / summaries from JSON.

    Structure:
    {
      "44": [
        {"lap": 30, "meta": {"summary": "..."}, "score": 0.9},
        ...
      ],
      "16": [ ... ]
    }
    """
    if not os.path.exists(TELEMETRY_EMB_FILE):
        return {}

    with open(TELEMETRY_EMB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Load once at import time
telemetry_index = load_telemetry_embeddings()


def telemetry_retriever(driver_id, lap=None, top_k: int = 1):
    """
    Retrieve top_k telemetry records for a given driver and (optional) lap.

    This is Sarah's GNN/telemetry output exposed in a simple way so that
    the planner (Albatool) can plug it into the QA / summary pipeline.
    """
    hits = telemetry_index.get(str(driver_id), [])

    if not hits:
        return []

    # Filter by lap if provided
    if lap is not None:
        lap_hits = [h for h in hits if h.get("lap") == lap]
        hits = lap_hits or hits  # fallback to all laps if there is no exact match

    # Sort descending by score
    sorted_hits = sorted(hits, key=lambda x: x.get("score", 1.0), reverse=True)

    return sorted_hits[:top_k]
