"""End-to-end test of My Routine + Reward Shop in demo mode (start streamlit on a fresh .demo_data.json first)."""
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
def scroll(p,y):
    p.evaluate(f"(()=>{{const m=document.querySelector('[data-testid=\"stMain\"]'); if(m) m.scrollTo(0,{y});}})()"); p.wait_for_timeout(500)
def btn(p,name,exact=False): return p.get_by_role("button",name=name,exact=exact)
def link(p,name): p.get_by_role("link",name=name).click(); wait(p,1800)
def login(p,who):
    p.goto(URL); wait(p,3000); btn(p,who).click(); wait(p,2000)
def logout(p):
    btn(p,"Log out").click(); wait(p,2000)
with sync_playwright() as pw:
    b=pw.chromium.launch(); p=b.new_page(viewport={"width":1300,"height":950})
    login(p,"I'm Siyonah"); shot(p,"01_home")
    link(p,"My Routine"); shot(p,"02_today")
    btn(p,"✅ Done!").nth(0).click(); wait(p)
    btn(p,"✅ Done!").nth(0).click(); wait(p)
    # skip the 3rd (now first remaining tick button's row) via popover
    p.get_by_role("button",name="Skip…").first.click(); wait(p,800)
    p.get_by_text("Family plans").first.click(); wait(p,600)
    btn(p,"Save",exact=True).first.click(); wait(p)
    shot(p,"03_today_ticked",True); scroll(p,500); shot(p,"03b_today_scrolled")
    # yesterday
    p.locator('[data-testid="stButtonGroup"] button:has-text("Yesterday")').first.click(); wait(p)
    btn(p,"✅ Done!").first.click(); wait(p); shot(p,"04_yesterday")
    p.get_by_role("tab",name="🗓️ My week").click(); wait(p); shot(p,"05_week")
    p.get_by_role("tab",name="✏️ Change my routine").click(); wait(p)
    p.locator('[data-testid="stButtonGroup"] button:has-text("Sat")').last.click(); wait(p)
    shot(p,"06_edit_sat")
    sel=p.locator('[data-testid="stSelectbox"]').last
    sel.click(); wait(p,600); p.get_by_role("option",name="📚 Reading").click(); wait(p,600)
    p.get_by_placeholder("e.g. Maths with Preetha's mum").last.fill("Reading for fun")
    btn(p,"Add it ✨").last.click(); wait(p)
    shot(p,"07_edit_added",True)
    link(p,"Reward Shop"); shot(p,"08_shop")
    p.get_by_role("tab",name="📝 Book wishlist").click(); wait(p)
    p.get_by_label("Book title").fill("Wonder"); p.get_by_label("Author (optional)").fill("R. J. Palacio")
    btn(p,"Add to my wishlist 📝").click(); wait(p); shot(p,"09_wishlist")
    logout(p)
    # Papa confirms
    login(p,"I'm Papa"); shot(p,"10_parent_banner")
    p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p); shot(p,"11_confirm")
    btn(p,"Confirm all").first.click(); wait(p,2000); shot(p,"12_confirmed")
    p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p)
    p.get_by_role("tab",name="🗓️ Her week").click(); wait(p); shot(p,"13_her_week")
    p.get_by_role("tab",name="🎁 Rewards").click(); wait(p); scroll(p,300); shot(p,"14_catalogue")
    p.get_by_role("tab",name="⚙️ XP rules").first.click(); wait(p); shot(p,"15_rules")
    link(p,"Her Routine"); shot(p,"16_parent_today",True)
    logout(p)
    # give her a pile of XP for the shop test
    d=json.load(open(DB)); kid=[x for x in d["profiles"] if x["role"]=="child"][0]["id"]
    d["xp_events"].append({"id":str(uuid.uuid4()),"user_id":kid,"amount":2000,"reason":"test top-up","created_at":"2026-10-19T00:00:00+00:00"})
    json.dump(d,open(DB,"w"))
    login(p,"I'm Siyonah"); shot(p,"17_home_after")
    link(p,"Reward Shop")
    btn(p,"🎯 Goal").nth(6).click(); wait(p)
    shot(p,"18_shop_goal")
    p.locator('.st-key-rw_5 button:has-text("Swap")').first.click(); wait(p,800)
    shot(p,"19_swap_pop")
    p.locator('[data-testid="stPopoverBody"] [data-testid="stSelectbox"]').first.click(); wait(p,500)
    p.get_by_role("option",name="Wonder by R. J. Palacio").click(); wait(p,600)
    btn(p,"Yes, swap it! 🎉").first.click(); wait(p,2000)
    p.get_by_role("tab",name="📦 My swaps").click(); wait(p); shot(p,"20_swaps")
    logout(p)
    login(p,"I'm Papa"); p.get_by_role("tab",name="🗓️ Routine & rewards").click(); wait(p)
    p.get_by_role("tab",name="🎁 Rewards").click(); wait(p)
    p.get_by_role("button",name="Given 🎁").first.click(); wait(p,600)
    btn(p,"Mark as given").first.click(); wait(p); logout(p)
    login(p,"I'm Siyonah"); link(p,"Reward Shop")
    p.get_by_role("tab",name="📚 My bookshelf").click(); wait(p); shot(p,"21_shelf")
    link(p,"My Stars"); shot(p,"22_stars",True)
    btn(p,"Log out").click(); wait(p,1500)
    p.set_viewport_size({"width":400,"height":860}); login(p,"I'm Siyonah"); shot(p,"23_mobile_home")
    p.locator('[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button').first.click(); wait(p)
    link(p,"My Routine"); shot(p,"24_mobile_routine")
    p.get_by_role("tab",name="🗓️ My week").click(); wait(p); shot(p,"25_mobile_week")
    print("ERRORS",len(errs))
