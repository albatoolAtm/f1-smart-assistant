# app/agents/nlp_agent.py

from typing import Dict, Any
import json
import re

from .summarizer import call_llm_system


# ---------- 1) Simple offline sentiment fallback ----------

_POSITIVE_WORDS = {
    "great", "good", "amazing", "fast", "love", "perfect",
    "excellent", "happy", "excited", "awesome", "brilliant"
}
_NEGATIVE_WORDS = {
    "bad", "slow", "terrible", "hate", "worst", "angry",
    "disappointed", "sad", "awful", "horrible", "frustrating"
}


def _offline_sentiment(text: str) -> Dict[str, Any]:
    """
    Very simple rule-based sentiment for offline fallback.
    Returns label + score + explanation.
    """
    t = (text or "").lower()
    pos = sum(w in t for w in _POSITIVE_WORDS)
    neg = sum(w in t for w in _NEGATIVE_WORDS)

    if pos == 0 and neg == 0:
        label = "neutral"
        score = 0.0
    elif pos > neg:
        label = "positive"
        score = min(1.0, (pos - neg) / 5.0)
    elif neg > pos:
        label = "negative"
        score = -min(1.0, (neg - pos) / 5.0)
    else:
        label = "neutral"
        score = 0.0

    explanation = (
        "Offline sentiment estimate based on simple keyword matching. "
        f"Positive hits: {pos}, negative hits: {neg}."
    )

    return {
        "type": "sentiment",
        "label": label,
        "score": score,
        "explanation": explanation,
        "raw_text": text,
    }


# ---------- 2) LLM-based sentiment analysis ----------
def analyze_sentiment(text: str, language: str | None = None) -> Dict[str, Any]:
    """
    Use LLM (OpenAI via call_llm_system) to analyze sentiment of a comment.
    Falls back to a simple offline classifier if LLM is unavailable.
    """
    if not text:
        return {
            "type": "sentiment",
            "label": "unknown",
            "score": 0.0,
            "explanation": "No text was provided.",
            "raw_text": text,
        }

    lang_hint = f" The text is in {language}." if language else ""
    prompt = (
        "You are a sentiment analysis engine for Formula 1 related comments, "
        "team radio messages and social media posts.\n"
        "Classify the overall sentiment of the given text as one of "
        "'positive', 'negative', or 'neutral'.\n"
        "Return the result as a STRICT JSON object with EXACTLY these keys "
        "(no additional text, no Markdown, no code fences):\n"
        "{ \"label\": <string>, \"score\": <number>, \"explanation\": <string> }\n"
        "- label: 'positive' | 'negative' | 'neutral'\n"
        "- score: a number between -1.0 (very negative) and 1.0 (very positive)\n"
        "- explanation: one short sentence explaining why.\n"
        "Do NOT wrap the JSON in ``` or any other formatting.\n"
        f"{lang_hint}\n\n"
        f"Text:\n{text}\n\n"
        "JSON:"
    )

    try:
        raw = call_llm_system(prompt)

        # لو summarizer في وضع offline
        if isinstance(raw, str) and raw.startswith("[Local fallback answer]"):
            return _offline_sentiment(text)

        # ====== تنظيف استجابة الـ LLM قبل json.loads ======
        clean = str(raw).strip()
        clean = re.sub(r"```json", "", clean, flags=re.IGNORECASE)
        clean = clean.replace("```", "").strip()
        clean = re.sub(r"^json", "", clean, flags=re.IGNORECASE).strip()

        try:
            data = json.loads(clean)
            label = data.get("label", "unknown")

            # نحاول نحول الـ score لرقم، لو فشل نحط فالباك حسب الـ label
            try:
                score = float(data.get("score"))
            except (TypeError, ValueError):
                score = None

            if score is None:
                if label == "positive":
                    score = 0.7
                elif label == "negative":
                    score = -0.7
                elif label == "neutral":
                    score = 0.0
                else:
                    score = 0.0

            explanation = data.get("explanation", "")

        except Exception:
            # لو فشل البارس برضو، رجّع الرسالة الخام عشان نقدر نشوفها
            return {
                "type": "sentiment",
                "label": "unknown",
                "score": 0.0,
                "explanation": f"LLM response (unparsed): {raw}",
                "raw_text": text,
            }

        return {
            "type": "sentiment",
            "label": label,
            "score": float(score),
            "explanation": explanation,
            "raw_text": text,
        }

    except Exception:
        # أي خطأ غير متوقّع → fallback
        return _offline_sentiment(text)



# ---------- 3) Summarization ----------

def summarize_text(text: str, max_words: int = 70) -> Dict[str, Any]:
    """
    Summarize a long F1-related text (article, review, race report, etc.).
    Summary is returned in the same language as the input.
    """
    if not text:
        return {
            "type": "summary",
            "summary": "",
            "original_length": 0,
        }

    prompt = (
        "You are a helpful assistant summarizing Formula 1 related text "
        "such as race reports, news articles, or fan discussions.\n"
        f"Rewrite the following text as a concise summary of at most {max_words} words.\n"
        "Preserve the key events, drivers, and outcomes. "
        "Use the same language as the original text.\n\n"
        f"Original text:\n{text}\n\n"
        "Summary:"
    )

    try:
        summary = call_llm_system(prompt)
        if isinstance(summary, str) and summary.startswith("[Local fallback answer]"):
            words = text.split()
            short = " ".join(words[:max_words])
            return {
                "type": "summary",
                "summary": short,
                "original_length": len(words),
            }

        return {
            "type": "summary",
            "summary": summary.strip(),
            "original_length": len(text.split()),
        }

    except Exception:
        words = text.split()
        short = " ".join(words[:max_words])
        return {
            "type": "summary",
            "summary": short,
            "original_length": len(words),
        }


# ---------- 4) Multilingual QA helper ----------

def multilingual_qa(context: str, question: str, target_lang: str = "en") -> Dict[str, Any]:
    """
    Answer a question based on the given context and respond in target_lang.
    This can be used later for a multilingual chat interface.
    """
    prompt = (
        "You are a multilingual assistant answering questions about Formula 1.\n"
        "Use ONLY the context below and your general F1 knowledge when needed.\n"
        f"Answer the user's question in the target language: {target_lang}.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )

    try:
        answer = call_llm_system(prompt)
    except Exception:
        answer = (
            "Multilingual QA model is currently unavailable. "
            "Please try again later with a simpler question."
        )

    return {
        "type": "multilingual_qa",
        "answer": str(answer).strip(),
        "target_language": target_lang,
    }
