# app/agents/planner.py

from typing import Dict, Any

from .qa_agent import answer_question
from .nlp_agent import analyze_sentiment, summarize_text, multilingual_qa
from .summarizer import call_llm_system
from .calendar_agent import is_calendar_question, answer_calendar_question
from .knowledge_agent import is_knowledge_question, answer_knowledge_question


def general_f1_answer(question: str) -> Dict[str, Any]:
    """
    General-purpose F1 Q&A (بدون تليمتري).
    مفيد لشرح المفاهيم والقوانين والاستراتيجيات.
    """
    prompt = (
        "You are an expert on Formula 1.\n"
        "Answer the user's question clearly in 2–4 sentences.\n"
        "If the user asks about live data such as the exact date of the next race, "
        "upcoming calendar, or anything that requires real-time information, "
        "explain that you don't have access to live schedules and recommend "
        "checking the official Formula 1 website or app.\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    try:
        answer = call_llm_system(prompt)
    except Exception:
        answer = (
            "I can't access live Formula 1 data right now. "
            "For the latest calendar and race information, "
            "please check the official Formula 1 website or app."
        )

    return {
        "type": "general",
        "answer": str(answer).strip(),
        "confidence": None,
        "evidence": [],
    }


def handle_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central planner/router for different query types.
      - 'qa'        → race / telemetry QA (Albatool + Sarah)
      - 'sentiment' → NLP sentiment (Somaya)
      - 'summary'   → NLP summarization
      - 'multi_qa'  → multilingual QA
      - 'general'   → general F1 info
    """
    qtype = (payload.get("type") or "").lower()

    # ---------- 1) Main QA ----------
    if qtype == "qa":
        question = payload.get("question") or ""
        driver_id = payload.get("driver_id")
        lap = payload.get("lap")

        # إذا مافيه driver ولا lap → يا Calendar يا Knowledge يا General
        if not driver_id and lap is None:
            # 1) جدول السباقات (next / last / سباق دولة معينة)
            if is_calendar_question(question):
                return answer_calendar_question(question)

            # 2) معلومات سائق أو حلبة (drivers / tracks من JSON)
            if is_knowledge_question(question):
                return answer_knowledge_question(question)

            # 3) سؤال عام عن F1 (مثل: what is DRS?)
            return general_f1_answer(question)

        # هنا سؤال فعلي عن سباق / سائق / لفة → استخدم الـ QA المتقدم
        return answer_question(**payload)

    # ---------- 2) Explicit general mode ----------
    if qtype == "general":
        question = payload.get("question") or ""
        return general_f1_answer(question)

    # ---------- 3) Sentiment ----------
    if qtype == "sentiment":
        text = payload.get("question") or ""
        language = payload.get("language")
        return analyze_sentiment(text, language=language)

    # ---------- 4) Summary ----------
    if qtype == "summary":
        text = payload.get("question") or ""
        max_words = payload.get("max_words") or 70
        return summarize_text(text, max_words=int(max_words))

    # ---------- 5) Multilingual QA ----------
    if qtype == "multi_qa":
        context = payload.get("context") or ""
        question = payload.get("question") or ""
        target_lang = payload.get("target_lang") or "en"
        return multilingual_qa(context, question, target_lang=target_lang)

    # ---------- 6) Unknown ----------
    return {
        "type": "error",
        "message": f"Unknown query type: {qtype}",
    }
