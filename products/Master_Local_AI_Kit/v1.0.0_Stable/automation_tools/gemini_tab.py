"""Helper: dapatkan tab Gemini yang sedang di section Video (Buat video).
Kalau tidak ada, buka tab baru + masuk section Video.
Dipakai oleh gemini_generate.py & gemini_poll.py.
"""
import asyncio
from playwright.async_api import async_playwright

async def get_video_tab(ctx):
    for pg in ctx.pages:
        try:
            t = await pg.evaluate("() => document.body.innerText")
            if ("Lanskap" in t) or ("Buat video" in t):
                return pg
        except Exception:
            pass
    pg = await ctx.new_page()
    await pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=45000)
    await pg.wait_for_timeout(4000)
    try:
        links = await pg.query_selector_all('a[aria-label="Video"]')
        if links:
            await links[0].click()
            await pg.wait_for_timeout(2500)
    except Exception:
        pass
    return pg

async def main():
    p = await async_playwright().start()
    b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    pg = await get_video_tab(ctx)
    t = await pg.evaluate("() => document.body.innerText")
    ok = ("Lanskap" in t) or ("Buat video" in t)
    print(f"VIDEO_TAB_OK={ok} url={pg.url[-16:]}")
    await b.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(main())
