"""📚 Past drills: open any finished drill again, question by question, and talk it through with Papa.

Both logins see the same page:
- Siyonah can flag any question ("🗣️ talk about this with Papa") and write what's confusing.
- Papa sees the talk list, writes notes from the chat, and ticks "talked it through".
The flags live on the `answers` rows (columns added by supabase/004_discuss.sql).
"""
import streamlit as st

from sb import answers as ans, data, gamify as g, style
from sb.style import esc

LETTERS = "ABCDE"
REASON_TXT = {"concept": "🧩 Didn't know how", "careless": "🙈 Careless slip",
              "misread": "👀 Misread the question", "time": "⏰ Ran out of time"}
FILTERS = {"all": "All", "wrong": "❌ Wrong or skipped", "talk": "🗣️ To talk about", "right": "✅ Right"}


def _fmt_secs(s):
    s = int(s or 0)
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


def _attempt_label(a, drills, flags_by_attempt):
    d = drills.get(a["drill_id"])
    day = g.to_local_date(a["finished_at"])
    title = d["title"] if d else a["drill_id"]
    n = flags_by_attempt.get(a["id"], 0)
    talk = f" · 🗣️ {n}" if n else ""
    return f"{day.strftime('%a %d %b') if day else '?'} · {title} · {a.get('score', 0)}/{a.get('total', 0)}{talk}"


def _status(q, a):
    if not a or a.get("chosen") in (None, "", "None"):
        return "skip"
    return "right" if a.get("correct") else "wrong"


def _mcq_html(q, a, attempt_id):
    """All options in the order she saw them, marking her pick and the right one."""
    chosen = None
    try:
        chosen = int(a["chosen"]) if a and a.get("chosen") not in (None, "", "None") else None
    except (TypeError, ValueError):
        pass
    rows = []
    for i, (orig, text) in enumerate(data.shuffled_options(q, attempt_id)):
        is_right = orig == int(q["answer"])
        is_hers = orig == chosen
        tag = ""
        if is_right and is_hers:
            tag = " ✅ <b>your answer, correct</b>"
        elif is_right:
            tag = " ✅ <b>correct</b>"
        elif is_hers:
            tag = " ❌ <b>your answer</b>"
        bg = "#e6fbf2" if is_right else ("#ffeaf0" if is_hers else "transparent")
        rows.append(f'<div style="padding:4px 10px;border-radius:10px;background:{bg}">'
                    f'<b>{LETTERS[i]}</b>&nbsp;&nbsp;{esc(text)}{tag}</div>')
    return '<div class="sb-card" style="padding:.5rem .6rem">' + "".join(rows) + "</div>"


def _answer_block(q, a, attempt_id):
    t = q.get("type", "mcq")
    if t == "word":
        from views.drill import _word_table
        st.markdown(_word_table(q, a["chosen"] if a else None), unsafe_allow_html=True)
    elif t == "numeric":
        c1, c2 = st.columns(2)
        hers = ans.answer_text(q, a["chosen"]) if a else "not answered"
        css = "sb-ok" if a and a.get("correct") else "sb-bad"
        c1.markdown(f'<div class="{css}">Your answer: {esc(hers)}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="sb-ok">Correct: {esc(ans.correct_text(q))}</div>', unsafe_allow_html=True)
    else:
        st.markdown(_mcq_html(q, a, attempt_id), unsafe_allow_html=True)


def _discussion(attempt, q, a, is_child):
    """The talk box under each question."""
    key = f"{attempt['id']}_{q['id']}"
    flagged = bool(a and a.get("discuss"))
    done = bool(a and a.get("discussed"))
    her = (a or {}).get("discuss_note") or ""
    papa = (a or {}).get("parent_note") or ""

    if flagged or papa:
        bits = []
        if flagged:
            bits.append(f'<div>🗣️ <b>{"Talked it through ✅" if done else "On the talk list"}</b></div>')
        if her:
            bits.append(f'<div style="margin-top:4px">✍️ <b>Siyonah:</b> {esc(her)}</div>')
        if papa:
            bits.append(f'<div style="margin-top:4px">💬 <b>Papa:</b> {esc(papa)}</div>')
        st.markdown(f'<div class="sb-tip">{"".join(bits)}</div>', unsafe_allow_html=True)

    with st.popover("🗣️ Talk about this" if not flagged else "✏️ Edit talk notes", use_container_width=False):
        if is_child:
            want = st.toggle("I want to talk about this with Papa", value=flagged, key=f"t_{key}")
            note = st.text_area("What's confusing, or what do you want to ask?", value=her, key=f"n_{key}",
                                placeholder="e.g. I don't get why the overlap is only taken away once")
            fields = {"discuss": want, "discuss_note": note.strip() or None}
            if not want:
                fields["discussed"] = False
        else:
            want = st.toggle("Put this on the talk list", value=flagged, key=f"t_{key}")
            note = st.text_area("Papa's notes (what we talked about, what to practise)", value=papa,
                                key=f"p_{key}", placeholder="e.g. Draw the 3 regions first: A only, overlap, B only")
            talked = st.checkbox("We've talked it through ✅", value=done, key=f"d_{key}")
            fields = {"discuss": want or talked, "parent_note": note.strip() or None, "discussed": talked}
        if st.button("Save 💾", key=f"s_{key}", use_container_width=True):
            err = data.save_discussion(attempt, q, fields, a)
            if err:
                st.error(err)
            else:
                st.toast("Saved 🗣️")
                st.rerun()


def _question(i, attempt, q, a, budget, is_child):
    stt = _status(q, a)
    icon = {"right": "✅", "wrong": "❌", "skip": "⏭️"}[stt]
    talk = " 🗣️" if a and a.get("discuss") and not a.get("discussed") else ""
    short = q.get("short") or q["stem"]
    short = short if len(short) <= 70 else short[:68] + "…"
    with st.expander(style.md(f"{icon} Q{i} · {g.TOPIC_LABEL.get(q.get('topic'), q.get('topic', ''))} · {short}{talk}")):
        secs = (a or {}).get("seconds")
        timing = (f"⏱️ {_fmt_secs(secs)} (exam pace {_fmt_secs(budget)})" if secs else "⏱️ not answered")
        slow = " · 🐢 over pace" if secs and secs > budget else ""
        st.markdown(f'<div class="sb-small">{timing}{slow}</div>'
                    f'<div class="sb-q" style="font-size:1.05rem;margin-top:4px">{esc(q["stem"])}</div>'
                    f'{style.img(q.get("image"), 380)}', unsafe_allow_html=True)
        _answer_block(q, a, attempt["id"])
        if q.get("type") == "word" and q.get("solution"):
            st.markdown("**Worked solution**")
            st.markdown("\n".join(f"{n}. {style.md(step)}" for n, step in enumerate(q["solution"], 1)))
        if q.get("explanation"):
            st.markdown(f"**How it works:** {style.md(q['explanation'])}")
        if q.get("technique"):
            st.markdown(f'<div class="sb-tip">💡 <b>Technique:</b> {esc(q["technique"])}</div>', unsafe_allow_html=True)
        if q.get("trap"):
            st.caption(f"🪤 Trap in this question: {style.md(q['trap'])}")
        if a and (a.get("reason") or a.get("fix_note")):
            st.markdown(f'<div class="sb-small" style="margin-top:6px">🔧 <b>Fix-it notes:</b> '
                        f'{esc(REASON_TXT.get(a.get("reason"), a.get("reason") or ""))}'
                        f'{" · " + esc(a["fix_note"]) if a.get("fix_note") else ""}</div>', unsafe_allow_html=True)
        _discussion(attempt, q, a, is_child)


def render():
    kid = data.child()
    is_child = data.me()["role"] == "child"
    st.markdown("## 📚 Past drills")
    st.caption("Open any drill you've finished and look at every question again: what you answered, the right "
               "answer and how it works. Tap 🗣️ on anything you want to talk about with Papa." if is_child else
               "Every finished drill, question by question. 🗣️ marks what she wants to talk about. Add your notes "
               "after you chat and tick 'talked it through'.")

    atts = data.finished_attempts(kid["id"])
    if not atts:
        style.card("No finished drills yet. Once a drill is done, it shows up here to look back on 🔍")
        return
    drills = {d["id"]: d for d in data.drills(include_archived=True)}
    all_ans = data.answers(kid["id"])
    by_attempt = {}
    for r in all_ans:
        by_attempt.setdefault(r["attempt_id"], {})[r["question_id"]] = r
    flags = [r for r in all_ans if r.get("discuss") and not r.get("discussed")]
    flags_by_attempt = {}
    for r in flags:
        flags_by_attempt[r["attempt_id"]] = flags_by_attempt.get(r["attempt_id"], 0) + 1
    atts = [a for a in atts if a["drill_id"] in drills]

    # ---- the talk list across all drills
    if flags:
        att_by_id = {a["id"]: a for a in atts}
        with st.container(border=True):
            st.markdown(f"#### 🗣️ To talk about ({len(flags)})")
            for r in flags:
                a = att_by_id.get(r["attempt_id"])
                if not a:
                    continue
                d = drills[a["drill_id"]]
                q = next((x for x in d["questions"] if x["id"] == r["question_id"]), None)
                if not q:
                    continue
                c1, c2 = st.columns([5, 1])
                note = f" — “{r['discuss_note']}”" if r.get("discuss_note") else ""
                stem = q.get('short') or q['stem']
                stem = stem if len(stem) <= 80 else stem[:78] + '…'
                c1.markdown(style.md(f"**{d['title']}** · {stem}{note}"))
                if c2.button("Open", key=f"open_{r['attempt_id']}_{r['question_id']}", use_container_width=True):
                    st.session_state.past_attempt = r["attempt_id"]
                    st.session_state.past_filter = "talk"
                    st.rerun()

    # ---- pick a drill attempt
    ids = [a["id"] for a in atts]
    pre = st.session_state.pop("past_attempt", None)
    if pre in ids:
        st.session_state["past_pick"] = pre
    if st.session_state.get("past_pick") not in ids:
        st.session_state["past_pick"] = ids[0]
    labels = {a["id"]: _attempt_label(a, drills, flags_by_attempt) for a in atts}
    pick = st.selectbox("Choose a drill", ids, format_func=lambda i: labels[i], key="past_pick")
    attempt = next(a for a in atts if a["id"] == pick)
    d = drills[attempt["drill_id"]]
    qm = {q["id"]: q for q in d["questions"]}
    served = [qid for qid in (attempt.get("question_ids") or list(qm)) if qid in qm]
    am = by_attempt.get(attempt["id"], {})
    pace = int(d.get("pace_seconds", 90))

    score = sum(1 for qid in served if am.get(qid, {}).get("correct"))
    n_skip = sum(1 for qid in served if _status(qm[qid], am.get(qid)) == "skip")
    took = int(data.seconds_since(attempt["started_at"]) - data.seconds_since(attempt["finished_at"]))
    limit = int(attempt.get("time_limit_sec") or len(served) * pace)
    style.card(f'<div class="sb-title" style="font-size:1.25rem">{esc(d["title"])}</div>'
               f'<div class="sb-small">{score} / {len(served)} right · {n_skip} not answered · '
               f'⏱️ {_fmt_secs(took)} of {_fmt_secs(limit)} · {esc(attempt.get("session_size") or "")}'
               f'{" · 🏁 beat the clock" if attempt.get("beat_clock") else ""}</div>'
               f'<div style="margin-top:6px">{"".join(style.pill(f, "lav") for f in (d.get("focus") or [])[:6])}</div>')

    pre_f = st.session_state.pop("past_filter", None)
    if pre_f:
        st.session_state["past_f"] = pre_f
    st.session_state.setdefault("past_f", "all")
    flt = st.segmented_control("Show", list(FILTERS), format_func=lambda k: FILTERS[k], key="past_f") or "all"

    shown = 0
    for i, qid in enumerate(served, 1):
        q, a = qm[qid], am.get(qid)
        stt = _status(q, a)
        if flt == "wrong" and stt == "right":
            continue
        if flt == "right" and stt != "right":
            continue
        if flt == "talk" and not (a and a.get("discuss")):
            continue
        shown += 1
        _question(i, attempt, q, a, ans.q_seconds(q, pace), is_child)
    if not shown:
        st.caption("Nothing here for this filter.")
