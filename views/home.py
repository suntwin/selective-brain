import streamlit as st

from sb import data, gamify as g, nav, style
from sb.style import esc

TIPS = [
    "Before you write the answer, read the question's last line again. Does your answer match what it asks?",
    "Ratio change? Draw before and after bar models, then find what stays the same.",
    "Percent of what? Circle the base amount before you multiply.",
    "Indices: if you're not sure, write it out the long way. (x³)² = x³ × x³ = x⁶",
    "Circle shapes: is it a whole circle, a half or a quarter? Decide that before you use a formula.",
    "Stuck for more than 90 seconds? Skip it and come back. Exam pace beats getting stuck.",
    "Units! Change everything to the same unit before you start.",
    "Angles: name the rule you're using, like 'straight line = 180°'.",
]
ENERGY = {1: "😴", 2: "🥱", 3: "🙂", 4: "😄", 5: "🤩"}
MOODS = ["😊 happy", "😌 calm", "😬 nervous", "😤 grumpy", "🤪 silly"]


def render():
    me, kid = data.me(), data.child()
    is_child = me["role"] == "child"
    s = data.stats(kid["id"])
    lvl, stk = s["level"], s["streak"]
    dte = g.days_to_exam(kid.get("exam_date"))
    hour = __import__("datetime").datetime.now(g.TZ).hour
    hello = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

    nxt = f"{lvl['to_next']} XP to Level {lvl['num'] + 1}" if lvl["next"] else "Max level reached 👑"
    style.card(
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;align-items:center">'
        f'<div><h1>{hello}, {esc(kid["display_name"])} {esc(kid.get("avatar", "🦄"))}</h1>'
        f'<div class="sb-sub">Level {lvl["num"]} · {lvl["icon"]} {lvl["name"]} · {s["xp"]} XP</div></div>'
        f'<div style="font-size:52px">{lvl["icon"]}</div></div>'
        f'<div style="margin-top:10px">{style.bar(lvl["pct"])}</div>'
        f'<div class="sb-sub" style="margin-top:6px;font-size:.9rem">{nxt}</div>', "sb-hero")

    due = data.due_cards(kid["id"])
    fire = "🔥" if stk["current"] else "🌱"
    st.markdown(
        '<div class="sb-stat">'
        f'<div class="box"><div class="big">{fire} {stk["current"]}</div><div class="lbl">day streak · best {stk["best"]}</div></div>'
        f'<div class="box"><div class="big">📅 {dte}</div><div class="lbl">days to exam day</div></div>'
        f'<div class="box"><div class="big">🎯 {len(s["answers"])}</div><div class="lbl">questions answered</div></div>'
        f'<div class="box"><div class="big">📒 {len(due)}</div><div class="lbl">recall cards due</div></div>'
        '</div>', unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([1.35, 1])
    with left:
        ci = data.checkin_today(kid["id"])
        if is_child and not ci:
            _checkin_form()
        else:
            _today_plan(ci, is_child, stk)
    with right:
        tip = TIPS[g.today().toordinal() % len(TIPS)]
        style.card(f'<div class="sb-title" style="font-size:1.15rem">💡 Today\'s Brain Tip</div>'
                   f'<div style="margin-top:6px;font-weight:700">{esc(tip)}</div>', "sb-card sb-tip")
        if due:
            style.card(f'<div class="sb-title" style="font-size:1.15rem">🧠 Recall time</div>'
                       f'<div class="sb-small">{len(due)} card(s) want to say hi. Each one you remember gives you '
                       f'+{g.XP["recall_got"]} XP.</div>')
            if is_child and st.button("Open my notebook 📒", use_container_width=True):
                nav.go("notebook")

    st.markdown("#### 🗺️ My Topic Map")
    tm = g.topic_map(s["answers"])
    chips = "".join(
        f'<span class="sb-topic {t["color"]}">{esc(t["label"])} '
        f'{"" if t["acc"] is None else "· " + str(round(t["acc"] * 100)) + "%"}</span>' for t in tm)
    style.card(chips + '<div class="sb-small" style="margin-top:6px">🟢 80%+ · 🟡 60–79% · 🔴 under 60% · '
               'based on your last 20 answers per topic</div>')

    got = data.badges(kid["id"])
    if got:
        st.markdown("#### 🏆 Latest badges")
        recent = sorted(got.values(), key=lambda b: str(b.get("earned_at")), reverse=True)[:6]
        st.markdown("".join(
            f'<div class="sb-badge"><div class="ic">{g.BADGES[b["badge_key"]][0]}</div>{esc(g.BADGES[b["badge_key"]][1])}</div>'
            for b in recent if b["badge_key"] in g.BADGES), unsafe_allow_html=True)


def _checkin_form():
    style.card('<div class="sb-title" style="font-size:1.35rem">☀️ 1-minute check-in</div>'
               '<div class="sb-small">How are you today? This decides how big today\'s session is.</div>')
    with st.container(border=False):
        energy = st.pills("Energy", options=list(ENERGY.keys()), format_func=lambda k: f"{ENERGY[k]} {k}",
                          default=3, key="ci_energy")
        mood = st.pills("Mood", options=MOODS, default=MOODS[0], key="ci_mood")
        minutes = st.segmented_control("Time I have", options=[10, 20, 30, 45, 60],
                                       format_func=lambda m: f"{m} min", default=45, key="ci_min")
        sug = g.suggest_size(energy or 3, minutes or 30)
        sizes = list(g.SIZES.keys())
        size = st.segmented_control("Session size", options=sizes, default=sug, key="ci_size",
                                    format_func=lambda k: f'{g.SIZES[k]["emoji"]} {g.SIZES[k]["label"]}')
        st.caption(f"Suggested: **{g.SIZES[sug]['emoji']} {g.SIZES[sug]['label']}** · {g.SIZES[size or sug]['blurb']}")
        if st.button("Save check-in ✨", use_container_width=True):
            data.save_checkin(energy or 3, mood or "", minutes or 30, size or sug)
            st.rerun()


def _today_plan(ci, is_child, stk):
    drills = data.drills()
    kid = data.child()
    done_ids = {a["drill_id"] for a in data.attempts(kid["id"]) if a.get("finished_at")}
    todo = [d for d in drills if d["id"] not in done_ids]
    size = (ci or {}).get("session_size")
    head = (f'{g.SIZES[size]["emoji"]} Today: <b>{g.SIZES[size]["label"]}</b> session'
            if size else "No check-in yet today")
    if stk["done_today"]:
        style.card(f'<div class="sb-title" style="font-size:1.3rem">🎉 Drill done today!</div>'
                   f'<div class="sb-small">{head}. Your streak is safe. Extra drills still earn XP.</div>')
    elif size == "Rest":
        style.card('<div class="sb-title" style="font-size:1.3rem">🛌 Rest day</div>'
                   '<div class="sb-small">Rest days keep your streak safe (one each week). '
                   'A few recall cards would be lovely, but they\'re optional 💜</div>')
    else:
        style.card(f'<div class="sb-title" style="font-size:1.3rem">🎯 Today\'s plan</div>'
                   f'<div class="sb-small">{head}</div>')
    if todo:
        d = sorted(todo, key=lambda x: x["drill_date"])[0]   # oldest unfinished first
        focus = "".join(style.pill(f, "pink") for f in (d.get("focus") or [])[:5])
        sz = size if size in ("Full", "Normal", "Light") else "Light"
        sel = data.pick_questions(d, sz) if size else [q["id"] for q in d["questions"]]
        nq = len(sel)
        mins = round(data.session_seconds(d, sel) / 60)
        nw = sum(1 for q in d["questions"] if q.get("type") == "word" and q["id"] in sel)
        extra = f" · 📝 {nw} word problem{'s' if nw != 1 else ''}" if nw else ""
        style.card(f'<div class="sb-title" style="font-size:1.2rem">{esc(d["title"])}</div>'
                   f'<div class="sb-small">{nq} questions · ⏳ {mins} min at exam pace{extra}</div>'
                   f'<div style="margin-top:6px">{focus}</div>')
        if is_child and st.button("Start my drill 🚀", use_container_width=True, disabled=size is None):
            st.session_state.drill_pick = d["id"]
            nav.go("drill")
        if is_child and size is None:
            st.caption("Do your check-in first ☝️")
    else:
        style.card('<div class="sb-small">No new drills right now. Papa is making the next one 🪄</div>')
