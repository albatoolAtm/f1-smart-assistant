# app/main.py

from typing import Any, Dict, Optional
import re

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# نستخدم الـ agents اللي انتي سويتيهم
from app.agents.nlp_agent import (
    analyze_sentiment,
    summarize_text,
)
from app.agents.planner import handle_query


# ==========================
# تهيئة FastAPI + CORS
# ==========================

app = FastAPI(title="F1 Smart Assistant API (OpenAI + Agents)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # للتسليم عادي، للإنتاج يفضّل تضييقها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# Models للـ Requests
# ==========================

class SentimentPayload(BaseModel):
    text: str
    language: str = "auto"  # "auto" / "en" / "ar"


class SummaryPayload(BaseModel):
    text: str
    language: str = "auto"
    length: str = "medium"  # "short" / "medium" / "long"


class QAPayload(BaseModel):
    context: str = ""
    question: str
    language: str = "auto"


class PlannerPayload(BaseModel):
    type: str
    question: Optional[str] = None
    driver_id: Optional[Any] = None
    lap: Optional[int] = None
    language: Optional[str] = None
    context: Optional[str] = None
    max_words: Optional[int] = None
    target_lang: Optional[str] = None


# ==========================
# Utilities بسيطة
# ==========================

def detect_lang(text: str) -> str:
    """كشف تقريبي للعربي/الإنجليزي"""
    if not text:
        return "en"
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    return "en"


# ==========================
# Health check
# ==========================

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ==========================
# 1) Sentiment Agent Endpoint
# ==========================
# متوافق مع الفرونت:
# POST http://127.0.0.1:8000/api/ai/sentiment
# body: { text, language }

@app.post("/api/ai/sentiment")
def sentiment_endpoint(payload: SentimentPayload):
    lang = payload.language
    if lang == "auto":
        lang = detect_lang(payload.text)

    result = analyze_sentiment(payload.text, language=lang)
    # result شكلها من nlp_agent:
    # {
    #   "type": "sentiment",
    #   "label": "positive|negative|neutral",
    #   "score": float,
    #   "explanation": str,
    #   "raw_text": str,
    # }

    label = result.get("label", "neutral")
    score = float(result.get("score", 0.0))
    explanation = result.get("explanation", "")

    return {
        "sentiment": label,        # عشان JS لو يستعمل data.sentiment
        "label": label,
        "score": score,
        "explanation": explanation,
        "raw": result,
    }


# ==========================
# 2) Summary Agent Endpoint
# ==========================
# متوافق مع summary.html:
# POST http://127.0.0.1:8000/api/ai/summary
# body: { text, language, length }

@app.post("/api/ai/summary")
def summary_endpoint(payload: SummaryPayload):
    lang = payload.language
    if lang == "auto":
        lang = detect_lang(payload.text)

    # نترجم length → max_words لـ summarize_text
    if payload.length == "short":
        max_words = 40
    elif payload.length == "long":
        max_words = 160
    else:  # medium
        max_words = 80

    result = summarize_text(payload.text, max_words=max_words)
    # result من nlp_agent:
    # {
    #   "type": "summary",
    #   "summary": "...",
    #   "original_length": int,
    # }

    summary_text = result.get("summary", "")

    return {
        "summary": summary_text,
        "original_length": result.get("original_length", None),
        "max_words": max_words,
        "language": lang,
    }


# ==========================
# 3) Q&A Agent Endpoint
# ==========================
# متوافق مع qa.html:
# POST http://127.0.0.1:8000/api/ai/qa
# body: { context, question, language }

@app.post("/api/ai/qa")
def qa_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    Q&A endpoint:
      - لو فيه context ⇒ نستخدم multilingual_qa (type = multi_qa)
      - لو ما فيه context ⇒ نستخدم planner.handle_query مع type = qa
        وهذي اللي تشغل calendar_agent / knowledge_agent / qa_agent / general_f1_answer
    """
    context = (payload.get("context") or "").strip()
    question = payload.get("question") or ""
    language = payload.get("language") or "auto"
    driver_id = payload.get("driver_id")
    lap = payload.get("lap")

    if not question:
        return {
            "type": "error",
            "message": "Question is required.",
        }

    # 1) لو فيه context → Multilingual QA
    if context:
        target_lang = "ar" if language == "ar" else "en"
        planner_payload = {
            "type": "multi_qa",
            "context": context,
            "question": question,
            "target_lang": target_lang,
        }
    else:
        # 2) بدون context → نخلي الـ planner يقرر:
        #    - calendar_agent (next race, last race...)
        #    - knowledge_agent (drivers / tracks)
        #    - qa_agent / general_f1_answer
        planner_payload = {
            "type": "qa",
            "question": question,
            "driver_id": driver_id,
            "lap": lap,
            "language": language,
        }

    result = handle_query(planner_payload)
    return result
