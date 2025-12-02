def verify_evidence(evidence_list):
    """
    Verifies and scores evidence items.
    
    - Increases confidence if multiple sources exist.
    - Returns vetted evidence (unchanged) and confidence score.
    """
    # Collect unique sources
    sources = {e.get("source") for e in evidence_list if e.get("source")}

    # Average score (default 0.5 if missing)
    avg_score = sum(e.get("score", 0.5) for e in evidence_list) / max(len(evidence_list), 1)

    # Boost confidence if multiple sources
    confidence = avg_score
    if len(sources) >= 2:
        confidence = min(1.0, confidence + 0.2)

    # Return vetted evidence (unchanged) and confidence
    vetted = evidence_list
    return vetted, float(confidence)
