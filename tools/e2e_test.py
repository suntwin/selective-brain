"""End-to-end smoke test in demo mode (run streamlit first). Saves screenshots to /tmp/claude-0/shots."""
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("URL", "http://localhost:8501")
OUT = "/tmp/claude-0/shots"
os.makedirs(OUT, exist_ok=True)
errors = []


def wait(page, ms=1200):
    page.wait_for_timeout(ms)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def shot(page, name, full=True):
    page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    exc = page.locator('[data-testid="stException"]')
    if exc.count():
        errors.append((name, exc.first.inner_text()[:1500]))
        print("EXCEPTION on", name, exc.first.inner_text()[:1500])


def click(page, name, exact=False, nth=0):
    page.get_by_role("button", name=name, exact=exact).nth(nth).click()
    wait(page)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto(URL)
    wait(page, 3000)
    shot(page, "01_login")
    click(page, "I'm Siyonah")
    shot(page, "02_home_checkin")
    # check-in: pick Light
    page.locator('button:has-text("Light")').first.click(); wait(page)
    click(page, "Save check-in")
    shot(page, "03_home_after_checkin")
    click(page, "Start my drill")
    wait(page, 1500)
    shot(page, "04_drill_q1", full=False)
    # exam mode: answer everything, flag one, go back once, then check & submit
    n = 0
    reopened = False
    while n < 60:
        n += 1
        if page.get_by_role("button", name="Submit my drill ✅").count():
            shot(page, f"05_check_{n}")
            opn = page.get_by_role("button", name="Open ✏️")
            if not reopened and opn.count():
                reopened = True
                opn.first.click(); wait(page)
                shot(page, "05_reopened", full=False)
                click(page, "🚩 Unflag")
                page.locator('[class*="st-key-opt_"] button').nth(2).click(); wait(page)
                continue
            box = page.locator('[class*="st-key-submit_ok"] input')
            if box.count():
                page.locator('[class*="st-key-submit_ok"] label').first.click(); wait(page)
            click(page, "Submit my drill ✅")
            break
        if n == 2:
            click(page, "🚩 Flag to check")
            shot(page, "05_flagged", full=False)
        if n == 4 and page.get_by_role("button", name="◀ Back").count():
            click(page, "◀ Back")
            shot(page, "05_back_prefilled", full=False)
            click(page, "Next ▶")
        opts = page.locator('[class*="st-key-opt_"] button')
        num = page.locator('[class*="st-key-in_"] input')
        wrd = page.locator('[class*="st-key-w_"] input')
        txt = page.locator('textarea')
        if opts.count():
            opts.nth(1 if n % 2 else 0).click(); wait(page)
        elif num.count():
            num.first.fill("7"); click(page, "Save my answer 💾")
        elif wrd.count():
            for i in range(wrd.count()):
                wrd.nth(i).fill("5")
            click(page, "Save my answers 💾")
            if page.get_by_role("button", name="Next ▶").count() and page.get_by_role("button", name="Next ▶").is_enabled():
                click(page, "Next ▶")
        elif txt.count():
            txt.first.fill("The key glinted in the gutter. " * 12)
            click(page, "Save my writing 💾")
            if page.get_by_role("button", name="Next ▶").count() and page.get_by_role("button", name="Next ▶").is_enabled():
                click(page, "Next ▶")
        else:
            shot(page, f"stuck_{n}")
            break
    wait(page, 2500)
    shot(page, "06_review")
    # fix first mistake
    if page.locator('button:has-text("Careless slip")').count():
        page.locator('button:has-text("Careless slip")').first.click(); wait(page)
        page.get_by_placeholder("check the last line").first.fill("I will re-read the question before choosing")
        page.keyboard.press("Tab"); wait(page)
        click(page, "Save to my notebook")
        shot(page, "07_review_fixed")
    click(page, "My notebook 📒", exact=True)
    shot(page, "08_notebook")
    click(page, "Flip card")
    shot(page, "09_notebook_flipped")
    click(page, "I remembered")
    page.get_by_role("tab", name="All my cards").click(); wait(page)
    shot(page, "10_notebook_all")
    page.get_by_role("link", name="My Stars").click(); wait(page, 2500)
    shot(page, "11_stars")
    page.get_by_role("link", name="Home").click(); wait(page, 2000)
    shot(page, "12_home_after")
    click(page, "Log out")
    click(page, "I'm Papa")
    wait(page, 2500)
    shot(page, "13_parent_week")
    page.get_by_role("tab", name="Export to vault").click(); wait(page)
    shot(page, "14_parent_export")
    page.get_by_role("tab", name="Publish a drill").click(); wait(page)
    shot(page, "15_parent_publish")
    # mobile view of child home
    m = b.new_page(viewport={"width": 390, "height": 844})
    m.goto(URL); wait(m, 3000)
    m.get_by_role("button", name="I'm Siyonah").click(); wait(m, 2500)
    shot(m, "16_mobile_home")
    b.close()

print("ERRORS:", len(errors))
for e in errors:
    print(e)
sys.exit(1 if errors else 0)
