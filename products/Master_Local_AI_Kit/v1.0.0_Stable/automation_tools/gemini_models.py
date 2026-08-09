"""Dump semua elemen DOM yang teksnya mirip nama model (Flash/Pro/Omni/Veo/Lite/Ultra)."""
import asyncio
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_models2.png"

JS = """
() => {
  const out = [];
  const keys = ['flash','pro','omni','veo','lite','ultra','gambar','video','image'];
  const els = document.querySelectorAll('div, span, mat-option, li, button, p, h1, h2, h3');
  for (const el of els) {
    if (el.children.length > 3) continue; // hanya leaf-ish
    const t = (el.textContent || '').trim();
    if (!t || t.length > 120) continue;
    const low = t.toLowerCase();
    if (keys.some(k => low.includes(k))) {
      out.push({tag: el.tagName, role: el.getAttribute('role'), cls: (el.className||'').toString().slice(0,60), text: t.slice(0,100)});
    }
  }
  return out;
}
"""

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = browser.contexts[0].pages[0]
    # pastikan picker masih terbuka; kalau tidak, buka lagi
    res = await page.evaluate(JS)
    if not res:
        # buka model picker lewat tombol Flash
        for el in await page.query_selector_all('button'):
            try:
                if (await el.inner_text()).strip() == "Flash":
                    await el.click(); break
            except Exception: pass
        await page.wait_for_timeout(1200)
        res = await page.evaluate(JS)
    seen = set()
    for r in res:
        k = (r['tag'], r['text'])
        if k in seen: continue
        seen.add(k)
        print(f"{r['tag']}/{r['role'] or '-'} {r['text']}")
    await page.screenshot(path=SHOT, full_page=False)
    print(f"SHOT: {SHOT}")
    await browser.close()
    await p.stop()

asyncio.run(main())
