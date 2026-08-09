"""Klik link 'Video' di sidebar, amati halaman yang terbuka."""
import asyncio
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
SHOT = r"C:\Users\ASUS\AppData\Local\Temp\gemini_video_section.png"

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = browser.contexts[0].pages[0]
    links = await page.query_selector_all('a[aria-label="Video"]')
    print(f"link Video: {len(links)}")
    if links:
        await links[0].click()
        await page.wait_for_timeout(3000)
    print("URL:", page.url)
    print("TITLE:", await page.title())
    await page.screenshot(path=SHOT, full_page=False)
    print(f"SHOT: {SHOT}")
    await browser.close()
    await p.stop()

asyncio.run(main())
