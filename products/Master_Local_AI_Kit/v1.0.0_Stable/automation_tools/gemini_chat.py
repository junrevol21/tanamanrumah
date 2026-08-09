"""
Helper: kirim prompt ke Gemini Omni via browser (chat biasa), ambil respons teks penuh.
Cara pakai: python gemini_chat.py "<prompt>" [out.txt] [--port N]
"""
import asyncio, sys, os, time, traceback
from playwright.async_api import async_playwright

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PORT = None
for a in sys.argv[1:]:
    if a.startswith("--port="):
        PORT = int(a.split("=")[1])
CDP = f"http://127.0.0.1:{PORT}" if PORT else "http://127.0.0.1:9222"
PROMPT = ARGS[0] if ARGS else "Halo"
OUT = ARGS[1] if len(ARGS) > 1 else None
JS_TEXT = "() => document.body.innerText"

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    page = await ctx.new_page()
    await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(3000)
    await page.keyboard.press("Escape")
    focused = await page.evaluate("""() => {
        const el = document.querySelector('div[contenteditable="true"]');
        if (el) { el.focus(); return true; }
        return false;
    }""")
    if not focused:
        print("NO_PROMPT_BOX")
        await browser.close(); await p.stop(); return
    await page.keyboard.type(PROMPT, delay=2)
    await page.keyboard.press("Enter")
    print("SENT")

    last_tail, stable, tail = "", 0, ""
    deadline = time.time() + 300
    while time.time() < deadline:
        await page.wait_for_timeout(6000)
        txt = await page.evaluate(JS_TEXT)
        idx = txt.rfind("Gemini berkata")
        if idx == -1:
            continue
        tail = txt[idx + len("Gemini berkata"):]
        if len(tail) > 150 and tail == last_tail:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
            last_tail = tail
    print(f"TAIL_LEN={len(tail)} stable={stable}")
    if OUT:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(tail)
        print(f"SAVED: {OUT}")
    else:
        print(tail[:1500])
    await browser.close()
    await p.stop()

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
