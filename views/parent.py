import io
import json
import zipfile
from collections import Counter
from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from sb import data, drillspec, gamify as g, style
from sb.store import now_iso


def render():
    kid = data.child()
    st.markdown(f"## 🧭 Parent Hub · {kid['display_name']}")
    t1, t2, t3, t4 = st.tabs(["📈 This week", "🪄 Publish a drill", "📤 Export to vault", "⚙️ Settings"])
    with t1:
        _week(kid)
    with t2:
        _publish()
    with t3:
        _export(kid)
    with t4:
        _reset(kid)
        st.divider()
        _settings(kid)


# ---------------------------------------------------------------- weekly review
def _week(kid):
    s = data.stats(kid["id"])
    since = g.today() - timedelta(days=6)
    att = [a for a in s["attempts"] if a.get("finished_at") and g.to_local_date(a["finished_at"]) >= since]
    ans = [a for a in s["answers"] if g.to_local_date(a["created_at"]) >= since]
    cis = [c for c in s["checkins"] if g.to_local_date(c["day"]) >= since]
    acc = (sum(1 for a in ans if a["correct"]) / len(ans)) if ans else None
    secs = sorted(a["seconds"] for a in ans if a.get("seconds"))
    c = st.columns(5)
    c[0].metric("Drills (7 days)", len(att))
    c[1].metric("Check-ins", f"{len(cis)}/7")
    c[2].metric("Accuracy", f"{acc * 100:.0f}%" if acc is not None else "—")
    c[3].metric("Median s/question", secs[len(secs) // 2] if secs else "—")
    c[4].metric("Streak", f"{s['streak']['current']} 🔥")
    st.caption(f"Level {s['level']['num']} {s['level']['name']} · {s['xp']} XP · "
               f"{g.days_to_exam(kid.get('exam_date'))} days to exam")

    if ans:
        df = pd.DataFrame(ans)
        tdf = df.groupby("topic").agg(n=("correct", "size"), acc=("correct", "mean")).reset_index()
        tdf["acc"] = (tdf["acc"] * 100).round()
        tdf["label"] = tdf["topic"].map(lambda t: g.TOPIC_LABEL.get(t, t))
        fig = px.bar(tdf.sort_values("acc"), x="acc", y="label", orientation="h", text="n",
                     color="acc", color_continuous_scale=["#ff5b7a", "#ffb23d", "#22c08a"], range_color=[40, 100])
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title="Accuracy by topic this week (bar label = questions)",
                          coloraxis_showscale=False, xaxis_range=[0, 100], xaxis_title="%", yaxis_title=None,
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    wrong = [a for a in ans if not a["correct"]]
    rc = Counter(a.get("reason") or "untagged" for a in wrong)
    l, r = st.columns(2)
    with l:
        st.markdown("**Top mistake reasons**")
        if rc:
            for k, n in rc.most_common(4):
                st.markdown(f"- {drillspec.REASON_TXT.get(k, k)}: **{n}**")
        else:
            st.caption("No mistakes logged this week.")
    with r:
        st.markdown("**Did the plan happen?**")
        for i in range(6, -1, -1):
            d = g.today() - timedelta(days=i)
            ci = next((c for c in cis if g.to_local_date(c["day"]) == d), None)
            did = [a for a in att if g.to_local_date(a["finished_at"]) == d]
            mark = "✅" if did else ("🛌" if ci and ci.get("session_size") == "Rest" else ("☑️ check-in only" if ci else "·"))
            extra = " · ".join(f"{a['score']}/{a['total']}" for a in did)
            st.markdown(f"{d.strftime('%a %d %b')}: {mark} {extra}")

    nb = [n for n in s["notebook"] if g.to_local_date(n.get("created_at")) and g.to_local_date(n["created_at"]) >= since]
    if nb:
        with st.expander(f"📒 {len(nb)} notebook card(s) she wrote this week"):
            for n in nb:
                st.markdown(style.md(f"- **{n['title']}** · _{n.get('reason') or n['kind']}_: {n.get('my_fix') or n.get('technique') or ''}"))
    st.info("Weekly 15-min review together: celebrate the streak and badges first, then pick 1–2 red topics for next week's drills.")


# ---------------------------------------------------------------- publish
def _publish():
    st.markdown("Upload a drill JSON (Claude builds these from the Obsidian vault into `Practice/App_Drills/`).")
    up = st.file_uploader("Drill file(s)", type=["json"], accept_multiple_files=True)
    pasted = st.text_area("…or paste JSON", height=120)
    payloads = []
    for f in up or []:
        try:
            payloads.append(json.loads(f.getvalue().decode("utf-8")))
        except Exception as e:
            st.error(f"{f.name}: not valid JSON ({e})")
    if pasted.strip():
        try:
            payloads.append(json.loads(pasted))
        except Exception as e:
            st.error(f"Pasted text is not valid JSON ({e})")
    ok = []
    for d in payloads:
        errs = drillspec.validate(d)
        with st.expander(f"{'✅' if not errs else '⚠️'} {d.get('title', '?')} — {len(d.get('questions', []))} questions",
                         expanded=bool(errs)):
            if errs:
                for e in errs:
                    st.error(e)
            else:
                topics = Counter(q["topic"] for q in d["questions"])
                st.write({g.TOPIC_LABEL.get(k, k): v for k, v in topics.items()})
                for q in d["questions"][:3]:
                    st.markdown(style.md(f"- {q['stem'][:140]}"))
                ok.append(d)
    if ok and st.button(f"Publish {len(ok)} drill(s) 🚀", use_container_width=True):
        fam = data.me()["family_id"]
        for d in ok:
            row = {k: d.get(k) for k in ("id", "title", "drill_date", "minutes", "pace_seconds", "subject",
                                         "focus", "questions", "source_note")}
            row.update({"family_id": fam, "status": "published", "minutes": d.get("minutes", 40),
                        "pace_seconds": d.get("pace_seconds", 90), "subject": d.get("subject", "Maths"),
                        "focus": d.get("focus", [])})
            data.store().upsert("drills", row, on_conflict="id")
        st.success("Published! She'll see it on her Home page.")

    st.divider()
    st.markdown("**Published drills**")
    for d in data.drills(include_archived=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"`{d['drill_date']}` **{d['title']}** · {len(d['questions'])} Qs · _{d['status']}_")
        if d["status"] == "published" and c2.button("Archive", key=f"arch_{d['id']}", type="tertiary"):
            data.store().update("drills", {"id": d["id"]}, {"status": "archived"})
            st.rerun()
        if d["status"] == "archived" and c2.button("Restore", key=f"rest_{d['id']}", type="tertiary"):
            data.store().update("drills", {"id": d["id"]}, {"status": "published"})
            st.rerun()


# ---------------------------------------------------------------- export
def _export(kid):
    st.markdown("Download finished drills as Markdown for `Practice/Results/` in the vault. Claude then folds the "
                "mistakes into `Mistake_Tracker` and `Maths_Brain` and builds the next drill.")
    att = [a for a in data.attempts(kid["id"]) if a.get("finished_at")]
    show_all = st.toggle("Include already-exported", value=False)
    if not show_all:
        att = [a for a in att if not a.get("exported_at")]
    if not att:
        st.caption("Nothing new to export.")
        return
    drills = {d["id"]: d for d in data.drills(include_archived=True)}
    cis = {str(c["day"])[:10]: c for c in data.checkins(kid["id"])}
    files = {}
    for a in att[::-1]:
        d = drills.get(a["drill_id"])
        if not d:
            continue
        day = g.to_local_date(a["finished_at"])
        md = drillspec.attempt_markdown(d, a, data.attempt_answers(a["id"]), cis.get(str(day)))
        name = f"Result_{day}_{d['id']}_{a['id'][:6]}.md"
        files[name] = md
        with st.expander(f"{day} · {d['title']} · {a['score']}/{a['total']}"):
            st.markdown(style.md(md))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, md in files.items():
            z.writestr(n, md)
        z.writestr("notebook_export.json", json.dumps(data.notebook(kid["id"]), indent=1, default=str))
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Download results (.zip)", buf.getvalue(), file_name=f"selective_brain_results_{g.today()}.zip",
                       mime="application/zip", use_container_width=True)
    if c2.button("Mark these as exported ✅", use_container_width=True, type="tertiary"):
        for a in att:
            data.store().update("attempts", {"id": a["id"]}, {"exported_at": now_iso()})
        st.rerun()


def _reset(kid):
    st.markdown("#### 🧹 Reset test data")
    st.caption("Use this after trying things out. It can't be undone.")
    uid = kid["id"]
    att = data.attempts(uid)
    drills = {d["id"]: d["title"] for d in data.drills(include_archived=True)}
    tried = sorted({a["drill_id"] for a in att})
    s = data.store()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Reset one drill**")
        st.caption("Removes her attempts and answers for that drill, and the notebook cards made from it, "
                   "so it shows as NEW again. XP and badges stay.")
        pick = st.selectbox("Drill", tried, format_func=lambda i: drills.get(i, i), key="reset_pick",
                            index=None, placeholder="Choose a drill she has tried")
        ok1 = st.checkbox("Yes, reset this drill", key="reset_ok1")
        if st.button("Reset drill", disabled=not (pick and ok1), use_container_width=True):
            for a in [a for a in att if a["drill_id"] == pick]:
                s.delete("answers", {"attempt_id": a["id"]})
                s.delete("attempts", {"id": a["id"]})
            s.delete("notebook", {"user_id": uid, "source": pick})
            st.session_state.pop("run", None)
            st.success("Done. That drill is fresh again.")
            st.rerun()
    with c2:
        st.markdown("**Start completely fresh**")
        st.caption("Wipes ALL her attempts, answers, notebook cards, XP, badges and check-ins. "
                   "Drills you've published stay.")
        word = st.text_input("Type RESET to confirm", key="reset_word")
        if st.button("Wipe everything", disabled=word.strip() != "RESET", use_container_width=True):
            for a in att:
                s.delete("answers", {"attempt_id": a["id"]})
            for t in ("attempts", "notebook", "xp_events", "badges", "checkins"):
                s.delete(t, {"user_id": uid})
            st.session_state.pop("run", None)
            st.success("All clean ✨ She starts at Level 1 with a fresh streak.")
            st.rerun()


def _settings(kid):
    st.markdown(f"**Exam date** (estimate until ACER publishes 2028-entry dates): `{kid.get('exam_date')}`")
    st.caption("To change it, edit `exam_date` on her row in Supabase → profiles.")
    st.markdown("**XP rules**")
    st.json(g.XP, expanded=False)
