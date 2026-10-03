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
    n = 0
    while n < 40:
        n += 1
        if page.get_by_role("button", name="See my results").count():
            click(page, "See my results")
            break
        if page.get_by_role("button", name="Next question").count():
            click(page, "Next question")
            continue
        if n == 3 and page.get_by_role("button", name="Skip for now").count():
            click(page, "Skip for now")
            continue
        opts = page.locator('[class*="st-key-opt_"] button')
        if opts.count() == 0:
            shot(page, f"stuck_{n}")
            break
        # alternate: pick B on odd, A on even (mix of right/wrong)
        idx = 1 if n % 2 else 0
        opts.nth(idx).click()
        wait(page)
        if n == 2:
            shot(page, "05_feedback", full=False)
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
