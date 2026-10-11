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
    order = [q for q in attempt.get("question_ids") or [q["id"] for q in d["questions"]] if q not in answered]
    st.session_state.run = {
        "attempt": attempt, "drill_id": d["id"], "order": order, "served": list(attempt.get("question_ids") or []),
        "answered": answered, "q_start": time.time(), "feedback": None, "skipped": [],
        "overtime_ok": False, "phase": "play", "xp": 0, "burst": False}


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


def _writing_input(q, d):
    mins = ans.q_seconds(q, int(d.get("pace_seconds", 90))) // 60
    tips = "".join(f"<li>{esc(t)}</li>" for t in q.get("tips") or [])
    st.markdown(f'{style.pill(f"✍️ Writing task · about {mins} min", "lav")}'
                f'<span class="sb-small">Plan for 3 minutes, write, then 2 minutes to check.</span>'
                + (f'<div class="sb-tip" style="margin-top:6px"><b>Tips</b><ul style="margin:.3rem 0 0 1.1rem">{tips}</ul></div>'
                   if tips else ""), unsafe_allow_html=True)
    with st.form(f"write_{q['id']}"):
        text = st.text_area("Your writing", height=380, key=f"wr_{q['id']}",
                            placeholder="Start writing here. Paragraphs: leave an empty line between them.")
        checks = []
        if q.get("checklist"):
            st.markdown("**Before you hand it in, tick what you did:**")
            for i, item in enumerate(q["checklist"]):
                if st.checkbox(item, key=f"ck_{q['id']}_{i}"):
                    checks.append(item)
        if st.form_submit_button("Hand in my writing ✨", use_container_width=True):
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
    timer.countdown(_start_ms(attempt), limit, done, total, max(1, round(limit / max(1, total))))

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
        if q.get("type") == "writing":
            w = ans.writing_given(fb["chosen"])
            st.markdown(f'<div class="sb-ok">✍️ Handed in! {w["words"]} words. +{fb["xp"]} XP. '
                        f'It goes to Papa and Claude to mark, and you\'ll get 2–3 tips back.</div>',
                        unsafe_allow_html=True)
        elif q.get("type") == "word":
            results = ans.word_results(q, fb["chosen"])
            n_ok = sum(r["ok"] for r in results)
            rows = "".join(f'<div>{"✅" if r["ok"] else "❌"} ({esc(r["label"])}) you wrote: <b>{esc(r["given"] or "—")}</b></div>'
                           for r in results)
            head = ("🌟 All parts right!" if fb["correct"]
                    else f"💜 {n_ok} of {len(results)} parts right. The full working is waiting for you in review.")
            speedy = " ⚡ speedy!" if fb["speedy"] else ""
            css = "sb-ok" if fb["correct"] else "sb-bad"
            st.markdown(f'<div class="{css}">{head} +{fb["xp"]} XP{speedy}'
                        f'<div style="margin-top:6px;font-weight:700">{rows}</div></div>', unsafe_allow_html=True)
        elif fb["correct"]:
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
    passage = data.passage_for(d, q)
    if passage:
        p_col, q_col = st.columns([1.15, 1], gap="medium")
        with p_col:
            _passage_card(passage)
        qbox = q_col
    else:
        qbox = contextlib.nullcontext()
    with qbox:
        style.card(
            f'<div>{style.pill(g.TOPIC_LABEL.get(q.get("topic"), q.get("topic", "")), "aqua")}'
            f'{style.pill(diff, "gold")}{style.pill("came back to this one", "pink") if skipped else ""}</div>'
            f'<div class="sb-q" style="margin-top:8px">{esc(q["stem"])}</div>{style.img(q.get("image"))}')

        chosen = None
        if q.get("type") == "writing":
            chosen = _writing_input(q, d)
        elif q.get("type") == "word":
            mins = ans.q_seconds(q, int(d.get("pace_seconds", 90))) / 60
            n_parts = len(q["parts"])
            tag = style.pill(f"📝 Word problem · {n_parts} parts · ⏳ about {mins:g} min", "lav")
            st.markdown(f'{tag}'
                        f'<span class="sb-small">Work it out on paper, then type each final answer.</span>',
                        unsafe_allow_html=True)
            asks = q.get("asks_for")
            with st.form(f"word_{qid}"):
                pick = None
                if asks:
                    pick = st.radio(f"🔍 {asks['prompt']}", options=list(range(len(asks["options"]))),
                                    format_func=lambda i: asks["options"][i], index=None, key=f"ask_{qid}")
                vals = {}
                for p in q["parts"]:
                    unit = f" ({p['unit']})" if p.get("unit") else ""
                    vals[p["label"]] = st.text_input(f"({p['label']}) {p.get('prompt', '')}{unit}", key=f"w_{qid}_{p['label']}")
                if st.form_submit_button("Check my answers ✨", use_container_width=True):
                    if not any(v.strip() for v in vals.values()):
                        st.warning("Type at least one answer first, or use Skip.")
                    else:
                        payload = {k: v.strip() for k, v in vals.items()}
                        if asks:
                            payload["_asks"] = pick
                        chosen = json.dumps(payload)
        elif q.get("type", "mcq") == "numeric":
            with st.form(f"num_{qid}", clear_on_submit=True):
                val = st.text_input(f"Your answer {('(' + q['unit'] + ')') if q.get('unit') else ''}", key=f"in_{qid}")
                if st.form_submit_button("Check ✨", use_container_width=True) and val.strip():
                    chosen = val.strip()
        else:
            opts = data.shuffled_options(q, attempt["id"])
            cols = st.container(key=f"opts_{qid}").columns(1 if passage else 2)
            for i, (orig_idx, text) in enumerate(opts):
                if cols[i % len(cols)].button(style.md(f"{LETTERS[i]}   {text}"), key=f"opt_{qid}_{orig_idx}", use_container_width=True,
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
        budget = ans.q_seconds(q, int(d.get("pace_seconds", 90)))
        gained = g.XP["attempt"]
        speedy = False
        if q.get("type") == "writing":
            w = ans.writing_given(chosen)
            gained = g.XP["writing_done"] + g.XP["writing_check"] * len(w["checks"])
            reason_txt = "Handed in a writing task"
        elif q.get("type") == "word":
            n_ok = sum(r["ok"] for r in ans.word_results(q, chosen))
            gained += g.XP["word_part"] * n_ok
            if correct:
                gained += g.XP["word_all"]
            asks = q.get("asks_for")
            if asks and ans.word_given(chosen).get("_asks") == asks["answer"]:
                gained += g.XP["read_right"]
            reason_txt = "Word problem: all parts right" if correct else f"Word problem: {n_ok} part(s) right"
        else:
            if correct:
                gained += g.XP["correct"]
            reason_txt = "Correct answer" if correct else "Gave it a go"
        if correct and secs <= budget and in_time and ans.is_scored(q):
            gained += g.XP["speedy"]
            speedy = True
        _xp(run, gained, reason_txt)
        run["feedback"] = {"qid": qid, "correct": correct, "xp": gained, "speedy": speedy, "chosen": chosen}
        st.session_state.pop("xp_toasts", None)  # feedback banner already shows XP
        st.rerun()


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
