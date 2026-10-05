"""Mistake Map views: the full analysis (Parent Hub tab) and the friendly 'My focus' tab (notebook)."""
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sb import data, gamify as g, insights, style
from sb.style import esc

TYPE_COLOURS = {"Method / concept gap": "#7b61ff", "Misread or missed a condition": "#ff4fa0",
                "Right method, wrong final answer": "#ffb23d", "Arithmetic slip": "#38d9c9",
                "Skipped / unfinished": "#b9aecb"}
STATUS_PILL = {"Active": "pink", "Watch": "gold", "Recheck": "lav"}
STATUS_TXT = {"Active": "🔴 Active", "Watch": "🟡 Watch", "Recheck": "🔵 Recheck"}


# ================================================================ Parent Hub tab
def render_parent(kid):
    m = data.mistake_map()
    if not m:
        style.card("<b>No Mistake Map yet.</b><br>Ask Claude in the project chat to <i>“refresh the mistake map for "
                   "the app”</i>. It saves a JSON file to the vault at <code>Practice/App_Insights/</code>. "
                   "Upload it below.")
        _upload(expanded=True)
        return
    answers = data.answers(kid["id"])
    s = m.get("stats", {})
    st.caption(f"Updated {m.get('updated')} · built by Claude from every test analysis in the vault · "
               "“In the app” is live from her drill answers.")
    c = st.columns(4)
    c[0].metric("Questions lost", s.get("questions_lost", "—"))
    c[1].metric("Logged mistakes", s.get("entries", "—"))
    c[2].metric("Tests & drills", s.get("tests", "—"))
    c[3].metric("Since", str(s.get("period", "—")).split("–")[0].strip())

    # ---- ranked problem areas
    st.markdown("### 🗺️ Where the marks go")
    st.caption("Ranked by how urgent each area is now. A topic test inflates its own topic, so the 2026 and "
               "last-4-tests columns matter more than the all-time total.")
    rows = []
    for i, a in enumerate(m["areas"], 1):
        p = insights.topic_progress(answers, a.get("app_topic"))
        live = (f'<span class="sb-topic {insights.colour(p["acc"])}" style="margin:0;padding:.2rem .55rem">'
                f'{p["acc"] * 100:.0f}% · {p["n"]} Qs</span>' if p else '<span class="sb-small">not yet</span>')
        rows.append(
            f'<tr><td class="sb-small">{i}</td><td class="nw"><b>{esc(a["label"])}</b></td>'
            f'<td class="n">{a.get("all", "")}</td><td class="n">{a.get("y2026", "")}</td><td class="n">{a.get("recent", "")}</td>'
            f'<td class="nw">{live}</td><td>{style.pill(STATUS_TXT.get(a["status"], a["status"]), STATUS_PILL.get(a["status"], "lav"))}</td>'
            f'<td class="why">{esc(a["why"])}</td></tr>')
    st.markdown(
        '<div class="sb-card sb-scroll"><table class="sb-table"><thead><tr><th>#</th><th>Topic</th><th class="n">All time</th>'
        '<th class="n">2026</th><th class="n">Last 4 tests</th><th>In the app</th><th>Status</th><th>What keeps going wrong</th>'
        '</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>", unsafe_allow_html=True)

    # ---- how marks are lost
    if m.get("periods"):
        st.markdown("### 🧭 How she loses marks")
        types = m.get("types") or list(TYPE_COLOURS)
        labels = [p["label"] for p in m["periods"]][::-1]
        fig = go.Figure()
        for t in types:
            vals = []
            for p in m["periods"][::-1]:
                tot = sum(p["counts"].values()) or 1
                vals.append(round(p["counts"].get(t, 0) / tot * 100))
            fig.add_bar(y=labels, x=vals, name=t, orientation="h", marker_color=TYPE_COLOURS.get(t, "#999"),
                        hovertemplate="%{y}: %{x}%<extra>" + t + "</extra>")
        fig.update_layout(barmode="stack", height=300, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis=dict(range=[0, 100], ticksuffix="%"), legend=dict(orientation="h", y=-0.2),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if m.get("type_note"):
            st.info(m["type_note"])

    # ---- habits
    st.markdown("### 🔁 Patterns across topics")
    cols = st.columns(2)
    for i, h in enumerate(m["habits"]):
        with cols[i % 2]:
            style.card(f'<div class="sb-title" style="font-size:1.1rem">{esc(h["title"])}</div>'
                       f'<div style="margin-top:4px">{esc(h.get("what", ""))}</div>'
                       f'<div class="sb-small" style="margin-top:6px">{esc(h.get("evidence", ""))}</div>'
                       f'<div class="sb-tip" style="margin-top:8px"><b>Fix:</b> {esc(h.get("fix", ""))}</div>')

    # ---- full list
    st.markdown("### 📋 Every logged mistake")
    df = pd.DataFrame(m["entries"])
    if not df.empty:
        f1, f2, f3, f4 = st.columns([1.2, 1.2, .8, 1.3])
        tp = f1.selectbox("Topic", ["All"] + [a["label"] for a in m["areas"]], key="mm_topic")
        ty = f2.selectbox("How it was lost", ["All"] + sorted(df["type"].dropna().unique()), key="mm_type")
        yr = f3.selectbox("Year", ["All"] + sorted({str(y) for y in df["year"]}, reverse=True), key="mm_year")
        q = f4.text_input("Search", placeholder="e.g. remaining, semicircle", key="mm_q").strip().lower()
        v = df
        if tp != "All":
            v = v[v["topic"] == tp]
        if ty != "All":
            v = v[v["type"] == ty]
        if yr != "All":
            v = v[v["year"].astype(str) == yr]
        if q:
            v = v[(v["q"] + " " + v["detail"] + " " + v["test"]).str.lower().str.contains(q, regex=False)]
        v = v.assign(_d=v["date"].where(v["date"].str[:1].str.isdigit(), "")).sort_values(["year", "_d"], ascending=False)
        st.caption(f"{len(v)} entries · {int(v['n'].sum())} questions")
        st.dataframe(v[["date", "test", "q", "detail", "topic", "type", "n"]], hide_index=True,
                     use_container_width=True, height=460,
                     column_config={"date": "Date", "test": "Test", "q": st.column_config.TextColumn("Question", width="medium"),
                                    "detail": st.column_config.TextColumn("What happened / fix", width="large"),
                                    "topic": "Topic", "type": "How lost", "n": st.column_config.NumberColumn("Qs", width="small")})
    if m.get("source_note"):
        st.caption(m["source_note"])
    _upload(expanded=False)


def _upload(expanded):
    with st.expander("🔄 Update the Mistake Map", expanded=expanded):
        up = st.file_uploader("Mistake map file (.json)", type=["json"], key="mm_up")
        if not up:
            return
        try:
            m = json.loads(up.getvalue().decode("utf-8"))
        except Exception as e:
            st.error(f"Not valid JSON ({e})")
            return
        errs = insights.validate(m)
        for e in errs:
            st.error(e)
        if not errs:
            st.success(f"Looks good: updated {m['updated']}, {len(m['areas'])} topics, {len(m['entries'])} mistakes.")
            if st.button("Publish the Mistake Map 🗺️", use_container_width=True, key="mm_pub"):
                try:
                    data.save_mistake_map(m)
                except Exception as e:
                    st.error(f"Couldn't save. Has supabase/003_mistake_map.sql been run in Supabase? ({e})")
                else:
                    st.success("Published! It's in this tab and in her notebook under 🎯 My focus.")
                    st.rerun()


# ================================================================ Notebook tab (her view)
def render_focus(is_child):
    m = data.mistake_map()
    if not m:
        style.card("🎯 Your focus list will appear here soon. It shows the few things that will win you the most marks.")
        return
    answers = data.answers()
    active = [a for a in m["areas"] if a["status"] == "Active"][:4]
    others = [a for a in m["areas"] if a["status"] != "Active"]
    style.card(f'<h3 style="margin:0">🎯 Your {len(active)} power-ups</h3>'
               '<div class="sb-sub" style="margin-top:4px">Get these right and you win the most marks in the exam. '
               'Your drills practise them every week. Watch the bars grow!</div>', "sb-hero")
    cols = st.columns(2)
    for i, a in enumerate(active):
        p = insights.topic_progress(answers, a.get("app_topic"))
        if p:
            prog = (f'<div class="sb-small" style="margin-top:10px">In your drills: {p["n"]} questions · '
                    f'<b>{p["acc"] * 100:.0f}% right lately</b></div>{style.bar(p["acc"])}')
        else:
            prog = '<div class="sb-small" style="margin-top:10px">Not in your drills yet. Coming soon! ✨</div>'
        with cols[i % 2]:
            style.card(f'<div class="sb-title" style="font-size:1.2rem">{esc(a.get("kid_title") or a["label"])}</div>'
                       f'<div>{style.pill(a["label"], "aqua")}</div>'
                       f'<div class="sb-tip" style="margin-top:6px">{esc(a.get("kid_tip") or a["why"])}</div>{prog}')

    if m.get("wins"):
        style.card('<div class="sb-title" style="font-size:1.15rem">🌟 Wins so far</div>'
                   + "".join(f'<div style="margin-top:6px">✅ {esc(w)}</div>' for w in m["wins"]))

    st.markdown("### 🦸 Super-power habits")
    st.caption("Little habits that save marks in every topic. Add one to your notebook and it comes back in Recall time.")
    have = {c["title"] for c in data.notebook()}
    cols = st.columns(2)
    for i, h in enumerate(m["habits"]):
        with cols[i % 2]:
            style.card(f'<div class="sb-title" style="font-size:1.1rem">{esc(h["kid_title"])}</div>'
                       f'<div style="margin-top:4px">{esc(h["kid_tip"])}</div>')
            if h["kid_title"] in have:
                st.markdown(style.pill("✅ In your notebook", "aqua"), unsafe_allow_html=True)
            elif is_child and st.button("➕ Add to my notebook", key=f"habit_{i}", use_container_width=True, type="tertiary"):
                data.add_card("technique", h.get("app_topic"), h["kid_title"], h["kid_tip"])
                data.add_xp(g.XP["technique_added"], "Added a technique")
                st.rerun()

    if others:
        st.markdown("### 👀 Also keep an eye on")
        st.markdown(" ".join(style.pill(a["label"], "lav") for a in others), unsafe_allow_html=True)
