"""
Gemini web bridge via Chrome CDP (port 9222).
Kontrol gemini.google.com langsung di Chrome yang terlihat (session 1).

Cara pakai:
  python gemini_cdp.py status          -> cek login + screenshot
  python gemini_cdp.py open            -> buka gemini.google.com
  python gemini_cdp.py send "<teks>"   -> ketik & kirim prompt ke chat Gemini (model aktif)
  python gemini_cdp.py shot            -> screenshot halaman aktif ke Temp
"""
import asyncio, sys, time
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
GEMINI = "https://gemini.google.com"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_state.png"

async def connect():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
    pages = ctx.pages
    if not pages:
        page = await ctx.new_page()
    else:
        page = pages[0]
    return p, browser, ctx, page

async def get_state(page):
    state = {"url": page.url, "title": await page.title()}
    cookies = await page.context.cookies("https://www.google.com")
    sid = [c["name"] for c in cookies if c["name"] in ("SID", "__Secure-1PSID", "SAPISID")]
    state["google_login"] = bool(sid)
    state["cookies"] = sid
    # deteksi UI Gemini: tombol "Sign in" vs area chat
    try:
        signin = await page.query_selector('a[href*="ServiceLogin"], a[href*="accounts.google"], button:has-text("Sign in")')
        state["signin_button"] = signin is not None
    except Exception:
        state["signin_button"] = None
    return state

async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    p, browser, ctx, page = await connect()
    try:
        if cmd == "open":
            await page.goto(GEMINI, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(4000)
        elif cmd == "status":
            if "gemini.google.com" not in page.url:
                await page.goto(GEMINI, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(4000)
        elif cmd == "send":
            text = sys.argv[2]
            if "gemini.google.com" not in page.url:
                await page.goto(GEMINI, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(4000)
            # fokus ke prompt box
            box = await page.query_selector('div.ql-editor, div[contenteditable="true"], textarea')
            if not box:
                print("PROMPT_BOX_NOT_FOUND")
                return
            await box.click()
            await box.type(text, delay=15)
            await page.keyboard.press("Enter")
            print("SENT_OK")
        elif cmd == "shot":
            pass
        await page.wait_for_timeout(2500)
        st = await get_state(page)
        print(f"URL: {st['url']}")
        print(f"TITLE: {st['title']}")
        print(f"GOOGLE_LOGIN: {st['google_login']}  cookies={st['cookies']}")
        print(f"SIGNIN_BUTTON: {st['signin_button']}")
        await page.screenshot(path=SHOT, full_page=False)
        print(f"SHOT: {SHOT}")
    finally:
        await browser.close()
        await p.stop()

asyncio.run(main())
