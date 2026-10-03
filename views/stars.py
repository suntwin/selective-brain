import pandas as pd
import plotly.express as px
import streamlit as st

from sb import data, gamify as g, style
from sb.style import esc


def render():
    kid = data.child()
    s = data.stats(kid["id"])
    lvl = s["level"]
    st.markdown("## 🏆 My Stars")
    style.card(f'<div style="display:flex;align-items:center;gap:16px"><div style="font-size:60px">{lvl["icon"]}</div>'
               f'<div style="flex:1"><h2 style="margin:0">Level {lvl["num"]} · {lvl["name"]}</h2>'
               f'<div class="sb-sub">{s["xp"]} XP total</div><div style="margin-top:8px">{style.bar(lvl["pct"])}</div></div></div>',
               "sb-hero")

    st.markdown("### 🎖️ Badges")
    have = data.badges(kid["id"])
    st.markdown("".join(
        f'<div class="sb-badge {"" if k in have else "locked"}" title="{esc(desc)}"><div class="ic">{ic}</div>{esc(name)}'
        f'<div class="sb-small" style="font-size:.66rem">{esc(desc)}</div></div>'
        for k, (ic, name, desc) in g.BADGES.items()), unsafe_allow_html=True)

    st.markdown("### 🪜 Level road")
    st.markdown(" ".join(
        style.pill(f"{ic} {i + 1}. {name} ({need})", "pink" if i + 1 <= lvl["num"] else "lav")
        for i, (need, name, ic) in enumerate(g.LEVELS)), unsafe_allow_html=True)

    ans = s["answers"]
    if ans:
        st.markdown("### ⏱️ My speed (seconds per question)")
        df = pd.DataFrame(ans)
        df["day"] = df["created_at"].map(lambda t: g.to_local_date(t))
        daily = df.groupby("day").agg(sec=("seconds", "median"), acc=("correct", "mean")).reset_index()
        daily["acc"] = (daily["acc"] * 100).round()
        fig = px.line(daily, x="day", y="sec", markers=True)
        fig.update_traces(line_color="#ff4fa0", marker=dict(size=10, color="#9b7bff"))
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(255,255,255,.6)", yaxis_title="median seconds", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        best = daily["sec"].min()
        st.caption(f"🏅 Personal best day: {best:.0f} s per question. Lower is faster!")
        st.markdown("### 🎯 Accuracy by day (%)")
        fig2 = px.bar(daily, x="day", y="acc")
        fig2.update_traces(marker_color="#38d9c9")
        fig2.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(255,255,255,.6)", yaxis_range=[0, 100], xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    ev = data.xp_events(kid["id"])[-12:][::-1]
    if ev:
        st.markdown("### ✨ Recent XP")
        st.markdown("".join(style.pill(f'+{e["amount"]} {e["reason"]}', "gold") for e in ev), unsafe_allow_html=True)
