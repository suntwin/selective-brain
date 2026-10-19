import contextlib
import json
import time
from datetime import datetime, timezone

import streamlit as st

from sb import answers as ans, data, gamify as g, nav, style, timer
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


def _is_correct(q, chosen):
    return ans.is_correct(q, chosen)


def _answer_text(q, chosen):
    return ans.answer_text(q, chosen)


def _correct_text(q):
    return ans.correct_text(q)


def _start_ms(attempt):
    dt = datetime.fromisoformat(str(attempt["started_at"]).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _new_run(d, attempt, answered=None):
    answered = answered or {}
    served = list(attempt.get("question_ids") or [q["id"] for q in d["questions"]])
    answered = {k: v for k, v in answered.items() if v.get("chosen") not in (None, "", "None")}
    first_blank = next((i for i, q in enumerate(served) if q not in answered), 0)
    st.session_state.run = {
        "attempt": attempt, "drill_id": d["id"], "served": served, "answered": answered,
        "pos": first_blank, "view": "question", "flags": [], "spent": {k: float(v.get("seconds") or 0)
                                                                       for k, v in answered.items()},
        "view_start": time.time(), "overtime_ok": False, "phase": "play", "xp": 0, "burst": False}


def _xp(run, amount, reason):
    data.add_xp(amount, reason)
    run["xp"] += amount


# ---------------------------------------------------------------- reading & writing helpers
def _passage_html(p, max_h="62vh"):
    paras = "".join(f"<p style='margin:0 0 .7rem 0'>{esc(x)}</p>" for x in str(p.get("text", "")).split("\n\n") if x.strip())
    src = f'<div class="sb-small" style="margin-top:6px">{esc(p["source"])}</div>' if p.get("source") else ""
    kind = style.pill(p["kind"], "lav") if p.get("kind") else ""
    return (f'<div class="sb-card" style="max-height:{max_h};overflow-y:auto">'
            f'<div>{style.pill("📖 Read this first", "pink")}{kind}</div>'
            f'<div class="sb-title" style="font-size:1.15rem;margin:.4rem 0">{esc(p.get("title", ""))}</div>'
            f'<div style="font-size:1.04rem;line-height:1.7">{paras}</div>{src}</div>')


def _passage_card(p):
    st.markdown(_passage_html(p), unsafe_allow_html=True)


def _h(s):
    """HTML-escape and hide $ so markdown doesn't read money as maths."""
    return esc(s).replace("$", "&#36;")


def _writing_input(q, d, prev=None, k=None):
    k = k or q["id"]
    g = ans.writing_given(prev) if prev not in (None, "", "None") else {"text": "", "checks": []}
    mins = ans.q_seconds(q, int(d.get("pace_seconds", 90))) // 60
    tips = "".join(f"<li>{esc(t)}</li>" for t in q.get("tips") or [])
    st.markdown(f'{style.pill(f"✍️ Writing task · about {mins} min", "lav")}'
                f'<span class="sb-small">Plan for 3 minutes, write, then 2 minutes to check.</span>'
                + (f'<div class="sb-tip" style="margin-top:6px"><b>Tips</b><ul style="margin:.3rem 0 0 1.1rem">{tips}</ul></div>'
                   if tips else ""), unsafe_allow_html=True)
    with st.form(f"write_{k}"):
        text = st.text_area("Your writing", value=g["text"], height=380, key=f"wr_{k}",
                            placeholder="Start writing here. Paragraphs: leave an empty line between them.")
        checks = []
        if q.get("checklist"):
            st.markdown("**Before you hand it in, tick what you did:**")
            for i, item in enumerate(q["checklist"]):
                if st.checkbox(item, value=item in g["checks"], key=f"ck_{k}_{i}"):
                    checks.append(item)
        if st.form_submit_button("Save my writing 💾", use_container_width=True):
            if len(text.split()) < 20:
                st.warning("Write a bit more first (at least a few sentences).")
            else:
                return json.dumps({"text": text.strip(), "checks": checks})
    return None


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
    subjects = [s for s in g.SUBJECTS if any(d.get("subject", "Maths") == s for d in drills)]
    if len(subjects) > 1:
        want = st.segmented_control("Subject", ["All"] + subjects, default="All", key="drill_subject",
                                    format_func=lambda s: s if s == "All" else f"{g.SUBJECTS[s]} {s}") or "All"
        if want != "All":
            drills = [d for d in drills if d.get("subject", "Maths") == want or d["id"] == pick]
    for d in sorted(drills, key=lambda x: (x["id"] in best, x["drill_date"])):
        n = len(d["questions"])
        sel = data.pick_questions(d, size)
        n_sz = len(sel)
        mins = round(data.session_seconds(d, sel) / 60)
        n_word = sum(1 for q in d["questions"] if q.get("type") == "word" and q["id"] in sel)
        n_write = sum(1 for q in d["questions"] if q.get("type") == "writing" and q["id"] in sel)
        n_pass = len({q.get("passage") for q in d["questions"] if q.get("passage") and q["id"] in sel})
        subj = d.get("subject", "Maths")
        extra = (f" · 📖 {n_pass} passage{'s' if n_pass != 1 else ''}" if n_pass else "") + \
                (f" · ✍️ {n_write} writing task{'s' if n_write != 1 else ''}" if n_write else "")
        done = d["id"] in best
        badge = (style.pill(f"Best {round(best[d['id']] * 100)}% " + style.stars(_stars(best[d['id']])), "gold")
                 if done else style.pill("NEW ✨", "pink"))
        focus = "".join(style.pill(f, "lav") for f in (d.get("focus") or [])[:6])
        style.card(f'<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">'
                   f'<div class="sb-title" style="font-size:1.25rem">{esc(d["title"])}</div><div>'
                   f'{style.pill(g.SUBJECTS.get(subj, "") + " " + subj, "aqua")}{badge}</div></div>'
                   f'<div class="sb-small">{d["drill_date"]} · {g.SIZES[size]["emoji"]} {size}: {n_sz} of {n} questions · '
                   f'⏳ {mins} min at exam pace{f" · 📝 {n_word} word problem" + ("s" if n_word != 1 else "") if n_word else ""}'
                   f'{extra}</div>'
                   f'<div style="margin-top:6px">{focus}</div>')
        open_a = data.open_attempt(d["id"])
        c1, c2 = st.columns([1, 3])
        label = "Resume ▶️" if open_a else ("Practise again 🔁" if done else "Start 🚀")
        if done:
            last = max((a for a in att if a["drill_id"] == d["id"] and a.get("finished_at")),
                       key=lambda a: str(a["finished_at"]), default=None)
            if last and c2.button("Look back at my answers 📚" if me["role"] == "child" else "See her answers 📚",
                                  key=f"past_{d['id']}", type="tertiary"):
                st.session_state.past_attempt = last["id"]
                nav.go("past")
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


# ---------------------------------------------------------------- play (exam mode)
# Exam-style: no right/wrong while she works. She can move back and forth, change any answer, and flag
# questions 🚩 to check again. Marking (and XP for answers) happens only when she submits.
STATUS_ICON = {"answered": "✅", "flagged": "🚩", "blank": "⭕"}


def _status(run, qid):
    if qid in run["flags"]:
        return "flagged"
    return "answered" if qid in run["answered"] else "blank"


def _bank_time(run):
    """Add the time spent on the question on screen to that question's total."""
    qid = run["served"][run["pos"]] if run["served"] else None
    if qid is not None:
        run["spent"][qid] = run["spent"].get(qid, 0) + max(0.0, time.time() - run["view_start"])
    run["view_start"] = time.time()


def _goto(run, pos=None, view="question"):
    _bank_time(run)
    if pos is not None:
        run["pos"] = max(0, min(len(run["served"]) - 1, pos))
    run["view"] = view


def _save_answer(run, q, chosen):
    attempt = run["attempt"]
    _bank_time(run)
    secs = int(run["spent"].get(q["id"], 0))
    correct = _is_correct(q, chosen)
    data.record_answer(attempt, q, chosen, correct, secs)          # saved straight away, so nothing is lost
    run["answered"][q["id"]] = {"question_id": q["id"], "chosen": str(chosen), "correct": correct, "seconds": secs}


def _next_pos(run):
    """After saving: the next question she hasn't answered yet (wrapping round), or the check screen."""
    n = len(run["served"])
    for step in range(1, n + 1):
        i = (run["pos"] + step) % n
        if run["served"][i] not in run["answered"]:
            return i
    return None


def _question_map(run, qm):
    served = run["served"]
    box = st.container(key="qmap")
    per_row = 10
    for start in range(0, len(served), per_row):
        cols = box.columns(per_row)
        for j, qid in enumerate(served[start:start + per_row]):
            i = start + j
            icon = "👉" if (i == run["pos"] and run.get("view") != "check") else STATUS_ICON[_status(run, qid)]
            if cols[j].button(f"{icon} {i + 1}", key=f"jump_{i}", use_container_width=True, type="tertiary",
                              help=g.TOPIC_LABEL.get(qm[qid].get("topic"), "")):
                _goto(run, i)
                st.rerun()
    n_ans = sum(1 for q in served if q in run["answered"])
    st.caption(f"✅ answered {n_ans} · 🚩 to check {len(run['flags'])} · ⭕ not answered {len(served) - n_ans}  "
               "— tap a number to jump to that question.")


def _answer_widgets(run, d, q, passage):
    """Draw the answer input for q, pre-filled with her saved answer. Returns a new answer or None."""
    attempt = run["attempt"]
    qid = q["id"]
    prev = run["answered"].get(qid, {}).get("chosen")
    k = f"{attempt['id'][:8]}_{qid}"
    t = q.get("type", "mcq")
    if t == "writing":
        return _writing_input(q, d, prev, k)
    if t == "word":
        mins = ans.q_seconds(q, int(d.get("pace_seconds", 90))) / 60
        n_parts = len(q["parts"])
        st.markdown(style.pill(f"📝 Word problem · {n_parts} parts · ⏳ about {mins:g} min", "lav") +
                    f'<span class="sb-small">Work it out on paper, then type each final answer.</span>',
                    unsafe_allow_html=True)
        given = ans.word_given(prev) if prev else {}
        asks = q.get("asks_for")
        with st.form(f"word_{k}"):
            pick = None
            if asks:
                pick = st.radio(f"🔍 {asks['prompt']}", options=list(range(len(asks["options"]))),
                                format_func=lambda i: asks["options"][i], index=given.get("_asks"), key=f"ask_{k}")
            vals = {}
            for p in q["parts"]:
                unit = f" ({p['unit']})" if p.get("unit") else ""
                vals[p["label"]] = st.text_input(f"({p['label']}) {p.get('prompt', '')}{unit}",
                                                 value=str(given.get(p["label"], "")), key=f"w_{k}_{p['label']}")
            if st.form_submit_button("Save my answers 💾", use_container_width=True):
                if not any(v.strip() for v in vals.values()):
                    st.warning("Type at least one answer first, or tap Next to come back later.")
                else:
                    payload = {kk: v.strip() for kk, v in vals.items()}
                    if asks:
                        payload["_asks"] = pick
                    return json.dumps(payload)
        return None
    if t == "numeric":
        with st.form(f"num_{k}"):
            val = st.text_input(f"Your answer {('(' + q['unit'] + ')') if q.get('unit') else ''}",
                                value=str(prev or ""), key=f"in_{k}")
            if st.form_submit_button("Save my answer 💾", use_container_width=True) and val.strip():
                return val.strip()
        return None
    # mcq: tap an option to choose it; the chosen one stays highlighted and can be changed any time
    try:
        picked = int(prev) if prev not in (None, "", "None") else None
    except (TypeError, ValueError):
        picked = None
    opts = data.shuffled_options(q, attempt["id"])
    cols = st.container(key=f"opts_{qid}").columns(1 if passage else 2)
    for i, (orig_idx, text) in enumerate(opts):
        chosen_now = orig_idx == picked
        label = f"{LETTERS[i]}   {text}" + ("   ✔️" if chosen_now else "")
        if cols[i % len(cols)].button(style.md(label), key=f"opt_{qid}_{orig_idx}", use_container_width=True,
                                      type="secondary" if chosen_now else "tertiary"):
            if not chosen_now:
                return orig_idx
    return None


def _check_screen(run, d, qm):
    served = run["served"]
    flagged = [q for q in served if q in run["flags"]]
    blank = [q for q in served if q not in run["answered"]]
    style.card('<div class="sb-title" style="font-size:1.35rem">🔎 Check before you submit</div>'
               f'<div class="sb-small">✅ {len(served) - len(blank)} answered · 🚩 {len(flagged)} flagged to check · '
               f'⭕ {len(blank)} not answered. Nothing is marked until you press Submit, so you can still change '
               'any answer.</div>')
    opts = {"flagged": f"🚩 Flagged ({len(flagged)})", "blank": f"⭕ Not answered ({len(blank)})",
            "all": f"All ({len(served)})"}
    default = "flagged" if flagged else ("blank" if blank else "all")
    show = st.segmented_control("Show", list(opts), format_func=lambda x: opts[x], default=default,
                                key="check_filter") or default
    rows = {"flagged": flagged, "blank": blank, "all": served}[show]
    if not rows:
        st.caption("Nothing here 🎉")
    for qid in rows:
        i = served.index(qid)
        q = qm[qid]
        a = run["answered"].get(qid)
        stem = q.get("short") or q["stem"]
        stem = stem if len(stem) <= 90 else stem[:88] + "…"
        mine = (_answer_text(q, a["chosen"]) if a else "not answered")
        mine = mine if len(mine) <= 60 else mine[:58] + "…"
        c1, c2 = st.columns([5, 1])
        c1.markdown(f'{STATUS_ICON[_status(run, qid)]} <b>Q{i + 1}</b> · {_h(stem)}'
                    f'<div class="sb-small">Your answer: {_h(mine)}</div>', unsafe_allow_html=True)
        if c2.button("Open ✏️", key=f"open_{qid}", use_container_width=True, type="tertiary"):
            _goto(run, i)
            st.rerun()
    st.write("")
    ok = True
    if blank:
        ok = st.checkbox(f"Submit anyway — {len(blank)} question(s) are not answered and will count as wrong",
                         key="submit_ok")
    c1, c2 = st.columns(2)
    if c1.button("◀ Back to the questions", use_container_width=True, type="tertiary"):
        _goto(run, run["pos"])
        st.rerun()
    if c2.button("Submit my drill ✅", use_container_width=True, disabled=not ok):
        _goto(run, None, "check")
        _finish(run, d)
        st.rerun()


def _play(run, d):
    qm = _qmap(d)
    attempt = run["attempt"]
    served = run["served"]
    total = len(served)
    done = len(run["answered"])
    limit = int(attempt.get("time_limit_sec") or total * 90)
    elapsed = data.seconds_since(attempt["started_at"])

    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown(f"### 🎯 {esc(d['title'])}")
    with top_r:
        if st.button("Pause ⏸️", type="tertiary", use_container_width=True):
            _bank_time(run)
            st.session_state.pop("run", None)
            st.toast("Paused. Your answers are saved. The clock keeps running, like in the real exam ⏳")
            st.rerun()
    timer.countdown(_start_ms(attempt), limit, done, total, max(1, round(limit / max(1, total))))

    @st.fragment(run_every=5)
    def _watch_clock():
        # bring up the "Time's up" screen by itself when the clock runs out
        if (not run["overtime_ok"] and not run.get("timeup_shown")
                and data.seconds_since(attempt["started_at"]) > limit):
            run["timeup_shown"] = True
            st.rerun()

    _watch_clock()

    if elapsed > limit and not run["overtime_ok"]:
        style.card('<div class="sb-title" style="font-size:1.4rem">⏰ Time\'s up!</div>'
                   f'<div class="sb-small">In the real exam, this is where pens go down. You answered '
                   f'{done} of {total}. Submit now, or keep going in overtime. Overtime answers still count, '
                   f'but they don\'t earn speed stars.</div>')
        c1, c2 = st.columns(2)
        if c1.button("Submit now 🏁", use_container_width=True):
            _goto(run, None, "check")
            _finish(run, d)
            st.rerun()
        if c2.button("Keep going 🌙", use_container_width=True, type="tertiary"):
            run["overtime_ok"] = True
            st.rerun()
        return

    _question_map(run, qm)

    if run.get("view") == "check":
        _check_screen(run, d, qm)
        return

    qid = served[run["pos"]]
    q = qm[qid]
    diff = "⭐" * int(q.get("difficulty", 2))
    flagged = qid in run["flags"]
    passage = data.passage_for(d, q)
    if passage:
        p_col, q_col = st.columns([1.15, 1], gap="medium")
        with p_col:
            _passage_card(passage)
        qbox = q_col
    else:
        qbox = contextlib.nullcontext()
    with qbox:
        saved = qid in run["answered"]
        qnum = run["pos"] + 1
        style.card(
            f'<div>{style.pill(f"Question {qnum} of {total}", "lav")}'
            f'{style.pill(g.TOPIC_LABEL.get(q.get("topic"), q.get("topic", "")), "aqua")}{style.pill(diff, "gold")}'
            f'{style.pill("🚩 flagged to check", "pink") if flagged else ""}'
            f'{style.pill("💾 answer saved", "aqua") if saved else ""}</div>'
            f'<div class="sb-q" style="margin-top:8px">{esc(q["stem"])}</div>{style.img(q.get("image"))}')
        chosen = _answer_widgets(run, d, q, passage)

        last = run["pos"] == total - 1
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("◀ Back", use_container_width=True, type="tertiary", disabled=run["pos"] == 0, key="nav_back"):
            _goto(run, run["pos"] - 1)
            st.rerun()
        if c2.button("🚩 Unflag" if flagged else "🚩 Flag to check", use_container_width=True, type="tertiary",
                     key="nav_flag"):
            if flagged:
                run["flags"].remove(qid)
            else:
                run["flags"].append(qid)
            st.rerun()
        if c3.button("Next ▶", use_container_width=True, type="tertiary", disabled=last, key="nav_next"):
            _goto(run, run["pos"] + 1)
            st.rerun()
        if c4.button("Check & submit 🔎", use_container_width=True, type="tertiary", key="nav_check"):
            _goto(run, None, "check")
            st.rerun()

    if chosen is not None:
        _save_answer(run, q, chosen)
        if q.get("type", "mcq") in ("mcq",) and not passage:
            st.toast("Saved 💾")
        nxt = _next_pos(run)
        if nxt is None:
            _goto(run, None, "check")          # everything answered: go to the check screen
        elif q.get("type", "mcq") == "mcq" or q.get("type") == "numeric":
            _goto(run, nxt)                   # quick questions move on by themselves
        st.rerun()


def _answer_xp(run, d):
    """XP for the answers, worked out once at submit (so changing an answer never double-counts)."""
    qm = _qmap(d)
    attempt = run["attempt"]
    limit = int(attempt.get("time_limit_sec") or len(run["served"]) * 90)
    in_time = data.seconds_since(attempt["started_at"]) <= limit
    pace = int(d.get("pace_seconds", 90))
    total = right = writing = 0
    for qid in run["served"]:
        a = run["answered"].get(qid)
        if not a:
            continue
        q = qm[qid]
        chosen, correct = a["chosen"], a["correct"]
        if q.get("type") == "writing":
            writing += g.XP["writing_done"] + g.XP["writing_check"] * len(ans.writing_given(chosen)["checks"])
            continue
        gained = g.XP["attempt"]
        if q.get("type") == "word":
            n_ok = sum(r["ok"] for r in ans.word_results(q, chosen))
            gained += g.XP["word_part"] * n_ok + (g.XP["word_all"] if correct else 0)
            asks = q.get("asks_for")
            if asks and ans.word_given(chosen).get("_asks") == asks["answer"]:
                gained += g.XP["read_right"]
        elif correct:
            gained += g.XP["correct"]
        if correct and in_time and (a.get("seconds") or 0) <= ans.q_seconds(q, pace):
            gained += g.XP["speedy"]
        right += 1 if correct else 0
        total += gained
    if total:
        _xp(run, total, f"Drill answers ({right} right)")
    if writing:
        _xp(run, writing, "Handed in writing")


def _finish(run, d):
    attempt = run["attempt"]
    if attempt.get("status") != "in_progress":
        run["phase"] = "review"
        return
    qm = _qmap(d)
    marked = [qid for qid in run["served"] if ans.is_scored(qm[qid])]
    total = len(marked)
    score = sum(1 for qid in marked if run["answered"].get(qid, {}).get("correct"))
    elapsed = data.seconds_since(attempt["started_at"])
    limit = int(attempt.get("time_limit_sec") or len(run["served"]) * 90)
    all_done = len(run["answered"]) >= len(run["served"])
    beat = bool(total) and all_done and elapsed <= limit and score / total >= 0.7
    if me_child():
        _answer_xp(run, d)
        _xp(run, g.XP["drill_done"], "Finished a drill")
        if total and score == total and all_done:
            _xp(run, g.XP["perfect"], "Perfect drill!")
    data.finish_attempt(attempt, score, total, run["xp"], beat, elapsed > limit)
    run["phase"] = "review"
    run["burst"] = True
    run["elapsed"] = elapsed
    if me_child():
        new = data.award_badges(data.stats())
        run["new_badges"] = new


def _word_table(q, chosen):
    rows = "".join(
        f'<tr><td style="padding:4px 10px">{"✅" if r["ok"] else "❌"} <b>({esc(r["label"])})</b> {esc(r["prompt"])}</td>'
        f'<td style="padding:4px 10px">{esc(r["given"] or "—")}</td>'
        f'<td style="padding:4px 10px;font-weight:800">{esc(r["correct"])}</td></tr>'
        for r in ans.word_results(q, chosen))
    asks = q.get("asks_for")
    extra = ""
    if asks:
        got = ans.word_given(chosen).get("_asks")
        ok = got == asks["answer"]
        extra = (f'<div class="sb-small" style="margin-top:6px">🔍 {esc(asks["prompt"])}: '
                 f'{"✅ you spotted it:" if ok else "❌ it was:"} <b>{esc(asks["options"][asks["answer"]])}</b></div>')
    return (f'<div class="sb-card" style="padding:.6rem .8rem"><table style="width:100%;border-collapse:collapse">'
            f'<tr style="text-align:left;color:#6c5785"><th style="padding:4px 10px">Part</th><th style="padding:4px 10px">You wrote</th>'
            f'<th style="padding:4px 10px">Answer</th></tr>{rows}</table>{extra}</div>')


def me_child():
    return data.me()["role"] == "child"


# ---------------------------------------------------------------- review
def _review(run, d):
    qm = _qmap(d)
    attempt = run["attempt"]
    marked = [qid for qid in run["served"] if ans.is_scored(qm[qid])]
    writing = [qid for qid in run["served"] if not ans.is_scored(qm[qid])]
    total = len(marked)
    score = sum(1 for qid in marked if run["answered"].get(qid, {}).get("correct"))
    pct = score / total if total else 1.0
    n_stars = _stars(pct)
    elapsed = int(run.get("elapsed") or data.seconds_since(attempt["started_at"]))
    limit = int(attempt.get("time_limit_sec") or len(run["served"]) * 90)
    if run.get("burst"):
        style.sparkle_burst()
        run["burst"] = False
    msg = ("Superstar!! 🌟" if n_stars == 3 else "Brilliant work! 💖" if n_stars == 2
           else "Good effort, and every mistake is a clue 🔍" if n_stars == 1 else "Tough one! Let's turn these into notebook cards 💪")
    if not total:
        msg = "Great effort! Your writing is on its way to be marked ✨"
    style.card(
        f'<div style="text-align:center"><div style="font-size:46px">{style.stars(n_stars)}</div>'
        f'<h1>{f"{score} / {total}" if total else "✍️ Writing done!"}</h1><div class="sb-sub">{msg}</div>'
        f'<div class="sb-sub" style="margin-top:6px">⏱️ {elapsed // 60}m {elapsed % 60:02d}s of {limit // 60}m · '
        f'✨ +{run["xp"]} XP so far</div></div>', "sb-hero")
    for k in run.get("new_badges") or []:
        if k in g.BADGES:
            ic, name, desc = g.BADGES[k]
            st.markdown(f'<div class="sb-badge new"><div class="ic">{ic}</div>{esc(name)}</div> '
                        f'<b>New badge!</b> {esc(desc)}', unsafe_allow_html=True)

    if marked:
        with st.expander(f"📋 Every answer ({score}/{total} right)", expanded=False):
            rows = []
            for i, qid in enumerate(run["served"], 1):
                q = qm[qid]
                if not ans.is_scored(q):
                    continue
                a = run["answered"].get(qid)
                mark = "⏭️" if not a else ("✅" if a.get("correct") else "❌")
                mine = _answer_text(q, a["chosen"]) if a else "not answered"
                rows.append(f"<tr><td>{mark} {i}</td><td>{_h(q.get('short') or q['stem'][:60])}</td>"
                            f"<td>{_h(mine)}</td><td>{_h(_correct_text(q))}</td></tr>")
            st.markdown('<table class="sb-table"><tr><th>#</th><th>Question</th><th>Your answer</th><th>Correct</th></tr>'
                        + "".join(rows) + "</table>", unsafe_allow_html=True)
    for qid in writing:
        a = run["answered"].get(qid)
        w = ans.writing_given(a["chosen"]) if a else {"text": "", "checks": [], "words": 0}
        with st.expander(f"✍️ Your writing · {w['words']} words", expanded=False):
            st.markdown(f'<div class="sb-q" style="font-size:1rem">{esc(qm[qid]["stem"])}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sb-card" style="white-space:pre-wrap">{esc(w["text"] or "Not handed in.")}</div>',
                        unsafe_allow_html=True)
            if w["checks"]:
                st.caption("You ticked: " + " · ".join(w["checks"]))
            st.caption("Papa exports it to the vault and Claude marks it with the writing rubric. Your tips come back soon.")
    wrong = [qid for qid in marked if not run["answered"].get(qid, {}).get("correct")]
    fixed = set(run.setdefault("fixed", []))
    if not wrong and marked:
        style.card("🎉 Nothing to fix. Every answer was right!")
    elif wrong:
        st.markdown(f"### 🛠️ Fix-it time ({len(fixed & set(wrong))}/{len(wrong)} fixed)")
        st.caption(f"For each one: why did it happen, and what will you do next time? Each fix earns +{g.XP['mistake_fixed']} XP "
                   "and saves a card to your notebook.")
    for qid in wrong:
        q = qm[qid]
        a = run["answered"].get(qid)
        is_fixed = qid in fixed
        title = style.md(("✅ " if is_fixed else "🔧 ") + (q.get("short") or q["stem"][:70]))
        with st.expander(title, expanded=not is_fixed and qid == next((w for w in wrong if w not in fixed), None)):
            p = data.passage_for(d, q)
            if p:
                with st.popover(f"📖 Re-read: {p.get('title', 'the passage')}", use_container_width=True):
                    st.markdown(_passage_html(p, "70vh"), unsafe_allow_html=True)
            st.markdown(f'<div class="sb-q" style="font-size:1.05rem">{esc(q["stem"])}</div>{style.img(q.get("image"), 380)}',
                        unsafe_allow_html=True)
            if q.get("type") == "word":
                st.markdown(_word_table(q, a["chosen"] if a else None), unsafe_allow_html=True)
                if q.get("solution"):
                    st.markdown("**Worked solution**")
                    st.markdown("\n".join(f"{i}. {style.md(step)}" for i, step in enumerate(q["solution"], 1)))
            else:
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
                data.tag_mistake(attempt, data.with_passage(d, q), _answer_text(q, a["chosen"]) if a else "", reason, note.strip(),
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
    st.caption("📚 You can open this drill again any time in **Past drills**: every question, your answer and "
               "the working. Tap 🗣️ there on anything you want to talk about with Papa.")
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
