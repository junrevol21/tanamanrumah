"""Dump elemen interaktif di section Video (kotak prompt, tombol, chip contoh)."""
import asyncio
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_video_composer.png"

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = browser.contexts[0].pages[0]
    await page.wait_for_timeout(1000)
    print("=== ELEMEN INPUT/PROMPT ===")
    for sel in ['textarea', 'div[contenteditable="true"]', 'input[type="text"]', 'input:not([type])']:
        els = await page.query_selector_all(sel)
        print(f"  {sel}: {len(els)}")
        for el in els[:5]:
            r = await el.bounding_box()
            ph = await el.get_attribute("placeholder") or (await el.inner_text())[:40]
            print(f"    box={r} placeholder='{ph}'")
    print("=== TOMBOL (text pendek) ===")
    seen = set()
    for el in await page.query_selector_all('button, div[role="button"]'):
        try:
            t = (await el.inner_text()).strip()
            if t and t not in seen and len(t) < 40:
                seen.add(t)
                r = await el.bounding_box()
                print(f"  '{t}' box={r}")
        except Exception:
            pass
    await page.screenshot(path=SHOT, full_page=False)
    print(f"SHOT: {SHOT}")
    await browser.close()
    await p.stop()

asyncio.run(main())
