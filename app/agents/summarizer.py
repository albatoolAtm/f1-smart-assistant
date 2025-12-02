# app/agents/summarizer.py

import os
import json
import requests
from dotenv import load_dotenv

# نتأكد إن .env مقروء هنا أيضاً
load_dotenv()

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def call_llm_system(prompt: str, max_tokens: int = 250) -> str:
    """
    Calls the OpenAI Chat Completions API (gpt-4o-mini by default)
    to generate a response to the given prompt.

    If the API call fails for any reason, it returns a safe local
    fallback string so that the rest of the app does not crash.
    """

    # نقرأ المفتاح من البيئة داخل الدالة (مو global)
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("WARNING: OPENAI_API_KEY is missing, using local fallback.")
        return "[Local fallback answer] " + prompt[:300]

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant and Formula 1 race engineer. "
                    "Answer clearly and concisely."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("WARNING: OpenAI LLM failed, using local fallback answer:", e)
        return "[Local fallback answer] " + prompt[:300]


def summarize_evidence(evidence_list, language: str = "en") -> str:
    """
    Produces a short summary of provided evidence using OpenAI
    (or the local fallback if the API is unavailable).
    """
    if not evidence_list:
        return "No evidence available to summarize."

    joined = "\n\n".join(
        [f"- {e.get('text')} (source: {e.get('source')})" for e in evidence_list]
    )

    # نعدل البرومبت حسب اللغة
    if language == "ar":
        prompt = (
            "أنت محلل مختص في سباقات الفورمولا 1.\n"
            "اقرأ الأدلة التالية، ثم اكتب ملخصًا قصيرًا وواضحًا باللغة العربية "
            "يوضح أهم النقاط أو يجيب على سؤال المستخدم.\n\n"
            f"الأدلة:\n{joined}\n\nالملخص:"
        )
    else:
        prompt = (
            "You are a concise Formula 1 race analyst.\n"
            "Read the evidence below and produce a short, clear summary that "
            "answers the user's question or explains the situation.\n\n"
            f"Evidence:\n{joined}\n\nSummary:"
        )

    return call_llm_system(prompt)
