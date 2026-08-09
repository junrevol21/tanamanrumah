"""
Orchestrator multi-akun Gemini Veo (7 profile Chrome, auto-switch saat kuota habis).
Cicil klip harian: tiap akun generate sampai kuotanya habis, lalu pindah akun berikutnya.

Cara pakai:
  python gemini_multi.py <prompts.json> [out_dir] [max_per_akun]
prompts.json: {"segmen": [{"veo_prompt": "..."}, ...]}  (format sama dgn gemini_script.py)

Log aktivitas ditulis ke <out_dir>/../multi_log.txt
"""
import asyncio, sys, json, os, base64, time, traceback
from playwright.async_api import async_playwright

ACCOUNTS = [
    ("chrome-veo", 9222), ("chrome-veo-2", 9223), ("chrome-veo-3", 9224),
    ("chrome-veo-4", 9225), ("chrome-veo-5", 9226), ("chrome-veo-6", 9227),
    ("chrome-veo-7", 9228),  # chrome-veo-8 (9229) belum login — tambah nanti kalau perlu
]
JS_VIDS = "() => [...new Set([...document.querySelectorAll('video')].map(v => v.src || v.currentSrc || '').filter(Boolean))]"
JS_TEXT = "() => document.body.innerText"

LOG = []
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state_multi.json")

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(st):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    LOG.append(line)
    print(line)

async def get_page(port):
    p = await async_playwright().start()
    b = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = b.contexts[0]
    pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
    if "gemini.google.com" not in pg.url:
        await pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(3000)
    return p, b, pg

async def ensure_section(pg):
    """Pastikan section 'Buat video' terbuka (klik link sidebar Video kalau belum)."""
    t = await pg.evaluate(JS_TEXT)
    # tutup popup consent/privacy kalau ada
    if "Persyaratan dan Pemberitahuan" in t or "Oke" in t:
        ok_btn = await pg.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')].filter(b => (b.innerText||'').trim() === 'Oke' || (b.innerText||'').trim() === 'OK' || (b.innerText||'').trim() === 'Okay');
            if (btns.length) { btns[btns.length-1].click(); return true; }
            return false;
        }""")
        if ok_btn:
            await pg.wait_for_timeout(2500)
    if "Buat video" not in t:
        links = await pg.query_selector_all('a[aria-label="Video"]')
        if links:
            await links[0].click(timeout=15000)
            await pg.wait_for_timeout(6000)
    return "Buat video" in (await pg.evaluate(JS_TEXT))

async def ensure_portrait(pg):
    """Pilih aspek Potret (9:16) di composer section video."""
    t = await pg.evaluate(JS_TEXT)
    if "Potret (9:16)" in t and "Lanskap (16:9)" not in t:
        return True  # sudah potret
    sel = await pg.evaluate("""() => {
        const btn = [...document.querySelectorAll('button')].find(el => (el.innerText||'').includes('Lanskap') || (el.innerText||'').includes('Potret'));
        if (btn) { btn.click(); return true; }
        return false;
    }""")
    await pg.wait_for_timeout(1500)
    opt = await pg.evaluate("""() => {
        const els = [...document.querySelectorAll('div, li')];
        for (const el of els) {
            const t = (el.innerText||'').trim();
            if (t === 'Potret (9:16)' && el.children.length <= 1) { el.click(); return true; }
        }
        return false;
    }""")
    await pg.wait_for_timeout(1500)
    return opt

async def submit_video(pg, prompt):
    """Di section video: ketik prompt polos (tanpa prefiks) + Enter."""
    ok = await pg.evaluate("""() => {
        const el = document.querySelector('div[contenteditable="true"]');
        if (el) { el.focus(); return true; }
        return false;
    }""")
    if not ok:
        return False
    await pg.keyboard.press("Control+a")
    await pg.keyboard.press("Delete")
    await pg.keyboard.type(prompt, delay=4)
    await pg.keyboard.press("Enter")
    return True

async def wait_video(pg, before_count, timeout_s=180):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        await pg.wait_for_timeout(12000)
        txt = await pg.evaluate(JS_TEXT)
        low = txt.lower()
        if ("limit resets" in low or "check your usage in settings" in low
                or "batas" in low and "video" in low and ("habis" in low or "mencapai" in low)
                or "tidak dapat membuat video" in low or "can't generate your video" in low):
            return "QUOTA"
        vids = await pg.evaluate(JS_VIDS)
        if len(vids) > before_count:
            return ("VIDEO", vids[-1])
    return "TIMEOUT"

async def download(page, src, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if src.startswith("blob:"):
        b64 = await page.evaluate("""(url) => fetch(url).then(r=>r.blob()).then(async b=>{
            const buf=await b.arrayBuffer(); const by=new Uint8Array(buf);
            let s=''; for(let i=0;i<by.length;i++) s+=String.fromCharCode(by[i]);
            return btoa(s);})""", src)
        data = base64.b64decode(b64)
    else:
        resp = await page.context.request.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=180000)
        data = await resp.body()
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data)

async def main():
    prompts_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\veo_clips"
    max_per_account = int(sys.argv[3]) if len(sys.argv) > 3 else 99
    with open(prompts_path, encoding="utf-8") as f:
        data = json.load(f)
    prompts = [s["veo_prompt"] for s in data["segmen"]]
    # buang spesifikasi aspek/panjang dari prompt (format vertikal sudah diatur section)
    import re as _re
    prompts = [_re.sub(r"(,?\s*(16:9|9:16|1:1|4:3)\s*(landscape|portrait|square)?,?\s*(8|10|15)\s*seconds?)|(,?\s*(landscape|portrait|square),?)|(,?\s*\d+\s*seconds?)", "", p, flags=_re.I) for p in prompts]
    prompts = [p.strip().rstrip(",").strip() for p in prompts]
    log(f"PROMPTS: {len(prompts)} | out={out_dir} | max/akun={max_per_account}")

    clips_dir = os.path.join(out_dir, "..", "multi_log.txt") if out_dir.endswith("veo_clips") else os.path.join(out_dir, "..", "multi_log.txt")
    usage = {}  # akun -> jumlah klip
    dead = set()  # akun bermasalah (skip di prompt berikutnya)
    # --- state harian + rotasi akun ---
    state = load_state()
    today = time.strftime("%Y-%m-%d")
    if state.get("date") != today:
        offset = (state.get("day_offset", 0) + 2) % len(ACCOUNTS)  # rotasi 2 akun/hari
        state = {"date": today, "usage": {}, "day_offset": offset}
        save_state(state)
    order = ACCOUNTS[state.get("day_offset", 0):] + ACCOUNTS[:state.get("day_offset", 0)]
    usage = state.get("usage", {})
    log(f"ROTASI hari ini: {[n for n, _ in order]} | usage: {usage}")
    # mulai nomor dari klip tertinggi yang sudah ada (hindari timpa clip1-3)
    existing = []
    try:
        existing = [int(f[4:-4]) for f in os.listdir(out_dir)
                    if f.startswith("clip") and f[4:-4].isdigit()]
    except OSError:
        pass
    clip_idx = (max(existing) if existing else 0) + 1
    log(f"nomor klip mulai dari {clip_idx}")
    for pi, prompt in enumerate(prompts, 1):
        log(f"=== PROMPT {pi}/{len(prompts)}: {prompt[:60]}...")
        done = False
        for name, port in order:
            if name in dead or usage.get(name, 0) >= max_per_account:
                continue
            log(f"  -> coba akun {name} (port {port}, sudah {usage.get(name,0)} klip)")
            try:
                p, b, pg = await get_page(port)
                sec = await ensure_section(pg)
                if not sec:
                    log("     section video tidak bisa dibuka, blacklist akun")
                    dead.add(name)
                    await b.close(); await p.stop()
                    continue
                por = await ensure_portrait(pg)
                if not por:
                    log("     pilihan Potret tidak ketemu, blacklist akun")
                    dead.add(name)
                    await b.close(); await p.stop()
                    continue
                before = len(await pg.evaluate(JS_VIDS))
                ok = await submit_video(pg, prompt)
                if not ok:
                    log("     prompt box tidak ketemu, blacklist akun")
                    dead.add(name)
                    await b.close(); await p.stop()
                    continue
                res = await wait_video(pg, before)
                if res == "QUOTA":
                    log(f"     QUOTA/ERROR di {name} — blacklist & pindah akun berikutnya")
                    dead.add(name)
                elif res == "TIMEOUT":
                    log(f"     TIMEOUT di {name} — blacklist & pindah akun berikutnya")
                    dead.add(name)
                else:
                    _, src = res
                    out_path = os.path.join(out_dir, f"clip{clip_idx}.mp4")
                    size = await download(pg, src, out_path)
                    usage[name] = usage.get(name, 0) + 1
                    log(f"     ✅ KLIP {clip_idx:02d} dari {name} ({size//1024} KB) -> {out_path}")
                    clip_idx += 1
                    done = True
                    await b.close(); await p.stop()
                    break
                await b.close(); await p.stop()
            except Exception as e:
                log(f"     ERROR {name}: {str(e)[:100]} — blacklist akun")
                dead.add(name)
        if not done:
            log("!!! SEMUA AKUN HABIS/ERROR — berhenti")
            break
    log(f"SELESAI. Total klip baru: {clip_idx-1}. Usage: {usage}")
    state["usage"] = usage
    save_state(state)
    with open(clips_dir, "a", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
