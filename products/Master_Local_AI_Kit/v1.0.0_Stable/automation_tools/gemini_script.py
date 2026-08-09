"""
Minta Gemini Omni (via browser) membuat script video terstruktur JSON:
segmen = [{veo_prompt (EN), overlay (ID), narasi (ID)}] + judul + deskripsi.
Cara pakai: python gemini_script.py "<topik>" [out.json]
"""
import asyncio, sys, json, re, os, time, traceback
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
TIMELAPSE = "--timelapse" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
TOPIC = ARGS[0] if len(ARGS) > 0 else ("A butterfly metamorphosis from caterpillar to butterfly" if TIMELAPSE else "Cara menyiram tanaman yang benar")
OUT = ARGS[1] if len(ARGS) > 1 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\scripts\auto_script.json"

PROMPT_TEMPLATE = """RESPOND ONLY WITH A SINGLE JSON OBJECT inside a ```json code block. NO other text, NO explanation, NO markdown outside the block. STRICTLY this schema:

```json
{
  "judul": "judul Indonesia, formula pain-point+benefit",
  "deskripsi": "deskripsi 2-3 kalimat + CTA",
  "segmen": [
    {
      "veo_prompt": "English cinematic Veo video prompt, 8-10s, landscape 16:9, photorealistic, detailed visual description",
      "overlay": "short Indonesian on-screen text, max 6 words",
      "narasi": "natural conversational Indonesian narration, 1-2 sentences"
    }
  ]
}
```

Rencana video YouTube (16:9 LANDSCAPE) 45-60 detik untuk channel tanaman rumah Indonesia. Topik: "{topic}". 4-6 segmen; segmen 1 = hook kuat; segmen terakhir = CTA subscribe/cek harga. Narasi natural seperti orang ngobrol. Output ONLY the JSON."""

TIMELAPSE_TEMPLATE = """RESPOND ONLY WITH A SINGLE JSON OBJECT inside a ```json code block. NO other text, NO explanation, NO markdown outside the block. STRICTLY this schema:

```json
{
  "judul": "English clickbait-ish title for the video",
  "deskripsi": "English 2-3 sentence description + CTA",
  "segmen": [
    {
      "veo_prompt": "English cinematic timelapse Veo video prompt, 8s, photorealistic, showing ONE progressive stage of the process in detail",
      "label": "Day 1"
    }
  ]
}
```

Plan a TIMELAPSE / process video (no narration, no talking — pure visuals + on-screen day/phase labels) for a GLOBAL YouTube audience. Topic: "{topic}". 18-24 segments covering the WHOLE process progressively (start -> middle stages -> final result). Each veo_prompt = ONE distinct stage, visually detailed, timelapse feel (e.g. "timelapse of...", "slowly..."). Each label = short English phase/day marker shown on screen (e.g. "Day 1", "Day 14", "Stage 3"). All text in ENGLISH. Output ONLY the JSON."""

JS_TEXT = "() => document.body.innerText"

def extract_json(text):
    # 1) blok kode json — ambil yang TERAKHIR (respons terbaru)
    blocks = re.findall(r"```(?:json|JSON)?\s*(\{.*?\})\s*```", text, re.S)
    if blocks:
        for b in reversed(blocks):
            try:
                return json.loads(b)
            except Exception:
                continue
    # 2) brace-matching dari { pertama (tahan nested braces)
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
    raise ValueError("JSON tidak ditemukan di respons")

async def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    # pakai TAB BARU supaya tidak mengganggu tab yang sedang generate video
    page = await ctx.new_page()
    await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(3000)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)

    prompt = (TIMELAPSE_TEMPLATE if TIMELAPSE else PROMPT_TEMPLATE).replace("{topic}", TOPIC)
    baseline = await page.evaluate(JS_TEXT)
    focused = await page.evaluate("""() => {
        const el = document.querySelector('div[contenteditable="true"]');
        if (el) { el.focus(); return true; }
        return false;
    }""")
    if not focused:
        print("NO_PROMPT_BOX")
        await browser.close(); await p.stop(); return
    await page.keyboard.type(prompt, delay=3)
    await page.keyboard.press("Enter")
    print("SENT. Menunggu respons Omni...")

    # poll sampai respons stabil & mengandung JSON (ambil teks SETELAH "Gemini berkata" terakhir)
    last_tail = ""
    stable = 0
    tail = ""
    deadline = time.time() + 180
    while time.time() < deadline:
        await page.wait_for_timeout(6000)
        txt = await page.evaluate(JS_TEXT)
        idx = txt.rfind("Gemini berkata")
        if idx == -1:
            continue  # respons belum mulai
        tail = txt[idx + len("Gemini berkata"):]
        if len(tail) > 200 and "segmen" in tail.lower() and ("```json" in tail.lower() or '"judul"' in tail.lower()):
            if tail == last_tail:
                stable += 1
            else:
                stable = 0
                last_tail = tail
            if stable >= 3:
                break
        else:
            stable = 0
            last_tail = tail
    print(f"TAIL_LEN={len(tail)} stable={stable}")
    try:
        data = extract_json(tail)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON_OK: {OUT}")
        print("JUDUL:", data.get("judul"))
        print(f"SEGMEN: {len(data.get('segmen', []))}")
        for i, s in enumerate(data.get("segmen", []), 1):
            txt_field = s.get("overlay") or s.get("label") or ""
            print(f"  {i}. text='{txt_field}'")
            print(f"     veo: {s.get('veo_prompt','')[:80]}")
    except Exception as e:
        print(f"PARSE_FAIL: {e}")
        raw = OUT.replace(".json", "_raw.txt")
        with open(raw, "w", encoding="utf-8") as f:
            f.write(tail[:5000])
        print(f"RAW disimpan: {raw}")
    await browser.close()
    await p.stop()

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
