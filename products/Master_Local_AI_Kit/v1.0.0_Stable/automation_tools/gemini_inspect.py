"""Inspect Gemini UI: daftar elemen interaktif (tombol/menu) untuk menemukan model picker & fitur Veo."""
import asyncio, sys
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_ui.png"

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    await page.wait_for_timeout(1500)

    print("=== URL:", page.url)
    print("=== ELEMEN INTERAKTIF (text) ===")
    # kumpulkan tombol & elemen berperan tombol, dedup
    seen = set()
    for sel in ['button', 'div[role="button"]', '[data-test-id]', 'mat-button-toggle']:
        els = await page.query_selector_all(sel)
        for el in els[:80]:
            try:
                txt = (await el.inner_text()).strip()
                if not txt or txt in seen:
                    continue
                seen.add(txt)
                print(f"  [{sel}] {txt[:70]}")
            except Exception:
                pass
    # model picker: biasanya tombol di header dengan nama model
    print("=== CANDIDAT MODEL PICKER (teks pendek di header) ===")
    for el in await page.query_selector_all('button, div[role="button"]'):
        try:
            txt = (await el.inner_text()).strip()
            if txt and len(txt) < 30 and any(k in txt.lower() for k in ["gemini", "omni", "veo", "flash", "pro", "model"]):
                print(f"  -> {txt}")
        except Exception:
            pass
    await page.screenshot(path=SHOT, full_page=False)
    print(f"SHOT: {SHOT}")
    await browser.close()
    await p.stop()

asyncio.run(main())
