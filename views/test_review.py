"""📝 Test Review: Siyonah logs the marks she lost on a paper test, with the test PDF and answer sheet beside her.

Child page: ➕ Review a test · 🔁 Redo list · 📊 My tests.
Parent: render_parent(kid), shown in Parent Hub → 📝 Test Reviews (trend, re-tag, notes, talk list).
"""
from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sb import data, gamify as g, style, testlog as tl
from sb.style import esc

TOPICS_FOR = {
    "Maths": g.MATHS_TOPICS,
    "Reading": g.READING_TOPICS,
    "Verbal": g.VERBAL_TOPICS,
    "Writing": g.WRITING_TOPICS,
    "English": g.READING_TOPICS + g.VERBAL_TOPICS + g.WRITING_TOPICS,
}
BUCKET_COLOUR = {"easy": "#ffb23d", "learn": "#9b7bff", "time": "#38d9c9"}

# guided "why did I lose it?" questions → loss type
Q1 = {"knew": "✅ Yes, I knew how to do it", "method": "🧩 Not really",
      "blank": "⏭️ I left it blank or didn't finish it"}
Q2 = {"ok": "✅ Yes, I read it properly", "misread": "👀 No, I misread it or missed a word"}
Q3 = {"slip": "🙈 I made a calculation slip in my working",
      "final": "🎯 My working was fine, but the final answer was wrong (units, didn't answer what it asked, copied it wrong)"}
Q4 = {"time": "⏰ I ran out of time", "skipped": "⏭️ I didn't know where to start, so I skipped it"}
DID_HINT = {
    "method": "e.g. I didn't know how to find the area of a quarter circle",
    "misread": "e.g. I missed the word 'remaining'",
    "slip": "e.g. 7 × 8 = 54",
    "final": "e.g. I found the width but it asked for the perimeter",
    "time": "e.g. I spent too long on Q9",
    "skipped": "e.g. I didn't know what to do first",
}


def _sql_needed(e=None):
    st.warning(f"Test Review needs its tables. Papa: run `{tl.SQL_FILE}` once in Supabase → SQL Editor, then reload."
               + (f"\n\n_({e})_" if e else ""))


def _topic_fmt(t):
    return "Something else" if t == "Other" else g.TOPIC_LABEL.get(t, t)


def _type_pill(m):
    t = tl.eff_type(m)
    if m.get("kind") == "lucky":
        return style.pill("🍀 lucky guess", "aqua")
    ic, lab, _, _ = tl.LOSS.get(t, ("❔", "not tagged", "", ""))
    return style.pill(f"{ic} {lab}", "gold" if tl.bucket(m) == "easy" else "lav")


def _score_txt(t):
    if t.get("score") is not None and t.get("total"):
        return f"{tl.fmt_marks(t['score'])}/{tl.fmt_marks(t['total'])}"
    return "score not entered"


def _mistake_html(m, test_title=None):
    head = f"<b>{esc(test_title)}</b> · " if test_title else ""
    marks = f" · −{tl.fmt_marks(m.get('marks'))}" if m.get("kind") == "lost" else ""
    body = (f'<div>{head}<b>{esc(m["q_ref"])}</b>{marks} &nbsp;{_type_pill(m)}'
            f'{style.pill(_topic_fmt(m.get("topic") or "Other"), "pink")}'
            + (style.pill(tl.CONF[m["confidence"]], "lav") if m.get("confidence") in tl.CONF else "")
            + ('&nbsp;' + style.pill("🗣️ talk", "pink") if m.get("discuss") and not m.get("discussed") else "")
            + ('&nbsp;' + style.pill("✅ fixed", "aqua") if m.get("fixed") else "") + '</div>')
    if m.get("what_i_did"):
        lab = "🤔 <b>Wasn't sure about:</b>" if m.get("kind") == "lucky" else "❌ <b>What I did:</b>"
        body += f'<div style="margin-top:6px">{lab} {esc(m["what_i_did"])}</div>'
    if m.get("should_do"):
        body += f'<div class="sb-tip" style="margin-top:6px">💡 <b>Next time:</b> {esc(m["should_do"])}</div>'
    if m.get("parent_note"):
        body += f'<div style="margin-top:6px">🧭 <b>Papa:</b> {esc(m["parent_note"])}</div>'
    return body


def _summary_html(t, ms, kid_voice=True):
    s = tl.summary(ms)
    rows = ""
    for b, (ic, name, why) in tl.BUCKETS.items():
        n = s["buckets"].get(b, 0)
        if n:
            rows += f'<div style="margin-top:4px">{ic} <b>{name}:</b> {tl.fmt_marks(n)} <span class="sb-small">({why})</span></div>'
    if not rows:
        rows = '<div class="sb-small">No lost marks logged yet.</div>'
    lead = (f"You lost <b>{tl.fmt_marks(s['lost'])}</b> mark(s) on {s['n']} question(s)." if kid_voice
            else f"<b>{tl.fmt_marks(s['lost'])}</b> mark(s) logged on {s['n']} question(s).")
    easy = s["buckets"].get("easy", 0)
    cheer = (f'<div class="sb-ok" style="margin-top:8px">✨ {tl.fmt_marks(easy)} of those were marks you already knew '
             f'how to get. Slowing down and checking wins them back!</div>') if kid_voice and easy else ""
    lucky = f'<div style="margin-top:4px">🍀 Lucky guesses spotted: <b>{s["lucky"]}</b></div>' if s["lucky"] else ""
    return (f'<div class="sb-title" style="font-size:1.2rem">{esc(t["title"])} · {esc(str(t["test_date"]))}</div>'
            f'<div class="sb-small">{esc(t.get("source") or "")} · {esc(t.get("subject") or "")} · {_score_txt(t)}'
            f'{" · ⏰ ran out of time" if t.get("ran_out_of_time") else ""}</div>'
            f'<div style="margin-top:8px">{lead}</div>{rows}{lucky}{cheer}')


# ====================================================================== child page
def render():
    if data.me()["role"] != "child":
        st.markdown("## 📝 Test Reviews")
        render_parent(data.child())
        return
    st.markdown("## 📝 Test Review")
    st.caption("Got a test back? Open the test and the answer sheet, then log every mark you lost. "
               "It takes about a minute per question, and each one comes back later for a fresh redo.")
    try:
        tests = tl.tests()
        allm = tl.mistakes()
    except tl.NotReady as e:
        _sql_needed(e)
        return
    due = [m for m in allm if not m.get("fixed") and m.get("redo_next") and str(m["redo_next"])[:10] <= str(g.today())]
    if st.session_state.pop("tr_burst", False):
        style.sparkle_burst("redo")
        st.success("✅ Fixed for good! That one won't trip you up again.")
    t_add, t_redo, t_mine = st.tabs(["➕ Review a test", f"🔁 Redo list ({len(due)} due)", "📊 My tests"])
    with t_add:
        _review_tab(tests, allm)
    with t_redo:
        _redo_tab(tests, allm, due)
    with t_mine:
        _mine_tab(tests, allm)


# ---------------------------------------------------------------------- ➕ review a test
def _review_tab(tests, allm):
    cur_id = st.session_state.get("tr_test")
    cur = next((t for t in tests if t["id"] == cur_id), None)
    if cur is None and not st.session_state.get("tr_new"):
        cur = next((t for t in tests if t.get("status") == "in_progress"), None)
    if cur is None:
        _start_form()
        return
    ms = [m for m in allm if m["test_id"] == cur["id"]]
    _logging(cur, ms)


def _start_form():
    style.card('<div class="sb-title" style="font-size:1.3rem">🗂️ Which test are you reviewing?</div>'
               '<div class="sb-small">Fill this in from the top of your test paper.</div>')
    with st.form("tr_start"):
        title = st.text_input("Test name", placeholder="e.g. Term 4 Test 1, or ACER practice paper 2")
        c1, c2, c3 = st.columns(3)
        day = c1.date_input("Date of the test", value=g.today(), format="DD/MM/YYYY")
        source = c2.selectbox("Where's it from?", tl.SOURCES)
        subject = c3.selectbox("Which part of the exam?", tl.SUBJECTS,
                               format_func=lambda s: f"{g.SUBJECTS.get(s, '')} {s}")
        c4, c5, c6 = st.columns(3)
        score = c4.number_input("My score", min_value=0.0, step=0.5, value=None, placeholder="e.g. 74")
        total = c5.number_input("Out of", min_value=0.0, step=0.5, value=None, placeholder="e.g. 100")
        minutes = c6.number_input("Minutes allowed (optional)", min_value=0, step=5, value=None)
        ran_out = st.checkbox("⏰ I ran out of time")
        go_ = st.form_submit_button("Start reviewing ➡️", use_container_width=True)
    if go_:
        if not title.strip():
            st.error("Give the test a name first.")
            return
        if score is not None and total and score > total:
            st.error("Your score is bigger than the total. Check those two numbers.")
            return
        t = tl.start_test(title, day, source, subject, score, total, int(minutes) if minutes else None, ran_out)
        st.session_state.tr_test = t["id"]
        st.session_state.tr_new = False
        st.rerun()
    if st.session_state.get("tr_new"):
        if st.button("← Back", type="tertiary"):
            st.session_state.tr_new = False
            st.rerun()


def _logging(t, ms):
    lost = [m for m in ms if m.get("kind") == "lost"]
    s = tl.summary(ms)
    gap = None
    if t.get("score") is not None and t.get("total"):
        gap = float(t["total"]) - float(t["score"])
    prog = ""
    if gap:
        prog = (f'<div style="margin-top:8px">{style.bar(min(1.0, s["lost"] / gap))}</div>'
                f'<div class="sb-small" style="margin-top:4px">Logged <b>{tl.fmt_marks(s["lost"])}</b> of '
                f'<b>{tl.fmt_marks(gap)}</b> lost marks</div>')
    style.card(f'<div class="sb-title" style="font-size:1.25rem">📝 {esc(t["title"])}</div>'
               f'<div class="sb-small">{esc(str(t["test_date"]))} · {esc(t.get("source") or "")} · '
               f'{esc(t.get("subject") or "")} · {_score_txt(t)}</div>{prog}', "sb-card")
    if st.session_state.pop("tr_edt_close", None) == t["id"]:
        st.session_state[f"tr_edt_{t['id']}"] = False
    if st.toggle("✏️ Fix the test details", key=f"tr_edt_{t['id']}"):
        _edit_test(t)

    if t.get("status") == "done":
        style.card(_summary_html(t, ms))
        if st.toggle("➕ Add a question I forgot", key=f"tr_more_{t['id']}"):
            _add_mistake(t)
            _add_lucky(t)
    else:
        _add_mistake(t)
        _add_lucky(t)

    if ms:
        st.markdown(f"#### Logged so far ({len(lost)} lost · {s['lucky']} lucky)")
        st.caption("Made a mistake in a card? Tap ✏️ to fix it.")
        for m in ms:
            _logged_row(t, m)

    st.divider()
    c1, c2 = st.columns(2)
    if t.get("status") != "done":
        short = gap is not None and s["lost"] + 0.01 < gap
        if short:
            c1.caption(f"Your score says you lost {tl.fmt_marks(gap)} marks, and you've logged "
                       f"{tl.fmt_marks(s['lost'])}. Did you miss any?")
        if c1.button("Finish my review 🎉", use_container_width=True, disabled=not lost):
            tl.finish_test(t)
            data.award_badges(data.stats())
            st.session_state.tr_done = t["id"]
            st.rerun()
    if c2.button("Review a different test 🗂️", use_container_width=True, type="tertiary"):
        st.session_state.tr_test = None
        st.session_state.tr_new = True
        st.rerun()
    if st.session_state.get("tr_done") == t["id"]:
        st.session_state.tr_done = None
        style.sparkle_burst("tr")


LOSS_KEYS = list(tl.LOSS)


def _loss_fmt(k):
    return f"{tl.LOSS[k][0]} {tl.LOSS[k][1]}"


def _logged_row(t, m):
    """One logged card with ✏️ edit and 🗑️ delete (delete asks first)."""
    mid = m["id"]
    editing = st.session_state.get("tr_edit") == mid
    c1, c2, c3 = st.columns([12, 1, 1])
    with c1:
        style.card(_mistake_html(m))
    if c2.button("✏️", key=f"tr_ed_{mid}", type="tertiary", help="Fix this card"):
        st.session_state.tr_edit = None if editing else mid
        st.session_state.tr_delask = None
        st.rerun()
    if c3.button("🗑️", key=f"tr_del_{mid}", type="tertiary", help="Remove this card"):
        st.session_state.tr_delask = mid
        st.session_state.tr_edit = None
        st.rerun()
    if st.session_state.get("tr_delask") == mid:
        st.warning(f"Remove {m['q_ref']} completely?" + (" Its notebook card goes too." if m.get("card_id") else ""))
        a, b = st.columns(2)
        if a.button("Yes, remove it", key=f"tr_dely_{mid}", use_container_width=True):
            tl.delete_mistake(m)
            st.session_state.tr_delask = None
            st.rerun()
        if b.button("No, keep it", key=f"tr_deln_{mid}", use_container_width=True, type="tertiary"):
            st.session_state.tr_delask = None
            st.rerun()
    if editing:
        _edit_mistake(t, m)


def _edit_mistake(t, m):
    mid = m["id"]
    lucky = m.get("kind") == "lucky"
    with st.form(f"tr_ef_{mid}"):
        st.markdown(f"**✏️ Fixing {m['q_ref']}**")
        kind = st.radio("This was…", ["lost", "lucky"], index=1 if lucky else 0, horizontal=True,
                        format_func=lambda k: "❌ a mark I lost" if k == "lost" else "🍀 a lucky guess (I got it right)")
        c1, c2, c3 = st.columns([1.2, 1, 1.6])
        q_ref = c1.text_input("Question number", value=m.get("q_ref") or "")
        marks = c2.number_input("Marks lost", min_value=0.0, step=0.5, format="%.1f",
                                value=float(m.get("marks") or 1.0) if not lucky else 1.0)
        topics = TOPICS_FOR.get(t.get("subject") or "Maths", g.MATHS_TOPICS) + ["Other"]
        if m.get("topic") and m["topic"] not in topics:
            topics = [m["topic"]] + topics
        topic = c3.selectbox("Topic", topics, format_func=_topic_fmt,
                             index=topics.index(m["topic"]) if m.get("topic") in topics else None)
        cur = m.get("loss_type")
        loss = st.selectbox("Why did I lose it? (for a lost mark)", LOSS_KEYS, format_func=_loss_fmt,
                            index=LOSS_KEYS.index(cur) if cur in LOSS_KEYS else None,
                            placeholder="Pick the reason")
        cl = list(tl.CONF)
        conf = st.radio("How sure was I?", cl, format_func=tl.CONF.get, horizontal=True,
                        index=cl.index(m["confidence"]) if m.get("confidence") in cl else None)
        did = st.text_input("What did I do? (or what wasn't I sure about)", value=m.get("what_i_did") or "")
        should = st.text_input("What should I have done? (my trick for next time)", value=m.get("should_do") or "")
        talk = st.checkbox("🗣️ I want to talk about this with Papa", value=bool(m.get("discuss")))
        talk_note = st.text_input("What's confusing? (if talking with Papa)", value=m.get("discuss_note") or "")
        card = False
        if not m.get("card_id"):
            card = st.checkbox("📒 Also make a notebook card")
        a, b = st.columns(2)
        save = a.form_submit_button("Save changes 💾", use_container_width=True)
        cancel = b.form_submit_button("Cancel", use_container_width=True, type="tertiary")
    if cancel:
        st.session_state.tr_edit = None
        st.rerun()
    if save:
        errs = []
        if not q_ref.strip():
            errs.append("The question number can't be empty.")
        if not topic:
            errs.append("Pick a topic.")
        if kind == "lost" and not loss:
            errs.append("Pick why you lost it.")
        if kind == "lost" and not marks:
            errs.append("Marks lost should be more than 0.")
        for e in errs:
            st.error(e)
        if not errs:
            tl.edit_mistake(t, m, kind=kind, q_ref=q_ref, marks=marks, topic=topic, loss_type=loss,
                            confidence=conf, what_i_did=did, should_do=should, discuss=talk,
                            discuss_note=talk_note, make_card=card)
            st.session_state.tr_edit = None
            st.toast("Card fixed ✅", icon="✏️")
            st.rerun()


def _edit_test(t):
    with st.form(f"tr_et_{t['id']}"):
        title = st.text_input("Test name", value=t.get("title") or "")
        c1, c2, c3 = st.columns(3)
        try:
            from datetime import date
            d0 = date.fromisoformat(str(t.get("test_date"))[:10])
        except Exception:
            d0 = g.today()
        day = c1.date_input("Date of the test", value=d0, format="DD/MM/YYYY")
        src = tl.SOURCES
        source = c2.selectbox("Where's it from?", src, index=src.index(t["source"]) if t.get("source") in src else 0)
        sub = tl.SUBJECTS
        subject = c3.selectbox("Which part of the exam?", sub, index=sub.index(t["subject"]) if t.get("subject") in sub else 0,
                               format_func=lambda x: f"{g.SUBJECTS.get(x, '')} {x}")
        c4, c5, c6 = st.columns(3)
        score = c4.number_input("My score", min_value=0.0, step=0.5,
                                value=float(t["score"]) if t.get("score") is not None else None)
        total = c5.number_input("Out of", min_value=0.0, step=0.5,
                                value=float(t["total"]) if t.get("total") is not None else None)
        minutes = c6.number_input("Minutes allowed (optional)", min_value=0, step=5,
                                  value=int(t["minutes"]) if t.get("minutes") else None)
        ran_out = st.checkbox("⏰ I ran out of time", value=bool(t.get("ran_out_of_time")))
        ok = st.form_submit_button("Save test details 💾", use_container_width=True)
    if ok:
        if not title.strip():
            st.error("Give the test a name.")
        elif score is not None and total and score > total:
            st.error("Your score is bigger than the total. Check those two numbers.")
        else:
            tl.update_test(t, {"title": title.strip(), "test_date": str(day), "source": source, "subject": subject,
                               "score": score, "total": total, "minutes": int(minutes) if minutes else None,
                               "ran_out_of_time": bool(ran_out)})
            st.session_state.tr_edt_close = t["id"]
            st.toast("Test details saved ✅", icon="✏️")
            st.rerun()


def _add_mistake(t):
    n = st.session_state.get("tr_n", 0)
    k = f"_{t['id'][:8]}_{n}"
    style.card('<div class="sb-title" style="font-size:1.15rem">➕ Log a mark I lost</div>'
               '<div class="sb-small">Look at the question, your answer and the answer sheet. Then answer these.</div>')
    c1, c2, c3 = st.columns([1.2, 1, 1.6])
    q_ref = c1.text_input("Question number", key="tr_q" + k, placeholder="e.g. Q12 or Paper 2 Q5b")
    marks = c2.number_input("Marks lost", min_value=0.5, step=0.5, value=1.0, format="%.1f", key="tr_m" + k)
    topics = TOPICS_FOR.get(t.get("subject") or "Maths", g.MATHS_TOPICS) + ["Other"]
    topic = c3.selectbox("Topic", topics, format_func=_topic_fmt, index=None, key="tr_t" + k,
                         placeholder="Pick the topic")

    st.markdown("**Why did I lose it?**")
    loss = None
    a1 = st.radio("1. Did I know how to do it?", list(Q1), format_func=Q1.get, index=None, key="tr_a1" + k)
    if a1 == "method":
        loss = "method"
    elif a1 == "knew":
        a2 = st.radio("2. Did I read the question properly?", list(Q2), format_func=Q2.get, index=None,
                      key="tr_a2" + k)
        if a2 == "misread":
            loss = "misread"
        elif a2 == "ok":
            a3 = st.radio("3. So where did it go wrong?", list(Q3), format_func=Q3.get, index=None, key="tr_a3" + k)
            loss = a3
    elif a1 == "blank":
        loss = st.radio("2. Why didn't I finish it?", list(Q4), format_func=Q4.get, index=None, key="tr_a4" + k)
    if loss:
        ic, lab, _, b = tl.LOSS[loss]
        st.markdown(style.pill(f"{ic} {lab}", "gold" if b == "easy" else "lav") +
                    f' <span class="sb-small">{tl.BUCKETS[b][0]} {tl.BUCKETS[b][1]}</span>', unsafe_allow_html=True)

    conf = None
    if loss and loss not in ("time", "skipped"):
        conf = st.radio("How sure was I when I answered?", list(tl.CONF), format_func=tl.CONF.get, index=None,
                        horizontal=True, key="tr_c" + k)
    did = st.text_input("What did I do?", key="tr_d" + k, placeholder=DID_HINT.get(loss, "In a few words"))
    should = st.text_input("What should I have done? (my trick for next time)", key="tr_s" + k,
                           placeholder="e.g. Underline what the last line asks for before I start")
    c4, c5 = st.columns(2)
    card = c4.checkbox("📒 Also make a notebook card", key="tr_card" + k,
                       help="It comes back in Recall time on the usual schedule.")
    talk = c5.checkbox("🗣️ I want to talk about this with Papa", key="tr_talk" + k)
    talk_note = st.text_input("What's confusing?", key="tr_tn" + k) if talk else ""
    ready = bool(q_ref.strip()) and bool(topic) and bool(loss)
    if st.button("Save this one 💾", use_container_width=True, disabled=not ready, key="tr_save" + k):
        tl.add_mistake(t, kind="lost", q_ref=q_ref, marks=marks, topic=topic, loss_type=loss, confidence=conf,
                       what_i_did=did, should_do=should, make_card=card, discuss=talk, discuss_note=talk_note)
        st.session_state.tr_n = n + 1
        st.rerun()
    if not ready:
        st.caption("Fill in the question number, the topic and the why-questions to save.")


def _add_lucky(t):
    n = st.session_state.get("tr_ln", 0)
    k = f"_{t['id'][:8]}_{n}"
    with st.expander("🍀 Got one right but you weren't sure? Log it as a lucky guess"):
        st.caption("These are sneaky. The mark says you know it, but you don't yet. They come back for a redo too.")
        c1, c2, c3 = st.columns([1, 1.4, 1.2])
        q_ref = c1.text_input("Question number", key="trl_q" + k)
        topics = TOPICS_FOR.get(t.get("subject") or "Maths", g.MATHS_TOPICS) + ["Other"]
        topic = c2.selectbox("Topic", topics, format_func=_topic_fmt, index=None, key="trl_t" + k,
                             placeholder="Pick the topic")
        conf = c3.radio("I was…", ["unsure", "guess"], format_func=tl.CONF.get, key="trl_c" + k)
        why = st.text_input("What wasn't I sure about?", key="trl_w" + k)
        if st.button("Save lucky guess 🍀", disabled=not (q_ref.strip() and topic), key="trl_s" + k,
                     use_container_width=True):
            tl.add_mistake(t, kind="lucky", q_ref=q_ref, marks=0, topic=topic, loss_type=None, confidence=conf,
                           what_i_did=why, should_do="", make_card=False, discuss=False, discuss_note="")
            st.session_state.tr_ln = n + 1
            st.rerun()


# ---------------------------------------------------------------------- 🔁 redo list
def _redo_tab(tests, allm, due):
    names = {t["id"]: t["title"] for t in tests}
    st.caption("Do each question again **on paper, without looking at the answer**. Then check the answer sheet. "
               "Two clean redos (after 3 days, then 2 weeks) and it's fixed for good ✅")
    if not due:
        waiting = [m for m in allm if not m.get("fixed") and m.get("redo_next")]
        if waiting:
            nxt = min(str(m["redo_next"])[:10] for m in waiting)
            style.card(f"🌈 Nothing to redo today. {len(waiting)} question(s) are resting; the next one is due on {nxt}.")
        else:
            style.card("🌈 Nothing to redo yet. Review a test to fill this list.")
    for m in due:
        style.card(_mistake_html(m, names.get(m["test_id"], "Test")) +
                   f'<div class="sb-small" style="margin-top:6px">Redo {int(m.get("redo_box") or 0) + 1} of '
                   f'{len(tl.REDO_DAYS)}</div>')
        c1, c2 = st.columns(2)
        if c1.button("✅ I got it right", key=f"rd_ok_{m['id']}", use_container_width=True):
            if tl.redo(m, True):
                st.session_state.tr_burst = True
            data.award_badges(data.stats())
            st.rerun()
        if c2.button("❌ Still tricky", key=f"rd_no_{m['id']}", use_container_width=True, type="tertiary"):
            tl.redo(m, False)
            st.rerun()
    fixed = [m for m in allm if m.get("fixed")]
    if fixed:
        st.markdown(f"#### ✅ Fixed for good ({len(fixed)})")
        st.markdown(" ".join(style.pill(f"{names.get(m['test_id'], '')} · {m['q_ref']}", "aqua") for m in fixed[-30:]),
                    unsafe_allow_html=True)


# ---------------------------------------------------------------------- 📊 my tests
def _mine_tab(tests, allm):
    if not tests:
        style.card("No tests reviewed yet. Start with the last test you got back 📝")
        return
    done = [t for t in tests if t.get("status") == "done"]
    s_all = tl.summary(allm)
    fixed = sum(1 for m in allm if m.get("fixed"))
    st.markdown(
        '<div class="sb-stat">'
        f'<div class="box"><div class="big">📝 {len(done)}</div><div class="lbl">tests reviewed</div></div>'
        f'<div class="box"><div class="big">✨ {tl.fmt_marks(s_all["buckets"].get("easy", 0))}</div><div class="lbl">easy marks to win back</div></div>'
        f'<div class="box"><div class="big">📚 {tl.fmt_marks(s_all["buckets"].get("learn", 0))}</div><div class="lbl">marks to learn</div></div>'
        f'<div class="box"><div class="big">✅ {fixed}</div><div class="lbl">fixed with redos</div></div>'
        '</div>', unsafe_allow_html=True)
    st.write("")
    _trend_chart(tests, allm, kid_voice=True)
    for t in tests:
        ms = [m for m in allm if m["test_id"] == t["id"]]
        badge = "✅" if t.get("status") == "done" else "✏️ in progress"
        with st.expander(f"{badge} {t['test_date']} · {t['title']} · {_score_txt(t)}"):
            style.card(_summary_html(t, ms))
            for m in ms:
                style.card(_mistake_html(m))
            if st.button("Open to add more ✏️", key=f"tr_open_{t['id']}", type="tertiary"):
                st.session_state.tr_test = t["id"]
                st.session_state.tr_new = False
                st.rerun()
            if t.get("status") == "done":
                st.caption("To fix a card, tap Open, then ✏️ on that card.")


def _trend_chart(tests, allm, kid_voice):
    done = sorted([t for t in tests if t.get("status") == "done"], key=lambda t: str(t["test_date"]))
    if len(done) < 1:
        return
    xs = [f"{str(t['test_date'])[5:]} {t['title'][:18]}" for t in done]
    fig = go.Figure()
    for b, (ic, name, _) in tl.BUCKETS.items():
        ys = [tl.summary([m for m in allm if m["test_id"] == t["id"]])["buckets"].get(b, 0) for t in done]
        fig.add_bar(x=xs, y=ys, name=f"{ic} {name}", marker_color=BUCKET_COLOUR[b])
    fig.update_layout(barmode="stack", height=300, bargap=0.75 if len(done) < 3 else 0.35, margin=dict(l=10, r=10, t=40, b=10),
                      title="Marks lost per test, by kind" if not kid_voice else "Where my marks went, test by test",
                      legend=dict(orientation="h", y=-0.25), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", yaxis_title="marks")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ====================================================================== parent
def render_parent(kid):
    try:
        tests = tl.tests(kid["id"])
        allm = tl.mistakes(kid["id"])
    except tl.NotReady as e:
        _sql_needed(e)
        return
    if not tests:
        st.info(f"{kid['display_name']} hasn't reviewed a paper test yet. She does it in 📝 Test Review: "
                "test PDF and answer sheet open, one quick card per lost mark.")
        return

    talk = [m for m in allm if m.get("discuss") and not m.get("discussed")]
    unchecked = [t for t in tests if t.get("status") == "done" and not t.get("parent_checked")]
    if talk:
        st.warning(f"🗣️ {kid['display_name']} wants to talk about **{len(talk)}** test question(s). They're marked 🗣️ below.")
    if unchecked:
        st.info(f"🔎 {len(unchecked)} finished review(s) for you to check: " + ", ".join(t["title"] for t in unchecked))

    s = tl.summary(allm)
    lost = s["lost"] or 1
    c = st.columns(5)
    c[0].metric("Tests reviewed", sum(1 for t in tests if t.get("status") == "done"))
    c[1].metric("Marks logged", tl.fmt_marks(s["lost"]))
    c[2].metric("Easy to win back", f"{s['buckets'].get('easy', 0) / lost * 100:.0f}%")
    c[3].metric("Lucky guesses", s["lucky"])
    c[4].metric("Fixed by redo", sum(1 for m in allm if m.get("fixed")))
    _trend_chart(tests, allm, kid_voice=False)

    lostm = [m for m in allm if m.get("kind") == "lost"]
    if lostm:
        df = pd.DataFrame([{"Topic": _topic_fmt(m.get("topic") or "Other"),
                            "Why": tl.LOSS.get(tl.eff_type(m), ("", "?", "", ""))[1],
                            "Marks": float(m.get("marks") or 0)} for m in lostm])
        pv = df.pivot_table(index="Topic", columns="Why", values="Marks", aggfunc="sum", fill_value=0)
        pv["Total"] = pv.sum(axis=1)
        st.markdown("**Marks lost by topic and reason (all reviewed tests)**")
        st.dataframe(pv.sort_values("Total", ascending=False), use_container_width=True)
        conf = Counter(m.get("confidence") for m in lostm if m.get("confidence"))
        if conf.get("sure"):
            st.caption(f"😎 {conf['sure']} lost mark(s) were answers she felt sure about. Those are the riskiest: "
                       "she won't double-check them in the exam.")

    st.markdown("#### Each test")
    types = list(tl.LOSS)
    for t in tests:
        ms = [m for m in allm if m["test_id"] == t["id"]]
        flag = " 🗣️" if any(m.get("discuss") and not m.get("discussed") for m in ms) else ""
        chk = " ✅ checked" if t.get("parent_checked") else (" 🔎 to check" if t.get("status") == "done" else " ✏️ in progress")
        with st.expander(f"{t['test_date']} · {t['title']} · {_score_txt(t)}{chk}{flag}"):
            style.card(_summary_html(t, ms, kid_voice=False))
            with st.form(f"pt_{t['id']}"):
                edits = {}
                for m in ms:
                    style.card(_mistake_html(m))
                    if m.get("discuss_note"):
                        st.markdown(style.md(f"🗣️ **Her question:** {m['discuss_note']}"))
                    a, b, c_ = st.columns([1.3, 2, 0.9])
                    cur = tl.eff_type(m)
                    if m.get("kind") == "lost":
                        newt = a.selectbox("Reason (re-tag)", types, index=types.index(cur) if cur in types else 0,
                                           format_func=lambda k: f"{tl.LOSS[k][0]} {tl.LOSS[k][1]}",
                                           key=f"pt_ty_{m['id']}")
                    else:
                        newt = None
                        a.caption("🍀 lucky guess")
                    note = b.text_input("Papa's note (she sees it)", value=m.get("parent_note") or "",
                                        key=f"pt_no_{m['id']}")
                    talked = c_.checkbox("Talked ✅", value=bool(m.get("discussed")), key=f"pt_tk_{m['id']}",
                                         disabled=not m.get("discuss"))
                    edits[m["id"]] = (m, newt, note, talked)
                tnote = st.text_input("Note on the whole test", value=t.get("parent_note") or "", key=f"pt_tn_{t['id']}")
                checked = st.checkbox("I've checked her tags ✅", value=bool(t.get("parent_checked")),
                                      key=f"pt_ck_{t['id']}")
                if st.form_submit_button("Save", use_container_width=True):
                    for mid, (m, newt, note, talked) in edits.items():
                        f = {}
                        if newt is not None:
                            pt = None if newt == m.get("loss_type") else newt
                            if pt != m.get("parent_type"):
                                f["parent_type"] = pt
                        if (note or None) != (m.get("parent_note") or None):
                            f["parent_note"] = note or None
                        if m.get("discuss") and talked != bool(m.get("discussed")):
                            f["discussed"] = talked
                        if f:
                            tl.update_mistake(m, f)
                    tl.update_test(t, {"parent_note": tnote or None, "parent_checked": checked})
                    st.success("Saved.")
                    st.rerun()
