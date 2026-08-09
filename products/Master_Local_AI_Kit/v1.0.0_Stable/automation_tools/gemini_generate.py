"""Generate video di Gemini (section Buat video).
Cara pakai: python gemini_generate.py "<prompt>" [wait_detik]
"""
import asyncio, sys, traceback
from playwright.async_api import async_playwright
from gemini_tab import get_video_tab

CDP = "http://127.0.0.1:9222"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_gen_status.png"

async def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A cat playing with a ball of yarn"
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = await get_video_tab(browser.contexts[0])
    await page.wait_for_timeout(1000)
    # tutup kemungkinan dialog/iframe overlay
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(600)
    # fokus via JS (hindari actionability check playwright)
    focused = await page.evaluate("""() => {
        const el = document.querySelector('div[contenteditable="true"]');
        if (el) { el.focus(); return true; }
        return false;
    }""")
    if not focused:
        print("NO_PROMPT_BOX")
        await browser.close(); await p.stop(); return
    await page.wait_for_timeout(400)
    await page.keyboard.type(prompt, delay=8)
    await page.wait_for_timeout(400)
    await page.keyboard.press("Enter")
    print("SUBMITTED:", prompt[:60])
    await page.wait_for_timeout(wait * 1000)
    await page.screenshot(path=SHOT, full_page=False)
    body = await page.evaluate("() => document.body.innerText.slice(0, 1600)")
    print("=== PAGE TEXT ===")
    print(body.replace("\n", " | ")[:1300])
    print(f"SHOT: {SHOT}")
    await browser.close()
    await p.stop()

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
