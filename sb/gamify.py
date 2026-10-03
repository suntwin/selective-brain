"""XP, levels, streaks and badges — all pure functions over plain rows."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Australia/Melbourne")

# ---------------------------------------------------------------- XP rules
XP = {
    "checkin": 5,
    "attempt": 2,          # any answered question
    "correct": 10,
    "word_part": 6,        # each correct part of a word problem
    "word_all": 6,         # bonus when every part is right
    "read_right": 3,       # picked what the question really asks for
    "speedy": 3,           # correct AND within exam pace
    "drill_done": 25,
    "perfect": 50,
    "mistake_fixed": 8,    # tagged reason + wrote fix → notebook
    "all_fixed": 20,
    "recall_got": 4,
    "recall_try": 1,
    "technique_added": 6,
}

# ---------------------------------------------------------------- levels
LEVELS = [
    (0, "Spark", "✨"),
    (150, "Twinkle", "⭐"),
    (400, "Shimmer", "💫"),
    (800, "Glow", "🌟"),
    (1400, "Sparkle Scholar", "🔮"),
    (2200, "Rainbow Thinker", "🌈"),
    (3200, "Starlight", "🌠"),
    (4500, "Moon Mathlete", "🌙"),
    (6200, "Supernova", "☄️"),
    (8500, "Galaxy Brain", "🌌"),
    (11500, "Selective Superstar", "👑"),
]


def level_for(xp: int) -> dict:
    idx = 0
    for i, (need, _, _) in enumerate(LEVELS):
        if xp >= need:
            idx = i
    need, name, icon = LEVELS[idx]
    nxt = LEVELS[idx + 1][0] if idx + 1 < len(LEVELS) else None
    pct = 1.0 if nxt is None else (xp - need) / (nxt - need)
    return {"num": idx + 1, "name": name, "icon": icon, "xp": xp, "floor": need,
            "next": nxt, "pct": max(0.0, min(1.0, pct)),
            "to_next": None if nxt is None else nxt - xp}


# ---------------------------------------------------------------- time helpers
def today() -> date:
    return datetime.now(TZ).date()


def to_local_date(ts) -> date | None:
    if not ts:
        return None
    if isinstance(ts, date) and not isinstance(ts, datetime):
        return ts
    s = str(ts).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return date.fromisoformat(s[:10])
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(TZ).date()


def days_to_exam(exam_date: str | date | None) -> int:
    d = exam_date or "2027-06-19"
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return (d - today()).days


# ---------------------------------------------------------------- streak
def streak(attempts: list[dict], checkins: list[dict]) -> dict:
    """Practice days build the streak; a 'Rest' check-in keeps it alive (max 1 per 7 days)."""
    practice = {to_local_date(a.get("finished_at")) for a in attempts if a.get("finished_at")}
    rest = {to_local_date(c.get("day")) for c in checkins if c.get("session_size") == "Rest"}
    t = today()
    d = t if (t in practice or t in rest) else t - timedelta(days=1)
    count, rests_used, last_rest = 0, 0, None
    while True:
        if d in practice:
            count += 1
        elif d in rest and (last_rest is None or (last_rest - d).days >= 7):
            rests_used += 1
            last_rest = d
        else:
            break
        d -= timedelta(days=1)
    best, run = 0, 0
    if practice | rest:
        lo, hi = min(practice | rest), max(practice | rest)
        cur = lo
        while cur <= hi:
            if cur in practice:
                run += 1
            elif cur not in rest:
                run = 0
            best = max(best, run)
            cur += timedelta(days=1)
    return {"current": count, "best": max(best, count), "done_today": t in practice,
            "rest_today": t in rest}


# ---------------------------------------------------------------- badges
BADGES = {
    "first_drill":   ("🎀", "First Drill", "Finished your very first drill"),
    "streak_3":      ("🔥", "3-Day Streak", "Practised 3 days in a row"),
    "streak_7":      ("🌈", "7-Day Streak", "A whole week of practice!"),
    "streak_14":     ("💎", "14-Day Streak", "Two sparkling weeks"),
    "streak_30":     ("👑", "30-Day Streak", "A month-long legend"),
    "perfect":       ("💯", "Perfect Drill", "Every answer right"),
    "speedy":        ("⚡", "Beat the Clock", "Finished a drill ahead of exam pace"),
    "fixer_5":       ("🛠️", "Mistake Mender", "Fixed 5 mistakes in your notebook"),
    "careless_5":    ("🔍", "Eagle Eye", "Fixed 5 careless slips"),
    "notebook_10":   ("📒", "Notebook Keeper", "10 cards in your notebook"),
    "recall_20":     ("🧠", "Memory Magic", "Remembered 20 notebook cards"),
    "mastered_5":    ("🏅", "Locked In", "Mastered 5 notebook cards"),
    "q_100":         ("🎯", "Century", "Answered 100 questions"),
    "q_500":         ("🚀", "Rocket Brain", "Answered 500 questions"),
    "indices_hero":  ("🦸", "Indices Hero", "80%+ on 20 indices questions"),
    "level_5":       ("🔮", "Sparkle Scholar", "Reached level 5"),
}


def earned_badges(ctx: dict) -> set[str]:
    """ctx keys: attempts, answers, notebook, xp, streak, recall_got."""
    got = set()
    fin = [a for a in ctx["attempts"] if a.get("finished_at")]
    if fin:
        got.add("first_drill")
    s = ctx["streak"]["best"]
    for n in (3, 7, 14, 30):
        if s >= n:
            got.add(f"streak_{n}")
    if any(a.get("total") and a.get("score") == a.get("total") for a in fin):
        got.add("perfect")
    if any(a.get("beat_clock") for a in fin):
        got.add("speedy")
    mistakes = [n for n in ctx["notebook"] if n.get("kind") == "mistake"]
    if len(mistakes) >= 5:
        got.add("fixer_5")
    if sum(1 for n in mistakes if n.get("reason") == "careless") >= 5:
        got.add("careless_5")
    if len(ctx["notebook"]) >= 10:
        got.add("notebook_10")
    if ctx.get("recall_got", 0) >= 20:
        got.add("recall_20")
    if sum(1 for n in ctx["notebook"] if n.get("mastered")) >= 5:
        got.add("mastered_5")
    nq = len(ctx["answers"])
    if nq >= 100:
        got.add("q_100")
    if nq >= 500:
        got.add("q_500")
    idx = [a for a in ctx["answers"] if a.get("topic") == "Indices"]
    if len(idx) >= 20 and sum(1 for a in idx if a.get("correct")) / len(idx) >= 0.8:
        got.add("indices_hero")
    if level_for(ctx["xp"])["num"] >= 5:
        got.add("level_5")
    return got


# ---------------------------------------------------------------- session sizing
SIZES = {
    "Full":   {"frac": 1.0,  "emoji": "🚀", "label": "Full power",  "blurb": "The whole drill"},
    "Normal": {"frac": 0.75, "emoji": "🌟", "label": "Normal",      "blurb": "About ¾ of the drill"},
    "Light":  {"frac": 0.4,  "emoji": "🌙", "label": "Light",       "blurb": "A short, gentle set"},
    "Rest":   {"frac": 0.0,  "emoji": "🛌", "label": "Rest day",    "blurb": "Recall cards only — streak stays safe"},
}


def suggest_size(energy: int, minutes: int) -> str:
    if energy <= 1 or minutes < 10:
        return "Rest"
    if energy == 2 or minutes < 25:
        return "Light"
    if energy >= 4 and minutes >= 40:
        return "Full"
    return "Normal"


# ---------------------------------------------------------------- spaced recall
INTERVALS = [1, 2, 4, 7, 14, 30]


def next_review(box: int, got_it: bool) -> tuple[int, date, bool]:
    if got_it:
        box = min(box + 1, len(INTERVALS) - 1)
        mastered = box >= len(INTERVALS) - 1
    else:
        box, mastered = 0, False
    return box, today() + timedelta(days=INTERVALS[box]), mastered


# ---------------------------------------------------------------- topic map
TOPICS = ["Fractions", "Ratio_Proportion", "Percentages", "Indices", "Algebra",
          "Angles_Geometry", "Circles_Composite_Shapes", "Statistics_Probability",
          "Speed_Distance_Time", "Money_Measurement", "Number", "Quantitative_Reasoning"]

TOPIC_LABEL = {
    "Fractions": "Fractions", "Ratio_Proportion": "Ratio", "Percentages": "Percentages",
    "Indices": "Indices", "Algebra": "Algebra", "Angles_Geometry": "Angles & Geometry",
    "Circles_Composite_Shapes": "Circles & Shapes", "Statistics_Probability": "Stats & Probability",
    "Speed_Distance_Time": "Speed", "Money_Measurement": "Money & Measures",
    "Number": "Number", "Quantitative_Reasoning": "Quant Reasoning",
}


def topic_map(answers: list[dict]) -> list[dict]:
    out = []
    for t in TOPICS:
        rows = [a for a in answers if a.get("topic") == t]
        if not rows:
            out.append({"topic": t, "label": TOPIC_LABEL[t], "n": 0, "acc": None, "color": "grey"})
            continue
        recent = rows[-20:]
        acc = sum(1 for a in recent if a.get("correct")) / len(recent)
        color = "green" if acc >= 0.8 else "amber" if acc >= 0.6 else "red"
        out.append({"topic": t, "label": TOPIC_LABEL[t], "n": len(rows), "acc": acc, "color": color})
    return out
