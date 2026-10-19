"""Weekly routine (her timetable) and the Reward Shop (XP → books, tennis treats, outings).

Tables (supabase/006_routine_rewards.sql):
  routine_blocks  the family's timetable: weekday (0 = Mon), start/end 'HH:MM' (or blank = any time),
                  kind, title, optional. Both Siyonah and her parents can edit it. Removing a block only
                  hides it (active = false), so old ticks keep their history.
  routine_logs    one row per block per day she ticks: approved straight away (auto_approve, the default:
                  XP paid at once, a parent can take it back → declined) or done (waiting) → approved | declined
                  when auto_approve is off; or skipped (with a reason) / excused (a parent let her off).
  rewards         the family's shop catalogue (parent edits). ask_book = ask "which book?" when she swaps.
  redemptions     her swaps: requested (XP held) → given | declined (XP back).
  book_wishlist   books she'd love; a parent can see the list when buying.
Wallet = all XP earned − XP held or spent in the shop. Levels use lifetime XP, so spending never drops a level.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from . import data, gamify as g
from .store import now_iso

SQL_FILE = "supabase/006_routine_rewards.sql"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# kind -> (emoji, group, colour class)
KINDS = {
    "Maths":       ("🔢", "study", "pink"),
    "English":     ("📖", "study", "lav"),
    "Writing":     ("✍️", "study", "lav"),
    "School work": ("🎒", "study", "aqua"),
    "Reading":     ("📚", "study", "gold"),
    "Tennis":      ("🎾", "active", "mint"),
    "Tennis match": ("🏆", "active", "mint"),
    "Swimming":    ("🏊", "active", "aqua"),
    "Other":       ("⭐", "active", "gold"),
}

# XP per activity, in line with Aadiv's Banana Quest (1 XP a minute, sport lesson +10, game/match +20).
#   per_min  XP for each minute of the block
#   cap      most XP the minutes can give in one block
#   bonus    added on top for every block of this kind
#   flat     XP when the block has no set time (e.g. "Tennis match · any time")
KIND_XP = {
    "Maths":        {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 30},
    "English":      {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 30},
    "Writing":      {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 30},
    "School work":  {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 30},
    "Reading":      {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 30},
    "Tennis":       {"per_min": 1, "cap": 120, "bonus": 10, "flat": 70},
    "Tennis match": {"per_min": 1, "cap": 120, "bonus": 20, "flat": 80},
    "Swimming":     {"per_min": 1, "cap": 120, "bonus": 10, "flat": 70},
    "Other":        {"per_min": 1, "cap": 120, "bonus": 0,  "flat": 20},
}

DEFAULT_SETTINGS = {
    "kinds": KIND_XP,      # XP per activity (Parent Hub → ⚙️ XP rules)
    "day_bonus": 15,       # every non-optional block that day confirmed
    "week_bonus": 50,      # every non-optional block Mon–Sun confirmed
    "days_back": 1,        # she can tick today and this many days back
    "auto_approve": True,  # True: XP the moment she ticks (a parent can take it back). False: a parent confirms first
}

# Siyonah's paper timetable, worked out with Mum (2026-10-19). (weekday, start, end, kind, title, optional)
STARTER = [
    (0, "16:00", "17:00", "School work", "School work", False),
    (0, "17:00", "18:00", "Tennis", "Tennis", False),
    (0, "18:30", "20:30", "Maths", "Maths with Preetha's mum", False),
    (0, "21:00", "22:30", "English", "English", False),
    (1, "16:30", "18:00", "English", "English", False),
    (1, "18:30", "19:30", "Swimming", "Swimming", False),
    (1, "21:00", "22:30", "Maths", "Maths", False),
    (2, "16:30", "18:30", "English", "English", False),
    (2, "19:30", "21:30", "Maths", "Maths", False),
    (2, "21:30", "22:00", "School work", "School work", False),
    (3, "16:30", "18:30", "English", "English", False),
    (3, "19:30", "21:30", "Maths", "Maths", False),
    (3, "21:30", "22:00", "School work", "School work (if any)", True),
    (4, "16:30", "18:30", "English", "English", False),
    (4, "19:30", "21:30", "Maths", "Maths", False),
    (4, "21:30", "22:00", "School work", "School work", False),
    (6, None, None, "Tennis match", "Tennis match", False),
]

# Shop starter catalogue. (emoji, title, category, cost, ask_book)
STARTER_REWARDS = [
    ("🌙", "+30 min bedtime reading (one night)", "Books", 150, False),
    ("🏛️", "Library adventure: pick 5 books", "Books", 250, False),
    ("🔖", "Fancy bookmark or reading-notebook set", "Books", 400, False),
    ("🛋️", "Reading night-in: blanket fort + snacks", "Books", 500, False),
    ("☕", "Bookshop trip + hot chocolate", "Books", 600, False),
    ("📕", "A new paperback of my choice", "Books", 1200, True),
    ("📗", "A new hardback or special edition", "Books", 2000, True),
    ("📚", "A whole book series box set", "Books", 5000, True),
    ("🎾", "New tube of tennis balls", "Tennis", 300, False),
    ("🖐️", "New overgrips for my racquet", "Tennis", 350, False),
    ("👨‍👧", "Hitting session with Papa (I pick the drills)", "Tennis", 400, False),
    ("🎽", "Tennis headband / wristbands", "Tennis", 700, False),
    ("🏟️", "Watch a live pro tennis match", "Tennis", 4000, False),
    ("🍦", "Weekend treat of my choice", "Treats", 300, False),
]
CATEGORIES = {"Books": "📚", "Tennis": "🎾", "Treats": "🍦"}

OK_STATES = ("approved", "excused")


class NotReady(Exception):
    """The tables don't exist yet (006_routine_rewards.sql not run)."""


def _safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # missing table on the live app until the SQL is run
        raise NotReady(str(e)) from e


def ready() -> bool:
    try:
        blocks(include_hidden=True)
        return True
    except NotReady:
        return False


# ---------------------------------------------------------------- settings
def settings() -> dict:
    fam = data.me()["family_id"]
    try:
        rows = data.store().select("insights", eq={"id": f"routine_settings_{fam}"})
    except Exception:
        rows = []
    s = dict(DEFAULT_SETTINGS)
    if rows:
        s.update({k: v for k, v in (rows[0].get("data") or {}).items() if k in DEFAULT_SETTINGS})
    kinds = {k: dict(v) for k, v in KIND_XP.items()}           # saved values on top of the defaults
    for k, v in (s.get("kinds") or {}).items():
        if k in kinds and isinstance(v, dict):
            kinds[k].update({f: v[f] for f in ("per_min", "cap", "bonus", "flat") if f in v})
    s["kinds"] = kinds
    return s


def save_settings(new: dict):
    fam = data.me()["family_id"]
    data.store().upsert("insights", {"id": f"routine_settings_{fam}", "family_id": fam, "kind": "routine_settings",
                                     "title": "Routine XP rules", "updated": str(g.today()), "data": new},
                        on_conflict="id")


# ---------------------------------------------------------------- timetable
def _mins(t: str | None) -> int | None:
    if not t:
        return None
    h, m = str(t)[:5].split(":")
    return int(h) * 60 + int(m)


def block_minutes(b: dict) -> int | None:
    s, e = _mins(b.get("start_time")), _mins(b.get("end_time"))
    if s is None or e is None:
        return None
    return e - s if e > s else e + 24 * 60 - s


def kind_xp(kind: str, minutes: int | None, st: dict | None = None) -> int:
    st = st or settings()
    r = st["kinds"].get(kind) or st["kinds"]["Other"]
    if not minutes:
        return int(r["flat"])
    return int(min(float(r["cap"]), round(minutes * float(r["per_min"])))) + int(r["bonus"])


def block_xp(b: dict, st: dict | None = None) -> int:
    return kind_xp(b.get("kind"), block_minutes(b), st)


def time_label(b: dict) -> str:
    def fmt(t):
        h, m = divmod(_mins(t), 60)
        suf = "am" if h < 12 else "pm"
        h = h % 12 or 12
        return f"{h}:{m:02d}{suf}" if m else f"{h}{suf}"
    if not b.get("start_time"):
        return "Any time"
    if not b.get("end_time"):
        return f"From {fmt(b['start_time'])}"
    return f"{fmt(b['start_time'])} – {fmt(b['end_time'])}"


def emoji(kind) -> str:
    return KINDS.get(kind, KINDS["Other"])[0]


def blocks(include_hidden=False) -> list[dict]:
    rows = _safe(data.store().select, "routine_blocks", eq={"family_id": data.me()["family_id"]})
    if not include_hidden:
        rows = [r for r in rows if r.get("active", True)]
    return sorted(rows, key=lambda r: (int(r["weekday"]), _mins(r.get("start_time")) if r.get("start_time") else 9999,
                                       str(r.get("title"))))


def day_blocks(day: date, all_blocks=None) -> list[dict]:
    wd = day.weekday()
    return [b for b in (all_blocks if all_blocks is not None else blocks()) if int(b["weekday"]) == wd]


def add_block(weekday, start, end, kind, title, optional=False) -> dict:
    return data.store().insert("routine_blocks", {
        "family_id": data.me()["family_id"], "weekday": int(weekday), "start_time": start, "end_time": end,
        "kind": kind, "title": title.strip() or kind, "optional": bool(optional), "active": True,
        "updated_by": data.me()["id"], "updated_at": now_iso()})


def update_block(bid, fields: dict):
    data.store().update("routine_blocks", {"id": bid},
                        {**fields, "updated_by": data.me()["id"], "updated_at": now_iso()})


def remove_block(bid):
    update_block(bid, {"active": False})


def seed_routine(replace=False) -> int:
    """Load the paper timetable. replace=True hides the current blocks first."""
    if replace:
        for b in blocks():
            remove_block(b["id"])
    for wd, s, e, k, t, opt in STARTER:
        add_block(wd, s, e, k, t, opt)
    return len(STARTER)


def copy_day(src_wd: int, targets: list[int]) -> int:
    n = 0
    src = [b for b in blocks() if int(b["weekday"]) == src_wd]
    for wd in targets:
        if wd == src_wd:
            continue
        for b in src:
            add_block(wd, b.get("start_time"), b.get("end_time"), b["kind"], b["title"], b.get("optional"))
            n += 1
    return n


# ---------------------------------------------------------------- ticks
def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def logs(uid=None, start: date | None = None, end: date | None = None) -> list[dict]:
    rows = _safe(data.store().select, "routine_logs", eq={"user_id": uid or data.child()["id"]})
    if start:
        rows = [r for r in rows if str(r["day"])[:10] >= str(start)]
    if end:
        rows = [r for r in rows if str(r["day"])[:10] <= str(end)]
    return rows


def log_map(uid=None, start=None, end=None) -> dict:
    """{(block_id, 'YYYY-MM-DD'): log}"""
    return {(r.get("block_id"), str(r["day"])[:10]): r for r in logs(uid, start, end)}


def _snap(b: dict, st=None) -> dict:
    return {"title": b["title"], "kind": b["kind"], "minutes": block_minutes(b), "xp": block_xp(b, st)}


def tick(b: dict, day: date) -> list[str]:
    """She did it. With auto_approve (default) the XP and any day/week bonus are paid at once;
    otherwise it waits for a parent to confirm. Returns messages."""
    st_ = settings()
    data.store().upsert("routine_logs", {
        "user_id": data.me()["id"], "block_id": b["id"], "day": str(day), "status": "done",
        **_snap(b, st_), "note": None, "parent_note": None, "ticked_at": now_iso(), "reviewed_at": None},
        on_conflict="user_id,block_id,day")
    if not st_.get("auto_approve", True):
        return []
    log = data.store().select("routine_logs", eq={"user_id": data.me()["id"], "block_id": b["id"], "day": str(day)})
    return confirm(log[0], auto=True) if log else []


def skip(b: dict, day: date, reason: str):
    data.store().upsert("routine_logs", {
        "user_id": data.me()["id"], "block_id": b["id"], "day": str(day), "status": "skipped",
        **_snap(b), "note": reason.strip(), "ticked_at": now_iso()}, on_conflict="user_id,block_id,day")


def undo(log: dict) -> list[str]:
    """She un-ticks a block (e.g. tapped by mistake). An approved block gives its XP back."""
    msgs = []
    if log.get("status") == "approved":
        msgs = take_back(log)
    if log.get("status") in ("done", "skipped", "approved"):
        data.store().delete("routine_logs", {"id": log["id"]})
    return msgs


def _net_paid(uid, reason) -> int:
    ev = data.xp_events(uid)
    return (sum(1 for e in ev if e["reason"] == reason)
            - sum(1 for e in ev if e["reason"] == f"{reason} (taken back)"))


def _bonus_paid(uid, reason) -> bool:
    return _net_paid(uid, reason) > 0


def confirm(log: dict, xp: int | None = None, auto: bool = False) -> list[str]:
    """Approve a tick: pays its XP, then any day / week bonus. Returns messages.
    auto=True when it's approved the moment she ticks (no parent involved)."""
    uid = log["user_id"]
    amount = int(log.get("xp") or 0) if xp is None else int(xp)
    data.store().update("routine_logs", {"id": log["id"]}, {
        "status": "approved", "xp": amount, "reviewed_at": now_iso(),
        "reviewed_by": None if auto else data.me()["id"]})
    day = date.fromisoformat(str(log["day"])[:10])
    msgs = []
    if amount:
        data.add_xp_for(uid, amount, f"Routine: {log.get('title')} ({SHORT[day.weekday()]} {day.day})")
        msgs.append(f"+{amount} XP · {log.get('title')}")
    msgs += check_bonuses(uid, day)
    return msgs


def decline(log: dict, note: str = "") -> list[str]:
    """Parent: 'not done'. If the XP was already paid (auto-approve), it is taken back, with any bonus it unlocked."""
    msgs = take_back(log) if log.get("status") == "approved" else []
    data.store().update("routine_logs", {"id": log["id"]}, {
        "status": "declined", "parent_note": note.strip() or None, "reviewed_at": now_iso(),
        "reviewed_by": data.me()["id"]})
    return msgs


def take_back(log: dict) -> list[str]:
    """Reverse an approved block's XP, then any day/week bonus that no longer holds. Returns messages."""
    uid = log["user_id"]
    day = date.fromisoformat(str(log["day"])[:10])
    amount = int(log.get("xp") or 0)
    msgs = []
    if amount:
        data.add_xp_for(uid, -amount, f"Routine taken back: {log.get('title')} ({SHORT[day.weekday()]} {day.day})")
        msgs.append(f"-{amount} XP · {log.get('title')}")
    data.store().update("routine_logs", {"id": log["id"]}, {"status": "declined"})   # so the bonus check sees it
    st_, all_b = settings(), blocks()
    ws = week_start(day)
    lm = log_map(uid, ws, ws + timedelta(days=6))
    day_ok = bool(day_complete(day, lm, all_b))
    week = [day_complete(ws + timedelta(days=i), lm, all_b) for i in range(7)]
    week_ok = any(w is not None for w in week) and all(w in (True, None) for w in week)
    for reason, amt, still in ((f"Routine day complete · {day}", st_["day_bonus"], day_ok),
                               (f"Routine week complete · {ws}", st_["week_bonus"], week_ok)):
        if not still and _bonus_paid(uid, reason):
            ev = [e for e in data.xp_events(uid) if e["reason"] == reason]
            paid = int(ev[-1]["amount"]) if ev else int(amt)
            data.add_xp_for(uid, -paid, f"{reason} (taken back)")
            msgs.append(f"-{paid} XP · bonus")
    return msgs


def excuse(b: dict, day: date, uid: str, note: str = "") -> list[str]:
    """Parent lets her off a block (sick, school event…). No XP, but it counts for the day/week bonus."""
    data.store().upsert("routine_logs", {
        "user_id": uid, "block_id": b["id"], "day": str(day), "status": "excused", **_snap(b), "xp": 0,
        "parent_note": note.strip() or None, "reviewed_at": now_iso(), "reviewed_by": data.me()["id"]},
        on_conflict="user_id,block_id,day")
    return check_bonuses(uid, day)


def day_complete(day: date, lm: dict, all_blocks) -> bool | None:
    """True when every non-optional block that day is approved/excused. None = nothing scheduled."""
    req = [b for b in day_blocks(day, all_blocks) if not b.get("optional")]
    if not req:
        return None
    return all(lm.get((b["id"], str(day)), {}).get("status") in OK_STATES for b in req)


def check_bonuses(uid, day: date) -> list[str]:
    st, all_b = settings(), blocks()
    ws = week_start(day)
    lm = log_map(uid, ws, ws + timedelta(days=6))
    msgs = []
    if day_complete(day, lm, all_b) and st["day_bonus"]:
        reason = f"Routine day complete · {day}"
        if not _bonus_paid(uid, reason):
            data.add_xp_for(uid, int(st["day_bonus"]), reason)
            msgs.append(f"+{st['day_bonus']} XP · whole {DAYS[day.weekday()]} done 🌟")
    week = [day_complete(ws + timedelta(days=i), lm, all_b) for i in range(7)]
    if any(w is not None for w in week) and all(w in (True, None) for w in week) and st["week_bonus"]:
        reason = f"Routine week complete · {ws}"
        if not _bonus_paid(uid, reason):
            data.add_xp_for(uid, int(st["week_bonus"]), reason)
            msgs.append(f"+{st['week_bonus']} XP · the WHOLE week done 🏆")
    return msgs


def pending(uid=None) -> list[dict]:
    try:
        rows = [r for r in logs(uid) if r.get("status") == "done"]
    except NotReady:
        return []
    return sorted(rows, key=lambda r: (str(r["day"]), str(r.get("ticked_at"))))


def week_summary(uid, ws: date) -> dict:
    all_b = blocks()
    lm = log_map(uid, ws, ws + timedelta(days=6))
    req = [(b, ws + timedelta(days=int(b["weekday"]))) for b in all_b if not b.get("optional")]
    done = sum(1 for b, d in req if lm.get((b["id"], str(d)), {}).get("status") in OK_STATES)
    waiting = sum(1 for r in lm.values() if r.get("status") == "done")
    xp = sum(int(r.get("xp") or 0) for r in lm.values() if r.get("status") == "approved")
    days_full = sum(1 for i in range(7) if day_complete(ws + timedelta(days=i), lm, all_b))
    return {"required": len(req), "done": done, "waiting": waiting, "xp": xp, "days_full": days_full, "map": lm}


# ---------------------------------------------------------------- wallet & shop
def rewards(include_hidden=False) -> list[dict]:
    rows = _safe(data.store().select, "rewards", eq={"family_id": data.me()["family_id"]})
    if not include_hidden:
        rows = [r for r in rows if r.get("active", True)]
    return sorted(rows, key=lambda r: (list(CATEGORIES).index(r.get("category")) if r.get("category") in CATEGORIES
                                       else 9, int(r.get("cost") or 0)))


def seed_rewards() -> int:
    fam = data.me()["family_id"]
    for i, (em, title, cat, cost, ask) in enumerate(STARTER_REWARDS):
        data.store().insert("rewards", {"family_id": fam, "emoji": em, "title": title, "category": cat,
                                        "cost": cost, "ask_book": ask, "active": True, "sort": i})
    return len(STARTER_REWARDS)


def redemptions(uid=None) -> list[dict]:
    try:
        rows = _safe(data.store().select, "redemptions", eq={"user_id": uid or data.child()["id"]})
    except NotReady:
        return []
    return sorted(rows, key=lambda r: str(r.get("created_at")), reverse=True)


def wallet(uid=None) -> dict:
    uid = uid or data.child()["id"]
    earned = data.xp_total(uid)
    reds = redemptions(uid)
    held = sum(int(r["cost"]) for r in reds if r["status"] == "requested")
    spent = sum(int(r["cost"]) for r in reds if r["status"] == "given")
    return {"earned": earned, "held": held, "spent": spent, "balance": earned - held - spent}


def request(rw: dict, note: str = "") -> str | None:
    """Swap XP for a reward. Returns an error message, or None."""
    w = wallet(data.me()["id"])
    if w["balance"] < int(rw["cost"]):
        return f"You need {int(rw['cost']) - w['balance']} more XP for this one."
    data.store().insert("redemptions", {
        "user_id": data.me()["id"], "reward_id": rw["id"], "title": rw["title"], "emoji": rw.get("emoji"),
        "category": rw.get("category"), "cost": int(rw["cost"]), "status": "requested",
        "note": note.strip() or None})
    return None


def cancel(red: dict):
    if red["status"] == "requested":
        data.store().delete("redemptions", {"id": red["id"]})


def give(red: dict, note: str = ""):
    data.store().update("redemptions", {"id": red["id"]}, {
        "status": "given", "parent_note": note.strip() or None, "decided_at": now_iso()})


def refuse(red: dict, note: str = ""):
    data.store().update("redemptions", {"id": red["id"]}, {
        "status": "declined", "parent_note": note.strip() or None, "decided_at": now_iso()})


def goal(uid=None) -> dict | None:
    uid = uid or data.child()["id"]
    rows = data.store().select("profiles", eq={"id": uid})
    gid = rows[0].get("reward_goal") if rows else None
    if not gid:
        return None
    try:
        return next((r for r in rewards() if r["id"] == gid), None)
    except NotReady:
        return None


def set_goal(rid: str | None):
    data.store().update("profiles", {"id": data.me()["id"]}, {"reward_goal": rid})


def bookshelf(uid=None) -> list[dict]:
    """Books she has got from the shop, oldest first (one spine each)."""
    return [r for r in redemptions(uid)[::-1] if r["status"] == "given" and r.get("category") == "Books"
            and r.get("note")]


def wishlist(uid=None) -> list[dict]:
    try:
        rows = _safe(data.store().select, "book_wishlist", eq={"user_id": uid or data.child()["id"]})
    except NotReady:
        return []
    return sorted(rows, key=lambda r: str(r.get("created_at")))


def add_wish(title, author=""):
    data.store().insert("book_wishlist", {"user_id": data.me()["id"], "title": title.strip(),
                                          "author": author.strip() or None, "status": "want"})


def remove_wish(wid):
    data.store().delete("book_wishlist", {"id": wid})


def safe_stats(uid) -> dict:
    """For badges: confirmed routine blocks, full weeks, books given. Empty if the SQL isn't run."""
    try:
        lg = logs(uid)
    except NotReady:
        lg = []
    weeks = sum(1 for e in data.xp_events(uid) if str(e["reason"]).startswith("Routine week complete"))
    return {"routine_done": sum(1 for r in lg if r.get("status") == "approved"), "routine_weeks": weeks,
            "books_got": len([r for r in redemptions(uid) if r["status"] == "given" and r.get("category") == "Books"])}


def parse_hhmm(t) -> str | None:
    if t is None:
        return None
    if isinstance(t, str):
        return t[:5]
    return f"{t.hour:02d}:{t.minute:02d}"


def to_time(s):
    if not s:
        return None
    return datetime.strptime(str(s)[:5], "%H:%M").time()
