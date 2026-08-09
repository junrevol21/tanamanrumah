"""Poll status generate video Gemini; kalau sudah siap, download otomatis ke file.
Cara pakai: python gemini_poll.py <output.mp4> [timeout_menit]
"""
import asyncio, sys, base64, os, time, traceback
from playwright.async_api import async_playwright
from gemini_tab import get_video_tab

CDP = "http://127.0.0.1:9222"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\veo_clips\clip1.mp4"
TIMEOUT_MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 10
MINCOUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 1  # jumlah video yg harus ada di percakapan

DETECT_JS = """
() => {
  const vids = [...document.querySelectorAll('video')].map(v => ({src: v.src || '', cur: v.currentSrc || ''})).filter(v => v.src || v.cur);
  const links = [...document.querySelectorAll('a[download], a[href*="download"], a[href*="videoplayback"]')].map(a => a.href);
  return {vids, links};
}
"""

FETCH_BLOB_JS = """
(url) => fetch(url).then(r => r.blob()).then(async b => {
  const buf = await b.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
})
"""

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = await get_video_tab(browser.contexts[0])
    deadline = time.time() + TIMEOUT_MIN * 60
    while time.time() < deadline:
        await page.wait_for_timeout(15000)
        state = await page.evaluate(DETECT_JS)
        if state["vids"] and len(state["vids"]) >= MINCOUNT:
            src = state["vids"][-1]["src"] or state["vids"][-1]["cur"]
            print(f"VIDEO_DETECTED src={src[:120]}")
            # coba unduh: kalau blob: fetch via JS
            try:
                if src.startswith("blob:"):
                    b64 = await page.evaluate(FETCH_BLOB_JS, src)
                    data = base64.b64decode(b64)
                    os.makedirs(os.path.dirname(OUT), exist_ok=True)
                    with open(OUT, "wb") as f:
                        f.write(data)
                    print(f"SAVED_BLOB: {OUT} ({len(data)} bytes)")
                else:
                    # pakai cookie browser context (context.request = cookie-aware)
                    resp = await page.context.request.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=180000)
                    data = await resp.body()
                    os.makedirs(os.path.dirname(OUT), exist_ok=True)
                    with open(OUT, "wb") as f:
                        f.write(data)
                    print(f"SAVED_HTTP: {OUT} ({len(data)} bytes) resp={resp.status}")
                await browser.close(); await p.stop(); return
            except Exception as e:
                print(f"DOWNLOAD_FAIL: {e}")
        else:
            txt = (await page.evaluate("() => document.body.innerText")).replace("\n", " | ")
            status = [s for s in txt.split("|") if any(k in s.lower() for k in ["video", "siap", "menit", "membuat"])]
            print(f"[{time.strftime('%H:%M:%S')}] " + (" | ".join(status[-4:]) if status else "menunggu..."))
    print("TIMEOUT — video belum siap dalam batas waktu")
    await browser.close()
    await p.stop()

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
