import streamlit as st

from sb import data, gamify as g, style
from sb.style import esc

KIND = {"mistake": ("🔧", "Mistake"), "technique": ("💡", "Technique"), "pattern": ("🔁", "Pattern")}
REASON = {"concept": "🧩 concept", "careless": "🙈 careless", "misread": "👀 misread", "time": "⏰ time"}


def _card_html(c, reveal=True):
    ic, kind = KIND.get(c["kind"], ("📝", c["kind"]))
    q = c.get("question") or {}
    pills = style.pill(f"{ic} {kind}", "pink") + style.pill(g.TOPIC_LABEL.get(c.get("topic"), c.get("topic") or "General"), "aqua")
    if c.get("reason"):
        pills += style.pill(REASON.get(c["reason"], c["reason"]), "gold")
    if c.get("mastered"):
        pills += style.pill("🏅 mastered", "lav")
    body = f'<div>{pills}</div><div class="sb-title" style="font-size:1.15rem;margin-top:6px">{esc(c["title"])}</div>'
    if q.get("stem") and q.get("stem") != c["title"]:
        body += f'<div class="sb-q" style="font-size:1rem;margin-top:4px">{esc(q["stem"])}</div>'
    if reveal:
        if q.get("options") is not None and q.get("type", "mcq") == "mcq":
            body += f'<div class="sb-ok" style="margin-top:8px">Answer: {esc(q["options"][int(q["answer"])])}</div>'
        elif q.get("answer") is not None:
            body += f'<div class="sb-ok" style="margin-top:8px">Answer: {esc(q["answer"])} {esc(q.get("unit", ""))}</div>'
        if c.get("my_fix"):
            body += f'<div style="margin-top:8px"><b>✍️ My fix:</b> {esc(c["my_fix"])}</div>'
        if c.get("technique"):
            body += f'<div class="sb-tip" style="margin-top:8px">💡 <b>Technique:</b> {esc(c["technique"])}</div>'
    return body


def render():
    is_child = data.me()["role"] == "child"
    st.markdown("## 📒 Mistake & Technique Notebook")
    st.caption("Every mistake you fix becomes a card. Cards come back on a schedule (1 → 2 → 4 → 7 → 14 → 30 days) "
               "until they're locked in.")
    tab_recall, tab_all, tab_add = st.tabs(["🧠 Recall time", "📚 All my cards", "➕ Add a technique"])

    with tab_recall:
        due = data.due_cards()
        if not due:
            style.card("🌈 No cards due right now. Come back tomorrow, or fix some mistakes to make new cards.")
        else:
            i = st.session_state.get("recall_i", 0) % len(due)
            c = due[i]
            st.markdown(f"**Card {i + 1} of {len(due)}**")
            shown = st.session_state.get("recall_show") == c["id"]
            style.card(_card_html(c, reveal=shown))
            if not shown:
                st.caption("Think: what's the answer, and what's the trick? Then flip the card.")
                if st.button("Flip card 🔄", use_container_width=True, key="flip"):
                    st.session_state.recall_show = c["id"]
                    st.rerun()
            elif is_child:
                c1, c2 = st.columns(2)
                if c1.button("I remembered! ✅", use_container_width=True):
                    data.review_card(c, True)
                    st.session_state.recall_show = None
                    data.award_badges(data.stats())
                    st.rerun()
                if c2.button("Not yet 🔁", use_container_width=True, type="tertiary"):
                    data.review_card(c, False)
                    st.session_state.recall_show = None
                    st.session_state.recall_i = i + 1
                    st.rerun()

    with tab_all:
        cards = data.notebook()
        if not cards:
            style.card("No cards yet. After a drill, fix your mistakes and they appear here ✨")
        else:
            c1, c2, c3 = st.columns(3)
            kinds = c1.multiselect("Type", list(KIND.keys()), format_func=lambda k: KIND[k][1])
            topics = sorted({c.get("topic") or "General" for c in cards})
            tps = c2.multiselect("Topic", topics, format_func=lambda t: g.TOPIC_LABEL.get(t, t))
            reasons = c3.multiselect("Why", list(REASON.keys()), format_func=lambda r: REASON[r])
            shown = [c for c in cards if (not kinds or c["kind"] in kinds)
                     and (not tps or (c.get("topic") or "General") in tps)
                     and (not reasons or c.get("reason") in reasons)]
            # pattern summary
            mist = [c for c in cards if c["kind"] == "mistake"]
            if mist:
                from collections import Counter
                rc = Counter(c.get("reason") for c in mist if c.get("reason"))
                tc = Counter(c.get("topic") for c in mist)
                st.markdown(
                    "**My patterns:** " + " ".join(style.pill(f"{REASON.get(r, r)} × {n}", "gold") for r, n in rc.most_common(4))
                    + " " + " ".join(style.pill(f"{g.TOPIC_LABEL.get(t, t)} × {n}", "aqua") for t, n in tc.most_common(3)),
                    unsafe_allow_html=True)
            for c in shown:
                style.card(_card_html(c))

    with tab_add:
        if not is_child:
            st.info("Siyonah adds her own techniques here, in her own words, so she owns them. "
                    "To suggest one, put it in a drill question's 'technique' field.")
            return
        with st.form("add_tech", clear_on_submit=True):
            kind = st.segmented_control("Card type", ["technique", "pattern"], default="technique",
                                        format_func=lambda k: f"{KIND[k][0]} {KIND[k][1]}")
            topic = st.selectbox("Topic", g.TOPICS, format_func=lambda t: g.TOPIC_LABEL[t])
            title = st.text_input("Name it", placeholder="e.g. Ratio change → find what stays the same")
            tech = st.text_area("How it works (your words)", placeholder="Draw before/after bars. The unchanged "
                                "person's units must match…")
            if st.form_submit_button("Add card ✨", use_container_width=True) and title.strip() and tech.strip():
                data.add_card(kind or "technique", topic, title.strip(), tech.strip())
                if is_child:
                    data.add_xp(g.XP["technique_added"], "Added a technique")
                st.success("Card added!")
