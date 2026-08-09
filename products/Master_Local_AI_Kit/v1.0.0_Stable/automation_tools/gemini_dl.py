"""Unduh video Gemini via cookie browser context. Cari <video> di halaman lalu simpan.
Cara pakai: python gemini_dl.py <output.mp4>
"""
import asyncio, sys, os, base64, traceback
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\veo_clips\clip1.mp4"

DETECT_JS = """
() => {
  const vids = [...document.querySelectorAll('video')].map(v => v.src || v.currentSrc || '').filter(Boolean);
  return [...new Set(vids)];
}
"""

async def main():
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    page = browser.contexts[0].pages[0]
    srcs = await page.evaluate(DETECT_JS)
    if not srcs:
        print("NO_VIDEO_IN_PAGE")
        await browser.close(); await p.stop(); return
    src = srcs[-1]
    print("SRC:", src[:130])
    data = None
    if src.startswith("blob:"):
        b64 = await page.evaluate("""(url) => fetch(url).then(r => r.blob()).then(async b => {
            const buf = await b.arrayBuffer(); const bytes = new Uint8Array(buf);
            let bin=''; for (let i=0;i<bytes.length;i++) bin+=String.fromCharCode(bytes[i]);
            return btoa(bin);})""", src)
        data = base64.b64decode(b64)
    else:
        resp = await page.context.request.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=180000)
        data = await resp.body()
        print("RESP:", resp.status)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    # validasi: cek magic bytes ftyp
    magic = data[:12]
    print(f"SAVED: {OUT} ({len(data)} bytes) magic={magic}")
    await browser.close()
    await p.stop()

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
