"""High-level data helpers used by the views."""
from __future__ import annotations

import math
import random
from datetime import datetime, timezone

import streamlit as st

from . import gamify as g
from .store import get_store, now_iso


def store():
    return get_store()


def me() -> dict:
    return st.session_state["profile"]


def child() -> dict:
    """The learner whose data we show. For a parent: the family's child."""
    p = me()
    if p["role"] == "child":
        return p
    kids = [r for r in store().select("profiles", eq={"family_id": p["family_id"]}) if r["role"] == "child"]
    return kids[0] if kids else p


# ---------------------------------------------------------------- reads
def drills(include_archived=False):
    rows = store().select("drills", eq={"family_id": me()["family_id"]}, order="drill_date", desc=True)
    return [d for d in rows if include_archived or d.get("status") == "published"]


def drill(drill_id):
    rows = store().select("drills", eq={"id": drill_id})
    return rows[0] if rows else None


def attempts(uid=None):
    return store().select("attempts", eq={"user_id": uid or child()["id"]}, order="started_at")


def answers(uid=None):
    return store().select("answers", eq={"user_id": uid or child()["id"]}, order="created_at")


def attempt_answers(attempt_id):
    return store().select("answers", eq={"attempt_id": attempt_id}, order="created_at")


def checkins(uid=None):
    return store().select("checkins", eq={"user_id": uid or child()["id"]}, order="day")


def checkin_today(uid=None):
    rows = store().select("checkins", eq={"user_id": uid or child()["id"], "day": str(g.today())})
    return rows[0] if rows else None


def notebook(uid=None):
    return store().select("notebook", eq={"user_id": uid or child()["id"]}, order="created_at", desc=True)


def xp_events(uid=None):
    return store().select("xp_events", eq={"user_id": uid or child()["id"]}, order="created_at")


def xp_total(uid=None):
    return sum(int(e["amount"]) for e in xp_events(uid))


def badges(uid=None):
    return {b["badge_key"]: b for b in store().select("badges", eq={"user_id": uid or child()["id"]})}


# ---------------------------------------------------------------- writes
def add_xp(amount: int, reason: str):
    if amount:
        store().insert("xp_events", {"user_id": me()["id"], "amount": int(amount), "reason": reason})
        st.session_state.setdefault("xp_toasts", []).append((amount, reason))


def save_checkin(energy, mood, minutes, size):
    first = checkin_today() is None
    store().upsert("checkins", {"user_id": me()["id"], "day": str(g.today()), "energy": energy,
                                "mood": mood, "minutes_available": minutes, "session_size": size},
                   on_conflict="user_id,day")
    if first:
        add_xp(g.XP["checkin"], "Daily check-in")


def pick_questions(d: dict, size: str) -> list[str]:
    qs = d["questions"]
    frac = g.SIZES.get(size, g.SIZES["Normal"])["frac"] or 1.0
    n = max(3, math.ceil(len(qs) * frac))
    if n >= len(qs):
        return [q["id"] for q in qs]
    # keep the drill's intended order but sample evenly across it
    step = len(qs) / n
    return [qs[int(i * step)]["id"] for i in range(n)]


def start_attempt(d: dict, size: str) -> dict:
    qids = pick_questions(d, size)
    limit = len(qids) * int(d.get("pace_seconds", 90))
    return store().insert("attempts", {
        "user_id": me()["id"], "drill_id": d["id"], "session_size": size,
        "started_at": now_iso(), "time_limit_sec": limit, "total": len(qids),
        "question_ids": qids, "status": "in_progress"})


def open_attempt(drill_id):
    rows = [a for a in store().select("attempts", eq={"user_id": me()["id"], "drill_id": drill_id})
            if a.get("status") == "in_progress"]
    return rows[-1] if rows else None


def record_answer(attempt, q, chosen, correct, seconds):
    store().upsert("answers", {
        "attempt_id": attempt["id"], "user_id": me()["id"], "question_id": q["id"],
        "topic": q.get("topic"), "chosen": str(chosen), "correct": bool(correct),
        "seconds": int(seconds)}, on_conflict="attempt_id,question_id")


def finish_attempt(attempt, score, total, xp, beat_clock, overtime):
    fields = {"finished_at": now_iso(), "score": score, "total": total, "xp_earned": xp,
              "beat_clock": beat_clock, "overtime": overtime, "status": "finished"}
    store().update("attempts", {"id": attempt["id"]}, fields)
    attempt.update(fields)


def tag_mistake(attempt, q, chosen_label, reason, fix_note, technique):
    store().update("answers", {"attempt_id": attempt["id"], "question_id": q["id"]},
                   {"reason": reason, "fix_note": fix_note})
    store().insert("notebook", {
        "user_id": me()["id"], "kind": "mistake", "topic": q.get("topic"),
        "title": q.get("short") or q["stem"][:80], "question": q, "my_fix": fix_note,
        "technique": technique, "reason": reason, "source": attempt["drill_id"],
        "box": 0, "next_review": str(g.today()), "reviews": 0, "mastered": False})


def add_card(kind, topic, title, technique, my_fix=""):
    store().insert("notebook", {
        "user_id": me()["id"], "kind": kind, "topic": topic, "title": title,
        "technique": technique, "my_fix": my_fix, "box": 0, "next_review": str(g.today()),
        "reviews": 0, "mastered": False})


def review_card(card, got_it):
    box, nxt, mastered = g.next_review(int(card.get("box", 0)), got_it)
    store().update("notebook", {"id": card["id"]}, {
        "box": box, "next_review": str(nxt), "reviews": int(card.get("reviews", 0)) + 1,
        "mastered": mastered})
    add_xp(g.XP["recall_got"] if got_it else g.XP["recall_try"],
           "Remembered a card" if got_it else "Practised a card")


def due_cards(uid=None):
    t = str(g.today())
    return [c for c in notebook(uid) if not c.get("mastered") and str(c.get("next_review"))[:10] <= t]


# ---------------------------------------------------------------- stats bundle
def stats(uid=None):
    uid = uid or child()["id"]
    a, c, ans, nb = attempts(uid), checkins(uid), answers(uid), notebook(uid)
    xp = xp_total(uid)
    s = g.streak(a, c)
    recall_got = sum(1 for e in xp_events(uid) if e["reason"] == "Remembered a card")
    return {"attempts": a, "checkins": c, "answers": ans, "notebook": nb, "xp": xp,
            "level": g.level_for(xp), "streak": s, "recall_got": recall_got}


def award_badges(ctx) -> list[str]:
    """Insert newly-earned badges; return their keys (only the child earns badges)."""
    if me()["role"] != "child":
        return []
    have = badges()
    new = [k for k in g.earned_badges(ctx) if k not in have]
    for k in new:
        store().upsert("badges", {"user_id": me()["id"], "badge_key": k, "earned_at": now_iso()},
                       on_conflict="user_id,badge_key")
    return new


def shuffled_options(q, seed):
    """Stable per-attempt shuffle so A–D positions vary between drills."""
    opts = list(enumerate(q["options"]))
    if q.get("shuffle", True):
        random.Random(f"{seed}-{q['id']}").shuffle(opts)
    return opts


def seconds_since(iso):
    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds()
