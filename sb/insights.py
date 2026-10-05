"""Mistake Map: Claude builds it from the Obsidian vault (every logged test mistake), the parent uploads it
in Parent Hub -> Mistake Map, and the app shows it two ways: the full analysis for the parent, and a short,
friendly 'My focus' tab in her notebook. App drill answers are folded in live, per topic.

JSON shape (kind = "mistake_map"):
  title, updated (YYYY-MM-DD), source_note
  stats    {questions_lost, entries, tests, period}
  types    [loss-type names, in display order]
  periods  [{label, counts: {type: n}}]          how marks were lost, per year / recent tests
  type_note  one-paragraph reading of the periods
  areas    [{label, app_topic, status (Active|Watch|Recheck), why, all, y2026, recent, kid_title, kid_tip}]
  habits   [{title, what, evidence, fix, kid_title, kid_tip, app_topic}]
  wins     [short strings]
  entries  [{date, year, test, q, detail, topic, type, n}]
"""
from __future__ import annotations

from .gamify import TOPICS

STATUSES = ("Active", "Watch", "Recheck")
MAP_KEY = "mistake_map"


def validate(m: dict) -> list[str]:
    errs = []
    if not isinstance(m, dict) or m.get("kind") != MAP_KEY:
        return ["This isn't a mistake map file (it needs \"kind\": \"mistake_map\")."]
    for k in ("updated", "areas", "habits", "entries", "stats"):
        if k not in m:
            errs.append(f"missing '{k}'")
    if errs:
        return errs
    for i, a in enumerate(m["areas"], 1):
        for k in ("label", "status", "why"):
            if not a.get(k):
                errs.append(f"area {i}: missing '{k}'")
        if a.get("status") and a["status"] not in STATUSES:
            errs.append(f"area {i} ({a.get('label')}): status must be one of {STATUSES}")
        t = a.get("app_topic")
        if t and t not in TOPICS:
            errs.append(f"area {i} ({a.get('label')}): unknown app_topic '{t}'")
    for i, h in enumerate(m["habits"], 1):
        for k in ("title", "kid_title", "kid_tip"):
            if not h.get(k):
                errs.append(f"habit {i}: missing '{k}'")
    if not isinstance(m["entries"], list):
        errs.append("'entries' must be a list")
    return errs


def topic_progress(answers: list[dict], topic: str | None, last: int = 20) -> dict | None:
    """Accuracy on her most recent app answers for one topic: {n, acc, recent_n} or None if none yet."""
    if not topic:
        return None
    rows = [a for a in answers if a.get("topic") == topic]
    if not rows:
        return None
    recent = rows[-last:]
    return {"n": len(rows), "recent_n": len(recent), "acc": sum(1 for a in recent if a.get("correct")) / len(recent)}


def colour(acc: float | None) -> str:
    if acc is None:
        return "grey"
    return "green" if acc >= 0.8 else "amber" if acc >= 0.6 else "red"
