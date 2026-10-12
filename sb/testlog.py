"""Test Review: marks lost on paper tests (school tests, practice papers, mocks), logged by Siyonah herself.

Tables (supabase/005_test_review.sql):
  tests          one row per test she reviews (title, date, source, subject, score/total, ran out of time)
  test_mistakes  one row per lost mark ('lost') or lucky guess ('lucky'):
                 q_ref, marks, topic, loss_type (her tag), parent_type (Papa's re-tag), confidence,
                 what_i_did, should_do, redo schedule (redo_box / redo_next / fixed), talk-list fields.

Loss types match the Mistake Map, plus 'time' (ran out of time), which the map counts as 'Skipped / unfinished'.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta

from . import data, gamify as g
from .store import now_iso

SQL_FILE = "supabase/005_test_review.sql"

SOURCES = ["School test", "Practice paper", "Mock exam", "Other"]
SUBJECTS = ["Maths", "Reading", "Verbal", "Writing", "English"]

# key -> (emoji, kid label, Mistake Map type, bucket)
LOSS = {
    "method":  ("🧩", "Didn't know the method", "Method / concept gap", "learn"),
    "misread": ("👀", "Misread the question", "Misread or missed a condition", "easy"),
    "final":   ("🎯", "Right working, wrong final answer", "Right method, wrong final answer", "easy"),
    "slip":    ("🙈", "Calculation slip", "Arithmetic slip", "easy"),
    "skipped": ("⏭️", "Skipped it / didn't start", "Skipped / unfinished", "learn"),
    "time":    ("⏰", "Ran out of time", "Skipped / unfinished", "time"),
}
BUCKETS = {
    "easy":  ("✨", "Easy marks to win back", "careless: you knew it"),
    "learn": ("📚", "Marks to learn", "a method to practise"),
    "time":  ("⏰", "Time marks", "pace and exam strategy"),
}
CONF = {"sure": "😎 I was sure", "unsure": "🤔 Not sure", "guess": "🎲 I guessed"}
NOTEBOOK_REASON = {"method": "concept", "skipped": "concept", "misread": "misread", "final": "careless",
                   "slip": "careless", "time": "time"}

REDO_DAYS = [3, 14]            # first clean redo after 3 days, second after 14 → fixed


class NotReady(Exception):
    """The tables don't exist yet (005_test_review.sql not run)."""


def _safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # missing table on the live app until the SQL is run
        raise NotReady(f"{e}") from e


# ---------------------------------------------------------------- reads
def tests(uid=None) -> list[dict]:
    rows = _safe(data.store().select, "tests", eq={"user_id": uid or data.child()["id"]})
    return sorted(rows, key=lambda r: (str(r.get("test_date")), str(r.get("created_at"))), reverse=True)


def mistakes(uid=None, test_id=None) -> list[dict]:
    eq = {"test_id": test_id} if test_id else {"user_id": uid or data.child()["id"]}
    return _safe(data.store().select, "test_mistakes", eq=eq, order="created_at")


def safe_tests(uid=None):
    try:
        return tests(uid)
    except NotReady:
        return []


def safe_mistakes(uid=None):
    try:
        return mistakes(uid)
    except NotReady:
        return []


def eff_type(m: dict) -> str | None:
    """Papa's re-tag wins over hers."""
    return m.get("parent_type") or m.get("loss_type")


def bucket(m: dict) -> str:
    return LOSS.get(eff_type(m), ("", "", "", "learn"))[3]


def summary(ms: list[dict]) -> dict:
    lost = [m for m in ms if m.get("kind", "lost") == "lost"]
    by_bucket = Counter()
    by_type = Counter()
    for m in lost:
        n = float(m.get("marks") or 1)
        by_bucket[bucket(m)] += n
        by_type[eff_type(m)] += n
    return {"lost": sum(by_bucket.values()), "n": len(lost), "buckets": by_bucket, "types": by_type,
            "lucky": sum(1 for m in ms if m.get("kind") == "lucky")}


def due_redos(uid=None) -> list[dict]:
    t = str(g.today())
    return [m for m in safe_mistakes(uid) if not m.get("fixed") and m.get("redo_next")
            and str(m["redo_next"])[:10] <= t]


def open_talk(uid=None) -> list[dict]:
    return [m for m in safe_mistakes(uid) if m.get("discuss") and not m.get("discussed")]


def fmt_marks(x) -> str:
    x = float(x or 0)
    return str(int(x)) if x == int(x) else f"{x:g}"


# ---------------------------------------------------------------- writes
def start_test(title, test_date, source, subject, score, total, minutes, ran_out) -> dict:
    return _safe(data.store().insert, "tests", {
        "user_id": data.me()["id"], "title": title.strip(), "test_date": str(test_date), "source": source,
        "subject": subject, "score": score, "total": total, "minutes": minutes, "ran_out_of_time": bool(ran_out),
        "status": "in_progress"})


def update_test(test: dict, fields: dict):
    _safe(data.store().update, "tests", {"id": test["id"]}, fields)
    test.update(fields)


def add_mistake(test: dict, *, kind, q_ref, marks, topic, loss_type, confidence, what_i_did, should_do,
                make_card, discuss, discuss_note) -> dict:
    row = {"test_id": test["id"], "user_id": data.me()["id"], "kind": kind, "q_ref": q_ref.strip(),
           "marks": float(marks or 0) if kind == "lost" else 0, "topic": topic,
           "loss_type": loss_type if kind == "lost" else None, "confidence": confidence,
           "what_i_did": (what_i_did or "").strip(), "should_do": (should_do or "").strip(),
           "redo_box": 0, "redo_next": str(g.today() + timedelta(days=REDO_DAYS[0])), "redo_count": 0,
           "fixed": False, "discuss": bool(discuss), "discuss_note": (discuss_note or "").strip() or None,
           "discussed": False}
    m = _safe(data.store().insert, "test_mistakes", row)
    if make_card:
        card = data.store().insert("notebook", {
            "user_id": data.me()["id"], "kind": "mistake", "topic": topic,
            "title": f"{test['title']} · {row['q_ref']}",
            "question": {"stem": ("What went wrong: " + row["what_i_did"]) if row["what_i_did"] else "",
                         "type": "test"},
            "my_fix": row["should_do"], "technique": "", "reason": NOTEBOOK_REASON.get(loss_type) if kind == "lost" else None,
            "source": f"test:{test['id']}", "box": 0, "next_review": str(g.today()), "reviews": 0, "mastered": False})
        data.store().update("test_mistakes", {"id": m["id"]}, {"card_id": card.get("id")})
        m["card_id"] = card.get("id")
    if kind == "lost":
        data.add_xp(g.XP["test_logged"], "Logged a test mistake")
    else:
        data.add_xp(g.XP["lucky_logged"], "Spotted a lucky guess")
    if make_card:
        data.add_xp(g.XP["technique_added"], "Made a notebook card")
    return m


def delete_mistake(m: dict):
    data.store().delete("test_mistakes", {"id": m["id"]})
    if m.get("card_id"):
        data.store().delete("notebook", {"id": m["card_id"]})


def edit_mistake(test: dict, m: dict, *, kind, q_ref, marks, topic, loss_type, confidence, what_i_did,
                 should_do, discuss, discuss_note, make_card=False):
    """Fix a logged card. No XP changes; the redo schedule is kept.

    If she changes the reason, Papa's re-tag is cleared and the test goes back to 'to check'."""
    lost = kind == "lost"
    fields = {"kind": kind, "q_ref": q_ref.strip(), "marks": float(marks or 0) if lost else 0, "topic": topic,
              "loss_type": loss_type if lost else None, "confidence": confidence,
              "what_i_did": (what_i_did or "").strip(), "should_do": (should_do or "").strip(),
              "discuss": bool(discuss), "discuss_note": (discuss_note or "").strip() or None}
    if fields["loss_type"] != m.get("loss_type") or kind != m.get("kind"):
        fields["parent_type"] = None
        if test.get("parent_checked"):
            update_test(test, {"parent_checked": False})
    if not discuss:
        fields["discussed"] = False
    update_mistake(m, fields)
    card_fields = {"title": f"{test['title']} · {fields['q_ref']}", "topic": topic,
                   "question": {"stem": ("What went wrong: " + fields["what_i_did"]) if fields["what_i_did"] else "",
                                "type": "test"},
                   "my_fix": fields["should_do"], "reason": NOTEBOOK_REASON.get(loss_type) if lost else None}
    if m.get("card_id"):
        data.store().update("notebook", {"id": m["card_id"]}, card_fields)
    elif make_card:
        card = data.store().insert("notebook", dict(card_fields, user_id=data.me()["id"], kind="mistake",
                                                    technique="", source=f"test:{test['id']}", box=0,
                                                    next_review=str(g.today()), reviews=0, mastered=False))
        update_mistake(m, {"card_id": card.get("id")})
        data.add_xp(g.XP["technique_added"], "Made a notebook card")


def update_mistake(m: dict, fields: dict):
    _safe(data.store().update, "test_mistakes", {"id": m["id"]}, fields)
    m.update(fields)


def finish_test(test: dict):
    first = test.get("status") != "done" and not test.get("finished_at")
    update_test(test, {"status": "done", "finished_at": test.get("finished_at") or now_iso()})
    if first:
        data.add_xp(g.XP["test_reviewed"], "Reviewed a test")


def redo(m: dict, got_it: bool) -> bool:
    """Record a fresh redo on paper. Returns True if this one is now fixed."""
    box = int(m.get("redo_box") or 0)
    fields = {"redo_count": int(m.get("redo_count") or 0) + 1}
    fixed = False
    if got_it:
        if box + 1 >= len(REDO_DAYS):
            fields.update({"fixed": True, "fixed_at": now_iso(), "redo_next": None, "redo_box": box + 1})
            fixed = True
        else:
            fields.update({"redo_box": box + 1, "redo_next": str(g.today() + timedelta(days=REDO_DAYS[box + 1]))})
    else:
        fields.update({"redo_box": 0, "redo_next": str(g.today() + timedelta(days=REDO_DAYS[0]))})
    update_mistake(m, fields)
    if fixed:
        data.add_xp(g.XP["redo_fixed"], "Fixed a test mistake for good")
    elif got_it:
        data.add_xp(g.XP["redo_right"], "Redid a test question right")
    else:
        data.add_xp(g.XP["redo_try"], "Had another go at a test question")
    return fixed


# ---------------------------------------------------------------- vault export
def test_markdown(t: dict, ms: list[dict]) -> str:
    s = summary(ms)
    score = f"{fmt_marks(t['score'])}/{fmt_marks(t['total'])}" if t.get("score") is not None and t.get("total") else "score not entered"
    lines = [f"# Test Review · {t['title']} · {t['test_date']}", "",
             f"- **Source:** {t.get('source') or '—'} · **Block:** {t.get('subject') or '—'} · **Score:** {score}",
             f"- **Ran out of time:** {'yes' if t.get('ran_out_of_time') else 'no'}"
             + (f" · **Minutes:** {t['minutes']}" if t.get("minutes") else ""),
             f"- **Logged by Siyonah in the app (Test Review).** Status: {t.get('status')}"
             + (" · Papa checked the tags ✅" if t.get("parent_checked") else ""), ""]
    if t.get("parent_note"):
        lines += [f"- **Papa's note:** {t['parent_note']}", ""]
    lines += ["## Summary", "", f"- Marks lost (logged): **{fmt_marks(s['lost'])}** across {s['n']} question(s)"]
    if t.get("score") is not None and t.get("total"):
        gap = float(t["total"]) - float(t["score"])
        if abs(gap - s["lost"]) > 0.01:
            lines.append(f"- ⚠️ Score says {fmt_marks(gap)} marks lost, but {fmt_marks(s['lost'])} were logged")
    for b, (ic, name, _) in BUCKETS.items():
        if s["buckets"].get(b):
            lines.append(f"- {ic} {name}: {fmt_marks(s['buckets'][b])}")
    lines.append(f"- 🍀 Lucky guesses (right, but not sure): {s['lucky']}")
    lines += ["", "## Mistake_Tracker lines", "",
              f"### {t['test_date']} | {t['title']} | {score} | (Test Review, app)"]
    for m in ms:
        if m.get("kind") != "lost":
            continue
        typ = LOSS.get(eff_type(m), ("", "", "?", ""))[2] + (" (ran out of time)" if eff_type(m) == "time" else "")
        retag = f" (Siyonah tagged: {LOSS.get(m.get('loss_type'), ('', '', m.get('loss_type'), ''))[2]})" \
            if m.get("parent_type") and m.get("parent_type") != m.get("loss_type") else ""
        lines.append(f"- **{t['test_date']}** | {m['q_ref']}: {g.TOPIC_LABEL.get(m.get('topic'), m.get('topic') or '—')} | "
                     f"{typ}{retag}, {fmt_marks(m.get('marks'))} mark(s), {CONF.get(m.get('confidence'), 'confidence —')} | "
                     f"What I did: {m.get('what_i_did') or '—'} | Should do: {m.get('should_do') or '—'}")
    lucky = [m for m in ms if m.get("kind") == "lucky"]
    if lucky:
        lines += ["", "## Lucky guesses (right, but a hidden weakness)", ""]
        for m in lucky:
            lines.append(f"- {m['q_ref']}: {g.TOPIC_LABEL.get(m.get('topic'), m.get('topic') or '—')} · "
                         f"{CONF.get(m.get('confidence'), '')} · {m.get('what_i_did') or ''}")
    talk = [m for m in ms if m.get("discuss") or m.get("parent_note")]
    if talk:
        lines += ["", "## Talked through with Papa", ""]
        for m in talk:
            lines.append(f"- {m['q_ref']}: her question: {m.get('discuss_note') or '—'} · Papa: {m.get('parent_note') or '—'}"
                         + (" ✅ talked" if m.get("discussed") else ""))
    lines += ["", "## Redo progress", "", "| Q | Redos | Status |", "|---|---|---|"]
    for m in ms:
        st_ = "✅ fixed" if m.get("fixed") else f"next redo {m.get('redo_next') or '—'}"
        lines.append(f"| {m['q_ref']} | {m.get('redo_count') or 0} | {st_} |")
    return "\n".join(lines) + "\n"
