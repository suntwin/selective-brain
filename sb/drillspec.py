"""Drill JSON format: validation + Markdown export for the Obsidian vault."""
from __future__ import annotations

from collections import Counter

from .gamify import TOPICS, TOPIC_LABEL, to_local_date

REQUIRED_Q = {"id", "topic", "stem"}


def validate(d: dict) -> list[str]:
    errs = []
    for k in ("id", "title", "drill_date", "questions"):
        if k not in d:
            errs.append(f"missing top-level '{k}'")
    if errs:
        return errs
    ids = set()
    for i, q in enumerate(d["questions"], 1):
        miss = REQUIRED_Q - set(q)
        if miss:
            errs.append(f"Q{i}: missing {sorted(miss)}")
            continue
        if q["id"] in ids:
            errs.append(f"Q{i}: duplicate id {q['id']}")
        ids.add(q["id"])
        if q["topic"] not in TOPICS:
            errs.append(f"Q{i} ({q['id']}): unknown topic '{q['topic']}' (use one of {TOPICS})")
        im = q.get("image")
        if im:
            if not (str(im).startswith("data:image/") or str(im).startswith("https://")):
                errs.append(f"Q{i} ({q['id']}): 'image' must be a data:image/... URI or an https:// URL")
            elif len(str(im)) > 400_000:
                errs.append(f"Q{i} ({q['id']}): image is too big ({len(str(im)) // 1000} KB) — keep under ~300 KB")
        t = q.get("type", "mcq")
        if t == "mcq":
            opts = q.get("options") or []
            if not 2 <= len(opts) <= 5:
                errs.append(f"Q{i} ({q['id']}): needs 2–5 options")
            if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(opts):
                errs.append(f"Q{i} ({q['id']}): 'answer' must be the 0-based index of the right option")
            if len(set(map(str, opts))) != len(opts):
                errs.append(f"Q{i} ({q['id']}): duplicate options")
        elif t == "numeric":
            try:
                float(q["answer"])
            except (KeyError, TypeError, ValueError):
                errs.append(f"Q{i} ({q['id']}): numeric 'answer' must be a number")
        else:
            errs.append(f"Q{i} ({q['id']}): unknown type '{t}'")
    return errs


REASON_TXT = {"concept": "Concept gap", "careless": "Careless slip", "misread": "Misread question",
              "time": "Ran out of time", None: "(not tagged)"}


def _ans(q, v):
    if v in (None, "", "None"):
        return "—"
    if q.get("type", "mcq") == "numeric":
        return f'{v} {q.get("unit", "")}'.strip()
    try:
        return str(q["options"][int(v)])
    except (ValueError, IndexError, KeyError):
        return str(v)


def _correct(q):
    return _ans(q, q["answer"]) if q.get("type", "mcq") == "numeric" else str(q["options"][int(q["answer"])])


def attempt_markdown(drill: dict, attempt: dict, answers: list[dict], checkin: dict | None = None) -> str:
    qm = {q["id"]: q for q in drill["questions"]}
    served = attempt.get("question_ids") or [q["id"] for q in drill["questions"]]
    am = {a["question_id"]: a for a in answers}
    day = to_local_date(attempt.get("finished_at") or attempt.get("started_at"))
    total = len(served)
    score = sum(1 for qid in served if am.get(qid, {}).get("correct"))
    secs = [a.get("seconds") or 0 for a in answers if a.get("seconds")]
    lines = [
        "---", "type: app_drill_result", f"date: {day}", f"drill_id: {drill['id']}",
        f"score: {score}/{total}", f"session_size: {attempt.get('session_size')}",
        f"beat_clock: {bool(attempt.get('beat_clock'))}", f"xp: {attempt.get('xp_earned', 0)}", "---", "",
        f"# App Drill Result — {day} — {drill['title']}", "",
        f"- **Score:** {score}/{total} ({round(score / max(1, total) * 100)}%)",
        f"- **Time limit:** {int(attempt.get('time_limit_sec') or 0) // 60} min at {drill.get('pace_seconds', 90)} s/question"
        f" · **Beat the clock:** {'yes' if attempt.get('beat_clock') else 'no'}"
        f"{' · finished in overtime' if attempt.get('overtime') else ''}",
        f"- **Median seconds/question:** {sorted(secs)[len(secs) // 2] if secs else '—'}",
    ]
    if checkin:
        lines.append(f"- **Check-in:** energy {checkin.get('energy')}/5, {checkin.get('mood', '')}, "
                     f"{checkin.get('minutes_available')} min available → {checkin.get('session_size')}")
    if drill.get("source_note"):
        lines.append(f"- **Drill built from:** {drill['source_note']}")
    lines += ["", "## Topic breakdown", "", "| Topic | Right | Of | % |", "|---|---|---|---|"]
    by = Counter(); right = Counter()
    for qid in served:
        t = qm[qid]["topic"]
        by[t] += 1
        right[t] += 1 if am.get(qid, {}).get("correct") else 0
    for t, n in by.most_common():
        lines.append(f"| {TOPIC_LABEL.get(t, t)} | {right[t]} | {n} | {round(right[t] / n * 100)}% |")
    lines += ["", "## Mistakes (for Mistake_Tracker)", ""]
    wrong = [qid for qid in served if not am.get(qid, {}).get("correct")]
    if not wrong:
        lines.append("None. Perfect drill.")
    rc = Counter()
    for qid in wrong:
        q, a = qm[qid], am.get(qid, {})
        rc[a.get("reason")] += 1
        lines += [
            f"### {qid} · {TOPIC_LABEL.get(q['topic'], q['topic'])}" + (f" · trap: {q['trap']}" if q.get("trap") else ""),
            f"- **Question:** {q['stem']}" + (" *(has diagram)*" if q.get("image") else ""),
            f"- **Her answer:** {_ans(q, a.get('chosen')) if a else 'not answered'} · **Correct:** {_correct(q)}"
            f" · **Time:** {a.get('seconds', '—')} s",
            f"- **Why (her tag):** {REASON_TXT.get(a.get('reason'), a.get('reason'))}",
            f"- **Her fix:** {a.get('fix_note') or '—'}",
        ]
        if q.get("source"):
            lines.append(f"- **Source:** {q['source']}")
        lines.append("")
    if wrong:
        lines += ["## Mistake reasons", ""] + [f"- {REASON_TXT.get(r, r)}: {n}" for r, n in rc.most_common()] + [""]
    lines += ["## All answers", "", "| # | Q | Topic | Result | Seconds |", "|---|---|---|---|---|"]
    for i, qid in enumerate(served, 1):
        a = am.get(qid, {})
        res = "✅" if a.get("correct") else ("❌" if a else "⏭️ not reached")
        lines.append(f"| {i} | {qid} | {TOPIC_LABEL.get(qm[qid]['topic'], qm[qid]['topic'])} | {res} | {a.get('seconds', '—')} |")
    lines += ["", "## Source", f"- Selective Brain app, attempt `{attempt['id']}`", "- Exported for vault ingest"]
    return "\n".join(lines) + "\n"
