import json
import os
from datetime import date
from typing import Any, Dict, List

# مسار ملف ال-calendar داخل مجلد app
_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "race_calendar.json")
)


def _load_calendar() -> Dict[str, Any]:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _parse_race_date(d: str) -> date:
    # d شكلها '2025-03-16'
    year, month, day = [int(x) for x in d.split("-")]
    return date(year, month, day)


def _get_races() -> List[Dict[str, Any]]:
    data = _load_calendar()
    return data.get("races", [])


def is_calendar_question(question: str) -> bool:
    """
    كشف للأسئلة المرتبطة بالرزنامة (next / last / مكان أو وقت سباق معيّن)
    بالإنجليزي والعربي.
    """
    if not question:
        return False

    q = question.lower()
    q_raw = question

    english_keywords = [
        "next race",
        "upcoming race",
        "race calendar",
        "race schedule",
        "grand prix",
        "gp",
        "last race",
        "final race",
        "season finale",
        "when is the race",
        "where is the race"
    ]

    arabic_keywords = [
        "متى السباق",
        "متى يكون السباق",
        "موعد السباق",
        "جدول السباقات",
        "اخر سباق",
        "آخر سباق",
        "اخر سباق في سنة",
        "آخر سباق في سنة",
        "سباق السعودية",
        "سباق البحرين",
        "سباق قطر",
        "سباق ابو ظبي",
        "سباق أبو ظبي"
    ]

    if any(k in q for k in english_keywords):
        return True

    if any(ak in q_raw for ak in arabic_keywords):
        return True

    return False


def answer_calendar_question(question: str) -> Dict[str, Any]:
    """
    يجيب عن أسئلة الرزنامة من ملف race_calendar.json
    - لو السؤال فيه last/final ⇒ يعطي آخر سباق في 2025
    - لو فيه اسم دولة/مدينة/سباق ⇒ يطلع تاريخ ومكان هذا السباق
    - لو فيه next/upcoming ⇒ يحسب أقرب سباق قادم بناءً على تاريخ اليوم
    """
    q = question.lower()
    q_raw = question
    data = _load_calendar()
    races = _get_races()
    season = data.get("season", 2025)

    if not races:
        return {
            "type": "calendar",
            "mode": "none",
            "answer": "No calendar data is configured in this demo.",
            "season": season,
            "race": None,
        }

    # 1) هل المستخدم يقصد "آخر سباق"؟
    want_last = (
        "last race" in q
        or "final race" in q
        or "season finale" in q
        or "اخر سباق" in q_raw
        or "آخر سباق" in q_raw
    )

    if want_last:
        last_race = max(races, key=lambda r: _parse_race_date(r["date"]))
        # نجاوب بالإنجليزي (لو حابة نترجمه للعربي لاحقاً نقدر)
        answer = (
            f"The final race in the {season} Formula 1 season is the "
            f"{last_race['name']} on {last_race['date']} at "
            f"{last_race['location']} in {last_race['city']}, "
            f"{last_race['country']}."
        )
        return {
            "type": "calendar",
            "mode": "final",
            "answer": answer,
            "season": season,
            "race": last_race,
        }

    # 2) هل السؤال عن دولة/مدينة/اسم سباق معيّن؟
    for race in races:
        name = race["name"].lower()
        city = race["city"].lower()
        country = race["country"].lower()

        if (
            name.split(" grand prix")[0] in q
            or city in q
            or country in q
        ):
            answer = (
                f"The {race['name']} in {season} is scheduled on {race['date']} "
                f"at {race['location']} in {race['city']}, {race['country']}."
            )
            return {
                "type": "calendar",
                "mode": "by_race",
                "answer": answer,
                "season": season,
                "race": race,
            }

    # 3) otherwise: نحسب "next race" بناءً على تاريخ اليوم
    today = date.today()
    future = [r for r in races if _parse_race_date(r["date"]) >= today]

    if future:
        next_race = min(future, key=lambda r: _parse_race_date(r["date"]))
    else:
        # لو كل السباقات عدّت، نرجع آخر سباق على أنه "أقرب"
        next_race = max(races, key=lambda r: _parse_race_date(r["date"]))

    answer = (
        f"The next race in the {season} season (based on this demo calendar) is "
        f"the {next_race['name']} on {next_race['date']} at "
        f"{next_race['location']} in {next_race['city']}, "
        f"{next_race['country']}."
    )

    return {
        "type": "calendar",
        "mode": "next",
        "answer": answer,
        "season": season,
        "race": next_race,
    }
