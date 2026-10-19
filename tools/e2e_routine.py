"""End-to-end test of My Routine + Reward Shop in demo mode (start streamlit on a fresh .demo_data.json first).
Run on a Monday-to-Friday (needs blocks today). Checks XP sums from .demo_data.json."""
import os, json, uuid
from playwright.sync_api import sync_playwright
URL=os.environ.get("URL","http://localhost:8501"); OUT="/tmp/claude-0/rt_shots"; os.makedirs(OUT,exist_ok=True); errs=[]
DB=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),".demo_data.json")
def wait(p,ms=1300):
    p.wait_for_timeout(ms)
    try: p.wait_for_selector('[data-testid="stStatusWidget"]',state="detached",timeout=10000)
    except Exception: pass
    p.wait_for_timeout(500)
def shot(p,n,full=False):
    p.screenshot(path=f"{OUT}/{n}.png",full_page=full)
    e=p.locator('[data-testid="stException"]')
    if e.count(): errs.append((n,e.first.inner_text()[:1500])); print("EXC",n,e.first.inner_text()[:1500])
def btn(p,name,exact=False): return p.get_by_role("button",name=name,exact=exact)
def link(p,name): p.get_by_role("link",name=name).click(); wait(p,1800)
def login(p,who): p.goto(URL); wait(p,3000); btn(p,who).click(); wait(p,2000)
def logout(p): btn(p,"Log out").click(); wait(p,2000)
def xp():
    d=json.load(open(DB)); kid=[x for x in d["profiles"] if x["role"]=="child"][0]["id"]
    return sum(int(e["amount"]) for e in d["xp_events"] if e["user_id"]==kid), [(e["amount"],e["reason"]) for e in d["xp_events"]]
with sync_playwright() as pw:
    b=pw.chromium.launch(); p=b.new_page(viewport={"width":1300,"height":950})
    login(p,"I'm Siyonah"); link(p,"My Routine")
    n=btn(p,"✅ Done!").count()
    for i in range(n):
        btn(p,"✅ Done!").first.click(); wait(p)
    shot(p,"a1_all_ticked",True)
    t1,ev=xp(); print("after ticking all today:",t1); print(ev)
    btn(p,"↩️ Undo").first.click(); wait(p)
    t2,ev=xp(); print("after undo one:",t2, ev[-2:])
    btn(p,"✅ Done!").first.click(); wait(p)
    t3,_=xp(); print("re-ticked:",t3)
    shot(p,"a2_retick")
    p.get_by_role("tab",name="🗓️ My week").click(); wait(p); shot(p,"a3_week")
    logout(p)
    login(p,"I'm Papa"); p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p); shot(p,"a4_her_ticks")
    p.get_by_role("button",name="Take back").first.click(); wait(p,700)
    p.get_by_label("Note for her (optional)").first.fill("We didn't do this one tonight")
    btn(p,"Take back the XP").first.click(); wait(p)
    t4,ev=xp(); print("parent took one back:",t4, ev[-2:])
    p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p)
    p.get_by_role("tab",name="⚙️ XP rules").click(); wait(p)
    p.get_by_text("XP the moment she ticks").click(); wait(p,500)
    btn(p,"Save XP rules").click(); wait(p); shot(p,"a5_rules_off")
    logout(p)
    login(p,"I'm Siyonah"); link(p,"My Routine")
    p.locator('[data-testid="stButtonGroup"] button:has-text("Yesterday")').first.click(); wait(p)
    if btn(p,"✅ Done!").count():
        btn(p,"✅ Done!").first.click(); wait(p)
    t5,_=xp(); print("ticked yesterday with approval ON (no XP yet):",t5)
    shot(p,"a6_waiting"); logout(p)
    login(p,"I'm Papa"); shot(p,"a7_banner")
    p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p)
    btn(p,"Confirm all").first.click(); wait(p)
    t6,ev=xp(); print("after confirm all:",t6, ev[-2:])
    link(p,"Her Stars"); shot(p,"a8_stars",True)
    print("ERRORS",len(errs))
