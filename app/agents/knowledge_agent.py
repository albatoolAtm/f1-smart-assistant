# app/agents/knowledge_agent.py

import json
import os
from typing import Any, Dict, List

_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "race_calendar.json")
)


def _load_data() -> Dict[str, Any]:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _get_drivers() -> List[Dict[str, Any]]:
    data = _load_data()
    return data.get("drivers", [])


def _get_tracks() -> List[Dict[str, Any]]:
    data = _load_data()
    return data.get("tracks", [])


def is_knowledge_question(question: str) -> bool:
    """
    يحدد إذا كان السؤال عن سائق أو حلبة.
    مثال:
      - what team does Hamilton drive for?
      - which country is VER from?
      - how long is Jeddah Corniche Circuit?
      - من اي دولة هاميلتون؟ (يتعرف على الاسم فقط)
    """
    if not question:
        return False

    q = question.lower()
    q_raw = question

    # كلمات تدل على سائق/فريق/بلد
    driver_keywords = [
        "driver", "car", "team", "which team", "drives for",
        "nationality", "country", "from which country",
        "سائق", "فريق", "من اي دولة", "من أي دولة"
    ]
    track_keywords = [
        "circuit", "track", "length", "laps",
        "how long is", "km", "kilometre", "kilometer",
        "طول الحلبة", "طول المضمار"
    ]

    if any(k in q for k in driver_keywords + track_keywords):
        return True

    # لو ذكر اسم سائق نعرفه أو كوده
    for d in _get_drivers():
        code = d.get("code", "").lower()
        name = d.get("name", "").lower()
        num = str(d.get("number", ""))

        if code and code.lower() in q:
            return True
        if name and any(part in q for part in name.split()):
            return True
        if num and num in q:
            return True

    # لو ذكر اسم حلبة
    for t in _get_tracks():
        name = t.get("name", "").lower()
        gp = t.get("grand_prix", "").lower()
        city = t.get("city", "").lower()
        country = t.get("country", "").lower()

        if name and name in q:
            return True
        if gp and gp in q:
            return True
        if city and city in q:
            return True
        if country and country in q:
            return True

    return False


def _answer_driver_question(q: str) -> Dict[str, Any] | None:
    q_lower = q.lower()
    drivers = _get_drivers()

    best_match = None

    for d in drivers:
        code = d.get("code", "").lower()
        name = d.get("name", "").lower()
        num = str(d.get("number", ""))

        if code and code in q_lower:
            best_match = d
            break
        if num and num in q_lower:
            best_match = d
            break
        # لو ذكر الاسم أو اللقب
        if name and any(part in q_lower for part in name.split()):
            best_match = d
            break

    if not best_match:
        return None

    name = best_match.get("name")
    team = best_match.get("team")
    country = best_match.get("country")
    number = best_match.get("number")
    code = best_match.get("code")

    # نجاوب بشكل عام ومفهوم
    answer = (
        f"{name} (car {number}, code {code}) drives for {team} "
        f"and is from {country}."
    )

    # لو السؤال عن team فقط
    if "team" in q_lower or "فريق" in q_lower:
        answer = f"{name} drives for {team}."

    # لو السؤال عن الدولة فقط
    if "country" in q_lower or "nationality" in q_lower or "من اي دولة" in q_lower or "من أي دولة" in q_lower:
        answer = f"{name} is from {country}."

    return {
        "type": "knowledge",
        "subtype": "driver",
        "answer": answer,
        "info": best_match,
    }


def _answer_track_question(q: str) -> Dict[str, Any] | None:
    q_lower = q.lower()
    tracks = _get_tracks()

    best_match = None

    for t in tracks:
        name = t.get("name", "").lower()
        gp = t.get("grand_prix", "").lower()
        city = t.get("city", "").lower()
        country = t.get("country", "").lower()

        if name and name in q_lower:
            best_match = t
            break
        if gp and gp in q_lower:
            best_match = t
            break
        if city and city in q_lower:
            best_match = t
            break
        if country and country in q_lower:
            best_match = t
            break

    if not best_match:
        return None

    name = best_match.get("name")
    gp = best_match.get("grand_prix")
    city = best_match.get("city")
    country = best_match.get("country")
    length = best_match.get("length_km")
    laps = best_match.get("laps")

    answer = (
        f"{name} hosts the {gp} in {city}, {country}. "
        f"The circuit length is about {length} km with around {laps} race laps."
    )

    if "length" in q_lower or "طول" in q_lower or "km" in q_lower:
        answer = f"{name} is approximately {length} km long."

    if "laps" in q_lower:
        answer = f"The race at {name} is usually around {laps} laps."

    return {
        "type": "knowledge",
        "subtype": "track",
        "answer": answer,
        "info": best_match,
    }


def answer_knowledge_question(question: str) -> Dict[str, Any]:
    """
    يحاول يجاوب من drivers ثم tracks.
    """
    # 1) سائق
    d_ans = _answer_driver_question(question)
    if d_ans is not None:
        return d_ans

    # 2) حلبة
    t_ans = _answer_track_question(question)
    if t_ans is not None:
        return t_ans

    # fallback (ما قدر يربط السؤال بالداتا)
    return {
        "type": "knowledge",
        "subtype": "unknown",
        "answer": "I could not match this question to the static F1 data (drivers/tracks).",
        "info": None,
    }
