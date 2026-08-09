"""
Launch Chrome profile khusus Gemini + tunggu login (cookie SID) sampai berhasil.
Cara pakai: python gemini_login_profile.py <nama_profile> <port> [timeout_menit]
  contoh:  python gemini_login_profile.py chrome-veo-2 9223 10
"""
import asyncio, sys, subprocess, time, traceback
from playwright.async_api import async_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = r"C:\Users\ASUS\AppData\Local\hermes"
GEMINI = "https://gemini.google.com/app"

def launch(profile, port):
    udd = rf"{BASE}\{profile}"
    args = [CHROME, f"--remote-debugging-port={port}", f"--user-data-dir={udd}",
            "--no-first-run", "--no-default-browser-check", GEMINI]
    subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    print(f"LAUNCHED profile={profile} port={port}")

async def check_login(port):
    p = await async_playwright().start()
    try:
        b = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = b.contexts[0]
        cookies = await ctx.cookies("https://www.google.com")
        sid = [c["name"] for c in cookies if c["name"] in ("SID", "__Secure-1PSID", "SAPISID")]
        await b.close()
        return bool(sid)
    finally:
        await p.stop()

async def main():
    profile, port = sys.argv[1], sys.argv[2]
    timeout_min = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    launch(profile, port)
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        await asyncio.sleep(10)
        try:
            if await check_login(port):
                print(f"LOGGED_IN profile={profile} port={port}")
                return
            else:
                print(f"[{time.strftime('%H:%M:%S')}] menunggu login...")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] cek gagal (chrome mungkin baru mulai): {str(e)[:60]}")
    print("TIMEOUT — login belum selesai. Jalankan ulang script ini untuk cek ulang.")

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
