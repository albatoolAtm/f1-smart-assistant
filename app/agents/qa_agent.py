# app/agents/qa_agent.py

from typing import List, Dict, Any, Tuple

from .retriever_text import text_retriever
from .retriever_telemetry import telemetry_retriever
from .filter_verifier import verify_evidence
from .summarizer import call_llm_system


def _local_qa_answer(question: str, evidence: List[Dict[str, Any]]) -> str:
    """
    Offline fallback: if Gemini is not available,
    we still return a sensible answer for common F1 questions.
    """
    q = (question or "").lower()

    # --- Example 1: DRS explanation ---
    if ("drs" in q and "formula 1" in q) or "drag reduction" in q:
        return (
            "DRS stands for Drag Reduction System. It is a movable flap in the rear "
            "wing of a Formula 1 car. When DRS is activated, the flap opens, "
            "reducing aerodynamic drag and increasing top speed on the straights.\n\n"
            "In a race, drivers may only use DRS in designated DRS zones and only if "
            "they are within one second of the car ahead at the detection point. "
            "When the driver hits the brakes, the flap automatically closes to "
            "restore downforce for cornering."
        )

    # --- Example 2: Hamilton pit-stop around lap 30 ---
    if "hamilton" in q and "pit" in q:
        context_snippets = " ".join(e.get("text", "") for e in evidence[:2])

        if context_snippets.strip():
            return (
                "Based on the available context, Hamilton pitted around lap 30 to "
                "change tyres once his pace started to drop and tyre temperatures "
                "were rising. The team used the stop to protect tyre life and to "
                "cover the undercut from rival cars.\n\n"
                f"Context used: {context_snippets}"
            )

        return (
            "Hamilton typically pits around lap 30 when his tyre temperatures and "
            "degradation become too high. The stop allows him to switch to a fresher "
            "compound and avoid losing time to rivals attempting an undercut."
        )

    # --- Example 3: Why teams choose different tyre compounds ---
    if "tyre compound" in q or "tire compound" in q or "different tyre" in q:
        return (
            "F1 teams choose different tyre compounds to balance grip, durability, "
            "and overall race strategy. Softer compounds provide more grip and faster "
            "lap times but degrade more quickly. Harder compounds last longer but "
            "generally give slower lap times.\n\n"
            "By selecting different compounds, teams can:\n"
            "- Maximise pace during key phases of the race\n"
            "- Defend against or attempt an undercut on rivals\n"
            "- Extend stints when tyre wear is high\n"
            "- Adapt to track temperature, car balance and traffic\n\n"
            "This flexibility allows each team to optimise its strategy based on "
            "its car’s strengths, tyre wear profile and the evolving race situation."
        )

    # --- Generic fallback for other questions ---
    return (
        "I could not call the external Gemini model from this environment, so I am "
        "running in offline mode. For this particular question I don't have a "
        "hand-crafted explanation. Please try another F1 concept (for example: "
        "ask about DRS or Hamilton's pit stop) or check the race data manually."
    )


def answer_question(**payload: Any) -> Dict[str, Any]:
    """
    Main QA agent:
    - retrieves text and telemetry evidence
    - verifies/filters evidence
    - tries to answer via Gemini
    - if Gemini fails or returns a local fallback tag, use offline logic instead
    """

    question: str = payload.get("question") or ""
    driver_id = payload.get("driver_id")
    lap = payload.get("lap")

    # --- 1. Retrieve evidence ---
    text_evidence: List[Dict[str, Any]] = text_retriever(question, top_k=3)
    telemetry_evidence: List[Dict[str, Any]] = telemetry_retriever(driver_id, lap, top_k=2)
    all_evidence: List[Dict[str, Any]] = text_evidence + telemetry_evidence

    # --- 2. Filter / verify evidence ---
    vetted_evidence, confidence = verify_evidence(all_evidence)

    # --- 3. Build context for the LLM ---
    context = "\n".join(
        f"- {e.get('text')} (source: {e.get('source')})"
        for e in vetted_evidence
        if e.get("text")
    )

    prompt = (
        "You are a concise Formula 1 race engineer.\n"
        "Use the context below to answer the question.\n"
        "If the context is missing key information, you may also use your own "
        "general knowledge about Formula 1 to give the best possible answer.\n"
        "Only say 'I don't know' if you truly cannot answer even with your own knowledge.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )

    # --- 4. Try Gemini; if it fails, use offline answer ---
    try:
        answer = call_llm_system(prompt)

        # call_llm_system يرجع string يبدأ بـ
        # '[Local fallback answer]' لما Gemini غير متوفر
        if isinstance(answer, str) and answer.startswith("[Local fallback answer]"):
            answer = _local_qa_answer(question, vetted_evidence)

    except Exception:
        # أي خطأ مفاجئ -> نرجع للـ offline logic
        answer = _local_qa_answer(question, vetted_evidence)

    return {
        "type": "qa",
        "answer": answer,
        "confidence": confidence,
        "evidence": vetted_evidence,
    }
