"""🎁 Reward Shop: swap XP for books, tennis treats and outings. Bookshelf + book wishlist. Parent catalogue editor."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sb import data, routine as rt, style
from sb.style import esc

SPINES = ["#f7a8d8", "#b9a7ff", "#8fd9e8", "#ffd27a", "#a6e3b8", "#ff9fb2", "#c5b3ff", "#9ad0ff"]
STATE = {"requested": ("⏳", "Waiting for Mum or Papa"), "given": ("🎁", "Got it!"), "declined": ("↩️", "XP given back")}


def render():
    me, kid = data.me(), data.child()
    is_child = me["role"] == "child"
    st.markdown("## 🎁 Reward Shop")
    if not rt.ready():
        st.info(f"The shop isn't open yet. Papa needs to run `{rt.SQL_FILE}` once in Supabase → SQL Editor.")
        return
    w = rt.wallet(kid["id"])
    gl = rt.goal(kid["id"])
    goal_html = ""
    if gl:
        pct = min(1.0, w["balance"] / max(1, int(gl["cost"])))
        left = max(0, int(gl["cost"]) - w["balance"])
        goal_html = (f'<div style="margin-top:10px" class="sb-small">🎯 My goal: {esc(gl.get("emoji") or "")} '
                     f'<b>{esc(gl["title"])}</b> · {"ready to swap! 🎉" if not left else f"{left:,} XP to go"}</div>'
                     f'<div style="margin-top:4px">{style.bar(pct)}</div>')
    style.card(
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;align-items:center">'
        f'<div><div class="sb-sub">{"My" if is_child else "Her"} wallet</div>'
        f'<h1 style="margin:0">🪙 {w["balance"]:,} XP</h1>'
        f'<div class="sb-small">Earned {w["earned"]:,} · waiting {w["held"]:,} · spent {w["spent"]:,}. '
        f'Spending never lowers your level.</div></div><div style="font-size:52px">📚</div></div>{goal_html}', "sb-hero")
    t1, t2, t3, t4 = st.tabs(["🛍️ Shop", "📦 My swaps", "📚 My bookshelf", "📝 Book wishlist"])
    with t1:
        _shop(kid, is_child, w, gl)
    with t2:
        _swaps(kid, is_child)
    with t3:
        _shelf(kid)
    with t4:
        _wishlist(kid, is_child)


def _shop(kid, is_child, w, gl):
    items = rt.rewards()
    if not items:
        st.caption("The shop is empty. Papa can add rewards in Parent Hub → 🗓️ Routine & rewards → 🎁 Rewards.")
        return
    cats = ["All"] + [c for c in rt.CATEGORIES if any(r.get("category") == c for r in items)]
    cat = st.segmented_control("Show", cats, default="All", key="shop_cat",
                               format_func=lambda c: c if c == "All" else f"{rt.CATEGORIES[c]} {c}") or "All"
    items = [r for r in items if cat == "All" or r.get("category") == cat]
    wish = [x for x in rt.wishlist(kid["id"]) if x.get("status") != "got"]
    cols = st.columns(3)
    for i, r in enumerate(items):
        cost = int(r["cost"])
        bal = w["balance"]
        can = bal >= cost
        is_goal = bool(gl) and gl["id"] == r["id"]
        with cols[i % 3], st.container(key=f"rw_{i}"):
            style.card(
                f'<div style="text-align:center"><div style="font-size:44px">{esc(r.get("emoji") or "🎁")}</div>'
                f'<div style="font-weight:900;font-size:1.05rem;min-height:2.8em">{esc(r["title"])}</div>'
                f'<div style="font-size:1.25rem;font-weight:900;margin:.2rem 0">🪙 {cost:,} XP</div>'
                f'{style.bar(min(1.0, w["balance"] / max(1, cost)))}'
                f'<div class="sb-small" style="margin-top:4px">{"✨ You can swap this!" if can else f"{cost - bal:,} XP to go"}'
                f'{" · 🎯 my goal" if is_goal else ""}</div></div>')
            if not is_child:
                continue
            c1, c2 = st.columns(2)
            if c1.button("🎯 Unpin" if is_goal else "🎯 Goal", key=f"goal_{r['id']}", use_container_width=True,
                         type="tertiary"):
                rt.set_goal(None if is_goal else r["id"])
                st.rerun()
            with c2.popover("Swap 🎁", use_container_width=True, disabled=not can):
                note = ""
                if r.get("ask_book"):
                    titles = [x["title"] + (f" by {x['author']}" if x.get("author") else "") for x in wish]
                    pick = st.selectbox("Which book?", titles + ["Something else…"], index=None,
                                        key=f"bk_{r['id']}", placeholder="Pick from my wishlist")
                    if pick == "Something else…" or not titles:
                        pick = st.text_input("Book title (and author)", key=f"bt_{r['id']}")
                    note = pick or ""
                else:
                    note = st.text_input("Anything Mum or Papa should know? (optional)", key=f"nt_{r['id']}")
                st.markdown(f"Swap **{cost:,} XP** for **{style.md(r['title'])}**?")
                if st.button("Yes, swap it! 🎉", key=f"sw_{r['id']}",
                             disabled=bool(r.get("ask_book")) and not note.strip()):
                    err = rt.request(r, note)
                    if err:
                        st.warning(err)
                    else:
                        if is_goal:
                            rt.set_goal(None)
                        style.sparkle_burst(f"sw{r['id']}")
                        st.toast("Swap sent! Mum or Papa will hand it over 🎁")
                        st.rerun()


def _swaps(kid, is_child):
    reds = rt.redemptions(kid["id"])
    if not reds:
        st.caption("No swaps yet. Save up for something lovely ✨")
        return
    for r in reds:
        ic, lab = STATE.get(r["status"], ("•", r["status"]))
        when = str(r.get("created_at"))[:10]
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown(f'{esc(r.get("emoji") or "🎁")} **{style.md(r["title"])}**'
                    + (f' · _{style.md(r["note"])}_' if r.get("note") else "")
                    + f' · {int(r["cost"]):,} XP · {ic} {lab} · {when}'
                    + (f'<br><span class="sb-small">💬 {esc(r["parent_note"])}</span>' if r.get("parent_note") else ""),
                    unsafe_allow_html=True)
        if is_child and r["status"] == "requested":
            if c2.button("Cancel", key=f"cx_{r['id']}", type="tertiary", use_container_width=True):
                rt.cancel(r)
                st.rerun()


def _shelf(kid):
    books = rt.bookshelf(kid["id"])
    if not books:
        style.card('<div class="sb-title" style="font-size:1.2rem">📚 My bookshelf is waiting…</div>'
                   '<div class="sb-small">Every book you earn in the shop gets a spine here. '
                   'Fill a shelf, then another!</div>')
        return
    spines = ""
    for i, b in enumerate(books):
        col = SPINES[i % len(SPINES)]
        h = 150 + (i * 37) % 50
        spines += (f'<div class="bk-spine" style="background:{col};height:{h}px" title="{esc(b["note"])}">'
                   f'<span>{esc(b["note"][:38])}</span></div>')
    st.markdown(f'<div class="bk-shelf">{spines}</div><div class="bk-plank"></div>'
                f'<div class="sb-small" style="margin-top:6px">{len(books)} book(s) earned with XP 💖</div>',
                unsafe_allow_html=True)


def _wishlist(kid, is_child):
    st.caption("Books I'd love next. Mum and Papa can see this list too.")
    if is_child:
        with st.form("wish_add", clear_on_submit=True):
            c1, c2 = st.columns([2, 1.3])
            t = c1.text_input("Book title")
            a = c2.text_input("Author (optional)")
            if st.form_submit_button("Add to my wishlist 📝") and t.strip():
                rt.add_wish(t, a)
                st.rerun()
    wl = rt.wishlist(kid["id"])
    if not wl:
        st.caption("Nothing on the list yet.")
    for x in wl:
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        c1.markdown(f'📖 **{style.md(x["title"])}**' + (f' · {style.md(x["author"])}' if x.get("author") else ""))
        if is_child and c2.button("Remove", key=f"wr_{x['id']}", type="tertiary", use_container_width=True):
            rt.remove_wish(x["id"])
            st.rerun()


# ---------------------------------------------------------------- Parent Hub: requests + catalogue
def render_parent(kid):
    w = rt.wallet(kid["id"])
    st.markdown(f"**Her wallet:** 🪙 {w['balance']:,} XP (earned {w['earned']:,} · waiting {w['held']:,} · "
                f"spent {w['spent']:,})")
    reqs = [r for r in rt.redemptions(kid["id"]) if r["status"] == "requested"]
    st.markdown(f"#### 🎁 Swaps to hand over ({len(reqs)})")
    if not reqs:
        st.caption("None waiting.")
    for r in reqs:
        c1, c2, c3 = st.columns([3.2, 1, 1], vertical_alignment="center")
        c1.markdown(f'{esc(r.get("emoji") or "🎁")} **{style.md(r["title"])}**'
                    + (f' · **{style.md(r["note"])}**' if r.get("note") else "")
                    + f' · {int(r["cost"]):,} XP · asked {str(r.get("created_at"))[:10]}')
        with c2.popover("Given 🎁", use_container_width=True):
            note = st.text_input("Note for her (optional)", key=f"gn_{r['id']}", placeholder="Enjoy it! 💖")
            if st.button("Mark as given", key=f"gv_{r['id']}"):
                rt.give(r, note)
                st.rerun()
        with c3.popover("Decline", use_container_width=True):
            note = st.text_input("Why? (she sees this; her XP comes back)", key=f"dn_{r['id']}")
            if st.button("Decline + refund", key=f"dc_{r['id']}"):
                rt.refuse(r, note)
                st.rerun()
    wl = [x for x in rt.wishlist(kid["id"])]
    if wl:
        with st.expander(f"📝 Her book wishlist ({len(wl)})"):
            for x in wl:
                st.markdown(f'- {style.md(x["title"])}' + (f' · {style.md(x["author"])}' if x.get("author") else ""))
    st.markdown("#### 🛍️ Shop catalogue")
    items = rt.rewards(include_hidden=True)
    if not items:
        if st.button("Add the starter rewards (books, tennis, treats)"):
            rt.seed_rewards()
            st.rerun()
        return
    st.caption("Edit in the table, add a row at the bottom, or delete a row. Untick **show** to hide a reward. "
               "**ask book** = she types which book when she swaps. Past swaps keep their title and price.")
    df = pd.DataFrame([{"id": r["id"], "emoji": r.get("emoji") or "🎁", "title": r["title"],
                        "category": r.get("category") or "Treats", "cost": int(r.get("cost") or 0),
                        "ask book": bool(r.get("ask_book")), "show": bool(r.get("active", True))} for r in items])
    ed = st.data_editor(
        df, key="rw_edit", num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "id": None,
            "emoji": st.column_config.TextColumn("emoji", width="small"),
            "title": st.column_config.TextColumn("title", width="large", required=True),
            "category": st.column_config.SelectboxColumn("category", options=list(rt.CATEGORIES), required=True),
            "cost": st.column_config.NumberColumn("cost (XP)", min_value=0, step=50, required=True),
            "ask book": st.column_config.CheckboxColumn("ask book"),
            "show": st.column_config.CheckboxColumn("show"),
        })
    if st.button("Save the shop 💾"):
        s, fam = data.store(), data.me()["family_id"]
        keep = set()
        for i, row in ed.iterrows():
            title = str(row.get("title") or "").strip()
            if not title:
                continue
            fields = {"emoji": str(row.get("emoji") or "🎁").strip() or "🎁", "title": title,
                      "category": row.get("category") or "Treats", "cost": int(row.get("cost") or 0),
                      "ask_book": bool(row.get("ask book")), "active": bool(row.get("show", True)), "sort": int(i)}
            rid = row.get("id")
            if isinstance(rid, str) and rid:
                s.update("rewards", {"id": rid}, fields)
                keep.add(rid)
            else:
                keep.add(s.insert("rewards", {"family_id": fam, **fields})["id"])
        for r in items:
            if r["id"] not in keep:
                s.delete("rewards", {"id": r["id"]})
        st.success("Shop saved ✨")
        st.rerun()
