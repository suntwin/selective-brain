"""🗓️ My Routine: her weekly timetable, ticking blocks off, and changing the plan. Plus the Parent Hub tab."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from sb import data, gamify as g, nav, routine as rt, style
from sb.style import esc

STATUS = {
    None:       ("⭕", "Not ticked yet"),
    "done":     ("⏳", "Waiting for Mum or Papa to confirm"),
    "approved": ("✅", "Confirmed"),
    "declined": ("❌", "Not confirmed"),
    "skipped":  ("⏭️", "Skipped"),
    "excused":  ("🌿", "Excused"),
}
SKIP_REASONS = ["Not feeling well 🤒", "School event / excursion 🏫", "Family plans 👨‍👩‍👧", "No school work today 🎉",
                "Too tired 😴", "Other"]


def _not_ready():
    st.info(f"The routine isn't switched on yet. Papa needs to run `{rt.SQL_FILE}` once in Supabase → SQL Editor.")


# ---------------------------------------------------------------- page
def render():
    me, kid = data.me(), data.child()
    is_child = me["role"] == "child"
    if not rt.ready():
        st.markdown("## 🗓️ My Routine")
        _not_ready()
        return
    w = rt.wallet(kid["id"])
    st.markdown(f"## 🗓️ {'My' if is_child else 'Her'} Routine")
    style.card(
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">'
        f'<div><div class="sb-title" style="font-size:1.2rem">Tick each block when it\'s done ✨</div>'
        f'<div class="sb-small">Mum or Papa confirm it, then the XP lands in your wallet. Finish a whole day for a bonus, '
        f'and a whole week for a big one. Spend XP in the 🎁 Reward Shop on books and tennis treats.</div></div>'
        f'<div style="text-align:right"><div style="font-size:1.6rem;font-weight:900">🪙 {w["balance"]:,} XP</div>'
        f'<div class="sb-small">in {"my" if is_child else "her"} wallet</div></div></div>', "sb-hero")
    t1, t2, t3 = st.tabs(["📅 Today", "🗓️ My week", "✏️ Change my routine"])
    with t1:
        _today(kid, is_child)
    with t2:
        _week(kid)
    with t3:
        _edit()


def _today(kid, is_child):
    st_ = rt.settings()
    back = int(st_.get("days_back", 1))
    opts = list(range(0, back + 1))
    labels = {0: "Today", 1: "Yesterday"}
    pick = st.segmented_control("Day", opts, default=0, key="rt_day",
                                format_func=lambda i: labels.get(i, f"{i} days ago")) or 0
    day = g.today() - timedelta(days=int(pick))
    all_b = rt.blocks()
    todays = rt.day_blocks(day, all_b)
    lm = rt.log_map(kid["id"], day, day)
    st.markdown(f"#### {rt.DAYS[day.weekday()]} {day.day} {day.strftime('%B')}")
    if not todays:
        style.card('<div class="sb-title" style="font-size:1.25rem">🌈 Free day!</div>'
                   '<div class="sb-small">Nothing on the plan. Read something lovely, play, rest. '
                   'You can add a block in ✏️ Change my routine if you want to.</div>')
        return
    req = [b for b in todays if not b.get("optional")]
    ok = sum(1 for b in req if lm.get((b["id"], str(day)), {}).get("status") in rt.OK_STATES)
    ticked = sum(1 for b in req if lm.get((b["id"], str(day)), {}).get("status") in ("done",) + rt.OK_STATES)
    full = rt.day_complete(day, lm, all_b)
    st.markdown(f'{style.bar(ticked / len(req) if req else 1)}'
                f'<div class="sb-small" style="margin:.3rem 0 .8rem">{ticked} of {len(req)} ticked · {ok} confirmed'
                f'{" · 🌟 whole day done, +" + str(st_["day_bonus"]) + " XP bonus!" if full else " · finish them all for +" + str(st_["day_bonus"]) + " XP"}'
                f'</div>', unsafe_allow_html=True)
    for b in todays:
        _block_row(b, day, lm.get((b["id"], str(day))), is_child, kid, st_)


def _block_row(b, day, log, is_child, kid, st_):
    status = (log or {}).get("status")
    icon, what = STATUS.get(status, STATUS[None])
    xp = (log or {}).get("xp") if log else rt.block_xp(b, st_)
    extra = ""
    if status == "skipped" and log.get("note"):
        extra = f" · {esc(log['note'])}"
    if log and log.get("parent_note"):
        extra += f'<div class="sb-small">💬 {esc(log["parent_note"])}</div>'
    opt = style.pill("only if needed", "gold") if b.get("optional") else ""
    c1, c2 = st.columns([3, 1.25], vertical_alignment="center")
    c1.markdown(
        f'<div class="sb-card" style="padding:.7rem 1rem;margin:0">'
        f'<div style="display:flex;gap:12px;align-items:center">'
        f'<div style="font-size:2rem">{rt.emoji(b["kind"])}</div>'
        f'<div><div style="font-weight:900;font-size:1.08rem">{esc(b["title"])} {opt}</div>'
        f'<div class="sb-small">🕒 {esc(rt.time_label(b))} · ✨ +{xp} XP · {icon} {what}{extra}</div></div></div></div>',
        unsafe_allow_html=True)
    k = f"{b['id']}_{day}"
    with c2:
        if is_child:
            if status is None or status == "declined":
                if st.button("✅ Done!", key=f"tick_{k}", use_container_width=True):
                    rt.tick(b, day)
                    st.toast(f"Ticked {b['title']} ⏳ Mum or Papa will confirm it")
                    st.rerun()
                with st.popover("Skip…", use_container_width=True):
                    why = st.radio("Why are you skipping it?", SKIP_REASONS, key=f"why_{k}", index=None)
                    more = st.text_input("Anything else?", key=f"more_{k}") if why == "Other" else ""
                    if st.button("Save", key=f"skip_{k}", disabled=not why):
                        rt.skip(b, day, more if why == "Other" and more.strip() else why)
                        st.rerun()
            elif status in ("done", "skipped"):
                if st.button("↩️ Undo", key=f"undo_{k}", use_container_width=True, type="tertiary"):
                    rt.undo(log)
                    st.rerun()
        else:
            if status == "done":
                if st.button("Confirm ✅", key=f"ok_{k}", use_container_width=True):
                    for m in rt.confirm(log):
                        st.toast(m)
                    st.rerun()
                if st.button("Not done ❌", key=f"no_{k}", use_container_width=True, type="tertiary"):
                    rt.decline(log)
                    st.rerun()
            elif status in (None, "skipped", "declined"):
                if st.button("Excuse 🌿", key=f"ex_{k}", use_container_width=True, type="tertiary",
                             help="Let her off this one (sick, school event…). No XP, but it still counts for the "
                                  "whole-day and whole-week bonus."):
                    for m in rt.excuse(b, day, kid["id"]):
                        st.toast(m)
                    st.rerun()


# ---------------------------------------------------------------- week
def _week_grid(kid, ws):
    all_b = rt.blocks()
    s = rt.week_summary(kid["id"], ws)
    lm = s["map"]
    today = g.today()
    cols = ""
    for i in range(7):
        d = ws + timedelta(days=i)
        bl = rt.day_blocks(d, all_b)
        full = rt.day_complete(d, lm, all_b)
        chips = ""
        for b in bl:
            lg = lm.get((b["id"], str(d)))
            ic = STATUS.get((lg or {}).get("status"), STATUS[None])[0]
            if lg is None and d < today and not b.get("optional"):
                ic = "▫️"
            t = rt.time_label(b).split(" – ")[0]
            chips += (f'<div class="rt-chip{" opt" if b.get("optional") else ""}">{ic} {rt.emoji(b["kind"])} '
                      f'<b>{esc(b["title"])}</b><span>{esc(t)}</span></div>')
        if not bl:
            chips = '<div class="rt-free">🌈 Free day</div>'
        head = f'{rt.SHORT[i]} {d.day}' + (" 🌟" if full else "")
        cols += (f'<div class="rt-day{" today" if d == today else ""}"><div class="rt-head">{head}</div>{chips}</div>')
    st.markdown(f'<div class="rt-week">{cols}</div>', unsafe_allow_html=True)
    return s


def _week(kid):
    off = st.session_state.get("rt_week_off", 0)
    ws = rt.week_start(g.today()) + timedelta(weeks=off)
    c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="center")
    if c1.button("◀ Week before", key="rt_prev", use_container_width=True, type="tertiary"):
        st.session_state.rt_week_off = off - 1
        st.rerun()
    label = "This week" if off == 0 else ("Last week" if off == -1 else f"Week of {ws.day} {ws.strftime('%b')}")
    c2.markdown(f'<div style="text-align:center;font-weight:900;font-size:1.15rem">{label} · '
                f'{ws.day} {ws.strftime("%b")} – {(ws + timedelta(days=6)).day} {(ws + timedelta(days=6)).strftime("%b")}'
                f'</div>', unsafe_allow_html=True)
    if c3.button("Week after ▶", key="rt_next", use_container_width=True, type="tertiary", disabled=off >= 0):
        st.session_state.rt_week_off = off + 1
        st.rerun()
    s = _week_grid(kid, ws)
    st_ = rt.settings()
    pct = s["done"] / s["required"] if s["required"] else 0
    st.markdown(
        '<div class="sb-stat">'
        f'<div class="box"><div class="big">✅ {s["done"]}/{s["required"]}</div><div class="lbl">blocks confirmed</div></div>'
        f'<div class="box"><div class="big">⏳ {s["waiting"]}</div><div class="lbl">waiting to confirm</div></div>'
        f'<div class="box"><div class="big">🌟 {s["days_full"]}</div><div class="lbl">whole days done</div></div>'
        f'<div class="box"><div class="big">✨ {s["xp"]}</div><div class="lbl">routine XP (plus bonuses)</div></div>'
        '</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="margin-top:.6rem">{style.bar(pct)}</div>'
                f'<div class="sb-small">Whole week: +{st_["week_bonus"]} XP when every block is done or excused. '
                '⭕ not ticked · ⏳ waiting · ✅ confirmed · ⏭️ skipped · 🌿 excused · ▫️ missed</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- edit
def _edit():
    st_ = rt.settings()
    st.caption("Change the plan any time: move a block, add one, or take one away. "
               "Ticks you've already made stay in your history.")
    all_b = rt.blocks()
    wd = st.segmented_control("Day", list(range(7)), default=g.today().weekday(), key="rt_edit_day",
                              format_func=lambda i: rt.SHORT[i])
    wd = g.today().weekday() if wd is None else wd
    mine = [b for b in all_b if int(b["weekday"]) == wd]
    st.markdown(f"#### {rt.DAYS[wd]}")
    if not mine:
        st.caption("Nothing planned. A free day 🌈")
    for b in mine:
        c1, c2, c3 = st.columns([4, 1, 1], vertical_alignment="center")
        c1.markdown(f'{rt.emoji(b["kind"])} **{style.md(b["title"])}** · {esc(rt.time_label(b))} · +{rt.block_xp(b, st_)} XP'
                    + (" · _only if needed_" if b.get("optional") else ""), unsafe_allow_html=True)
        with c2.popover("✏️", use_container_width=True):
            _block_form(f"e_{b['id']}", b)
        with c3.popover("🗑️", use_container_width=True):
            st.markdown(f"Remove **{style.md(b['title'])}** from {rt.DAYS[wd]}s?")
            if st.button("Yes, remove it", key=f"rm_{b['id']}"):
                rt.remove_block(b["id"])
                st.rerun()
    st.write("")
    with st.expander("➕ Add a block", expanded=not mine):
        _block_form(f"add_{wd}", None, wd)
    if mine:
        with st.expander(f"📋 Copy {rt.DAYS[wd]} to other days"):
            tgt = st.multiselect("Copy to", [i for i in range(7) if i != wd], format_func=lambda i: rt.DAYS[i],
                                 key=f"cp_{wd}")
            st.caption("The blocks are added on top of what's already there.")
            if st.button("Copy", key=f"cpb_{wd}", disabled=not tgt):
                n = rt.copy_day(wd, tgt)
                st.toast(f"Copied {n} block(s) ✨")
                st.rerun()
    with st.expander("↩️ Start again from the paper timetable"):
        st.caption("Replaces the whole week with the timetable Siyonah and Mum wrote on paper (19 Oct 2026).")
        ok = st.checkbox("Yes, replace my whole routine", key="rt_reset_ok")
        if st.button("Replace", key="rt_reset", disabled=not ok):
            rt.seed_routine(replace=True)
            st.rerun()


def _block_form(key, b=None, wd=None):
    st_ = rt.settings()
    kinds = list(rt.KINDS)
    with st.form(key, border=False):
        if b is None:
            days = st.multiselect("Which days?", list(range(7)), default=[wd], format_func=lambda i: rt.DAYS[i])
        kind = st.selectbox("What is it?", kinds, index=kinds.index(b["kind"]) if b and b["kind"] in kinds else 0,
                            format_func=lambda k: f"{rt.KINDS[k][0]} {k}")
        title = st.text_input("Name (optional)", value=b["title"] if b else "",
                              placeholder="e.g. Maths with Preetha's mum")
        anytime = st.checkbox("No set time (e.g. a tennis match)", value=bool(b) and not b.get("start_time"))
        c1, c2 = st.columns(2)
        start = c1.time_input("Starts", value=rt.to_time((b or {}).get("start_time") or "16:30"), step=900)
        end = c2.time_input("Ends", value=rt.to_time((b or {}).get("end_time") or "18:00"), step=900)
        optional = st.checkbox("Only if needed (like school work 'if any'). Doesn't stop the whole-day bonus.",
                               value=bool((b or {}).get("optional")))
        preview = {"kind": kind, "start_time": None if anytime else rt.parse_hhmm(start),
                   "end_time": None if anytime else rt.parse_hhmm(end)}
        st.caption(f"Worth about +{rt.block_xp(preview, st_)} XP once confirmed.")
        if st.form_submit_button("Save ✨" if b else "Add it ✨", use_container_width=True):
            s, e = preview["start_time"], preview["end_time"]
            if s and e and s == e:
                st.warning("Start and end are the same time.")
                return
            name = title.strip() or kind
            if b:
                rt.update_block(b["id"], {"kind": kind, "title": name, "start_time": s, "end_time": e,
                                          "optional": optional})
            else:
                if not days:
                    st.warning("Pick at least one day.")
                    return
                for d in days:
                    rt.add_block(d, s, e, kind, name, optional)
            st.rerun()


# ---------------------------------------------------------------- Parent Hub tab
def render_parent(kid):
    if not rt.ready():
        _not_ready()
        return
    a, b, c, d = st.tabs(["✅ To confirm", "🗓️ Her week", "🎁 Rewards", "⚙️ XP rules"])
    with a:
        _confirm_list(kid)
    with b:
        _week(kid)
        st.caption("Tap 🗓️ Her Routine in the sidebar to see a day block by block, or to excuse a block.")
    with c:
        from views import shop
        shop.render_parent(kid)
    with d:
        _xp_rules()


def _confirm_list(kid):
    pend = rt.pending(kid["id"])
    if not pend:
        st.success("Nothing waiting. All her ticks are confirmed 🎉")
        return
    st.markdown(f"**{len(pend)} block(s) she ticked as done.** Confirm to pay her XP (day and week bonuses are added "
                "by themselves).")
    if st.button(f"Confirm all {len(pend)} ✅", key="rt_all"):
        msgs = []
        for lg in pend:
            msgs += rt.confirm(lg)
        for m in msgs[-6:]:
            st.toast(m)
        st.rerun()
    for lg in pend:
        day = pd.to_datetime(str(lg["day"])[:10]).date()
        c1, c2, c3 = st.columns([3.2, 1, 1], vertical_alignment="center")
        c1.markdown(f'{rt.emoji(lg.get("kind"))} **{style.md(lg.get("title"))}** · {rt.SHORT[day.weekday()]} {day.day} '
                    f'{day.strftime("%b")} · {lg.get("minutes") or "–"} min · +{lg.get("xp")} XP')
        if c2.button("Confirm", key=f"pc_{lg['id']}", use_container_width=True):
            for m in rt.confirm(lg):
                st.toast(m)
            st.rerun()
        with c3.popover("Not done", use_container_width=True):
            note = st.text_input("Note for her (optional)", key=f"pn_{lg['id']}")
            if st.button("Mark not done", key=f"pd_{lg['id']}"):
                rt.decline(lg, note)
                st.rerun()


def _xp_rules():
    s = rt.settings()
    st.caption("How much the routine pays. A normal school week (about 21 hours of study) comes to roughly "
               "550 XP with the defaults, on top of drill XP.")
    with st.form("rt_rules"):
        c1, c2 = st.columns(2)
        xph = c1.number_input("Study blocks: XP per hour", 0, 200, int(s["xp_per_hour"]), 5)
        act = c2.number_input("Tennis / swimming / match: XP per block", 0, 200, int(s["active_xp"]), 5)
        dayb = c1.number_input("Whole day done: bonus XP", 0, 500, int(s["day_bonus"]), 5)
        wkb = c2.number_input("Whole week done: bonus XP", 0, 1000, int(s["week_bonus"]), 5)
        back = c1.number_input("She can tick blocks up to … days back", 0, 3, int(s["days_back"]), 1)
        if st.form_submit_button("Save XP rules"):
            rt.save_settings({"xp_per_hour": int(xph), "active_xp": int(act), "day_bonus": int(dayb),
                              "week_bonus": int(wkb), "days_back": int(back)})
            st.success("Saved. New ticks use these numbers (already-ticked blocks keep theirs).")


def home_card(kid, is_child):
    """Small 'today's routine' card for Home."""
    try:
        if not rt.ready():
            return
        day = g.today()
        bl = rt.day_blocks(day)
        lm = rt.log_map(kid["id"], day, day)
        w = rt.wallet(kid["id"])
        gl = rt.goal(kid["id"])
    except Exception:
        return
    req = [b for b in bl if not b.get("optional")]
    ticked = sum(1 for b in req if lm.get((b["id"], str(day)), {}).get("status") in ("done", "approved", "excused"))
    nxt = next((b for b in bl if (b["id"], str(day)) not in lm), None)
    if bl:
        body = (f'<div class="sb-small">{ticked} of {len(req)} blocks ticked today'
                + (f' · next: {rt.emoji(nxt["kind"])} <b>{esc(nxt["title"])}</b> ({esc(rt.time_label(nxt))})' if nxt else " 🎉")
                + '</div>' + f'<div style="margin-top:6px">{style.bar(ticked / len(req) if req else 1)}</div>')
    else:
        body = '<div class="sb-small">🌈 Free day today. Enjoy it!</div>'
    goal_html = ""
    if gl:
        pct = min(1.0, w["balance"] / max(1, int(gl["cost"])))
        goal_html = (f'<div class="sb-small" style="margin-top:8px">🎯 Saving for {esc(gl.get("emoji") or "")} '
                     f'<b>{esc(gl["title"])}</b>: {w["balance"]:,} / {int(gl["cost"]):,} XP</div>'
                     f'<div style="margin-top:4px">{style.bar(pct)}</div>')
    style.card(f'<div class="sb-title" style="font-size:1.15rem">🗓️ Today\'s routine</div>{body}'
               f'<div class="sb-small" style="margin-top:8px">🪙 Wallet: <b>{w["balance"]:,} XP</b></div>{goal_html}')
    c1, c2 = st.columns(2)
    if c1.button("My routine 🗓️" if is_child else "Her routine 🗓️", use_container_width=True, key="home_rt"):
        nav.go("routine")
    if c2.button("Reward Shop 🎁", use_container_width=True, key="home_shop", type="tertiary"):
        nav.go("shop")
