import time
from datetime import datetime, timezone
from fractions import Fraction

import streamlit as st

from sb import data, gamify as g, nav, style, timer
from sb.style import esc

LETTERS = "ABCDE"
REASONS = {
    "concept": "🧩 Didn't know how",
    "careless": "🙈 Careless slip",
    "misread": "👀 Misread the question",
    "time": "⏰ Ran out of time",
}
FIX_HINTS = {
    "concept": "e.g. The rule is …  / Next time I will draw …",
    "careless": "e.g. I wrote 24 instead of 42 — check the last line again",
    "misread": "e.g. It asked for Ben's share, not Amy's — underline the question",
    "time": "e.g. Skip after 90 seconds and come back later",
}


# ---------------------------------------------------------------- helpers
def _qmap(d):
    return {q["id"]: q for q in d["questions"]}


def _parse_num(s):
    s = str(s).strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    if not s:
        return None
    try:
        if "/" in s:
            return float(Fraction(s))
        return float(s)
    except (ValueError, ZeroDivisionError):
        return None


def _is_correct(q, chosen):
    if q.get("type", "mcq") == "numeric":
        v = _parse_num(chosen)
        return v is not None and abs(v - float(q["answer"])) <= float(q.get("tolerance", 0.001))
    return int(chosen) == int(q["answer"])


def _answer_text(q, chosen):
    if chosen in (None, "", "None"):
        return "—"
    if q.get("type", "mcq") == "numeric":
        return f'{chosen} {q.get("unit", "")}'.strip()
    try:
        return q["options"][int(chosen)]
    except (ValueError, IndexError):
        return str(chosen)


def _correct_text(q):
    if q.get("type", "mcq") == "numeric":
        return f'{q["answer"]} {q.get("unit", "")}'.strip()
    return q["options"][int(q["answer"])]


def _start_ms(attempt):
    dt = datetime.fromisoformat(str(attempt["started_at"]).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _new_run(d, attempt, answered=None):
    answered = answered or {}
    order = [q for q in attempt.get("question_ids") or [q["id"] for q in d["questions"]] if q not in answered]
    st.session_state.run = {
        "attempt": attempt, "drill_id": d["id"], "order": order, "served": list(attempt.get("question_ids") or []),
        "answered": answered, "q_start": time.time(), "feedback": None, "skipped": [],
        "overtime_ok": False, "phase": "play", "xp": 0, "burst": False}


def _xp(run, amount, reason):
    data.add_xp(amount, reason)
    run["xp"] += amount


# ---------------------------------------------------------------- picker
def _picker():
    me = data.me()
    st.markdown("## 🎯 Drills")
    ci = data.checkin_today()
    if not ci:
        style.card('<b>☀️ Check in first</b><div class="sb-small">Your check-in decides the size of today\'s drill.</div>')
        if st.button("Go to check-in 🏠"):
            nav.go("home")
        return
    size = ci["session_size"]
    if size == "Rest":
        style.card('🛌 <b>It\'s a rest day.</b> <span class="sb-small">If you still want to practise, '
                   'I\'ll make it a Light one.</span>')
        size = "Light"
    att = data.attempts()
    best = {}
    for a in att:
        if a.get("finished_at"):
            pct = (a.get("score") or 0) / max(1, a.get("total") or 1)
            best[a["drill_id"]] = max(best.get(a["drill_id"], 0), pct)
    drills = data.drills()
    if not drills:
        style.card("No drills yet. Papa is cooking one up 🪄")
        return
    pick = st.session_state.pop("drill_pick", None)
    for d in sorted(drills, key=lambda x: (x["id"] in best, x["drill_date"])):
        n = len(d["questions"])
        n_sz = len(data.pick_questions(d, size))
        mins = round(n_sz * d.get("pace_seconds", 90) / 60)
        done = d["id"] in best
        badge = (style.pill(f"Best {round(best[d['id']] * 100)}% " + style.stars(_stars(best[d['id']])), "gold")
                 if done else style.pill("NEW ✨", "pink"))
        focus = "".join(style.pill(f, "lav") for f in (d.get("focus") or [])[:6])
        style.card(f'<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">'
                   f'<div class="sb-title" style="font-size:1.25rem">{esc(d["title"])}</div><div>{badge}</div></div>'
                   f'<div class="sb-small">{d["drill_date"]} · {g.SIZES[size]["emoji"]} {size}: {n_sz} of {n} questions · '
                   f'⏳ {mins} min at exam pace</div><div style="margin-top:6px">{focus}</div>')
        open_a = data.open_attempt(d["id"])
        c1, c2 = st.columns([1, 3])
        label = "Resume ▶️" if open_a else ("Practise again 🔁" if done else "Start 🚀")
        if me["role"] != "child":
            continue
        if c1.button(label, key=f"go_{d['id']}", use_container_width=True) or (pick == d["id"] and not done):
            if open_a:
                answered = {r["question_id"]: r for r in data.attempt_answers(open_a["id"])}
                _new_run(d, open_a, answered)
            else:
                _new_run(d, data.start_attempt(d, size))
            st.rerun()
    if me["role"] != "child":
        st.info("Parents see drills here; attempts are recorded only from Siyonah's login.")


def _stars(pct):
    return 3 if pct >= 0.9 else 2 if pct >= 0.7 else 1 if pct >= 0.5 else 0


# ---------------------------------------------------------------- play
def _play(run, d):
    qm = _qmap(d)
    attempt = run["attempt"]
    total = len(run["served"])
    done = len(run["answered"])
    limit = int(attempt.get("time_limit_sec") or total * 90)
    elapsed = data.seconds_since(attempt["started_at"])

    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown(f"### 🎯 {esc(d['title'])}")
    with top_r:
        if st.button("Pause ⏸️", type="tertiary", use_container_width=True):
            st.session_state.pop("run", None)
            st.toast("Paused. Your answers are saved. The clock keeps running, like in the real exam ⏳")
            st.rerun()
    timer.countdown(_start_ms(attempt), limit, done, total, int(d.get("pace_seconds", 90)))

    @st.fragment(run_every=5)
    def _watch_clock():
        # bring up the "Time's up" screen by itself when the clock runs out
        if (not run["overtime_ok"] and not run.get("timeup_shown") and run["order"]
                and data.seconds_since(attempt["started_at"]) > limit):
            run["timeup_shown"] = True
            st.rerun()

    _watch_clock()

    # time's up gate
    if elapsed > limit and not run["overtime_ok"] and run["order"] and not run["feedback"]:
        style.card('<div class="sb-title" style="font-size:1.4rem">⏰ Time\'s up!</div>'
                   f'<div class="sb-small">In the real exam, this is where pens go down. You answered '
                   f'{done} of {total}. You can finish now, or keep going in overtime. '
                   f'Overtime answers still count, but they don\'t earn speed stars.</div>')
        c1, c2 = st.columns(2)
        if c1.button("Finish now 🏁", use_container_width=True):
            _finish(run, d)
            st.rerun()
        if c2.button("Keep going 🌙", use_container_width=True, type="tertiary"):
            run["overtime_ok"] = True
            st.rerun()
        return

    fb = run["feedback"]
    if fb:
        q = qm[fb["qid"]]
        if fb["correct"]:
            st.markdown(f'<div class="sb-ok">✅ Yes! +{fb["xp"]} XP {"⚡ speedy!" if fb["speedy"] else ""}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="sb-bad">💜 Not this time. You\'ll fix it in review and it goes into your notebook.</div>',
                        unsafe_allow_html=True)
        st.write("")
        last = not run["order"]
        if st.button("See my results 🌈" if last else "Next question ➡️", use_container_width=True, key="next"):
            run["feedback"] = None
            run["q_start"] = time.time()
            if last:
                _finish(run, d)
            st.rerun()
        return

    if not run["order"]:
        _finish(run, d)
        st.rerun()
        return

    qid = run["order"][0]
    q = qm[qid]
    diff = "⭐" * int(q.get("difficulty", 2))
    skipped = qid in run["skipped"]
    style.card(
        f'<div>{style.pill(g.TOPIC_LABEL.get(q.get("topic"), q.get("topic", "")), "aqua")}'
        f'{style.pill(diff, "gold")}{style.pill("came back to this one", "pink") if skipped else ""}</div>'
        f'<div class="sb-q" style="margin-top:8px">{esc(q["stem"])}</div>')
    if q.get("image"):
        st.image(q["image"], use_container_width=False, width=420)

    chosen = None
    if q.get("type", "mcq") == "numeric":
        with st.form(f"num_{qid}", clear_on_submit=True):
            val = st.text_input(f"Your answer {('(' + q['unit'] + ')') if q.get('unit') else ''}", key=f"in_{qid}")
            if st.form_submit_button("Check ✨", use_container_width=True) and val.strip():
                chosen = val.strip()
    else:
        opts = data.shuffled_options(q, attempt["id"])
        cols = st.container(key=f"opts_{qid}").columns(2)
        for i, (orig_idx, text) in enumerate(opts):
            if cols[i % 2].button(style.md(f"{LETTERS[i]}   {text}"), key=f"opt_{qid}_{orig_idx}", use_container_width=True,
                                  type="tertiary"):
                chosen = orig_idx

    c1, _ = st.columns([1, 3])
    if len(run["order"]) > 1 and not skipped:
        if c1.button("Skip for now ⏭️", type="tertiary", key=f"skip_{qid}"):
            run[f"pre_{qid}"] = int(time.time() - run["q_start"])
            run["order"].append(run["order"].pop(0))
            run["skipped"].append(qid)
            run["q_start"] = time.time()
            st.rerun()

    if chosen is not None:
        secs = int(time.time() - run["q_start"])
        if skipped:
            secs += int(run.get(f"pre_{qid}", 0))
        correct = _is_correct(q, chosen)
        data.record_answer(attempt, q, chosen, correct, secs)
        run["answered"][qid] = {"question_id": qid, "chosen": str(chosen), "correct": correct, "seconds": secs}
        run["order"].pop(0)
        in_time = data.seconds_since(attempt["started_at"]) <= limit
        gained = g.XP["attempt"]
        speedy = False
        if correct:
            gained += g.XP["correct"]
            if secs <= int(d.get("pace_seconds", 90)) and in_time:
                gained += g.XP["speedy"]
                speedy = True
        _xp(run, gained, "Correct answer" if correct else "Gave it a go")
        run["feedback"] = {"qid": qid, "correct": correct, "xp": gained, "speedy": speedy}
        st.session_state.pop("xp_toasts", None)  # feedback banner already shows XP
        st.rerun()


def _finish(run, d):
    attempt = run["attempt"]
    if attempt.get("status") != "in_progress":
        run["phase"] = "review"
        return
    total = len(run["served"])
    score = sum(1 for a in run["answered"].values() if a["correct"])
    elapsed = data.seconds_since(attempt["started_at"])
    limit = int(attempt.get("time_limit_sec") or total * 90)
    all_done = len(run["answered"]) >= total
    beat = all_done and elapsed <= limit and score / max(1, total) >= 0.7
    if me_child():
        _xp(run, g.XP["drill_done"], "Finished a drill")
        if total and score == total:
            _xp(run, g.XP["perfect"], "Perfect drill!")
    data.finish_attempt(attempt, score, total, run["xp"], beat, elapsed > limit)
    run["phase"] = "review"
    run["burst"] = True
    run["elapsed"] = elapsed
    if me_child():
        new = data.award_badges(data.stats())
        run["new_badges"] = new


def me_child():
    return data.me()["role"] == "child"


# ---------------------------------------------------------------- review
def _review(run, d):
    qm = _qmap(d)
    attempt = run["attempt"]
    total = len(run["served"])
    score = sum(1 for a in run["answered"].values() if a["correct"])
    pct = score / max(1, total)
    n_stars = _stars(pct)
    elapsed = int(run.get("elapsed") or data.seconds_since(attempt["started_at"]))
    limit = int(attempt.get("time_limit_sec") or total * 90)
    if run.get("burst"):
        style.sparkle_burst()
        run["burst"] = False
    msg = ("Superstar!! 🌟" if n_stars == 3 else "Brilliant work! 💖" if n_stars == 2
           else "Good effort, and every mistake is a clue 🔍" if n_stars == 1 else "Tough one! Let's turn these into notebook cards 💪")
    style.card(
        f'<div style="text-align:center"><div style="font-size:46px">{style.stars(n_stars)}</div>'
        f'<h1>{score} / {total}</h1><div class="sb-sub">{msg}</div>'
        f'<div class="sb-sub" style="margin-top:6px">⏱️ {elapsed // 60}m {elapsed % 60:02d}s of {limit // 60}m · '
        f'✨ +{run["xp"]} XP so far</div></div>', "sb-hero")
    for k in run.get("new_badges") or []:
        if k in g.BADGES:
            ic, name, desc = g.BADGES[k]
            st.markdown(f'<div class="sb-badge new"><div class="ic">{ic}</div>{esc(name)}</div> '
                        f'<b>New badge!</b> {esc(desc)}', unsafe_allow_html=True)

    wrong = [qid for qid in run["served"] if not run["answered"].get(qid, {}).get("correct")]
    fixed = set(run.setdefault("fixed", []))
    if not wrong:
        style.card("🎉 Nothing to fix. Every answer was right!")
    else:
        st.markdown(f"### 🛠️ Fix-it time ({len(fixed & set(wrong))}/{len(wrong)} fixed)")
        st.caption(f"For each one: why did it happen, and what will you do next time? Each fix earns +{g.XP['mistake_fixed']} XP "
                   "and saves a card to your notebook.")
    for qid in wrong:
        q = qm[qid]
        a = run["answered"].get(qid)
        is_fixed = qid in fixed
        title = style.md(("✅ " if is_fixed else "🔧 ") + (q.get("short") or q["stem"][:70]))
        with st.expander(title, expanded=not is_fixed and qid == next((w for w in wrong if w not in fixed), None)):
            st.markdown(f'<div class="sb-q" style="font-size:1.05rem">{esc(q["stem"])}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="sb-bad">Your answer: {esc(_answer_text(q, a["chosen"]) if a else "not answered")}</div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="sb-ok">Correct: {esc(_correct_text(q))}</div>', unsafe_allow_html=True)
            if q.get("explanation"):
                st.markdown(f"**How it works:** {style.md(q['explanation'])}")
            if q.get("technique"):
                st.markdown(f'<div class="sb-tip">💡 <b>Technique:</b> {esc(q["technique"])}</div>', unsafe_allow_html=True)
            if q.get("trap"):
                st.caption(f"🪤 Trap in this question: {style.md(q['trap'])}")
            if is_fixed or not me_child():
                continue
            reason = st.pills("Why did it happen?", options=list(REASONS.keys()),
                              format_func=lambda k: REASONS[k], key=f"r_{qid}",
                              default="time" if not a else None)
            note = st.text_input("My fix, in my words", key=f"f_{qid}",
                                 placeholder=FIX_HINTS.get(reason or "concept"))
            if st.button("Save to my notebook ✨", key=f"save_{qid}", disabled=not (reason and note.strip())):
                if not a:
                    data.record_answer(attempt, q, "", False, 0)
                data.tag_mistake(attempt, q, _answer_text(q, a["chosen"]) if a else "", reason, note.strip(),
                                 q.get("technique", ""))
                _xp(run, g.XP["mistake_fixed"], "Fixed a mistake")
                run["fixed"].append(qid)
                if set(wrong) <= set(run["fixed"]):
                    _xp(run, g.XP["all_fixed"], "Fixed every mistake!")
                    data.store().update("attempts", {"id": attempt["id"]}, {"status": "reviewed", "xp_earned": run["xp"]})
                    run["new_badges"] = data.award_badges(data.stats())
                    run["burst"] = True
                st.rerun()
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Back home 🏠", use_container_width=True):
        data.store().update("attempts", {"id": attempt["id"]}, {"xp_earned": run["xp"]})
        st.session_state.pop("run", None)
        nav.go("home")
    if c2.button("My notebook 📒", use_container_width=True, type="tertiary"):
        st.session_state.pop("run", None)
        nav.go("notebook")


# ---------------------------------------------------------------- entry
def render():
    run = st.session_state.get("run")
    if not run:
        _picker()
        return
    d = data.drill(run["drill_id"])
    if not d:
        st.session_state.pop("run", None)
        st.rerun()
    if run["phase"] == "play":
        _play(run, d)
    else:
        _review(run, d)
